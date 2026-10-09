"""Helpers for the Haas+Sohn local integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, Concatenate

from homeassistant.exceptions import HomeAssistantError

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
                "The stove rejected the command. Check the PIN code in the "
                "integration options."
            ) from err
        except HspConnectionError as err:
            raise HomeAssistantError(
                f"Error communicating with the stove: {err}"
            ) from err
        except HspError as err:
            raise HomeAssistantError(
                f"Unexpected error communicating with the stove: {err}"
            ) from err

    return handler
