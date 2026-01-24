from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for JWT payload."""
    sub: str  # subject (user ID)
    exp: int  # expiration time
    iat: int  # issued at
    role: str  # user role


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str
