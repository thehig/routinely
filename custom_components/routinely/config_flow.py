"""Config flow for the Routinely integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_DEFAULT_ADVANCEMENT_MODE,
    CONF_ENABLE_NOTIFICATIONS,
    CONF_ENABLE_TTS,
    CONF_NOTIFICATION_TARGETS,
    CONF_TASK_ENDING_WARNING,
    CONF_TTS_ENTITY,
    DEFAULT_ADVANCEMENT_MODE,
    DEFAULT_TASK_ENDING_WARNING,
    DOMAIN,
    AdvancementMode,
)

_LOGGER = logging.getLogger(__name__)


class RoutinelyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Routinely."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        # Only allow a single instance
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="Routinely", data={})

        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return RoutinelyOptionsFlow(config_entry)


class RoutinelyOptionsFlow(OptionsFlow):
    """Handle options flow for Routinely."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_ENABLE_NOTIFICATIONS,
                        default=options.get(CONF_ENABLE_NOTIFICATIONS, True),
                    ): bool,
                    vol.Optional(
                        CONF_NOTIFICATION_TARGETS,
                        default=options.get(CONF_NOTIFICATION_TARGETS, ""),
                    ): str,
                    vol.Optional(
                        CONF_TASK_ENDING_WARNING,
                        default=options.get(
                            CONF_TASK_ENDING_WARNING, DEFAULT_TASK_ENDING_WARNING
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=60)),
                    vol.Optional(
                        CONF_DEFAULT_ADVANCEMENT_MODE,
                        default=options.get(
                            CONF_DEFAULT_ADVANCEMENT_MODE, DEFAULT_ADVANCEMENT_MODE
                        ),
                    ): vol.In([m.value for m in AdvancementMode]),
                    vol.Optional(
                        CONF_ENABLE_TTS,
                        default=options.get(CONF_ENABLE_TTS, False),
                    ): bool,
                    vol.Optional(
                        CONF_TTS_ENTITY,
                        default=options.get(CONF_TTS_ENTITY, ""),
                    ): str,
                }
            ),
        )
