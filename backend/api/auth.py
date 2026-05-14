"""
Authentication API routes.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    TokenRefreshRequest,
    TokenRefreshResponse,
    UserResponse,
)
from config.settings import settings
from middleware.auth import get_current_user
from mysql_module.auth import (
    create_user,
    get_user_by_email,
    get_user_by_phone,
    get_user_by_username,
)
from mysql_module.dao import async_session
from utils.security import create_access_token, create_refresh_token, decode_token

router = APIRouter(prefix="/api/auth", tags=["authentication"])

security = HTTPBearer()


@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    """
    Register a new user.
    """
    # Validate passwords match
    if req.password != req.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Check if username already exists
    async with async_session() as session:
        # Check username
        existing_user = await get_user_by_username(session, req.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check email (if provided)
        if req.email:
            existing_email = await get_user_by_email(session, req.email)
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Check phone (if provided)
        if req.phone:
            existing_phone = await get_user_by_phone(session, req.phone)
            if existing_phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone already registered"
                )
        
        # Create user
        user = await create_user(
            session=session,
            username=req.username,
            email=req.email,
            phone=req.phone,
            password=req.password,
            role="user"
        )
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone": user.phone,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """
    Login user with username/email/phone and password.
    """
    async with async_session() as session:
        # Authenticate user
        from mysql_module.auth import authenticate_user
        
        user = await authenticate_user(
            session=session,
            login_type=req.login_type,
            identifier=req.username or req.email or req.phone,
            password=req.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email/phone or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone": user.phone,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(req: TokenRefreshRequest):
    """
    Refresh access token using refresh token.
    """
    # Decode refresh token
    payload = decode_token(req.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user to verify still active
    async with async_session() as session:
        from mysql_module.auth import get_user_by_id
        
        user = await get_user_by_id(session, int(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current user information.
    """
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "phone": current_user["phone"],
        "role": current_user["role"],
        "is_active": current_user["is_active"],
        "created_at": None  # Will be filled from database if needed
    }
