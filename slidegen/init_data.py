"""
Initial data setup for the application.
Creates the first superuser if it doesn't exist.
"""
import logging

from slidegen.core.config import settings
from slidegen.core.database import AsyncSessionLocal, async_engine
from slidegen.models import Base
from slidegen.models.user import UserCreate
from slidegen.services.user.auth import UserCenter

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Initialize database tables."""
    async with async_engine.begin() as conn:
        # Create all tables if they don't exist
        # Note: In production, use Alembic migrations instead
        await conn.run_sync(Base.metadata.create_all)


async def create_first_superuser() -> None:
    """
    Create the first superuser if it doesn't exist.
    Uses configuration from settings.FIRST_SUPERUSER and settings.FIRST_SUPERUSER_PASSWORD.
    """
    async with AsyncSessionLocal() as session:
        try:
            user_center = UserCenter(session)

            # Check if superuser already exists
            existing_user = await user_center.get_user_by_username_or_email(
                username=settings.FIRST_SUPERUSER
            )

            if existing_user:
                if existing_user.is_superuser:
                    logger.info(
                        f"Superuser already exists: {settings.FIRST_SUPERUSER}"
                    )
                else:
                    logger.warning(
                        f"User {settings.FIRST_SUPERUSER} exists but is not a superuser"
                    )
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
            raise


async def init_app_data() -> None:
    """
    Initialize application data on startup.
    This function is called during the application lifespan.
    """
    logger.info("Initializing application data...")

    try:
        # Initialize database tables (if not using Alembic)
        # await init_db()

        # Create first superuser
        await create_first_superuser()

        logger.info("Application data initialization completed")
    except Exception as e:
        logger.error(f"Failed to initialize application data: {e}")
        # Don't raise - allow app to start even if initialization fails
