"""Config flow for the Haas+Sohn local integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult, OptionsFlowWithReload
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_HOST,
    CONF_PIN,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .hsp_client import HspClient, HspConnectionError, HspError, HspStatus

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PIN): str,
    }
)


def _format_title(status: HspStatus, host: str) -> str:
    """Build a human readable entry title."""
    model = f"Haas+Sohn {status.meta.typ}".strip()
    identifier = status.meta.sn or host
    return f"{model} ({identifier})"


class HspLocalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Haas+Sohn (local)."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            pin = user_input[CONF_PIN].strip()

            client = HspClient(async_get_clientsession(self.hass), host, pin)
            try:
                status = await client.async_get_status()
            except HspConnectionError:
                errors["base"] = "cannot_connect"
            except HspError:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(status.meta.sn or host)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=_format_title(status, host),
                    data={CONF_HOST: host, CONF_PIN: pin},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow."""
        return HspLocalOptionsFlow()


class HspLocalOptionsFlow(OptionsFlowWithReload):
    """Handle options for the Haas+Sohn local integration."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SCAN_INTERVAL, default=current): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                }
            ),
        )
