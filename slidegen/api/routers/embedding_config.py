import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from loguru import logger
from sqlmodel import col, func, select

from slidegen.api.deps import CurrentUser, SessionDep
from slidegen.exceptions import NotFoundError, ParamsCheckError
from slidegen.models.embedding_config import (
    DEFAULT_EMBEDDING_CONFIGS,
    EmbeddingConfigCreate,
    EmbeddingConfigModel,
    EmbeddingConfigPublic,
    EmbeddingConfigsPublic,
    EmbeddingConfigUpdate,
    EmbeddingProvider,
)
from slidegen.models.user import Message
from slidegen.schemas.embedding_config import (
    EMBEDDING_PROVIDER_INFO,
    AvailableEmbeddingModels,
    EmbeddingConfigTest,
    EmbeddingConfigTestResult,
    EmbeddingProvidersInfo,
)
from slidegen.services.factories.embedding_factory import EmbeddingFactory

router = APIRouter()


def _is_masked_secret(value: str | None) -> bool:
    if value is None:
        return False
    return bool(value) and value.startswith("***")


@router.get("/providers", response_model=EmbeddingProvidersInfo)
async def get_providers() -> EmbeddingProvidersInfo:
    """Get all supported embedding providers information"""
    return EmbeddingProvidersInfo(providers=list(EMBEDDING_PROVIDER_INFO.values()))


@router.get("/providers/{provider}/models", response_model=AvailableEmbeddingModels)
async def get_provider_models(provider: EmbeddingProvider) -> AvailableEmbeddingModels:
    """Get available models for a specific provider"""
    if provider not in DEFAULT_EMBEDDING_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Provider {provider} does not have preset model configurations")

    models = DEFAULT_EMBEDDING_CONFIGS[provider]
    return AvailableEmbeddingModels(provider=provider, models=models)


@router.post("/test", response_model=EmbeddingConfigTestResult)
async def test_embedding_config(
    config: EmbeddingConfigTest,
    session: SessionDep,
    current_user: CurrentUser,
) -> EmbeddingConfigTestResult:
    """Test if the embedding configuration is valid"""
    if config.config_id and (not config.api_key or _is_masked_secret(config.api_key)):
        stored_config = await session.get(EmbeddingConfigModel, config.config_id)
        if not stored_config or stored_config.user_id != current_user.id:
            raise NotFoundError("Configuration not found")

        config = config.model_copy(update={"api_key": stored_config.api_key})

    # First validate configuration basic parameters
    is_valid, error_msg = EmbeddingFactory.validate_config(config)
    if not is_valid:
        return EmbeddingConfigTestResult(success=False, error=error_msg)

    # Perform actual test
    result = await EmbeddingFactory.test_embedding_config(config)
    return result


