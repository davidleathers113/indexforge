"""Authentication infrastructure for IndexForge.

This module provides core authentication functionality including:
- User authentication and session management
- Password hashing and verification
- Token generation and validation
- Rate limiting and brute force protection
"""

import asyncio
from datetime import datetime, timedelta
import hashlib
import hmac
import secrets
import time
from uuid import UUID, uuid4

import jwt
from pydantic import BaseModel, EmailStr, SecretStr, validator

from src.core.errors import SecurityError


class AuthenticationError(SecurityError):
    """Base class for authentication errors."""


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid."""

    def __init__(self, message: str = "Invalid credentials provided"):
        super().__init__(message)


class TokenExpiredError(AuthenticationError):
    """Raised when authentication token has expired."""

    def __init__(self, message: str = "Authentication token has expired"):
        super().__init__(message)


class RateLimitExceededError(AuthenticationError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded, please try again later"):
        super().__init__(message)


class User(BaseModel):
    """User model with authentication details."""

    id: UUID
    email: EmailStr
    password_hash: str
    salt: str
    is_active: bool = True
    last_login: datetime | None = None
    failed_attempts: int = 0
    lockout_until: datetime | None = None

    @validator("password_hash")
    def validate_password_hash(cls, v: str) -> str:
        """Validate password hash format.

        Args:
            v: Password hash to validate

        Returns:
            Validated password hash

        Raises:
            ValueError: If hash format is invalid
        """
        if not v or len(v) != 128:  # SHA-512 hex length
            raise ValueError("Invalid password hash format")
        return v


class AuthConfig(BaseModel):
    """Authentication configuration."""

    secret_key: SecretStr
    token_expiry: int = 3600  # 1 hour in seconds
    max_failed_attempts: int = 5
    lockout_duration: int = 900  # 15 minutes in seconds
    rate_limit_window: int = 60  # 1 minute in seconds
    rate_limit_max_requests: int = 30
    min_password_length: int = 12
    require_special_chars: bool = True
    require_numbers: bool = True
    require_uppercase: bool = True
    require_lowercase: bool = True


class AuthenticationManager:
    """Manages user authentication and session handling."""

    def __init__(self, config: AuthConfig):
        """Initialize authentication manager.

        Args:
            config: Authentication configuration
        """
        self.config = config
        self._rate_limits: dict[str, set[float]] = {}
        self._lock = asyncio.Lock()

    def _check_rate_limit(self, key: str) -> None:
        """Check if rate limit is exceeded.

        Args:
            key: Rate limit key (e.g. IP address)

        Raises:
            RateLimitExceededError: If rate limit is exceeded
        """
        now = time.time()
        window_start = now - self.config.rate_limit_window

        # Clean old entries
        if key in self._rate_limits:
            self._rate_limits[key] = {ts for ts in self._rate_limits[key] if ts > window_start}
        else:
            self._rate_limits[key] = set()

        # Check limit
        if len(self._rate_limits[key]) >= self.config.rate_limit_max_requests:
            raise RateLimitExceededError()

        # Add timestamp
        self._rate_limits[key].add(now)

    def _hash_password(self, password: str, salt: str | None = None) -> tuple[str, str]:
        """Hash password with salt using PBKDF2-HMAC-SHA512.

        Args:
            password: Password to hash
            salt: Optional salt (generated if not provided)

        Returns:
            Tuple of (password_hash, salt)
        """
        if not salt:
            salt = secrets.token_hex(32)

        key = hashlib.pbkdf2_hmac(
            "sha512",
            password.encode(),
            salt.encode(),
            100000,  # Iterations
            dklen=64,  # Key length
        )
        return key.hex(), salt

    def _verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against stored hash.

        Args:
            password: Password to verify
            password_hash: Stored password hash
            salt: Stored salt

        Returns:
            True if password matches, False otherwise
        """
        test_hash, _ = self._hash_password(password, salt)
        return hmac.compare_digest(test_hash, password_hash)

    def _generate_token(self, user_id: UUID) -> str:
        """Generate JWT authentication token.

        Args:
            user_id: User ID to include in token

        Returns:
            JWT token string
        """
        now = datetime.utcnow()
        payload = {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(seconds=self.config.token_expiry),
        }
        return jwt.encode(
            payload,
            self.config.secret_key.get_secret_value(),
            algorithm="HS512",
        )

    def _validate_token(self, token: str) -> UUID:
        """Validate JWT token and return user ID.

        Args:
            token: JWT token to validate

        Returns:
            User ID from token

        Raises:
            TokenExpiredError: If token has expired
            AuthenticationError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.config.secret_key.get_secret_value(),
                algorithms=["HS512"],
            )
            return UUID(payload["sub"])
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError()
        except (jwt.InvalidTokenError, ValueError) as e:
            raise AuthenticationError(f"Invalid token: {e!s}")

    def validate_password_strength(self, password: str) -> None:
        """Validate password meets strength requirements.

        Args:
            password: Password to validate

        Raises:
            ValueError: If password does not meet requirements
        """
        if len(password) < self.config.min_password_length:
            raise ValueError(
                f"Password must be at least {self.config.min_password_length} characters"
            )

        if self.config.require_special_chars and not any(
            c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password
        ):
            raise ValueError("Password must contain at least one special character")

        if self.config.require_numbers and not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one number")

        if self.config.require_uppercase and not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")

        if self.config.require_lowercase and not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter")

    async def create_user(self, email: str, password: str) -> User:
        """Create new user with given credentials.

        Args:
            email: User email
            password: User password

        Returns:
            Created user object

        Raises:
            ValueError: If password does not meet requirements
        """
        self.validate_password_strength(password)

        password_hash, salt = self._hash_password(password)
        return User(
            id=uuid4(),
            email=email,
            password_hash=password_hash,
            salt=salt,
        )

    async def authenticate(self, user: User, password: str, request_key: str) -> str:
        """Authenticate user with password and generate token.

        Args:
            user: User to authenticate
            password: Password to verify
            request_key: Key for rate limiting (e.g. IP address)

        Returns:
            JWT authentication token

        Raises:
            InvalidCredentialsError: If credentials are invalid
            RateLimitExceededError: If rate limit is exceeded
        """
        async with self._lock:
            self._check_rate_limit(request_key)

            # Check if account is locked
            if user.lockout_until and user.lockout_until > datetime.utcnow():
                raise InvalidCredentialsError(f"Account is locked until {user.lockout_until}")

            # Verify password
            if not self._verify_password(password, user.password_hash, user.salt):
                user.failed_attempts += 1

                # Check if should lock account
                if user.failed_attempts >= self.config.max_failed_attempts:
                    user.lockout_until = datetime.utcnow() + timedelta(
                        seconds=self.config.lockout_duration
                    )

                raise InvalidCredentialsError()

            # Reset failed attempts on successful login
            user.failed_attempts = 0
            user.last_login = datetime.utcnow()

            return self._generate_token(user.id)

    async def validate_authentication(self, token: str) -> UUID:
        """Validate authentication token.

        Args:
            token: JWT token to validate

        Returns:
            User ID from token

        Raises:
            TokenExpiredError: If token has expired
            AuthenticationError: If token is invalid
        """
        return self._validate_token(token)
