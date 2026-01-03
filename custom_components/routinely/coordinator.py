"""DataUpdateCoordinator for the Routinely integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, SessionStatus
from .engine import RoutineEngine
from .notifications import RoutinelyNotifications
from .storage import RoutinelyStorage

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class RoutinelyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for managing Routinely state updates."""

    def __init__(self, hass: HomeAssistant, storage: RoutinelyStorage) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=1),
        )
        self.storage = storage
        self.notifications = RoutinelyNotifications(hass, storage)
        self.engine = RoutineEngine(
            hass, storage, self.notifications, self._on_engine_update
        )

    def _on_engine_update(self) -> None:
        """Handle engine state updates."""
        self.async_set_updated_data(self._build_data())

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the engine."""
        return self._build_data()

    def _build_data(self) -> dict[str, Any]:
        """Build the data dictionary from current state."""
        session = self.engine.session
        
        if not session or session.status not in (
            SessionStatus.RUNNING,
            SessionStatus.PAUSED,
        ):
            return {
                "active": False,
                "status": SessionStatus.IDLE.value,
                "routine_id": None,
                "routine_name": None,
                "current_task_index": 0,
                "current_task_name": None,
                "current_task_duration": 0,
                "time_remaining": 0,
                "elapsed_time": 0,
                "completed_tasks": 0,
                "skipped_tasks": 0,
                "total_tasks": 0,
                "progress_percent": 0,
                "confirm_window_active": False,
            }

        routine = self.storage.get_routine(session.routine_id)
        task = self.engine.get_current_task()
        completed, skipped, total = self.engine.get_progress()
        time_remaining = self.engine.get_time_remaining()

        progress_percent = 0
        if total > 0:
            # Calculate based on completed tasks plus current task progress
            task_progress = 0
            if task and task.duration > 0:
                task_progress = min(1.0, session.task_elapsed_time / task.duration)
            progress_percent = int(((completed + task_progress) / total) * 100)

        return {
            "active": True,
            "status": session.status.value,
            "routine_id": session.routine_id,
            "routine_name": routine.name if routine else None,
            "routine_icon": routine.icon if routine else None,
            "current_task_index": session.current_task_index,
            "current_task_name": task.name if task else None,
            "current_task_icon": task.icon if task else None,
            "current_task_duration": task.duration if task else 0,
            "advancement_mode": task.advancement_mode.value if task else None,
            "time_remaining": time_remaining,
            "time_remaining_formatted": self._format_time(time_remaining),
            "elapsed_time": session.elapsed_time,
            "task_elapsed_time": session.task_elapsed_time,
            "completed_tasks": completed,
            "skipped_tasks": skipped,
            "total_tasks": total,
            "progress_percent": progress_percent,
            "confirm_window_active": session.confirm_window_active,
            "started_at": session.started_at,
        }

    @staticmethod
    def _format_time(seconds: int) -> str:
        """Format seconds as MM:SS or HH:MM:SS."""
        if seconds < 0:
            seconds = 0
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    # Expose engine methods
    async def start_routine(self, routine_id: str) -> bool:
        """Start a routine."""
        return await self.engine.start_routine(routine_id)

    async def pause(self) -> bool:
        """Pause the active routine."""
        return await self.engine.pause()

    async def resume(self) -> bool:
        """Resume the paused routine."""
        return await self.engine.resume()

    async def skip_task(self) -> bool:
        """Skip the current task."""
        return await self.engine.skip_task()

    async def complete_task(self) -> bool:
        """Complete the current task manually."""
        return await self.engine.complete_task()

    async def confirm(self) -> bool:
        """Confirm task during confirm window."""
        return await self.engine.confirm()

    async def snooze(self, seconds: int = 30) -> bool:
        """Snooze the confirm window."""
        return await self.engine.snooze(seconds)

    async def cancel(self) -> bool:
        """Cancel the active routine."""
        return await self.engine.cancel()
