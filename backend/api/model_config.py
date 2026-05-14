"""
User model configuration API routes.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    ModelConfigCreateRequest,
    ModelConfigListResponse,
    ModelConfigResponse,
    ModelConfigUpdateRequest,
)
from middleware.auth import get_current_admin_user
from mysql_module.dao import get_session
from mysql_module.model_config import (
    create_model_config,
    delete_model_config,
    get_default_model_config,
    get_model_config,
    get_user_model_configs,
    mask_api_key,
    update_model_config,
)
from utils.encryption import decrypt_api_key

router = APIRouter(prefix="/api/model-configs", tags=["model-configs"])

@router.post("", response_model=ModelConfigResponse)
async def create_config(
    req: ModelConfigCreateRequest,
    current_user: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new model configuration.
    """
    model_config = await create_model_config(
        session=session,
        user_id=current_user["id"],
        provider=req.provider,
        model_name=req.model_name,
        api_key=req.api_key,
        base_url=req.base_url,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
        is_default=req.is_default
    )
    
    # Return masked API key
    return {
        "id": model_config.id,
        "user_id": model_config.user_id,
        "provider": model_config.provider,
        "model_name": model_config.model_name,
        "api_key_masked": mask_api_key(model_config.api_key_encrypted),
        "base_url": model_config.base_url,
        "temperature": model_config.temperature,
        "max_tokens": model_config.max_tokens,
        "is_default": model_config.is_default,
        "created_at": model_config.created_at.isoformat() if model_config.created_at else "",
        "updated_at": model_config.updated_at.isoformat() if model_config.updated_at else "",
    }


@router.get("", response_model=ModelConfigListResponse)
async def get_configs(
    current_user: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get all model configs for current user.
    """
    configs = await get_user_model_configs(
        session=session,
        user_id=current_user["id"]
    )
    
    items = [
        {
            "id": config.id,
            "user_id": config.user_id,
            "provider": config.provider,
            "model_name": config.model_name,
            "api_key_masked": mask_api_key(config.api_key_encrypted),
            "base_url": config.base_url,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "is_default": config.is_default,
            "created_at": config.created_at.isoformat() if config.created_at else "",
            "updated_at": config.updated_at.isoformat() if config.updated_at else "",
        }
        for config in configs
    ]
    
    return {
        "items": items,
        "total": len(items)
    }


@router.get("/default", response_model=ModelConfigResponse)
async def get_default_config(
    current_user: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get the default model config for current admin.
    """
    model_config = await get_default_model_config(
        session=session,
        user_id=current_user["id"]
    )
    
    if not model_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到默认模型配置"
        )
    
    return {
        "id": model_config.id,
        "user_id": model_config.user_id,
        "provider": model_config.provider,
        "model_name": model_config.model_name,
        "api_key_masked": mask_api_key(model_config.api_key_encrypted),
        "base_url": model_config.base_url,
        "temperature": model_config.temperature,
        "max_tokens": model_config.max_tokens,
        "is_default": model_config.is_default,
        "created_at": model_config.created_at.isoformat() if model_config.created_at else "",
        "updated_at": model_config.updated_at.isoformat() if model_config.updated_at else "",
    }


@router.get("/{config_id}", response_model=ModelConfigResponse)
async def get_config(
    config_id: int,
    current_user: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get a single model config by ID.
    """
    model_config = await get_model_config(
        session=session,
        config_id=config_id,
        user_id=current_user["id"]
    )
    
    if not model_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型配置未找到"
        )
    
    return {
        "id": model_config.id,
        "user_id": model_config.user_id,
        "provider": model_config.provider,
        "model_name": model_config.model_name,
        "api_key_masked": mask_api_key(model_config.api_key_encrypted),
        "base_url": model_config.base_url,
        "temperature": model_config.temperature,
        "max_tokens": model_config.max_tokens,
        "is_default": model_config.is_default,
        "created_at": model_config.created_at.isoformat() if model_config.created_at else "",
        "updated_at": model_config.updated_at.isoformat() if model_config.updated_at else "",
    }


@router.put("/{config_id}", response_model=ModelConfigResponse)
async def update_config(
    config_id: int,
    req: ModelConfigUpdateRequest,
    current_user: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Update a model config.
    """
    # Prepare update parameters
    update_params = {}
    
    if req.provider is not None:
        update_params["provider"] = req.provider
    
    if req.model_name is not None:
        update_params["model_name"] = req.model_name
    
    if req.api_key is not None:
        update_params["api_key"] = req.api_key
    
    if req.base_url is not None:
        update_params["base_url"] = req.base_url
    
    if req.temperature is not None:
        update_params["temperature"] = req.temperature
    
    if req.max_tokens is not None:
        update_params["max_tokens"] = req.max_tokens
    
    if req.is_default is not None:
        update_params["is_default"] = req.is_default
    
    # Update config
    model_config = await update_model_config(
        session=session,
        config_id=config_id,
        user_id=current_user["id"],
        **update_params
    )
    
    if not model_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型配置未找到"
        )
    
    return {
        "id": model_config.id,
        "user_id": model_config.user_id,
        "provider": model_config.provider,
        "model_name": model_config.model_name,
        "api_key_masked": mask_api_key(model_config.api_key_encrypted),
        "base_url": model_config.base_url,
        "temperature": model_config.temperature,
        "max_tokens": model_config.max_tokens,
        "is_default": model_config.is_default,
        "created_at": model_config.created_at.isoformat() if model_config.created_at else "",
        "updated_at": model_config.updated_at.isoformat() if model_config.updated_at else "",
    }


@router.delete("/{config_id}")
async def delete_config(
    config_id: int,
    current_user: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a model config.
    """
    success = await delete_model_config(
        session=session,
        config_id=config_id,
        user_id=current_user["id"]
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型配置未找到"
        )
    
    return {"status": "success", "message": "模型配置已删除"}


@router.post("/{config_id}/set-default", response_model=ModelConfigResponse)
async def set_default_config(
    config_id: int,
    current_user: dict = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Set a model config as default.
    """
    # Get config
    model_config = await get_model_config(
        session=session,
        config_id=config_id,
        user_id=current_user["id"]
    )
    
    if not model_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型配置未找到"
        )
    
    # Set as default
    from mysql_module.model_config import _unset_other_defaults
    
    await _unset_other_defaults(session, current_user["id"], exclude_id=config_id)
    
    model_config.is_default = True
    await session.commit()
    await session.refresh(model_config)
    
    return {
        "id": model_config.id,
        "user_id": model_config.user_id,
        "provider": model_config.provider,
        "model_name": model_config.model_name,
        "api_key_masked": mask_api_key(model_config.api_key_encrypted),
        "base_url": model_config.base_url,
        "temperature": model_config.temperature,
        "max_tokens": model_config.max_tokens,
        "is_default": model_config.is_default,
        "created_at": model_config.created_at.isoformat() if model_config.created_at else "",
        "updated_at": model_config.updated_at.isoformat() if model_config.updated_at else "",
    }

