import uuid
from typing import Any

from fastapi import APIRouter
from loguru import logger
from sqlmodel import col, func, select

from slidegen.api.deps import CurrentUser, SessionDep
from slidegen.exceptions import NotFoundError, ParamsCheckError
from slidegen.models.llm_config import (
    LLMConfigCreate,
    LLMConfigModel,
    LLMConfigPublic,
    LLMConfigsPublic,
    LLMConfigUpdate,
    LLMProvider,
)
from slidegen.models.user import Message
from slidegen.schemas.llm_config import (
    PROVIDER_INFO,
    AvailableModels,
    LLMConfigTest,
    LLMConfigTestResult,
    LLMModelsFetchRequest,
    LLMProvidersInfo,
)
from slidegen.services.factories.llm_factory import LLMFactory

router = APIRouter()


@router.get("/providers", response_model=LLMProvidersInfo)
async def get_providers() -> Any:
    """Get all supported LLM providers information"""
    return LLMProvidersInfo(providers=list(PROVIDER_INFO.values()))


@router.post("/test", response_model=LLMConfigTestResult)
async def test_llm_config(config: LLMConfigTest) -> Any:
    """Test if the LLM configuration is valid"""
    # 首先验证配置基本参数
    is_valid, error_msg = LLMFactory.validate_config(config)
    if not is_valid:
        return LLMConfigTestResult(success=False, error=error_msg)

    # Perform actual test
    result = await LLMFactory.test_llm_config(config)
    return result


@router.post("/fetch-models", response_model=AvailableModels)
async def fetch_models(config: LLMModelsFetchRequest) -> Any:
    """Fetch available models using the current provider configuration"""
    models = await LLMFactory.fetch_available_models(config)
    return models


@router.get("/", response_model=LLMConfigsPublic)
async def get_llm_configs(session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100) -> Any:
    """Get list of LLM configurations for the current user"""
    count_statement = select(func.count()).select_from(LLMConfigModel).where(LLMConfigModel.user_id == current_user.id)
    count = (await session.execute(count_statement)).scalar_one()

    statement = (
        select(LLMConfigModel)
        .where(LLMConfigModel.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(col(LLMConfigModel.is_default).desc(), col(LLMConfigModel.create_time).desc())
    )
    configs = (await session.execute(statement)).scalars().all()

    return LLMConfigsPublic(data=configs, count=count)


@router.post("/", response_model=LLMConfigPublic)
async def create_llm_config(*, session: SessionDep, current_user: CurrentUser, config_in: LLMConfigCreate) -> Any:
    """Create new LLM configuration"""
    # Validate configuration
    is_valid, error_msg = LLMFactory.validate_config(config_in)
    if not is_valid:
        logger.warning(f"Invalid LLM config for user {current_user.id}: {error_msg}")
        raise ParamsCheckError(error_msg)

    # Set user ID
    config_in.user_id = current_user.id

    # If set as default configuration, cancel other default configurations
    if config_in.is_default:
        # Cancel other default configurations for the current user
        statement = select(LLMConfigModel).where(LLMConfigModel.user_id == current_user.id, LLMConfigModel.is_default)
        existing_defaults = (await session.execute(statement)).scalars().all()
        for default_config in existing_defaults:
            default_config.is_default = False
            session.add(default_config)

    # Create configuration
    config = LLMConfigModel.model_validate(config_in)
    session.add(config)
    await session.commit()
    await session.refresh(config)

    logger.info(f"Created LLM config {config.id} for user {current_user.id}: {config.provider} - {config.model_id}")

    return config


@router.get("/{config_id}", response_model=LLMConfigPublic)
async def get_llm_config(session: SessionDep, current_user: CurrentUser, config_id: uuid.UUID) -> Any:
    """Get specified LLM configuration"""
    config = await session.get(LLMConfigModel, config_id)
    if not config:
        raise NotFoundError("Configuration not found")

    if config.user_id != current_user.id:
        raise NotFoundError("Configuration not found")

    return config


@router.patch("/{config_id}", response_model=LLMConfigPublic)
async def update_llm_config(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    config_id: uuid.UUID,
    config_in: LLMConfigUpdate,
) -> Any:
    """Update LLM configuration"""
    config = await session.get(LLMConfigModel, config_id)
    if not config:
        raise NotFoundError("Configuration not found")

    if config.user_id != current_user.id:
        raise NotFoundError("Configuration not found")

    # If set as default configuration, cancel other default configurations
    if config_in.is_default:
        statement = select(LLMConfigModel).where(
            LLMConfigModel.user_id == current_user.id, LLMConfigModel.is_default, LLMConfigModel.id != config_id
        )
        existing_defaults = (await session.execute(statement)).scalars().all()
        for default_config in existing_defaults:
            default_config.is_default = False
            session.add(default_config)

    # Update configuration
    config_data = config_in.model_dump(exclude_unset=True)
    config.sqlmodel_update(config_data)

    # Validate updated configuration
    is_valid, error_msg = LLMFactory.validate_config(config)
    if not is_valid:
        raise ParamsCheckError(error_msg)

    session.add(config)
    await session.commit()
    await session.refresh(config)

    return config


@router.delete("/{config_id}", response_model=Message)
async def delete_llm_config(session: SessionDep, current_user: CurrentUser, config_id: uuid.UUID) -> Any:
    """Delete LLM configuration"""
    config = await session.get(LLMConfigModel, config_id)
    if not config:
        raise NotFoundError("Configuration not found")

    if config.user_id != current_user.id:
        raise NotFoundError("Configuration not found")

    await session.delete(config)
    await session.commit()

    logger.info(f"Deleted LLM config {config_id} for user {current_user.id}")

    return Message(message="Configuration deleted successfully")


@router.post("/{config_id}/set-default", response_model=Message)
async def set_default_llm_config(session: SessionDep, current_user: CurrentUser, config_id: uuid.UUID) -> Any:
    """Set default LLM configuration"""
    config = await session.get(LLMConfigModel, config_id)
    if not config:
        raise NotFoundError("Configuration not found")

    if config.user_id != current_user.id:
        raise NotFoundError("Configuration not found")

    # Cancel other default configurations for the current user
    statement = select(LLMConfigModel).where(LLMConfigModel.user_id == current_user.id, LLMConfigModel.is_default)
    existing_defaults = (await session.execute(statement)).scalars().all()
    for default_config in existing_defaults:
        default_config.is_default = False
        session.add(default_config)

    # Set new default configuration
    config.is_default = True
    session.add(config)
    await session.commit()

    return Message(message="Default configuration set successfully")


@router.get("/default/current", response_model=LLMConfigPublic | None)
async def get_default_llm_config(session: SessionDep, current_user: CurrentUser) -> Any:
    """Get default LLM configuration for the current user"""
    statement = select(LLMConfigModel).where(
        LLMConfigModel.user_id == current_user.id, LLMConfigModel.is_default, LLMConfigModel.is_active
    )
    config = (await session.execute(statement)).scalars().first()

    return config