@router.get("/", response_model=EmbeddingConfigsPublic)
async def get_embedding_configs(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> EmbeddingConfigsPublic:
    """Get list of embedding configurations for the current user"""
    count_statement = (
        select(func.count()).select_from(EmbeddingConfigModel).where(EmbeddingConfigModel.user_id == current_user.id)
    )
    count = (await session.execute(count_statement)).scalar_one()

    statement = (
        select(EmbeddingConfigModel)
        .where(EmbeddingConfigModel.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(col(EmbeddingConfigModel.is_default).desc(), col(EmbeddingConfigModel.create_time).desc())
    )
    configs = (await session.execute(statement)).scalars().all()

    return EmbeddingConfigsPublic(data=configs, count=count)


@router.post("/", response_model=EmbeddingConfigPublic)
async def create_embedding_config(
    *, session: SessionDep, current_user: CurrentUser, config_in: EmbeddingConfigCreate
) -> Any:
    """Create new embedding configuration"""
    # Validate configuration
    is_valid, error_msg = EmbeddingFactory.validate_config(config_in)
    if not is_valid:
        logger.warning(f"Invalid embedding config for user {current_user.id}: {error_msg}")
        raise ParamsCheckError(error_msg)

    # If set as default configuration, cancel other default configurations
    if config_in.is_default:
        # Cancel other default configurations for the current user
        statement = select(EmbeddingConfigModel).where(
            EmbeddingConfigModel.user_id == current_user.id, EmbeddingConfigModel.is_default
        )
        existing_defaults = (await session.execute(statement)).scalars().all()
        for default_config in existing_defaults:
            default_config.is_default = False
            session.add(default_config)

    # Create configuration
    config = EmbeddingConfigModel.model_validate(
        {
            **config_in.model_dump(),
            "user_id": current_user.id,
        }
    )
    session.add(config)
    await session.commit()
    await session.refresh(config)

    logger.info(
        f"Created embedding config {config.id} for user {current_user.id}: {config.provider} - {config.model_id}"
    )

    return config


@router.get("/{config_id}", response_model=EmbeddingConfigPublic)
async def get_embedding_config(session: SessionDep, current_user: CurrentUser, config_id: uuid.UUID) -> Any:
    """Get specified embedding configuration"""
    config = await session.get(EmbeddingConfigModel, config_id)
    if not config:
        raise NotFoundError("Configuration not found")

    if config.user_id != current_user.id:
        raise NotFoundError("Configuration not found")

    return config


@router.patch("/{config_id}", response_model=EmbeddingConfigPublic)
async def update_embedding_config(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    config_id: uuid.UUID,
    config_in: EmbeddingConfigUpdate,
) -> Any:
    """Update embedding configuration"""
    config = await session.get(EmbeddingConfigModel, config_id)
    if not config:
        raise NotFoundError("Configuration not found")

    if config.user_id != current_user.id:
        raise NotFoundError("Configuration not found")

    # If set as default configuration, cancel other default configurations
    if config_in.is_default:
        statement = select(EmbeddingConfigModel).where(
            EmbeddingConfigModel.user_id == current_user.id,
            EmbeddingConfigModel.is_default,
            EmbeddingConfigModel.id != config_id,
        )
        existing_defaults = (await session.execute(statement)).scalars().all()
        for default_config in existing_defaults:
            default_config.is_default = False
            session.add(default_config)

    # Update configuration
    config_data = config_in.model_dump(exclude_unset=True)
    if "api_key" in config_data and _is_masked_secret(config_data["api_key"]):
        config_data.pop("api_key")
    config.sqlmodel_update(config_data)

    # Validate updated configuration
    is_valid, error_msg = EmbeddingFactory.validate_config(config)
    if not is_valid:
        raise ParamsCheckError(error_msg)

    session.add(config)
    await session.commit()
    await session.refresh(config)

    return config


@router.delete("/{config_id}", response_model=Message)
async def delete_embedding_config(session: SessionDep, current_user: CurrentUser, config_id: uuid.UUID) -> Message:
    """Delete embedding configuration"""
    config = await session.get(EmbeddingConfigModel, config_id)
    if not config:
        raise NotFoundError("Configuration not found")

    if config.user_id != current_user.id:
        raise NotFoundError("Configuration not found")

    await session.delete(config)
    await session.commit()

    logger.info(f"Deleted embedding config {config_id} for user {current_user.id}")

    return Message(message="Configuration deleted successfully")


@router.post("/{config_id}/set-default", response_model=Message)
async def set_default_embedding_config(session: SessionDep, current_user: CurrentUser, config_id: uuid.UUID) -> Message:
    """Set default embedding configuration"""
    config = await session.get(EmbeddingConfigModel, config_id)
    if not config:
        raise NotFoundError("Configuration not found")

    if config.user_id != current_user.id:
        raise NotFoundError("Configuration not found")

    # Cancel other default configurations for the current user
    statement = select(EmbeddingConfigModel).where(
        EmbeddingConfigModel.user_id == current_user.id, EmbeddingConfigModel.is_default
    )
    existing_defaults = (await session.execute(statement)).scalars().all()
    for default_config in existing_defaults:
        default_config.is_default = False
        session.add(default_config)

    # Set new default configuration
    config.is_default = True
    session.add(config)
    await session.commit()

    return Message(message="Default configuration set successfully")


@router.get("/default/current", response_model=EmbeddingConfigPublic | None)
async def get_default_embedding_config(session: SessionDep, current_user: CurrentUser) -> Any:
    """Get default embedding configuration for the current user"""
    statement = select(EmbeddingConfigModel).where(
        EmbeddingConfigModel.user_id == current_user.id,
        EmbeddingConfigModel.is_default,
        EmbeddingConfigModel.is_active,
    )
    config = (await session.execute(statement)).scalars().first()

    return config
