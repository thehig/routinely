"""Storage handler for the Routinely integration."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION
from .logger import Loggers
from .models import Routine, SessionHistory, Task

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_log = Loggers.storage

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
        _log.debug("Storage handler initialized", storage_key=STORAGE_KEY)

    async def async_load(self) -> None:
        """Load data from storage."""
        if self._loaded:
            _log.debug("Storage already loaded, skipping")
            return

        _log.debug("Loading storage data")
        data = await self._store.async_load()
        if data:
            self._data = data
            _log.debug(
                "Storage data loaded",
                tasks=len(self._data.get("tasks", {})),
                routines=len(self._data.get("routines", {})),
                history_entries=len(self._data.get("history", [])),
            )
        else:
            _log.debug("No existing storage data found, using defaults")
        self._loaded = True

    async def async_save(self) -> None:
        """Save data to storage."""
        _log.debug("Saving storage data")
        await self._store.async_save(self._data)
        _log.debug("Storage data saved")

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
        _log.debug("Creating task", task_id=task.id, name=task.name)
        self._data["tasks"][task.id] = task.to_dict()
        await self.async_save()
        _log.info("Task created", task_id=task.id, name=task.name)
        return task

    async def async_update_task(self, task: Task) -> Task:
        """Update an existing task."""
        if task.id not in self._data["tasks"]:
            _log.error("Task not found for update", task_id=task.id)
            raise ValueError(f"Task {task.id} not found")
        _log.debug("Updating task", task_id=task.id, name=task.name)
        self._data["tasks"][task.id] = task.to_dict()
        await self.async_save()
        _log.info("Task updated", task_id=task.id, name=task.name)
        return task

    async def async_delete_task(self, task_id: str) -> None:
        """Delete a task."""
        if task_id in self._data["tasks"]:
            task_name = self._data["tasks"][task_id].get("name", "unknown")
            _log.debug("Deleting task", task_id=task_id, name=task_name)
            del self._data["tasks"][task_id]
            # Remove from all routines
            affected_routines = 0
            for routine_data in self._data["routines"].values():
                old_len = len(routine_data["task_ids"])
                routine_data["task_ids"] = [
                    tid for tid in routine_data["task_ids"] if tid != task_id
                ]
                if len(routine_data["task_ids"]) < old_len:
                    affected_routines += 1
            await self.async_save()
            _log.info(
                "Task deleted",
                task_id=task_id,
                name=task_name,
                affected_routines=affected_routines,
            )
        else:
            _log.warning("Attempted to delete non-existent task", task_id=task_id)

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
        _log.debug(
            "Creating routine",
            routine_id=routine.id,
            name=routine.name,
            task_count=len(routine.task_ids),
        )
        self._data["routines"][routine.id] = routine.to_dict()
        await self.async_save()
        _log.info("Routine created", routine_id=routine.id, name=routine.name)
        return routine

    async def async_update_routine(self, routine: Routine) -> Routine:
        """Update an existing routine."""
        if routine.id not in self._data["routines"]:
            _log.error("Routine not found for update", routine_id=routine.id)
            raise ValueError(f"Routine {routine.id} not found")
        _log.debug("Updating routine", routine_id=routine.id, name=routine.name)
        self._data["routines"][routine.id] = routine.to_dict()
        await self.async_save()
        _log.info("Routine updated", routine_id=routine.id, name=routine.name)
        return routine

    async def async_delete_routine(self, routine_id: str) -> None:
        """Delete a routine."""
        if routine_id in self._data["routines"]:
            routine_name = self._data["routines"][routine_id].get("name", "unknown")
            _log.debug("Deleting routine", routine_id=routine_id, name=routine_name)
            del self._data["routines"][routine_id]
            await self.async_save()
            _log.info("Routine deleted", routine_id=routine_id, name=routine_name)
        else:
            _log.warning("Attempted to delete non-existent routine", routine_id=routine_id)

    # History operations
    def get_history(self, limit: int = 50) -> list[SessionHistory]:
        """Get session history."""
        history_data = self._data.get("history", [])[:limit]
        _log.debug("Retrieved history", count=len(history_data), limit=limit)
        return [SessionHistory.from_dict(h) for h in history_data]

    async def async_add_history(self, session: SessionHistory) -> None:
        """Add a session to history."""
        _log.debug(
            "Adding session to history",
            session_id=session.id,
            routine=session.routine_name,
            status=session.status.value,
        )
        self._data["history"].insert(0, session.to_dict())
        # Trim to max entries
        old_len = len(self._data["history"])
        self._data["history"] = self._data["history"][:MAX_HISTORY_ENTRIES]
        trimmed = old_len - len(self._data["history"])
        if trimmed > 0:
            _log.debug("Trimmed history entries", trimmed=trimmed)
        await self.async_save()
        _log.info("Session added to history", session_id=session.id)

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
