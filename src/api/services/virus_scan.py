"""Virus scanning service using ClamAV."""

import asyncio
import logging
from typing import Union

import clamd
from fastapi import HTTPException, UploadFile, status

logger = logging.getLogger(__name__)


class VirusScanService:
    """Service for scanning files for viruses using ClamAV."""

    def __init__(self, host: str = "localhost", port: int = 3310):
        """Initialize the virus scanning service.

        Args:
            host: ClamAV daemon host
            port: ClamAV daemon port
        """
        self.host = host
        self.port = port
        self._cd = None

    async def _get_clamd(self) -> clamd.ClamdAsyncNetworkSocket:
        """Get or create ClamAV connection.

        Returns:
            ClamAV async network socket
        """
        if not self._cd:
            try:
                self._cd = clamd.ClamdAsyncNetworkSocket(host=self.host, port=self.port)
                await self._cd.ping()
            except Exception as e:
                logger.error(f"Failed to connect to ClamAV: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Virus scanning service unavailable",
                )
        return self._cd

    async def scan_file(self, file: Union[UploadFile, bytes]) -> bool:
        """Scan a file for viruses.

        Args:
            file: File to scan (UploadFile or bytes)

        Returns:
            True if file is clean, False if infected

        Raises:
            HTTPException: If scanning fails
        """
        try:
            cd = await self._get_clamd()

            if isinstance(file, UploadFile):
                content = await file.read()
                # Reset file position for subsequent reads
                await file.seek(0)
            else:
                content = file

            # Scan the file content
            scan_result = await cd.instream(content)

            # Parse scan results
            if scan_result and scan_result.get("stream"):
                status = scan_result["stream"][0]
                if status == "OK":
                    return True
                else:
                    logger.warning(f"Virus found in file: {status}")
                    return False

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="File scanning failed"
            )

        except Exception as e:
            logger.error(f"Error during virus scan: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="File scanning failed"
            )

    async def scan_files(self, files: list[UploadFile]) -> dict[str, bool]:
        """Scan multiple files for viruses.

        Args:
            files: List of files to scan

        Returns:
            Dictionary mapping filenames to scan results
        """
        results = {}
        for file in files:
            results[file.filename] = await self.scan_file(file)
        return results
