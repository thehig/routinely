"""Storage handler for the Routinely integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION
from .models import Routine, SessionHistory, Task

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

MAX_HISTORY_ENTRIES = 100


class RoutinelyStorage:
    """Handle storage for Routinely data."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize storage."""
        self.hass = hass
        self._store: Store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: dict[str, Any] = {
            "tasks": {},
            "routines": {},
            "history": [],
            "settings": {},
        }
        self._loaded = False

    async def async_load(self) -> None:
        """Load data from storage."""
        if self._loaded:
            return

        data = await self._store.async_load()
        if data:
            self._data = data
        self._loaded = True
        _LOGGER.debug("Loaded Routinely storage data")

    async def async_save(self) -> None:
        """Save data to storage."""
        await self._store.async_save(self._data)

    # Task operations
    def get_tasks(self) -> dict[str, Task]:
        """Get all tasks."""
        return {
            task_id: Task.from_dict(task_data)
            for task_id, task_data in self._data["tasks"].items()
        }

    def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        task_data = self._data["tasks"].get(task_id)
        return Task.from_dict(task_data) if task_data else None

    async def async_create_task(self, task: Task) -> Task:
        """Create a new task."""
        self._data["tasks"][task.id] = task.to_dict()
        await self.async_save()
        return task

    async def async_update_task(self, task: Task) -> Task:
        """Update an existing task."""
        if task.id not in self._data["tasks"]:
            raise ValueError(f"Task {task.id} not found")
        self._data["tasks"][task.id] = task.to_dict()
        await self.async_save()
        return task

    async def async_delete_task(self, task_id: str) -> None:
        """Delete a task."""
        if task_id in self._data["tasks"]:
            del self._data["tasks"][task_id]
            # Remove from all routines
            for routine_data in self._data["routines"].values():
                routine_data["task_ids"] = [
                    tid for tid in routine_data["task_ids"] if tid != task_id
                ]
            await self.async_save()

    # Routine operations
    def get_routines(self) -> dict[str, Routine]:
        """Get all routines."""
        return {
            routine_id: Routine.from_dict(routine_data)
            for routine_id, routine_data in self._data["routines"].items()
        }

    def get_routine(self, routine_id: str) -> Routine | None:
        """Get a routine by ID."""
        routine_data = self._data["routines"].get(routine_id)
        return Routine.from_dict(routine_data) if routine_data else None

    async def async_create_routine(self, routine: Routine) -> Routine:
        """Create a new routine."""
        self._data["routines"][routine.id] = routine.to_dict()
        await self.async_save()
        return routine

    async def async_update_routine(self, routine: Routine) -> Routine:
        """Update an existing routine."""
        if routine.id not in self._data["routines"]:
            raise ValueError(f"Routine {routine.id} not found")
        self._data["routines"][routine.id] = routine.to_dict()
        await self.async_save()
        return routine

    async def async_delete_routine(self, routine_id: str) -> None:
        """Delete a routine."""
        if routine_id in self._data["routines"]:
            del self._data["routines"][routine_id]
            await self.async_save()

    # History operations
    def get_history(self, limit: int = 50) -> list[SessionHistory]:
        """Get session history."""
        history_data = self._data.get("history", [])[:limit]
        return [SessionHistory.from_dict(h) for h in history_data]

    async def async_add_history(self, session: SessionHistory) -> None:
        """Add a session to history."""
        self._data["history"].insert(0, session.to_dict())
        # Trim to max entries
        self._data["history"] = self._data["history"][:MAX_HISTORY_ENTRIES]
        await self.async_save()

    # Settings operations
    def get_settings(self) -> dict[str, Any]:
        """Get all settings."""
        return self._data.get("settings", {})

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a single setting."""
        return self._data.get("settings", {}).get(key, default)

    async def async_update_settings(self, settings: dict[str, Any]) -> None:
        """Update settings."""
        self._data["settings"].update(settings)
        await self.async_save()

    # Utility
    def calculate_routine_duration(self, routine: Routine) -> int:
        """Calculate total duration of a routine in seconds."""
        total = 0
        for task_id in routine.task_ids:
            task = self.get_task(task_id)
            if task:
                total += task.duration
        return total

    def get_routine_tasks(self, routine: Routine) -> list[Task]:
        """Get all tasks for a routine in order."""
        tasks = []
        for task_id in routine.task_ids:
            task = self.get_task(task_id)
            if task:
                tasks.append(task)
        return tasks
