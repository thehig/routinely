"""Notification handler for the Routinely integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.notify import ATTR_DATA, ATTR_MESSAGE, ATTR_TITLE
from homeassistant.const import ATTR_NAME

from .const import (
    CONF_NOTIFICATION_TARGETS,
    DOMAIN,
    NotificationAction,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .models import Routine, Task
    from .storage import RoutinelyStorage

_LOGGER = logging.getLogger(__name__)

# Default notification messages (can be overridden per task)
DEFAULT_MESSAGES = {
    "routine_started": "Starting {routine_name} - {total_tasks} tasks, ~{duration_min} minutes",
    "task_started": "{task_name} - {duration_formatted}",
    "task_ending_soon": "{task_name} ending in {seconds_remaining} seconds",
    "task_complete_confirm": "{task_name} complete. Tap to continue or wait {confirm_window}s",
    "task_complete_manual": "{task_name} timer finished. Mark complete when ready.",
    "routine_paused": "{routine_name} paused",
    "routine_resumed": "{routine_name} resumed - {current_task}",
    "routine_completed": "{routine_name} complete! {tasks_completed} tasks in {duration_formatted}",
    "routine_cancelled": "{routine_name} cancelled",
}


class RoutinelyNotifications:
    """Handle notifications for Routinely."""

    def __init__(self, hass: HomeAssistant, storage: RoutinelyStorage) -> None:
        """Initialize notification handler."""
        self.hass = hass
        self.storage = storage

    def _get_targets(self) -> list[str]:
        """Get notification targets from settings."""
        targets = self.storage.get_setting(CONF_NOTIFICATION_TARGETS, "")
        if isinstance(targets, str):
            # Handle comma-separated string
            if not targets:
                return []
            return [t.strip() for t in targets.split(",") if t.strip()]
        return targets or []

    async def async_send(
        self,
        notification_type: str,
        title: str,
        message: str,
        actions: list[NotificationAction] | None = None,
        data: dict[str, Any] | None = None,
        tts_message: str | None = None,
        critical: bool = False,
    ) -> None:
        """Send notification to all configured targets.
        
        Args:
            notification_type: Type identifier for the notification
            title: Notification title
            message: Notification body message
            actions: List of actionable buttons
            data: Additional platform-specific data
            tts_message: Message to be spoken aloud (defaults to message if not set)
            critical: Whether this is a critical/time-sensitive notification
        """
        targets = self._get_targets()
        if not targets:
            _LOGGER.debug("No notification targets configured")
            return

        # Build notification data
        notification_data = self._build_notification_data(
            notification_type=notification_type,
            actions=actions,
            tts_message=tts_message or message,
            critical=critical,
            extra_data=data,
        )

        for target in targets:
            try:
                await self._send_to_target(target, title, message, notification_data)
            except Exception as err:
                _LOGGER.error("Failed to send notification to %s: %s", target, err)

    async def _send_to_target(
        self,
        target: str,
        title: str,
        message: str,
        data: dict[str, Any],
    ) -> None:
        """Send notification to a specific target."""
        service_data = {
            ATTR_TITLE: title,
            ATTR_MESSAGE: message,
            ATTR_DATA: data,
        }

        # Determine service to call
        if target.startswith("mobile_app_"):
            # Mobile app notification
            await self.hass.services.async_call(
                "notify",
                target,
                service_data,
            )
        elif "." in target:
            # Full service path (e.g., notify.my_service)
            domain, service = target.split(".", 1)
            await self.hass.services.async_call(domain, service, service_data)
        else:
            # Assume it's a notify service name
            await self.hass.services.async_call("notify", target, service_data)

    def _build_notification_data(
        self,
        notification_type: str,
        actions: list[NotificationAction] | None,
        tts_message: str,
        critical: bool,
        extra_data: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Build cross-platform notification data with TTS support."""
        data: dict[str, Any] = {
            "tag": f"routinely_{notification_type}",
            "group": "routinely",
        }

        # iOS-specific data for TTS and critical alerts
        # This enables Siri to read notifications aloud
        data["push"] = {
            # Announce notification via Siri TTS
            "sound": {
                "name": "default",
                "critical": 1 if critical else 0,
                "volume": 1.0,
            },
            # iOS 15+ interruption level
            # critical: Breaks through DND/Focus
            # time-sensitive: May break through some Focus modes  
            # active: Normal notification
            # passive: Silent
            "interruption-level": "time-sensitive" if critical else "active",
        }

        # iOS announcement - Siri will speak this
        # Requires "Announce Notifications" enabled in iOS Settings
        data["apns_headers"] = {
            "apns-push-type": "alert",
        }
        
        # Spoken announcement content for iOS
        # This is what Siri will read aloud
        data["tts_text"] = tts_message

        # Android-specific data for TTS
        data["ttl"] = 0
        data["priority"] = "high" if critical else "normal"
        data["channel"] = "routinely_alerts" if critical else "routinely"
        
        # Android TTS via notification channel settings or automation
        data["tts"] = tts_message
        data["speak"] = tts_message  # Alternative TTS field

        # Persistent notification (stays until dismissed)
        data["persistent"] = notification_type in ("task_started", "routine_paused")
        data["sticky"] = data["persistent"]

        # Actionable notification buttons
        if actions:
            data["actions"] = [
                {
                    "action": action.value,
                    "title": self._get_action_title(action),
                    "icon": self._get_action_icon(action),
                }
                for action in actions
            ]

        # Merge extra data
        if extra_data:
            data.update(extra_data)

        return data

    @staticmethod
    def _get_action_title(action: NotificationAction) -> str:
        """Get display title for action button."""
        titles = {
            NotificationAction.PAUSE: "Pause",
            NotificationAction.RESUME: "Resume",
            NotificationAction.SKIP: "Skip",
            NotificationAction.COMPLETE: "Done",
            NotificationAction.CONFIRM: "Continue",
            NotificationAction.SNOOZE: "+30s",
            NotificationAction.CANCEL: "Cancel",
        }
        return titles.get(action, action.value)

    @staticmethod
    def _get_action_icon(action: NotificationAction) -> str:
        """Get icon for action button."""
        icons = {
            NotificationAction.PAUSE: "sfsymbols:pause.fill",
            NotificationAction.RESUME: "sfsymbols:play.fill",
            NotificationAction.SKIP: "sfsymbols:forward.fill",
            NotificationAction.COMPLETE: "sfsymbols:checkmark.circle.fill",
            NotificationAction.CONFIRM: "sfsymbols:arrow.right.circle.fill",
            NotificationAction.SNOOZE: "sfsymbols:clock.badge.plus",
            NotificationAction.CANCEL: "sfsymbols:xmark.circle.fill",
        }
        return icons.get(action, "")

    # High-level notification methods

    async def notify_routine_started(
        self,
        routine: Routine,
        total_tasks: int,
        estimated_duration: int,
    ) -> None:
        """Send routine started notification."""
        duration_min = round(estimated_duration / 60, 1)
        message = DEFAULT_MESSAGES["routine_started"].format(
            routine_name=routine.name,
            total_tasks=total_tasks,
            duration_min=duration_min,
        )
        tts = f"Starting {routine.name}. {total_tasks} tasks, about {int(duration_min)} minutes."

        await self.async_send(
            notification_type="routine_started",
            title=f"▶️ {routine.name}",
            message=message,
            tts_message=tts,
            actions=[NotificationAction.PAUSE, NotificationAction.CANCEL],
        )

    async def notify_task_started(
        self,
        task: Task,
        routine_name: str,
        task_index: int,
        total_tasks: int,
    ) -> None:
        """Send task started notification."""
        duration_formatted = self._format_duration(task.duration)
        
        # Use custom message if set on task, otherwise default
        message = (task.notification_message or DEFAULT_MESSAGES["task_started"]).format(
            task_name=task.name,
            duration_formatted=duration_formatted,
            routine_name=routine_name,
            task_index=task_index + 1,
            total_tasks=total_tasks,
        )
        
        # TTS announcement
        tts = task.tts_message or f"{task.name}. {self._format_duration_spoken(task.duration)}."

        actions = [NotificationAction.SKIP, NotificationAction.PAUSE]
        if task.advancement_mode.value == "manual":
            actions.insert(0, NotificationAction.COMPLETE)

        await self.async_send(
            notification_type="task_started",
            title=f"⏱️ {task.name}",
            message=f"{message} ({task_index + 1}/{total_tasks})",
            tts_message=tts,
            actions=actions,
            critical=False,
        )

    async def notify_task_ending_soon(
        self,
        task: Task,
        seconds_remaining: int,
    ) -> None:
        """Send task ending soon warning."""
        message = DEFAULT_MESSAGES["task_ending_soon"].format(
            task_name=task.name,
            seconds_remaining=seconds_remaining,
        )
        tts = f"{task.name} ending in {seconds_remaining} seconds."

        await self.async_send(
            notification_type="task_ending",
            title=f"⚠️ {task.name}",
            message=message,
            tts_message=tts,
            critical=True,
            actions=[NotificationAction.SKIP, NotificationAction.COMPLETE],
        )

    async def notify_task_awaiting_input(
        self,
        task: Task,
        is_confirm_mode: bool,
        confirm_window: int | None = None,
    ) -> None:
        """Send notification that task needs user input."""
        if is_confirm_mode:
            message = DEFAULT_MESSAGES["task_complete_confirm"].format(
                task_name=task.name,
                confirm_window=confirm_window or 30,
            )
            tts = f"{task.name} complete. Tap continue or snooze."
            actions = [NotificationAction.CONFIRM, NotificationAction.SNOOZE]
        else:
            message = DEFAULT_MESSAGES["task_complete_manual"].format(task_name=task.name)
            tts = f"{task.name} timer finished. Mark complete when ready."
            actions = [NotificationAction.COMPLETE, NotificationAction.SKIP]

        await self.async_send(
            notification_type="awaiting_input",
            title=f"✅ {task.name}",
            message=message,
            tts_message=tts,
            critical=True,
            actions=actions,
        )

    async def notify_routine_paused(self, routine: Routine) -> None:
        """Send routine paused notification."""
        message = DEFAULT_MESSAGES["routine_paused"].format(routine_name=routine.name)
        tts = f"{routine.name} paused."

        await self.async_send(
            notification_type="routine_paused",
            title=f"⏸️ {routine.name}",
            message=message,
            tts_message=tts,
            actions=[NotificationAction.RESUME, NotificationAction.CANCEL],
        )

    async def notify_routine_resumed(
        self,
        routine: Routine,
        current_task: Task,
    ) -> None:
        """Send routine resumed notification."""
        message = DEFAULT_MESSAGES["routine_resumed"].format(
            routine_name=routine.name,
            current_task=current_task.name,
        )
        tts = f"{routine.name} resumed. Current task: {current_task.name}."

        await self.async_send(
            notification_type="routine_resumed",
            title=f"▶️ {routine.name}",
            message=message,
            tts_message=tts,
            actions=[NotificationAction.PAUSE, NotificationAction.SKIP],
        )

    async def notify_routine_completed(
        self,
        routine: Routine,
        tasks_completed: int,
        tasks_skipped: int,
        total_duration: int,
    ) -> None:
        """Send routine completed notification."""
        duration_formatted = self._format_duration(total_duration)
        message = DEFAULT_MESSAGES["routine_completed"].format(
            routine_name=routine.name,
            tasks_completed=tasks_completed,
            duration_formatted=duration_formatted,
        )
        
        tts = f"{routine.name} complete! {tasks_completed} tasks finished in {self._format_duration_spoken(total_duration)}."
        if tasks_skipped > 0:
            tts += f" {tasks_skipped} tasks skipped."

        await self.async_send(
            notification_type="routine_completed",
            title=f"🎉 {routine.name} Complete!",
            message=message,
            tts_message=tts,
        )

    async def notify_routine_cancelled(self, routine: Routine) -> None:
        """Send routine cancelled notification."""
        message = DEFAULT_MESSAGES["routine_cancelled"].format(routine_name=routine.name)
        tts = f"{routine.name} cancelled."

        await self.async_send(
            notification_type="routine_cancelled",
            title=f"⏹️ {routine.name}",
            message=message,
            tts_message=tts,
        )

    async def clear_notifications(self) -> None:
        """Clear all Routinely notifications."""
        targets = self._get_targets()
        for target in targets:
            try:
                # Send clear command
                await self.hass.services.async_call(
                    "notify",
                    target,
                    {
                        ATTR_MESSAGE: "clear_notification",
                        ATTR_DATA: {"tag": "routinely_task_started"},
                    },
                )
            except Exception:
                pass

    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Format seconds as human-readable duration."""
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        secs = seconds % 60
        if secs == 0:
            return f"{minutes}m"
        return f"{minutes}m {secs}s"

    @staticmethod
    def _format_duration_spoken(seconds: int) -> str:
        """Format duration for TTS (spoken)."""
        if seconds < 60:
            return f"{seconds} seconds"
        minutes = seconds // 60
        secs = seconds % 60
        if minutes == 1:
            result = "1 minute"
        else:
            result = f"{minutes} minutes"
        if secs > 0:
            result += f" {secs} seconds"
        return result
