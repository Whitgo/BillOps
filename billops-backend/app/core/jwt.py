from datetime import datetime, timedelta, timezone
from typing import Any
import jwt

from app.config.settings import get_settings

settings = get_settings()


def encode_jwt(
    payload: dict[str, Any],
    expires_delta: timedelta | None = None,
    algorithm: str = "HS256",
) -> str:
    """
    Encode a JWT token.
    
    Args:
        payload: The payload to encode.
        expires_delta: The token expiration time. Defaults to 24 hours.
        algorithm: The algorithm to use for signing. Defaults to HS256.
        
    Returns:
        The encoded JWT token.
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=settings.jwt_expiration_hours)
    
    expire = datetime.now(timezone.utc) + expires_delta
    payload.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    
    encoded_jwt = jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=algorithm,
    )
    return encoded_jwt


def decode_jwt(token: str, algorithm: str = "HS256") -> dict[str, Any]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: The JWT token to decode.
        algorithm: The algorithm used to sign the token. Defaults to HS256.
        
    Returns:
        The decoded payload.
        
    Raises:
        jwt.InvalidTokenError: If the token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise jwt.InvalidTokenError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")
