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
    CONF_NOTIFY_BEFORE,
    CONF_NOTIFY_ON_COMPLETE,
    CONF_NOTIFY_ON_START,
    CONF_NOTIFY_OVERDUE,
    CONF_NOTIFY_REMAINING,
    CONF_AUTONEXT_NOTIFY_BEFORE,
    CONF_AUTONEXT_NOTIFY_REMAINING,
    DEFAULT_AUTONEXT_NOTIFY_BEFORE,
    DEFAULT_AUTONEXT_NOTIFY_REMAINING,
    DEFAULT_CONFIRM_WINDOW,
    DEFAULT_NOTIFY_BEFORE,
    DEFAULT_NOTIFY_ON_COMPLETE,
    DEFAULT_NOTIFY_ON_START,
    DEFAULT_NOTIFY_OVERDUE,
    DEFAULT_NOTIFY_REMAINING,
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
    NotificationSettings,
    Routine,
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
        self._task_timer_expired = False

    def _notifications_enabled(self) -> bool:
        """Check if notifications are enabled."""
        return (
            self.notifications is not None
            and self.storage.get_setting(CONF_ENABLE_NOTIFICATIONS, True)
        )

    def _get_notification_settings(self, routine: Routine | None = None) -> NotificationSettings:
        """Get notification settings, using routine override if present."""
        # Check for routine-level override
        if routine and routine.notification_settings:
            return routine.notification_settings
        
        # Use global config settings
        return NotificationSettings(
            notify_before=self.storage.get_setting(CONF_NOTIFY_BEFORE, DEFAULT_NOTIFY_BEFORE),
            notify_on_start=self.storage.get_setting(CONF_NOTIFY_ON_START, DEFAULT_NOTIFY_ON_START),
            notify_remaining=self.storage.get_setting(CONF_NOTIFY_REMAINING, DEFAULT_NOTIFY_REMAINING),
            notify_overdue=self.storage.get_setting(CONF_NOTIFY_OVERDUE, DEFAULT_NOTIFY_OVERDUE),
            notify_on_complete=self.storage.get_setting(CONF_NOTIFY_ON_COMPLETE, DEFAULT_NOTIFY_ON_COMPLETE),
            autonext_notify_before=self.storage.get_setting(CONF_AUTONEXT_NOTIFY_BEFORE, DEFAULT_AUTONEXT_NOTIFY_BEFORE),
            autonext_notify_remaining=self.storage.get_setting(CONF_AUTONEXT_NOTIFY_REMAINING, DEFAULT_AUTONEXT_NOTIFY_REMAINING),
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
        # Use session's task_ids for ordering
        if self._session.current_task_index < len(self._session.task_ids):
            task_id = self._session.task_ids[self._session.current_task_index]
            return self.storage.get_task(task_id)
        return None
    
    def _get_session_tasks(self) -> list[Task]:
        """Get tasks for current session in session order."""
        if not self._session:
            return []
        tasks = []
        for task_id in self._session.task_ids:
            task = self.storage.get_task(task_id)
            if task:
                tasks.append(task)
        return tasks

    def get_time_remaining(self) -> int:
        """Get remaining time for current task in seconds.
        
        Returns negative values for manual tasks when overtime (counting up).
        """
        if not self._session or not self.is_active:
            return 0
        task = self.get_current_task()
        if not task:
            return 0

        if self._session.confirm_window_active:
            return self._session.confirm_window_remaining

        remaining = task.duration - self._session.task_elapsed_time
        
        # For manual/confirm tasks, allow negative (overtime) values
        if task.advancement_mode != AdvancementMode.AUTO:
            return remaining
        
        return max(0, remaining)

    def get_progress(self) -> tuple[int, int, int, int]:
        """Get progress as (completed, skipped, total, active_total).
        
        active_total is the number of tasks that weren't pre-skipped in review.
        """
        if not self._session:
            return (0, 0, 0, 0)
        completed = sum(
            1
            for ts in self._session.task_states
            if ts.status == TaskStatus.COMPLETED
        )
        skipped = sum(
            1 for ts in self._session.task_states if ts.status == TaskStatus.SKIPPED
        )
        # Count tasks that are not pre-skipped (either active, pending, or completed during execution)
        # Pre-skipped tasks have status SKIPPED but no started_at time
        active_total = sum(
            1 for ts in self._session.task_states
            if ts.status != TaskStatus.SKIPPED or ts.started_at is not None
        )
        return (completed, skipped, len(self._session.task_states), active_total)
    
    def get_active_task_index(self) -> int:
        """Get current task index relative to non-pre-skipped tasks only."""
        if not self._session:
            return 0
        # Count how many non-skipped tasks come before current index
        active_index = 0
        for i in range(self._session.current_task_index):
            ts = self._session.task_states[i]
            # Only count if it wasn't pre-skipped (was started at some point)
            if ts.status != TaskStatus.SKIPPED or ts.started_at is not None:
                active_index += 1
        return active_index

    async def start_routine(
        self, 
        routine_id: str, 
        skip_task_ids: list[str] | None = None,
        task_order: list[str] | None = None
    ) -> bool:
        """Start a routine execution.
        
        Args:
            routine_id: ID of the routine to start
            skip_task_ids: Optional list of task IDs to skip (pre-completed)
            task_order: Optional custom task order (overrides routine's default order)
        """
        _log.debug("Start routine requested", routine_id=routine_id, skip_tasks=skip_task_ids, task_order=task_order)
        
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

        # Get tasks - use custom order if provided
        if task_order:
            # Reorder tasks based on provided order
            all_tasks = {t.id: t for t in self.storage.get_routine_tasks(routine)}
            tasks = []
            for tid in task_order:
                if tid in all_tasks:
                    tasks.append(all_tasks[tid])
                else:
                    _log.warning("Task not found in routine", task_id=tid)
            # Add any tasks not in task_order at the end
            for tid, task in all_tasks.items():
                if tid not in task_order:
                    tasks.append(task)
        else:
            tasks = self.storage.get_routine_tasks(routine)
        
        if not tasks:
            _log.error("Routine has no tasks", routine_id=routine_id, name=routine.name)
            return False

        skip_task_ids = skip_task_ids or []

        # Create new session
        now = datetime.now().isoformat()
        task_states = []
        task_ids = [t.id for t in tasks]  # Store ordered task IDs
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
            task_ids=task_ids,
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
        settings = self._get_notification_settings(routine)
        
        # Set routine-specific notification targets if configured
        if self._notifications_enabled() and settings.notification_targets:
            self.notifications.set_active_routine_targets(settings.notification_targets)
        
        if self._notifications_enabled():
            await self.notifications.notify_routine_started(
                routine=routine,
                total_tasks=active_task_count,
                estimated_duration=estimated_duration,
            )
            if settings.notify_on_start:
                await self.notifications.notify_task_started(
                    task=tasks[first_active_index],
                    routine_name=routine.name,
                    task_index=first_active_index,
                    total_tasks=len(tasks),
                )
                # Mark as sent
                self._session.task_states[first_active_index].sent_start_notification = True

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

    def adjust_task_time(self, seconds: int) -> bool:
        """Adjust the current task's remaining time.
        
        Args:
            seconds: Seconds to add (positive) or subtract (negative)
            
        Returns:
            True if adjustment was made, False otherwise
        """
        if not self._session or not self.is_active:
            _log.debug("Cannot adjust time: no active routine")
            return False
        
        task = self.get_current_task()
        if not task:
            _log.debug("Cannot adjust time: no current task")
            return False
        
        # Calculate new elapsed time (subtracting seconds adds time, adding reduces remaining)
        new_elapsed = self._session.task_elapsed_time - seconds
        
        # Allow negative elapsed time (means time remaining > original duration)
        # This lets users extend tasks beyond their original duration
        # Only cap to prevent unreasonable negative values (e.g., -1 hour)
        min_elapsed = -3600  # Allow extending up to 1 hour beyond original
        if new_elapsed < min_elapsed:
            new_elapsed = min_elapsed
        
        self._session.task_elapsed_time = new_elapsed
        self._notify_update()
        
        _log.info(
            "Task time adjusted",
            task_id=task.id,
            adjustment=seconds,
            new_elapsed=new_elapsed,
            time_remaining=task.duration - new_elapsed,
        )
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

        # Send notification and clear routine targets
        if self._notifications_enabled() and routine:
            await self.notifications.notify_routine_cancelled(routine)
            await self.notifications.clear_notifications()
            self.notifications.clear_active_routine_targets()

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

        # Send task completion notification if enabled
        if self._notifications_enabled() and task:
            routine = self.storage.get_routine(self._session.routine_id)
            settings = self._get_notification_settings(routine)
            if settings.notify_on_complete and not current_state.sent_complete_notification:
                current_state.sent_complete_notification = True
                await self.notifications.notify_task_complete(task)

        await self._advance_to_next_task()

    async def _advance_to_next_task(self) -> None:
        """Advance to the next task or complete routine."""
        if not self._session:
            return

        self._stop_timer()
        self._session.confirm_window_active = False
        self._ending_soon_fired = False
        self._task_timer_expired = False

        next_index = self._session.current_task_index + 1
        routine = self.storage.get_routine(self._session.routine_id)
        tasks = self._get_session_tasks()

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

        # Move to next task, skipping any pre-skipped tasks
        while next_index < len(tasks):
            current_state = self._session.task_states[next_index]
            # If this task was pre-skipped in review, skip over it
            if current_state.status == TaskStatus.SKIPPED:
                _log.debug("Skipping pre-skipped task", task_index=next_index)
                next_index += 1
                continue
            break
        
        # Check if we've reached the end
        if next_index >= len(tasks):
            _log.debug("All tasks complete (including pre-skipped), finishing routine")
            await self._complete_routine()
            return
        
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

        # Send task started notification if enabled
        if self._notifications_enabled() and routine:
            settings = self._get_notification_settings(routine)
            if settings.notify_on_start:
                await self.notifications.notify_task_started(
                    task=next_task,
                    routine_name=routine.name,
                    task_index=next_index,
                    total_tasks=len(tasks),
                )
                # Mark as sent
                self._session.task_states[next_index].sent_start_notification = True

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
        completed, skipped, total, _active_total = self.get_progress()
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

        # Send completion notification and clear routine targets
        if self._notifications_enabled() and routine:
            await self.notifications.notify_routine_completed(
                routine=routine,
                tasks_completed=completed,
                tasks_skipped=skipped,
                total_duration=elapsed_time,
            )
            await self.notifications.clear_notifications()
            self.notifications.clear_active_routine_targets()

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
        completed, skipped, total, _active_total = self.get_progress()

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
        overdue = -remaining if remaining < 0 else 0
        
        # Get current task state
        current_state = self._session.task_states[self._session.current_task_index]
        
        # Get notification settings
        routine = self.storage.get_routine(self._session.routine_id)
        settings = self._get_notification_settings(routine)
        
        # Determine which timing lists to use based on task mode
        is_auto = task.advancement_mode == AdvancementMode.AUTO
        notify_before = settings.autonext_notify_before if is_auto else settings.notify_before
        notify_remaining = settings.autonext_notify_remaining if is_auto else settings.notify_remaining
        notify_overdue = settings.notify_overdue

        if self._notifications_enabled():
            # Send "time remaining" notifications
            for seconds in notify_remaining:
                if remaining == seconds and seconds not in current_state.sent_remaining_notifications:
                    current_state.sent_remaining_notifications.append(seconds)
                    await self.notifications.notify_time_remaining(task, seconds)
            
            # Send "overdue" notifications (for manual/confirm mode tasks)
            if overdue > 0 and not is_auto:
                for seconds in notify_overdue:
                    if overdue >= seconds and seconds not in current_state.sent_overdue_notifications:
                        current_state.sent_overdue_notifications.append(seconds)
                        await self.notifications.notify_task_overdue(task, seconds)
            
            # Check for upcoming task notifications (notify_before)
            # This sends notifications about the NEXT task
            next_task_index = self._session.current_task_index + 1
            tasks = self._get_session_tasks()
            
            # Find next non-skipped task
            while next_task_index < len(tasks):
                next_state = self._session.task_states[next_task_index]
                if next_state.status != TaskStatus.SKIPPED:
                    break
                next_task_index += 1
            
            if next_task_index < len(tasks) and remaining > 0:
                next_task = tasks[next_task_index]
                next_state = self._session.task_states[next_task_index]
                
                # Time until current task ends = remaining (this is when next task starts)
                for seconds in notify_before:
                    if remaining == seconds and seconds not in next_state.sent_before_notifications:
                        next_state.sent_before_notifications.append(seconds)
                        await self.notifications.notify_time_until_task(next_task, seconds)

        # Legacy: Fire ending soon event  
        warning_time = self.storage.get_setting(
            "task_ending_warning", DEFAULT_TASK_ENDING_WARNING
        )
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

        # Task timer expired - only handle once
        if remaining <= 0 and not self._task_timer_expired:
            self._task_timer_expired = True
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
