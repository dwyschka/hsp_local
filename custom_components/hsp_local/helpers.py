"""Helpers for the Haas+Sohn local integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, Concatenate

from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .entity import HspLocalEntity
from .hsp_client import HspAuthError, HspConnectionError, HspError


def hsp_exception_handler(
    func: Callable[Concatenate[HspLocalEntity, Any], Awaitable[Any]],
) -> Callable[Concatenate[HspLocalEntity, Any], Awaitable[None]]:
    """Translate client errors into HomeAssistantError exceptions."""

    @wraps(func)
    async def handler(entity: HspLocalEntity, *args: Any, **kwargs: Any) -> None:
        try:
            await func(entity, *args, **kwargs)
        except HspAuthError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="authentication_error",
            ) from err
        except HspConnectionError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="communication_error",
                translation_placeholders={"error": str(err)},
            ) from err
        except HspError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="unknown_error",
                translation_placeholders={"error": str(err)},
            ) from err

    return handler
