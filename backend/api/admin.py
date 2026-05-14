"""
Admin API routes for user management.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import UserResponse
from config.settings import settings
from middleware.auth import get_current_admin_user, get_current_user
from mysql_module.auth import (
    create_user,
    deactivate_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_phone,
    get_user_by_username,
    update_user_password,
    update_user_role,
)
from mysql_module.dao import get_session
from mysql_module.models import User

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/users", response_model=List[UserResponse])
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get paginated list of all users (admin only).
    """
    from sqlalchemy import func, select
    
    # Get total count
    total = await session.execute(select(func.count()).select_from(User))
    total = total.scalar_one()
    
    # Get paginated users
    offset = (page - 1) * page_size
    result = await session.execute(
        select(User)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    users = result.scalars().all()
    
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        for user in users
    ]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get a single user by ID (admin only).
    """
    user = await get_user_by_id(session, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.put("/users/{user_id}/role")
async def update_user_role_endpoint(
    user_id: int,
    new_role: str,
    current_user: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Update a user's role (admin only).
    """
    if new_role not in ["user", "staff", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'user', 'staff' or 'admin'"
        )
    
    success = await update_user_role(session, user_id, new_role)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"status": "success", "message": f"User role updated to {new_role}"}


@router.put("/users/{user_id}/deactivate")
async def deactivate_user_endpoint(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Deactivate a user (admin only).
    """
    # Prevent admin from deactivating themselves
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    success = await deactivate_user(session, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"status": "success", "message": "User deactivated"}


@router.put("/users/{user_id}/activate")
async def activate_user_endpoint(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Activate a user (admin only).
    """
    user = await get_user_by_id(session, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    await session.commit()
    
    return {"status": "success", "message": "User activated"}


@router.delete("/users/{user_id}")
async def delete_user_endpoint(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a user (admin only).
    """
    # Prevent admin from deleting themselves
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = await get_user_by_id(session, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await session.delete(user)
    await session.commit()
    
    return {"status": "success", "message": "User deleted"}
