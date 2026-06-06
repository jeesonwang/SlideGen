from enum import Enum

from slidegen.core.config import settings


class ImageProvider(Enum):
    PEXELS = "pexels"
    PIXABAY = "pixabay"
    GEMINI_FLASH = "gemini_flash"
    GPT_IMAGE = "gpt-image"


def is_pexels_selected() -> bool:
    return ImageProvider.PEXELS == get_selected_image_provider()


def is_pixabay_selected() -> bool:
    return ImageProvider.PIXABAY == get_selected_image_provider()


def is_gemini_flash_selected() -> bool:
    return ImageProvider.GEMINI_FLASH == get_selected_image_provider()


def is_gpt_image_selected() -> bool:
    return ImageProvider.GPT_IMAGE == get_selected_image_provider()


def get_selected_image_provider() -> ImageProvider | None:
    """
    Get the selected image provider from environment variables.
    Returns:
        ImageProvider: The selected image provider.
    """
    if settings.IMAGE_PROVIDER:
        return ImageProvider(settings.IMAGE_PROVIDER)
    return None


def get_image_provider_api_key() -> str | None:
    selected_image_provider = get_selected_image_provider()
    if selected_image_provider == ImageProvider.PEXELS:
        return settings.PEXELS_API_KEY
    elif selected_image_provider == ImageProvider.PIXABAY:
        return settings.PIXABAY_API_KEY
    elif selected_image_provider == ImageProvider.GEMINI_FLASH:
        return settings.GOOGLE_API_KEY
    elif selected_image_provider == ImageProvider.GPT_IMAGE:
        return settings.OPENAI_API_KEY
    else:
        raise ValueError(f"Invalid image provider: {selected_image_provider}")
