import asyncio
import os
import uuid
from collections.abc import Awaitable, Callable
from urllib.parse import quote_plus

import aiohttp
from google import genai
from google.genai.types import GenerateContentConfig
from loguru import logger
from openai import AsyncOpenAI

from slidegen.models.image_asset import ImageAsset
from slidegen.schemas.image_prompt import ImagePrompt
from slidegen.workflows.utils.download_helpers import download_file
from slidegen.workflows.utils.get_env import get_pexels_api_key_env, get_pixabay_api_key_env
from slidegen.workflows.utils.image_provider import (
    is_dalle3_selected,
    is_gemini_flash_selected,
    is_pexels_selected,
    is_pixabay_selected,
)


class ImageGenerator:
    def __init__(self, output_directory: str) -> None:
        self.output_directory = output_directory
        self.image_gen_func = self.get_image_gen_func()

    def get_image_gen_func(self) -> Callable[..., Awaitable[str]] | None:
        if is_pixabay_selected():
            return self.get_image_from_pixabay
        elif is_pexels_selected():
            return self.get_image_from_pexels
        elif is_gemini_flash_selected():
            return self.generate_image_google
        elif is_dalle3_selected():
            return self.generate_image_openai
        return None

    def is_stock_provider_selected(self) -> bool:
        return is_pexels_selected() or is_pixabay_selected()

    async def generate_image(self, prompt: ImagePrompt) -> ImageAsset:
        """
        Generates an image based on the provided prompt.
        - If no image generation function is available, returns a placeholder image.
        - If the stock provider is selected, it uses the prompt directly,
        otherwise it uses the full image prompt with theme.
        - Output Directory is used for saving the generated image not the stock provider.
        """
        if not self.image_gen_func:
            logger.info("No image generation function found. Using placeholder image.")
            return ImageAsset(path="/static/images/placeholder.jpg")

        image_prompt = prompt.get_image_prompt(with_theme=not self.is_stock_provider_selected())
        logger.info(f"Request - Generating Image for {image_prompt}")

        try:
            image_path = await self.image_gen_func(image_prompt, self.output_directory)
            if image_path:
                if os.path.exists(image_path):
                    return ImageAsset(
                        path=image_path,
                        extras={
                            "prompt": prompt.prompt,
                            "theme_prompt": prompt.theme_prompt,
                        },
                    )
            raise Exception(f"Image not found at {image_path}")

        except Exception as e:
            logger.info(f"Error generating image: {e!s}")
            return ImageAsset(path="/static/images/placeholder.jpg")

    async def generate_image_openai(self, prompt: str, output_directory: str) -> str:
        client = AsyncOpenAI()
        result = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            quality="standard",
            size="1024x1024",
        )
        image_url = result.data[0].url
        if not image_url:
            raise Exception("Image URL not found")
        return await download_file(image_url, output_directory)

    async def generate_image_google(self, prompt: str, output_directory: str) -> str:
        client = genai.Client()
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.0-flash-preview-image-generation",
            contents=prompt,
            config=GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
        )

        for part in response.candidates[0].content.parts:  # type: ignore
            if part.text is not None:
                logger.info(part.text)
            elif part.inline_data is not None:
                image_path = os.path.join(output_directory, f"{uuid.uuid4()}.jpg")
                with open(image_path, "wb") as f:
                    f.write(part.inline_data.data)  # type: ignore

        return image_path

    async def get_image_from_pexels(self, prompt: str, output_directory: str) -> str:
        async with aiohttp.ClientSession(trust_env=True) as session:
            response = await session.get(
                f"https://api.pexels.com/v1/search?query={quote_plus(prompt)}&per_page=1",
                headers={"Authorization": f"{get_pexels_api_key_env()}"},
            )
            data = await response.json()
            try:
                image_url = data["photos"][0]["src"]["large"]
            except Exception:
                logger.exception("Pexels response parsing failed or no result")
                raise
            return await download_file(image_url, output_directory)

    async def get_image_from_pixabay(self, prompt: str, output_directory: str) -> str:
        async with aiohttp.ClientSession(trust_env=True) as session:
            response = await session.get(
                f"https://pixabay.com/api/?key={get_pixabay_api_key_env()}&q={quote_plus(prompt)}&image_type=photo&per_page=3"
            )
            data = await response.json()
            try:
                image_url = data["hits"][0]["largeImageURL"]
            except Exception:
                logger.exception("Pixabay response parsing failed or no result")
                raise
            return await download_file(image_url, output_directory)
