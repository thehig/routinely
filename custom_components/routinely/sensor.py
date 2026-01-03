"""Sensor platform for the Routinely integration."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .logger import Loggers

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import RoutinelyCoordinator

_log = Loggers.sensor


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Routinely sensor entities."""
    _log.debug("Setting up sensor entities")
    coordinator: RoutinelyCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        RoutinelyStatusSensor(coordinator, entry),
        RoutinelyCurrentTaskSensor(coordinator, entry),
        RoutinelyTimeRemainingSensor(coordinator, entry),
        RoutinelyProgressSensor(coordinator, entry),
        RoutinelyTaskCountSensor(coordinator, entry),
        RoutinelyRoutineCountSensor(coordinator, entry),
    ]
    async_add_entities(entities)
    _log.debug("Sensor entities registered", count=len(entities))


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


class RoutinelyTaskCountSensor(RoutinelyBaseSensor):
    """Sensor showing number of configured tasks with task list in attributes."""

    _attr_icon = "mdi:format-list-checks"

    def __init__(self, coordinator: RoutinelyCoordinator, entry: ConfigEntry) -> None:
        """Initialize the task count sensor."""
        super().__init__(coordinator, entry, "Tasks", "task_count")

    @property
    def native_value(self) -> int:
        """Return the number of tasks."""
        tasks = self.coordinator.storage.get_tasks()
        return len(tasks)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return task list as attributes."""
        tasks = self.coordinator.storage.get_tasks()
        task_list = []
        for task_id, task in tasks.items():
            task_list.append({
                "id": task_id,
                "name": task.name,
                "duration": task.duration,
                "duration_formatted": self._format_duration(task.duration),
                "icon": task.icon,
                "mode": task.advancement_mode.value,
            })
        return {
            "tasks": task_list,
            "task_ids": list(tasks.keys()),
        }

    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Format duration as human readable."""
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        secs = seconds % 60
        if secs == 0:
            return f"{minutes}m"
        return f"{minutes}m {secs}s"


class RoutinelyRoutineCountSensor(RoutinelyBaseSensor):
    """Sensor showing number of configured routines with routine list in attributes."""

    _attr_icon = "mdi:playlist-check"

    def __init__(self, coordinator: RoutinelyCoordinator, entry: ConfigEntry) -> None:
        """Initialize the routine count sensor."""
        super().__init__(coordinator, entry, "Routines", "routine_count")

    @property
    def native_value(self) -> int:
        """Return the number of routines."""
        routines = self.coordinator.storage.get_routines()
        return len(routines)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return routine list as attributes."""
        routines = self.coordinator.storage.get_routines()
        storage = self.coordinator.storage
        routine_list = []
        all_tags = set()
        for routine_id, routine in routines.items():
            duration = storage.calculate_routine_duration(routine)
            routine_list.append({
                "id": routine_id,
                "name": routine.name,
                "icon": routine.icon,
                "task_ids": routine.task_ids,
                "task_count": len(routine.task_ids),
                "duration": duration,
                "duration_formatted": self._format_duration(duration),
                "tags": routine.tags,
                "schedule_time": routine.schedule_time,
                "schedule_days": routine.schedule_days,
            })
            all_tags.update(routine.tags)
        return {
            "routines": routine_list,
            "routine_ids": list(routines.keys()),
            "all_tags": sorted(all_tags),
        }

    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Format duration as human readable."""
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m"
        hours = minutes // 60
        mins = minutes % 60
        if mins == 0:
            return f"{hours}h"
        return f"{hours}h {mins}m"
