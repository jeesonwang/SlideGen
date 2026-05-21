from typing import Any, cast

import httpx


class BaseFactory:
    """Shared helpers for provider-backed factories."""

    @staticmethod
    async def _request_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return cast(dict[str, Any], response.json())
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip()
            raise ValueError(
                f"Model discovery failed with status {exc.response.status_code}: {detail or exc.response.reason_phrase}"
            ) from exc
        except httpx.RequestError as exc:
            raise ValueError(f"Model discovery request failed: {exc!s}") from exc
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("Model discovery returned invalid JSON") from exc

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        return base_url.rstrip("/")
