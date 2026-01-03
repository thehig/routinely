"""Sensor platform for the Routinely integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity
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
    """Set up Routinely sensor entities."""
    coordinator: RoutinelyCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        RoutinelyStatusSensor(coordinator, entry),
        RoutinelyCurrentTaskSensor(coordinator, entry),
        RoutinelyTimeRemainingSensor(coordinator, entry),
        RoutinelyProgressSensor(coordinator, entry),
    ]
    async_add_entities(entities)


class RoutinelyBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Routinely sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: RoutinelyCoordinator,
        entry: ConfigEntry,
        name: str,
        key: str,
    ) -> None:
        """Initialize the sensor."""
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


class RoutinelyStatusSensor(RoutinelyBaseSensor):
    """Sensor showing the current routine execution status."""

    _attr_icon = "mdi:playlist-play"

    def __init__(self, coordinator: RoutinelyCoordinator, entry: ConfigEntry) -> None:
        """Initialize the status sensor."""
        super().__init__(coordinator, entry, "Status", "status")

    @property
    def native_value(self) -> str:
        """Return the current status."""
        return self.coordinator.data.get("status", "idle")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        data = self.coordinator.data
        return {
            "routine_id": data.get("routine_id"),
            "routine_name": data.get("routine_name"),
            "routine_icon": data.get("routine_icon"),
            "current_task_index": data.get("current_task_index"),
            "total_tasks": data.get("total_tasks"),
            "completed_tasks": data.get("completed_tasks"),
            "skipped_tasks": data.get("skipped_tasks"),
            "elapsed_time": data.get("elapsed_time"),
            "started_at": data.get("started_at"),
            "confirm_window_active": data.get("confirm_window_active"),
        }


class RoutinelyCurrentTaskSensor(RoutinelyBaseSensor):
    """Sensor showing the current task name."""

    def __init__(self, coordinator: RoutinelyCoordinator, entry: ConfigEntry) -> None:
        """Initialize the current task sensor."""
        super().__init__(coordinator, entry, "Current Task", "current_task")

    @property
    def native_value(self) -> str | None:
        """Return the current task name."""
        return self.coordinator.data.get("current_task_name")

    @property
    def icon(self) -> str:
        """Return the icon."""
        return self.coordinator.data.get("current_task_icon") or "mdi:checkbox-marked-circle-outline"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        data = self.coordinator.data
        return {
            "duration": data.get("current_task_duration"),
            "advancement_mode": data.get("advancement_mode"),
            "task_elapsed_time": data.get("task_elapsed_time"),
            "task_index": data.get("current_task_index"),
        }


class RoutinelyTimeRemainingSensor(RoutinelyBaseSensor):
    """Sensor showing time remaining for current task."""

    _attr_icon = "mdi:timer-outline"

    def __init__(self, coordinator: RoutinelyCoordinator, entry: ConfigEntry) -> None:
        """Initialize the time remaining sensor."""
        super().__init__(coordinator, entry, "Time Remaining", "time_remaining")

    @property
    def native_value(self) -> str:
        """Return the formatted time remaining."""
        return self.coordinator.data.get("time_remaining_formatted", "0:00")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "seconds": self.coordinator.data.get("time_remaining", 0),
            "confirm_window_active": self.coordinator.data.get("confirm_window_active"),
        }


class RoutinelyProgressSensor(RoutinelyBaseSensor):
    """Sensor showing routine progress percentage."""

    _attr_icon = "mdi:progress-check"
    _attr_native_unit_of_measurement = "%"

    def __init__(self, coordinator: RoutinelyCoordinator, entry: ConfigEntry) -> None:
        """Initialize the progress sensor."""
        super().__init__(coordinator, entry, "Progress", "progress")

    @property
    def native_value(self) -> int:
        """Return the progress percentage."""
        return self.coordinator.data.get("progress_percent", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        data = self.coordinator.data
        return {
            "completed_tasks": data.get("completed_tasks", 0),
            "skipped_tasks": data.get("skipped_tasks", 0),
            "total_tasks": data.get("total_tasks", 0),
        }
