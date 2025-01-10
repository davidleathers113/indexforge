"""Supabase client dependency."""

from typing import AsyncGenerator

from fastapi import Depends
from supabase.client import AsyncClient, create_client

from src.api.config.settings import settings


async def get_supabase_client() -> AsyncGenerator[AsyncClient, None]:
    """Get Supabase client."""
    client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY,
    )
    try:
        yield client
    finally:
        await client.aclose()
