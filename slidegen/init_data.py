"""
Initial data setup for the application.
Creates the first superuser if it doesn't exist.
"""

from loguru import logger

from slidegen.core.config import settings
from slidegen.core.database import AsyncSessionLocal
from slidegen.models.user import UserCreate
from slidegen.services.user.auth import UserCenter


async def create_first_superuser() -> None:
    """
    Create the first superuser if it doesn't exist.
    Uses configuration from settings.FIRST_SUPERUSER and settings.FIRST_SUPERUSER_PASSWORD.
    """
    async with AsyncSessionLocal() as session:
        try:
            user_center = UserCenter(session)

            # Check if superuser already exists
            existing_user = await user_center.get_user_by_username_or_email(username=settings.FIRST_SUPERUSER)

            if existing_user:
                if existing_user.is_superuser:
                    logger.info(f"Superuser already exists: {settings.FIRST_SUPERUSER}")
                else:
                    logger.warning(f"User {settings.FIRST_SUPERUSER} exists but is not a superuser")
                return

            # Create the superuser
            user_create = UserCreate(
                email=settings.FIRST_SUPERUSER,
                username=settings.FIRST_SUPERUSER,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                is_superuser=True,
                is_active=True,
            )

            user = await user_center.create_user(user_create)
            logger.info(f"First superuser created successfully: {user.email}")

        except Exception as e:
            logger.error(f"Error creating first superuser: {e}")
            raise e


async def init_app_data() -> None:
    """
    Initialize application data on startup.
    This function is called during the application lifespan.
    """
    logger.info("Initializing application data...")

    try:
        # Initialize database tables (if not using Alembic)
        # from slidegen.core.database import init_models
        # from slidegen.models.base import Base

        # await init_models(Base)

        # Create first superuser
        await create_first_superuser()
        # Ensure output directory exists
        settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Application data initialization completed")
    except Exception as e:
        logger.error(f"Failed to initialize application data: {e}")
        raise e
