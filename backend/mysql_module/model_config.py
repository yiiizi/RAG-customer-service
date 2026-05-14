"""
User model configuration related database operations.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mysql_module.models import UserModelConfig
from utils.encryption import decrypt_api_key, encrypt_api_key


async def create_model_config(
    session: AsyncSession,
    user_id: int,
    provider: str,
    model_name: str,
    api_key: str,
    base_url: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    is_default: bool = False
) -> UserModelConfig:
    """Create a new model configuration."""
    # Encrypt API key
    api_key_encrypted = encrypt_api_key(api_key)
    
    # If this is set as default, unset other defaults for this user
    if is_default:
        await _unset_other_defaults(session, user_id)
    
    model_config = UserModelConfig(
        user_id=user_id,
        provider=provider,
        model_name=model_name,
        api_key_encrypted=api_key_encrypted,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        is_default=is_default
    )
    
    session.add(model_config)
    await session.commit()
    await session.refresh(model_config)
    
    return model_config


async def get_model_config(
    session: AsyncSession,
    config_id: int,
    user_id: Optional[int] = None
) -> Optional[UserModelConfig]:
    """Get a model configuration by ID, optionally filtered by user_id."""
    query = select(UserModelConfig).where(UserModelConfig.id == config_id)
    
    if user_id is not None:
        query = query.where(UserModelConfig.user_id == user_id)
    
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_user_model_configs(
    session: AsyncSession,
    user_id: int
) -> List[UserModelConfig]:
    """Get all model configurations for a user."""
    query = (
        select(UserModelConfig)
        .where(UserModelConfig.user_id == user_id)
        .order_by(UserModelConfig.created_at.desc())
    )
    
    result = await session.execute(query)
    return result.scalars().all()


async def get_default_model_config(
    session: AsyncSession,
    user_id: int
) -> Optional[UserModelConfig]:
    """Get the default model configuration for a user."""
    query = (
        select(UserModelConfig)
        .where(UserModelConfig.user_id == user_id)
        .where(UserModelConfig.is_default == True)
    )
    
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_global_default_model_config(
    session: AsyncSession,
) -> Optional[UserModelConfig]:
    """Get the globally selected default model configuration."""
    query = (
        select(UserModelConfig)
        .where(UserModelConfig.is_default == True)
        .order_by(UserModelConfig.updated_at.desc())
        .limit(1)
    )
    
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def update_model_config(
    session: AsyncSession,
    config_id: int,
    user_id: int,
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    is_default: Optional[bool] = None
) -> Optional[UserModelConfig]:
    """Update a model configuration."""
    model_config = await get_model_config(session, config_id, user_id)
    
    if not model_config:
        return None
    
    # Update fields if provided
    if provider is not None:
        model_config.provider = provider
    
    if model_name is not None:
        model_config.model_name = model_name
    
    if api_key is not None:
        model_config.api_key_encrypted = encrypt_api_key(api_key)
    
    if base_url is not None:
        model_config.base_url = base_url
    
    if temperature is not None:
        model_config.temperature = temperature
    
    if max_tokens is not None:
        model_config.max_tokens = max_tokens
    
    if is_default is not None:
        if is_default:
            # Unset other defaults for this user
            await _unset_other_defaults(session, user_id, exclude_id=config_id)
        model_config.is_default = is_default
    
    await session.commit()
    await session.refresh(model_config)
    
    return model_config


async def delete_model_config(
    session: AsyncSession,
    config_id: int,
    user_id: int
) -> bool:
    """Delete a model configuration."""
    model_config = await get_model_config(session, config_id, user_id)
    
    if not model_config:
        return False
    
    await session.delete(model_config)
    await session.commit()
    
    return True


async def _unset_other_defaults(
    session: AsyncSession,
    user_id: int,
    exclude_id: Optional[int] = None
) -> None:
    """Unset is_default for all other model configs of the user."""
    from sqlalchemy import update
    
    query = (
        update(UserModelConfig)
        .where(UserModelConfig.user_id == user_id)
        .values(is_default=False)
    )
    
    if exclude_id is not None:
        query = query.where(UserModelConfig.id != exclude_id)
    
    await session.execute(query)
    await session.commit()


def mask_api_key(encrypted_api_key: str) -> str:
    """Mask an encrypted API key for display (return as-is for security)."""
    # For security, we don't decrypt the key for display
    # Just return a masked version
    if not encrypted_api_key:
        return ""
    
    # Return a placeholder indicating the key exists
    return "••••••••" + encrypted_api_key[-4:] if len(encrypted_api_key) > 4 else "••••••••"


async def get_decrypted_api_key(
    session: AsyncSession,
    config_id: int,
    user_id: int
) -> Optional[str]:
    """Get the decrypted API key for a model configuration."""
    model_config = await get_model_config(session, config_id, user_id)
    
    if not model_config:
        return None
    
    return decrypt_api_key(model_config.api_key_encrypted)
