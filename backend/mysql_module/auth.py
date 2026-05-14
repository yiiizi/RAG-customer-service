"""
Authentication-related database operations.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mysql_module.models import User
from utils.security import hash_password, verify_password


async def create_user(
    session: AsyncSession,
    username: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    password: str = None,
    role: str = "user"
) -> User:
    """Create a new user."""
    password_hash = hash_password(password)
    
    user = User(
        username=username,
        email=email,
        phone=phone,
        password_hash=password_hash,
        role=role,
        is_active=True
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    return user


async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
    """Get user by username."""
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """Get user by email."""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_phone(session: AsyncSession, phone: str) -> Optional[User]:
    """Get user by phone."""
    result = await session.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID."""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def authenticate_user(
    session: AsyncSession,
    login_type: str,
    identifier: str,
    password: str
) -> Optional[User]:
    """Authenticate user with username/email/phone and password."""
    
    # Get user based on login type
    if login_type == "username":
        user = await get_user_by_username(session, identifier)
    elif login_type == "email":
        user = await get_user_by_email(session, identifier)
    elif login_type == "phone":
        user = await get_user_by_phone(session, identifier)
    else:
        return None
    
    # Verify password
    if user and verify_password(password, user.password_hash):
        return user
    
    return None


async def update_user_password(session: AsyncSession, user_id: int, new_password: str) -> bool:
    """Update user's password."""
    user = await get_user_by_id(session, user_id)
    if not user:
        return False
    
    user.password_hash = hash_password(new_password)
    await session.commit()
    return True


async def update_user_role(session: AsyncSession, user_id: int, new_role: str) -> bool:
    """Update user's role (admin only)."""
    user = await get_user_by_id(session, user_id)
    if not user:
        return False
    
    user.role = new_role
    await session.commit()
    return True


async def deactivate_user(session: AsyncSession, user_id: int) -> bool:
    """Deactivate a user (soft delete)."""
    user = await get_user_by_id(session, user_id)
    if not user:
        return False
    
    user.is_active = False
    await session.commit()
    return True
