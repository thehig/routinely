"""The Routinely integration."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.const import Platform
from homeassistant.core import Event

from .const import CONF_LOG_LEVEL, DEFAULT_LOG_LEVEL, DOMAIN, NotificationAction
from .coordinator import RoutinelyCoordinator
from .logger import Loggers, configure_logging, set_log_level
from .services import async_setup_services, async_unload_services
from .storage import RoutinelyStorage

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_log = Loggers.init
_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

# Frontend card URL
CARD_URL = f"/hacsfiles/{DOMAIN}/routinely-card.js"
CARD_PATH = Path(__file__).parent / "www" / "routinely-card.js"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Routinely from a config entry."""
    # Configure logging first
    log_level = entry.options.get(CONF_LOG_LEVEL, DEFAULT_LOG_LEVEL)
    configure_logging(hass, log_level)
    
    _log.info("Setting up Routinely integration", version="1.0.0")
    _log.debug("Entry options", options=dict(entry.options))
    
    hass.data.setdefault(DOMAIN, {})

    # Initialize storage
    _log.debug("Initializing storage")
    storage = RoutinelyStorage(hass)
    await storage.async_load()
    _log.debug(
        "Storage loaded",
        tasks=len(storage.get_tasks()),
        routines=len(storage.get_routines()),
    )

    # Apply options to storage settings
    if entry.options:
        await storage.async_update_settings(dict(entry.options))
        _log.debug("Applied entry options to storage")

    # Initialize coordinator
    _log.debug("Initializing coordinator")
    coordinator = RoutinelyCoordinator(hass, storage)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up services
    _log.debug("Registering services")
    await async_setup_services(hass, storage, coordinator)

    # Set up platforms
    _log.debug("Setting up platforms", platforms=PLATFORMS)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register frontend card
    try:
        if CARD_PATH.exists():
            await hass.http.async_register_static_paths([
                StaticPathConfig(
                    f"/local/{DOMAIN}/routinely-card.js",
                    str(CARD_PATH),
                    cache_headers=False,
                )
            ])
            _log.debug("Registered frontend card")
    except Exception as err:
        _LOGGER.warning("Could not register frontend card: %s", err)

    # Listen for mobile app notification actions (iOS/Android companion app)
    async def handle_notification_action(event: Event) -> None:
        """Handle mobile app notification action events."""
        action = event.data.get("action", "")
        
        _log.debug("Received notification action event", action=action, event_data=event.data)
        
        # Map notification actions to coordinator methods (use .value for explicit string keys)
        action_handlers = {
            NotificationAction.PAUSE.value: coordinator.pause,
            NotificationAction.RESUME.value: coordinator.resume,
            NotificationAction.SKIP.value: coordinator.skip_task,
            NotificationAction.COMPLETE.value: coordinator.complete_task,
            NotificationAction.CONFIRM.value: coordinator.confirm,
            NotificationAction.SNOOZE.value: lambda: coordinator.snooze(30),
            NotificationAction.CANCEL.value: coordinator.cancel,
        }

        handler = action_handlers.get(action)
        if handler:
            _log.info("Executing notification action", action=action)
            try:
                await handler()
            except Exception as err:
                _log.error("Failed to execute notification action", action=action, error=str(err))
        elif action.startswith("ROUTINELY_"):
            _log.warning("Unhandled Routinely notification action", action=action)

    entry.async_on_unload(
        hass.bus.async_listen("mobile_app_notification_action", handle_notification_action)
    )
    _log.debug("Registered notification action listener")

    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    _log.info("Routinely integration setup complete")
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _log.debug("Options update received", options=dict(entry.options))
    
    # Update log level if changed
    log_level = entry.options.get(CONF_LOG_LEVEL, DEFAULT_LOG_LEVEL)
    set_log_level(log_level)
    
    coordinator: RoutinelyCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.storage.async_update_settings(dict(entry.options))
    _log.info("Routinely options updated")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _log.info("Unloading Routinely integration")
    
    # Cancel any active routine
    coordinator: RoutinelyCoordinator = hass.data[DOMAIN][entry.entry_id]
    if coordinator.engine.is_active:
        _log.debug("Cancelling active routine before unload")
        await coordinator.cancel()

    # Unload platforms
    _log.debug("Unloading platforms")
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        _log.debug("Removed coordinator from hass.data")

        # Only unload services if this was the last entry
        if not hass.data[DOMAIN]:
            _log.debug("Unregistering services (last entry)")
            async_unload_services(hass)

    _log.info("Routinely integration unloaded", success=unload_ok)
    return unload_ok
