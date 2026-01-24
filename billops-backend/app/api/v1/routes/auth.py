from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.hashing import hash_password, verify_password
from app.core.jwt import encode_jwt, decode_jwt
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, RefreshTokenRequest
from app.schemas.user import UserCreate, UserResponse, UserLogin

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(
    user_data: UserCreate,
    db: Session = Depends(get_db),
) -> dict:
    """
    Register a new user.
    
    Args:
        user_data: User registration data.
        db: Database session.
        
    Returns:
        Access and refresh tokens.
        
    Raises:
        HTTPException: If user already exists.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        name=user_data.name,
        role="member",
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate tokens
    access_token = encode_jwt(
        {"sub": str(new_user.id), "role": new_user.role}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": None,
        "token_type": "bearer",
    }


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
) -> dict:
    """
    Authenticate a user and return tokens.
    
    Args:
        credentials: User login credentials.
        db: Database session.
        
    Returns:
        Access and refresh tokens.
        
    Raises:
        HTTPException: If credentials are invalid.
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Generate access token
    access_token = encode_jwt(
        {"sub": str(user.id), "role": user.role}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": None,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Refresh an access token.
    
    Args:
        request: Refresh token request.
        db: Database session.
        
    Returns:
        New access token.
        
    Raises:
        HTTPException: If refresh token is invalid.
    """
    try:
        payload = decode_jwt(request.refresh_token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        # Generate new access token
        new_access_token = encode_jwt(
            {"sub": str(user.id), "role": user.role}
        )
        
        return {
            "access_token": new_access_token,
            "refresh_token": None,
            "token_type": "bearer",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {str(e)}",
        )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get information about the current authenticated user.
    
    Args:
        current_user: The current authenticated user.
        
    Returns:
        User information.
    """
    return current_user
