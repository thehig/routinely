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
    CONF_LOG_LEVEL,
    CONF_NOTIFICATION_TARGETS,
    CONF_NOTIFY_BEFORE,
    CONF_NOTIFY_ON_START,
    CONF_NOTIFY_REMAINING,
    CONF_NOTIFY_OVERDUE,
    CONF_NOTIFY_ON_COMPLETE,
    CONF_TASK_ENDING_WARNING,
    CONF_TTS_ENTITY,
    DEFAULT_ADVANCEMENT_MODE,
    DEFAULT_LOG_LEVEL,
    DEFAULT_NOTIFY_BEFORE,
    DEFAULT_NOTIFY_ON_COMPLETE,
    DEFAULT_NOTIFY_ON_START,
    DEFAULT_NOTIFY_OVERDUE,
    DEFAULT_NOTIFY_REMAINING,
    DEFAULT_TASK_ENDING_WARNING,
    DOMAIN,
    LOG_LEVEL_DEBUG,
    LOG_LEVEL_ERROR,
    LOG_LEVEL_INFO,
    LOG_LEVEL_WARNING,
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
        _LOGGER.debug("Config flow user step, has_input=%s", user_input is not None)
        
        # Only allow a single instance
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            _LOGGER.info("Creating Routinely config entry")
            return self.async_create_entry(title="Routinely", data={})

        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return RoutinelyOptionsFlow(config_entry)


def _list_to_str(values: list[int]) -> str:
    """Convert list of seconds to comma-separated minutes."""
    return ",".join(str(v // 60) for v in values)


def _str_to_list(value: str) -> list[int]:
    """Convert comma-separated minutes to list of seconds."""
    if not value or not value.strip():
        return []
    return [int(v.strip()) * 60 for v in value.split(",") if v.strip().isdigit()]


class RoutinelyOptionsFlow(OptionsFlow):
    """Handle options flow for Routinely."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry
        self._data: dict[str, Any] = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options - main settings."""
        _LOGGER.debug("Options flow init step, has_input=%s", user_input is not None)
        
        if user_input is not None:
            self._data = dict(self._config_entry.options)
            self._data.update(user_input)
            return await self.async_step_notifications()

        options = self._config_entry.options
        _LOGGER.debug("Current options: %s", dict(options))

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
                    vol.Optional(
                        CONF_LOG_LEVEL,
                        default=options.get(CONF_LOG_LEVEL, DEFAULT_LOG_LEVEL),
                    ): vol.In([
                        LOG_LEVEL_DEBUG,
                        LOG_LEVEL_INFO,
                        LOG_LEVEL_WARNING,
                        LOG_LEVEL_ERROR,
                    ]),
                }
            ),
        )

    async def async_step_notifications(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure notification timings."""
        if user_input is not None:
            # Convert string inputs to lists
            self._data[CONF_NOTIFY_BEFORE] = _str_to_list(user_input.get("notify_before_str", ""))
            self._data[CONF_NOTIFY_ON_START] = user_input.get(CONF_NOTIFY_ON_START, True)
            self._data[CONF_NOTIFY_REMAINING] = _str_to_list(user_input.get("notify_remaining_str", ""))
            self._data[CONF_NOTIFY_OVERDUE] = _str_to_list(user_input.get("notify_overdue_str", ""))
            self._data[CONF_NOTIFY_ON_COMPLETE] = user_input.get(CONF_NOTIFY_ON_COMPLETE, False)
            
            _LOGGER.info("Updating Routinely options: %s", self._data)
            return self.async_create_entry(title="", data=self._data)

        options = self._config_entry.options
        
        return self.async_show_form(
            step_id="notifications",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "notify_before_str",
                        description={"suggested_value": _list_to_str(options.get(CONF_NOTIFY_BEFORE, DEFAULT_NOTIFY_BEFORE))},
                    ): str,
                    vol.Optional(
                        CONF_NOTIFY_ON_START,
                        default=options.get(CONF_NOTIFY_ON_START, DEFAULT_NOTIFY_ON_START),
                    ): bool,
                    vol.Optional(
                        "notify_remaining_str",
                        description={"suggested_value": _list_to_str(options.get(CONF_NOTIFY_REMAINING, DEFAULT_NOTIFY_REMAINING))},
                    ): str,
                    vol.Optional(
                        "notify_overdue_str",
                        description={"suggested_value": _list_to_str(options.get(CONF_NOTIFY_OVERDUE, DEFAULT_NOTIFY_OVERDUE))},
                    ): str,
                    vol.Optional(
                        CONF_NOTIFY_ON_COMPLETE,
                        default=options.get(CONF_NOTIFY_ON_COMPLETE, DEFAULT_NOTIFY_ON_COMPLETE),
                    ): bool,
                }
            ),
        )
