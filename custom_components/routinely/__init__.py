"""The Routinely integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.core import Event, callback

from .const import DOMAIN, NotificationAction
from .coordinator import RoutinelyCoordinator
from .services import async_setup_services, async_unload_services
from .storage import RoutinelyStorage

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Routinely from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Initialize storage
    storage = RoutinelyStorage(hass)
    await storage.async_load()

    # Apply options to storage settings
    if entry.options:
        await storage.async_update_settings(dict(entry.options))

    # Initialize coordinator
    coordinator = RoutinelyCoordinator(hass, storage)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up services
    await async_setup_services(hass, storage, coordinator)

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listen for mobile app notification actions
    async def handle_notification_action(event: Event) -> None:
        """Handle mobile app notification action events."""
        action = event.data.get("action", "")
        
        # Map notification actions to coordinator methods
        action_handlers = {
            NotificationAction.PAUSE: coordinator.pause,
            NotificationAction.RESUME: coordinator.resume,
            NotificationAction.SKIP: coordinator.skip_task,
            NotificationAction.COMPLETE: coordinator.complete_task,
            NotificationAction.CONFIRM: coordinator.confirm,
            NotificationAction.SNOOZE: lambda: coordinator.snooze(30),
            NotificationAction.CANCEL: coordinator.cancel,
        }

        handler = action_handlers.get(action)
        if handler:
            _LOGGER.debug("Handling notification action: %s", action)
            await handler()

    entry.async_on_unload(
        hass.bus.async_listen("mobile_app_notification_action", handle_notification_action)
    )

    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    _LOGGER.info("Routinely integration loaded")
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    coordinator: RoutinelyCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.storage.async_update_settings(dict(entry.options))
    _LOGGER.debug("Routinely options updated")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Cancel any active routine
    coordinator: RoutinelyCoordinator = hass.data[DOMAIN][entry.entry_id]
    if coordinator.engine.is_active:
        await coordinator.cancel()

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

        # Only unload services if this was the last entry
        if not hass.data[DOMAIN]:
            async_unload_services(hass)

    _LOGGER.info("Routinely integration unloaded")
    return unload_ok
