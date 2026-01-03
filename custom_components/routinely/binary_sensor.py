"""Binary sensor platform for the Routinely integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import RoutinelyCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Routinely binary sensor entities."""
    coordinator: RoutinelyCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        RoutinelyActiveSensor(coordinator, entry),
        RoutinelyPausedSensor(coordinator, entry),
        RoutinelyAwaitingInputSensor(coordinator, entry),
    ]
    async_add_entities(entities)


class RoutinelyBaseBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Base class for Routinely binary sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: RoutinelyCoordinator,
        entry: ConfigEntry,
        name: str,
        key: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Routinely",
            "manufacturer": "Routinely",
            "model": "Timer-Guided Routine Execution",
        }


class RoutinelyActiveSensor(RoutinelyBaseBinarySensor):
    """Binary sensor indicating if a routine is active."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_icon = "mdi:play-circle"

    def __init__(self, coordinator: RoutinelyCoordinator, entry: ConfigEntry) -> None:
        """Initialize the active sensor."""
        super().__init__(coordinator, entry, "Active", "active")

    @property
    def is_on(self) -> bool:
        """Return True if a routine is active."""
        return self.coordinator.data.get("active", False)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        data = self.coordinator.data
        if not data.get("active"):
            return {}
        return {
            "routine_id": data.get("routine_id"),
            "routine_name": data.get("routine_name"),
            "status": data.get("status"),
        }


class RoutinelyPausedSensor(RoutinelyBaseBinarySensor):
    """Binary sensor indicating if a routine is paused."""

    _attr_icon = "mdi:pause-circle"

    def __init__(self, coordinator: RoutinelyCoordinator, entry: ConfigEntry) -> None:
        """Initialize the paused sensor."""
        super().__init__(coordinator, entry, "Paused", "paused")

    @property
    def is_on(self) -> bool:
        """Return True if the routine is paused."""
        return self.coordinator.data.get("status") == "paused"


class RoutinelyAwaitingInputSensor(RoutinelyBaseBinarySensor):
    """Binary sensor indicating if awaiting user input."""

    _attr_icon = "mdi:account-question"

    def __init__(self, coordinator: RoutinelyCoordinator, entry: ConfigEntry) -> None:
        """Initialize the awaiting input sensor."""
        super().__init__(coordinator, entry, "Awaiting Input", "awaiting_input")

    @property
    def is_on(self) -> bool:
        """Return True if awaiting input (manual mode or confirm window)."""
        data = self.coordinator.data
        if data.get("confirm_window_active"):
            return True
        # Also true if task timer expired in manual mode
        if data.get("advancement_mode") == "manual" and data.get("time_remaining", 1) <= 0:
            return True
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        data = self.coordinator.data
        return {
            "confirm_window_active": data.get("confirm_window_active"),
            "advancement_mode": data.get("advancement_mode"),
        }
