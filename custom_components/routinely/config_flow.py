"""Config flow for the Routinely integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_DEFAULT_ADVANCEMENT_MODE,
    CONF_ENABLE_BROWSER_MOD_TTS,
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


def _get_notify_services(hass: HomeAssistant) -> dict[str, str]:
    """Get available notify services, prioritizing mobile_app services."""
    services = {}
    notify_services = hass.services.async_services().get("notify", {})
    
    for service_name in notify_services:
        if service_name == "persistent_notification":
            continue  # Skip this one
        
        # Create a friendly label
        if service_name.startswith("mobile_app_"):
            device_name = service_name.replace("mobile_app_", "").replace("_", " ").title()
            label = f"📱 {device_name} (iOS/Android)"
        else:
            label = f"🔔 {service_name.replace('_', ' ').title()}"
        
        services[service_name] = label
    
    # Sort with mobile_app services first
    sorted_services = dict(sorted(
        services.items(),
        key=lambda x: (0 if x[0].startswith("mobile_app_") else 1, x[1])
    ))
    
    return sorted_services


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
        self._test_message_sent: bool = False

    @staticmethod
    def _is_android_target(target: str) -> bool:
        """Check if target is likely an Android device."""
        target_lower = target.lower()
        if "android" in target_lower or "pixel" in target_lower or "galaxy" in target_lower:
            return True
        if "iphone" in target_lower or "ipad" in target_lower or "ios" in target_lower:
            return False
        return target.startswith("mobile_app_")

    async def _send_test_notification(self, message: str) -> bool:
        """Send a test notification to configured targets.
        
        Returns True if notification was sent successfully to at least one target.
        """
        success = False
        
        # Send to mobile notification targets
        targets_str = self._data.get(CONF_NOTIFICATION_TARGETS, "")
        if targets_str:
            targets = [t.strip() for t in targets_str.split(",") if t.strip()]
            
            for target in targets:
                try:
                    is_android = self._is_android_target(target)
                    
                    # For Android TTS, message must be "TTS" to trigger speech
                    effective_message = "TTS" if is_android else message
                    
                    service_data = {
                        "title": "🧪 Routinely Test",
                        "message": effective_message,
                        "data": {
                            "push": {
                                "sound": {"name": "default", "volume": 1.0},
                                "interruption-level": "active",
                            },
                            "tts_text": message,
                            "tag": "routinely_test",
                            # Android-specific TTS settings
                            "ttl": 0,
                            "priority": "high",
                            "channel": "routinely",
                            "actions": [
                                {"action": "ROUTINELY_TEST_OK", "title": "OK"},
                            ],
                        },
                    }
                    
                    if target.startswith("mobile_app_"):
                        await self.hass.services.async_call("notify", target, service_data)
                    elif "." in target:
                        domain, service = target.split(".", 1)
                        await self.hass.services.async_call(domain, service, service_data)
                    else:
                        await self.hass.services.async_call("notify", target, service_data)
                    
                    _LOGGER.info("Test notification sent to %s", target)
                    success = True
                except Exception as err:
                    _LOGGER.error("Failed to send test notification to %s: %s", target, err)
        
        # Also speak via TTS entity if configured (for iOS users with HomePod, etc.)
        tts_entity = self._data.get(CONF_TTS_ENTITY, "")
        if self._data.get(CONF_ENABLE_TTS, False) and tts_entity:
            try:
                await self.hass.services.async_call(
                    "tts",
                    "speak",
                    {
                        "entity_id": tts_entity,
                        "message": message,
                        "media_player_entity_id": tts_entity,
                    },
                    blocking=False,
                )
                _LOGGER.info("Test TTS sent to %s", tts_entity)
                success = True
            except Exception as err:
                _LOGGER.debug("tts.speak failed, trying cloud_say: %s", err)
                try:
                    await self.hass.services.async_call(
                        "tts",
                        "cloud_say",
                        {
                            "entity_id": tts_entity,
                            "message": message,
                        },
                        blocking=False,
                    )
                    _LOGGER.info("Test TTS (cloud_say) sent to %s", tts_entity)
                    success = True
                except Exception as err2:
                    _LOGGER.error("Failed to send test TTS to %s: %s", tts_entity, err2)
        
        # Speak via browser_mod if enabled (for iOS Safari and other browsers)
        if self._data.get(CONF_ENABLE_BROWSER_MOD_TTS, False):
            if self.hass.services.has_service("browser_mod", "javascript"):
                escaped_message = message.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
                js_code = f"""
                    if ('speechSynthesis' in window) {{
                        const utterance = new SpeechSynthesisUtterance('{escaped_message}');
                        utterance.rate = 1.0;
                        utterance.pitch = 1.0;
                        utterance.volume = 1.0;
                        speechSynthesis.speak(utterance);
                    }}
                """
                try:
                    await self.hass.services.async_call(
                        "browser_mod",
                        "javascript",
                        {"code": js_code},
                        blocking=False,
                    )
                    _LOGGER.info("Test browser_mod TTS sent")
                    success = True
                except Exception as err:
                    _LOGGER.error("Failed to send test browser_mod TTS: %s", err)
            else:
                _LOGGER.warning("browser_mod.javascript service not available - install browser_mod from HACS")
        
        return success

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options - main settings."""
        _LOGGER.debug("Options flow init step, has_input=%s", user_input is not None)
        
        if user_input is not None:
            self._data = dict(self._config_entry.options)
            self._data.update(user_input)
            
            # Convert notification targets list to comma-separated string
            targets = self._data.get(CONF_NOTIFICATION_TARGETS, [])
            if isinstance(targets, list):
                self._data[CONF_NOTIFICATION_TARGETS] = ",".join(targets)
            
            # Go to test notification step if targets are configured
            if self._data.get(CONF_NOTIFICATION_TARGETS):
                return await self.async_step_test_notification()
            
            return await self.async_step_notifications()

        options = self._config_entry.options
        _LOGGER.debug("Current options: %s", dict(options))

        # Get available notify services
        notify_services = _get_notify_services(self.hass)
        
        # Convert stored targets to list format
        stored_targets = options.get(CONF_NOTIFICATION_TARGETS, "")
        if isinstance(stored_targets, str):
            current_targets = [t.strip() for t in stored_targets.split(",") if t.strip()]
        else:
            current_targets = stored_targets or []

        # Build schema - use multi-select if services available, else text input
        if notify_services:
            targets_schema = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(value=k, label=v)
                        for k, v in notify_services.items()
                    ],
                    multiple=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        else:
            # Fallback to text input if no services found
            targets_schema = str

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
                        default=current_targets if notify_services else stored_targets,
                    ): targets_schema,
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
                        CONF_ENABLE_BROWSER_MOD_TTS,
                        default=options.get(CONF_ENABLE_BROWSER_MOD_TTS, False),
                    ): bool,
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

    async def async_step_test_notification(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Test notification step - allows sending multiple test messages."""
        errors: dict[str, str] = {}
        description_placeholders: dict[str, str] = {}
        
        if user_input is not None:
            test_message = user_input.get("test_message", "").strip()
            send_test = user_input.get("send_test", False)
            
            if send_test and test_message:
                # Send test notification and stay on this page
                success = await self._send_test_notification(test_message)
                if success:
                    self._test_message_sent = True
                    description_placeholders["status"] = "✅ Test notification sent!"
                else:
                    errors["base"] = "notification_failed"
                    description_placeholders["status"] = "❌ Failed to send notification"
            elif not send_test:
                # Continue to next step (user clicked "Continue")
                return await self.async_step_notifications()
            else:
                # Send was clicked but no message
                errors["test_message"] = "message_required"
                description_placeholders["status"] = ""
        else:
            description_placeholders["status"] = ""

        return self.async_show_form(
            step_id="test_notification",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "test_message",
                        description={"suggested_value": "This is a notification test from Routinely"},
                    ): str,
                    vol.Optional("send_test", default=True): bool,
                }
            ),
            errors=errors,
            description_placeholders=description_placeholders,
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
