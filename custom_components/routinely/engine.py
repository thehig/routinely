"""Execution engine for running routines."""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, Callable

from .const import (
    ATTR_ACTUAL_DURATION,
    ATTR_ADVANCEMENT_MODE,
    ATTR_CURRENT_TASK_INDEX,
    ATTR_DURATION,
    ATTR_ROUTINE_ID,
    ATTR_ROUTINE_NAME,
    ATTR_TASK_ID,
    ATTR_TASK_NAME,
    ATTR_TIME_REMAINING,
    ATTR_TOTAL_TASKS,
    ATTR_WAS_AUTO_ADVANCED,
    CONF_ENABLE_NOTIFICATIONS,
    DEFAULT_CONFIRM_WINDOW,
    DEFAULT_SNOOZE_DURATION,
    DEFAULT_TASK_ENDING_WARNING,
    EVENT_ROUTINE_CANCELLED,
    EVENT_ROUTINE_COMPLETED,
    EVENT_ROUTINE_PAUSED,
    EVENT_ROUTINE_RESUMED,
    EVENT_ROUTINE_STARTED,
    EVENT_TASK_AWAITING_INPUT,
    EVENT_TASK_COMPLETED,
    EVENT_TASK_ENDING_SOON,
    EVENT_TASK_SKIPPED,
    EVENT_TASK_STARTED,
    AdvancementMode,
    SessionStatus,
    TaskStatus,
)
from .logger import Loggers
from .models import (
    ExecutionSession,
    SessionHistory,
    Task,
    TaskState,
    generate_id,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .notifications import RoutinelyNotifications
    from .storage import RoutinelyStorage

_log = Loggers.engine


class RoutineEngine:
    """Engine for executing routines."""

    def __init__(
        self,
        hass: HomeAssistant,
        storage: RoutinelyStorage,
        notifications: RoutinelyNotifications | None = None,
        update_callback: Callable[[], None] | None = None,
    ) -> None:
        """Initialize the engine."""
        self.hass = hass
        self.storage = storage
        self.notifications = notifications
        self._update_callback = update_callback
        self._session: ExecutionSession | None = None
        self._timer_task: asyncio.Task | None = None
        self._ending_soon_fired = False

    def _notifications_enabled(self) -> bool:
        """Check if notifications are enabled."""
        return (
            self.notifications is not None
            and self.storage.get_setting(CONF_ENABLE_NOTIFICATIONS, True)
        )

    @property
    def session(self) -> ExecutionSession | None:
        """Return the current session."""
        return self._session

    @property
    def is_active(self) -> bool:
        """Return True if a routine is currently active."""
        return self._session is not None and self._session.status in (
            SessionStatus.RUNNING,
            SessionStatus.PAUSED,
        )

    @property
    def is_running(self) -> bool:
        """Return True if a routine is currently running (not paused)."""
        return self._session is not None and self._session.status == SessionStatus.RUNNING

    def get_current_task(self) -> Task | None:
        """Get the current task being executed."""
        if not self._session:
            return None
        routine = self.storage.get_routine(self._session.routine_id)
        if not routine:
            return None
        tasks = self.storage.get_routine_tasks(routine)
        if self._session.current_task_index < len(tasks):
            return tasks[self._session.current_task_index]
        return None

    def get_time_remaining(self) -> int:
        """Get remaining time for current task in seconds."""
        if not self._session or not self.is_running:
            return 0
        task = self.get_current_task()
        if not task:
            return 0

        if self._session.confirm_window_active:
            return self._session.confirm_window_remaining

        return max(0, task.duration - self._session.task_elapsed_time)

    def get_progress(self) -> tuple[int, int, int]:
        """Get progress as (completed, skipped, total)."""
        if not self._session:
            return (0, 0, 0)
        completed = sum(
            1
            for ts in self._session.task_states
            if ts.status == TaskStatus.COMPLETED
        )
        skipped = sum(
            1 for ts in self._session.task_states if ts.status == TaskStatus.SKIPPED
        )
        return (completed, skipped, len(self._session.task_states))

    async def start_routine(self, routine_id: str, skip_task_ids: list[str] | None = None) -> bool:
        """Start a routine execution.
        
        Args:
            routine_id: ID of the routine to start
            skip_task_ids: Optional list of task IDs to skip (pre-completed)
        """
        _log.debug("Start routine requested", routine_id=routine_id, skip_tasks=skip_task_ids)
        
        if self.is_active:
            _log.warning(
                "Cannot start routine: another routine is active",
                requested=routine_id,
                active=self._session.routine_id if self._session else None,
            )
            return False

        routine = self.storage.get_routine(routine_id)
        if not routine:
            _log.error("Routine not found", routine_id=routine_id)
            return False

        tasks = self.storage.get_routine_tasks(routine)
        if not tasks:
            _log.error("Routine has no tasks", routine_id=routine_id, name=routine.name)
            return False

        skip_task_ids = skip_task_ids or []

        # Create new session
        now = datetime.now().isoformat()
        task_states = []
        for t in tasks:
            state = TaskState(task_id=t.id)
            if t.id in skip_task_ids:
                state.status = TaskStatus.SKIPPED
                state.skipped_at = now
            task_states.append(state)
        
        self._session = ExecutionSession(
            id=generate_id(),
            routine_id=routine_id,
            status=SessionStatus.RUNNING,
            current_task_index=0,
            task_states=task_states,
            started_at=now,
            elapsed_time=0,
            task_elapsed_time=0,
        )

        # Find first non-skipped task
        first_active_index = 0
        for i, state in enumerate(self._session.task_states):
            if state.status != TaskStatus.SKIPPED:
                first_active_index = i
                break
        
        self._session.current_task_index = first_active_index
        
        # Check if all tasks were skipped
        if all(s.status == TaskStatus.SKIPPED for s in self._session.task_states):
            _log.warning("All tasks were skipped, completing routine immediately")
            self._session.status = SessionStatus.COMPLETED
            self._fire_event(EVENT_ROUTINE_COMPLETED, {ATTR_ROUTINE_ID: routine_id})
            self._notify_update()
            return True

        # Mark first active task as active
        self._session.task_states[first_active_index].status = TaskStatus.ACTIVE
        self._session.task_states[first_active_index].started_at = now

        # Count active tasks (not pre-skipped)
        active_task_count = sum(1 for s in self._session.task_states if s.status != TaskStatus.SKIPPED or s.task_id == tasks[first_active_index].id)
        
        # Fire events
        self._fire_event(
            EVENT_ROUTINE_STARTED,
            {
                ATTR_ROUTINE_ID: routine_id,
                ATTR_ROUTINE_NAME: routine.name,
                ATTR_TOTAL_TASKS: active_task_count,
                "skipped_tasks": len(skip_task_ids),
            },
        )
        self._fire_task_started_event(tasks[first_active_index], first_active_index)

        # Send notifications
        estimated_duration = self.storage.calculate_routine_duration(routine, skip_task_ids)
        if self._notifications_enabled():
            await self.notifications.notify_routine_started(
                routine=routine,
                total_tasks=active_task_count,
                estimated_duration=estimated_duration,
            )
            await self.notifications.notify_task_started(
                task=tasks[first_active_index],
                routine_name=routine.name,
                task_index=first_active_index,
                total_tasks=len(tasks),
            )

        # Start timer
        self._start_timer()
        self._notify_update()

        _log.info(
            "Routine started",
            routine_id=routine_id,
            name=routine.name,
            total_tasks=len(tasks),
            skipped_tasks=len(skip_task_ids),
            estimated_duration=estimated_duration,
        )
        return True

    async def pause(self) -> bool:
        """Pause the current routine."""
        _log.debug("Pause requested")
        
        if not self._session or self._session.status != SessionStatus.RUNNING:
            _log.debug("Cannot pause: no running routine")
            return False

        self._stop_timer()
        self._session.status = SessionStatus.PAUSED
        self._session.paused_at = datetime.now().isoformat()

        routine = self.storage.get_routine(self._session.routine_id)
        self._fire_event(
            EVENT_ROUTINE_PAUSED,
            {
                ATTR_ROUTINE_ID: self._session.routine_id,
                ATTR_ROUTINE_NAME: routine.name if routine else "",
            },
        )

        # Send notification
        if self._notifications_enabled() and routine:
            await self.notifications.notify_routine_paused(routine)

        self._notify_update()

        _log.info(
            "Routine paused",
            routine_id=self._session.routine_id,
            elapsed_time=self._session.elapsed_time,
        )
        return True

    async def resume(self) -> bool:
        """Resume the current routine."""
        _log.debug("Resume requested")
        
        if not self._session or self._session.status != SessionStatus.PAUSED:
            _log.debug("Cannot resume: no paused routine")
            return False

        self._session.status = SessionStatus.RUNNING
        self._session.paused_at = None

        routine = self.storage.get_routine(self._session.routine_id)
        self._fire_event(
            EVENT_ROUTINE_RESUMED,
            {
                ATTR_ROUTINE_ID: self._session.routine_id,
                ATTR_ROUTINE_NAME: routine.name if routine else "",
            },
        )

        # Send notification
        if self._notifications_enabled() and routine:
            task = self.get_current_task()
            if task:
                await self.notifications.notify_routine_resumed(routine, task)

        self._start_timer()
        self._notify_update()

        _log.info("Routine resumed", routine_id=self._session.routine_id)
        return True

    async def skip_task(self) -> bool:
        """Skip the current task."""
        _log.debug("Skip task requested")
        
        if not self._session or not self.is_active:
            _log.debug("Cannot skip: no active routine")
            return False

        task = self.get_current_task()
        current_state = self._session.task_states[self._session.current_task_index]
        current_state.status = TaskStatus.SKIPPED
        current_state.completed_at = datetime.now().isoformat()
        current_state.actual_duration = self._session.task_elapsed_time

        self._fire_event(
            EVENT_TASK_SKIPPED,
            {
                ATTR_ROUTINE_ID: self._session.routine_id,
                ATTR_TASK_ID: task.id if task else "",
                ATTR_TASK_NAME: task.name if task else "",
            },
        )

        _log.info(
            "Task skipped",
            task_id=task.id if task else None,
            task_name=task.name if task else None,
            elapsed=self._session.task_elapsed_time,
        )

        await self._advance_to_next_task()
        return True

    async def complete_task(self) -> bool:
        """Manually complete the current task."""
        _log.debug("Complete task requested")
        
        if not self._session or not self.is_active:
            _log.debug("Cannot complete: no active routine")
            return False

        task = self.get_current_task()
        if not task:
            _log.debug("Cannot complete: no current task")
            return False

        # Only allow manual completion for manual/confirm mode tasks
        if task.advancement_mode == AdvancementMode.AUTO:
            _log.debug(
                "Cannot manually complete auto-advance task",
                task_id=task.id,
                mode=task.advancement_mode,
            )
            return False

        _log.info("Task manually completed", task_id=task.id, task_name=task.name)
        await self._complete_current_task(auto_advanced=False)
        return True

    async def confirm(self) -> bool:
        """Confirm task completion during confirm window."""
        _log.debug("Confirm requested")
        
        if not self._session or not self._session.confirm_window_active:
            _log.debug("Cannot confirm: no confirm window active")
            return False

        task = self.get_current_task()
        _log.info("Task confirmed", task_id=task.id if task else None)
        
        self._session.confirm_window_active = False
        await self._complete_current_task(auto_advanced=False)
        return True

    async def snooze(self, seconds: int = DEFAULT_SNOOZE_DURATION) -> bool:
        """Snooze the confirm window."""
        _log.debug("Snooze requested", seconds=seconds)
        
        if not self._session or not self._session.confirm_window_active:
            _log.debug("Cannot snooze: no confirm window active")
            return False

        self._session.confirm_window_remaining += seconds
        _log.info(
            "Confirm window snoozed",
            added_seconds=seconds,
            new_remaining=self._session.confirm_window_remaining,
        )
        self._notify_update()
        return True

    async def cancel(self) -> bool:
        """Cancel the current routine."""
        _log.debug("Cancel requested")
        
        if not self._session or not self.is_active:
            _log.debug("Cannot cancel: no active routine")
            return False

        self._stop_timer()

        routine = self.storage.get_routine(self._session.routine_id)
        routine_id = self._session.routine_id
        elapsed = self._session.elapsed_time
        
        self._session.status = SessionStatus.CANCELLED
        self._session.completed_at = datetime.now().isoformat()

        # Save to history
        await self._save_to_history()

        self._fire_event(
            EVENT_ROUTINE_CANCELLED,
            {
                ATTR_ROUTINE_ID: routine_id,
                ATTR_ROUTINE_NAME: routine.name if routine else "",
            },
        )

        # Send notification
        if self._notifications_enabled() and routine:
            await self.notifications.notify_routine_cancelled(routine)
            await self.notifications.clear_notifications()

        self._session = None
        self._notify_update()

        _log.info(
            "Routine cancelled",
            routine_id=routine_id,
            name=routine.name if routine else None,
            elapsed_time=elapsed,
        )
        return True

    async def _complete_current_task(self, auto_advanced: bool) -> None:
        """Complete the current task and advance."""
        if not self._session:
            return

        task = self.get_current_task()
        current_state = self._session.task_states[self._session.current_task_index]
        current_state.status = TaskStatus.COMPLETED
        current_state.completed_at = datetime.now().isoformat()
        current_state.actual_duration = self._session.task_elapsed_time
        current_state.was_auto_advanced = auto_advanced

        _log.debug(
            "Task completed",
            task_id=task.id if task else None,
            task_name=task.name if task else None,
            auto_advanced=auto_advanced,
            actual_duration=current_state.actual_duration,
        )

        self._fire_event(
            EVENT_TASK_COMPLETED,
            {
                ATTR_ROUTINE_ID: self._session.routine_id,
                ATTR_TASK_ID: task.id if task else "",
                ATTR_TASK_NAME: task.name if task else "",
                ATTR_WAS_AUTO_ADVANCED: auto_advanced,
                ATTR_ACTUAL_DURATION: current_state.actual_duration,
            },
        )

        await self._advance_to_next_task()

    async def _advance_to_next_task(self) -> None:
        """Advance to the next task or complete routine."""
        if not self._session:
            return

        self._stop_timer()
        self._session.confirm_window_active = False
        self._ending_soon_fired = False

        next_index = self._session.current_task_index + 1
        routine = self.storage.get_routine(self._session.routine_id)
        tasks = self.storage.get_routine_tasks(routine) if routine else []

        _log.debug(
            "Advancing to next task",
            next_index=next_index,
            total_tasks=len(tasks),
        )

        if next_index >= len(tasks):
            # Routine complete
            _log.debug("All tasks complete, finishing routine")
            await self._complete_routine()
            return

        # Move to next task
        self._session.current_task_index = next_index
        self._session.task_elapsed_time = 0

        current_state = self._session.task_states[next_index]
        current_state.status = TaskStatus.ACTIVE
        current_state.started_at = datetime.now().isoformat()

        next_task = tasks[next_index]
        _log.info(
            "Task started",
            task_id=next_task.id,
            task_name=next_task.name,
            task_index=next_index,
            duration=next_task.duration,
            mode=next_task.advancement_mode.value,
        )

        self._fire_task_started_event(next_task, next_index)

        # Send task started notification
        if self._notifications_enabled() and routine:
            await self.notifications.notify_task_started(
                task=next_task,
                routine_name=routine.name,
                task_index=next_index,
                total_tasks=len(tasks),
            )

        if self._session.status == SessionStatus.RUNNING:
            self._start_timer()

        self._notify_update()

    async def _complete_routine(self) -> None:
        """Complete the routine."""
        if not self._session:
            return

        self._session.status = SessionStatus.COMPLETED
        self._session.completed_at = datetime.now().isoformat()

        routine = self.storage.get_routine(self._session.routine_id)
        completed, skipped, total = self.get_progress()
        elapsed_time = self._session.elapsed_time
        routine_id = self._session.routine_id

        self._fire_event(
            EVENT_ROUTINE_COMPLETED,
            {
                ATTR_ROUTINE_ID: routine_id,
                ATTR_ROUTINE_NAME: routine.name if routine else "",
                "tasks_completed": completed,
                "tasks_skipped": skipped,
                "total_duration": elapsed_time,
            },
        )

        await self._save_to_history()

        # Send completion notification
        if self._notifications_enabled() and routine:
            await self.notifications.notify_routine_completed(
                routine=routine,
                tasks_completed=completed,
                tasks_skipped=skipped,
                total_duration=elapsed_time,
            )
            await self.notifications.clear_notifications()

        _log.info(
            "Routine completed",
            routine_id=routine_id,
            name=routine.name if routine else None,
            tasks_completed=completed,
            tasks_skipped=skipped,
            total_duration=elapsed_time,
        )
        self._session = None
        self._notify_update()

    async def _save_to_history(self) -> None:
        """Save current session to history."""
        if not self._session:
            return

        routine = self.storage.get_routine(self._session.routine_id)
        completed, skipped, total = self.get_progress()

        history = SessionHistory(
            id=self._session.id,
            routine_id=self._session.routine_id,
            routine_name=routine.name if routine else "",
            status=self._session.status,
            started_at=self._session.started_at or "",
            completed_at=self._session.completed_at or datetime.now().isoformat(),
            total_duration=self._session.elapsed_time,
            tasks_completed=completed,
            tasks_skipped=skipped,
            total_tasks=total,
        )
        await self.storage.async_add_history(history)

    def _start_timer(self) -> None:
        """Start the internal timer."""
        if self._timer_task and not self._timer_task.done():
            _log.debug("Timer already running")
            return

        _log.debug("Starting timer loop")
        self._timer_task = self.hass.async_create_task(self._timer_loop())

    def _stop_timer(self) -> None:
        """Stop the internal timer."""
        if self._timer_task and not self._timer_task.done():
            _log.debug("Stopping timer loop")
            self._timer_task.cancel()
            self._timer_task = None

    async def _timer_loop(self) -> None:
        """Timer loop that ticks every second."""
        _log.debug("Timer loop started")
        try:
            while self._session and self._session.status == SessionStatus.RUNNING:
                await asyncio.sleep(1)

                if not self._session or self._session.status != SessionStatus.RUNNING:
                    _log.debug("Timer loop exiting: session ended or paused")
                    break

                self._session.elapsed_time += 1
                self._session.task_elapsed_time += 1

                task = self.get_current_task()
                if not task:
                    _log.warning("Timer loop: no current task found")
                    break

                if self._session.confirm_window_active:
                    await self._handle_confirm_window_tick()
                else:
                    await self._handle_task_tick(task)

                self._notify_update()

        except asyncio.CancelledError:
            _log.debug("Timer loop cancelled")
        except Exception as e:
            _log.exception("Timer loop error", error=str(e))

    async def _handle_task_tick(self, task: Task) -> None:
        """Handle a timer tick during normal task execution."""
        remaining = task.duration - self._session.task_elapsed_time
        warning_time = self.storage.get_setting(
            "task_ending_warning", DEFAULT_TASK_ENDING_WARNING
        )

        # Fire ending soon event and notification
        if remaining == warning_time and not self._ending_soon_fired:
            self._ending_soon_fired = True
            self._fire_event(
                EVENT_TASK_ENDING_SOON,
                {
                    ATTR_ROUTINE_ID: self._session.routine_id,
                    ATTR_TASK_ID: task.id,
                    ATTR_TASK_NAME: task.name,
                    ATTR_TIME_REMAINING: remaining,
                },
            )
            # Send ending soon notification with TTS
            if self._notifications_enabled():
                await self.notifications.notify_task_ending_soon(task, remaining)

        # Task timer expired
        if remaining <= 0:
            await self._handle_task_timer_expired(task)

    async def _handle_task_timer_expired(self, task: Task) -> None:
        """Handle when task timer expires."""
        match task.advancement_mode:
            case AdvancementMode.AUTO:
                await self._complete_current_task(auto_advanced=True)
            case AdvancementMode.MANUAL:
                self._fire_event(
                    EVENT_TASK_AWAITING_INPUT,
                    {
                        ATTR_ROUTINE_ID: self._session.routine_id,
                        ATTR_TASK_ID: task.id,
                        ATTR_TASK_NAME: task.name,
                        ATTR_ADVANCEMENT_MODE: task.advancement_mode.value,
                    },
                )
                # Send awaiting input notification with TTS
                if self._notifications_enabled():
                    await self.notifications.notify_task_awaiting_input(
                        task=task,
                        is_confirm_mode=False,
                    )
            case AdvancementMode.CONFIRM:
                self._session.confirm_window_active = True
                self._session.confirm_window_remaining = (
                    task.confirm_window or DEFAULT_CONFIRM_WINDOW
                )
                self._fire_event(
                    EVENT_TASK_AWAITING_INPUT,
                    {
                        ATTR_ROUTINE_ID: self._session.routine_id,
                        ATTR_TASK_ID: task.id,
                        ATTR_TASK_NAME: task.name,
                        ATTR_ADVANCEMENT_MODE: task.advancement_mode.value,
                    },
                )
                # Send awaiting input notification with TTS
                if self._notifications_enabled():
                    await self.notifications.notify_task_awaiting_input(
                        task=task,
                        is_confirm_mode=True,
                        confirm_window=task.confirm_window or DEFAULT_CONFIRM_WINDOW,
                    )

    async def _handle_confirm_window_tick(self) -> None:
        """Handle a timer tick during confirm window."""
        self._session.confirm_window_remaining -= 1

        if self._session.confirm_window_remaining <= 0:
            self._session.confirm_window_active = False
            await self._complete_current_task(auto_advanced=True)

    def _fire_event(self, event_type: str, data: dict) -> None:
        """Fire a Home Assistant event."""
        self.hass.bus.async_fire(event_type, data)

    def _fire_task_started_event(self, task: Task, index: int) -> None:
        """Fire task started event."""
        self._fire_event(
            EVENT_TASK_STARTED,
            {
                ATTR_ROUTINE_ID: self._session.routine_id,
                ATTR_TASK_ID: task.id,
                ATTR_TASK_NAME: task.name,
                ATTR_CURRENT_TASK_INDEX: index,
                ATTR_DURATION: task.duration,
                ATTR_ADVANCEMENT_MODE: task.advancement_mode.value,
            },
        )

    def _notify_update(self) -> None:
        """Notify coordinator of state change."""
        if self._update_callback:
            self._update_callback()
