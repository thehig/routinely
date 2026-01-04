"""Notification handler for the Routinely integration."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.notify import ATTR_DATA, ATTR_MESSAGE, ATTR_TITLE

from .const import (
    CONF_ENABLE_BROWSER_MOD_TTS,
    CONF_ENABLE_HA_PERSISTENT,
    CONF_ENABLE_TTS,
    CONF_NOTIFICATION_TARGETS,
    CONF_TTS_ENTITY,
    DOMAIN,
    NotificationAction,
)
from .logger import Loggers

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .models import Routine, Task
    from .storage import RoutinelyStorage

_log = Loggers.notifications

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
        self._active_routine_targets: str | None = None

    def set_active_routine_targets(self, targets: str | None) -> None:
        """Set notification targets for the active routine.
        
        Args:
            targets: Comma-separated targets, or None to use global defaults
        """
        self._active_routine_targets = targets
        _log.debug("Active routine targets set", targets=targets)

    def clear_active_routine_targets(self) -> None:
        """Clear routine-specific targets (use global defaults)."""
        self._active_routine_targets = None

    def _get_targets(self) -> list[str]:
        """Get notification targets from settings.
        
        Uses routine-specific targets if set, otherwise global targets.
        """
        # Check for routine-specific targets first
        if self._active_routine_targets:
            return [t.strip() for t in self._active_routine_targets.split(",") if t.strip()]
        
        # Fall back to global targets
        targets = self.storage.get_setting(CONF_NOTIFICATION_TARGETS, "")
        if isinstance(targets, str):
            # Handle comma-separated string
            if not targets:
                return []
            return [t.strip() for t in targets.split(",") if t.strip()]
        return targets or []

    def _tts_enabled(self) -> bool:
        """Check if TTS via speaker is enabled."""
        return bool(
            self.storage.get_setting(CONF_ENABLE_TTS, False)
            and self.storage.get_setting(CONF_TTS_ENTITY, "")
        )

    def _browser_mod_tts_enabled(self) -> bool:
        """Check if browser_mod TTS is enabled."""
        return bool(self.storage.get_setting(CONF_ENABLE_BROWSER_MOD_TTS, False))

    def _ha_persistent_enabled(self) -> bool:
        """Check if HA persistent notifications (toasts) are enabled."""
        return bool(self.storage.get_setting(CONF_ENABLE_HA_PERSISTENT, False))

    async def _speak_tts(self, message: str) -> None:
        """Speak message via configured TTS entity (HomePod, Google Home, etc).
        
        This provides TTS for iOS users since iOS doesn't support TTS in notifications.
        Also useful for any user who wants announcements on smart speakers.
        """
        if not self._tts_enabled():
            return

        tts_entity = self.storage.get_setting(CONF_TTS_ENTITY, "")
        if not tts_entity:
            return

        try:
            # Try tts.speak service first (newer HA versions)
            # This works with media_player entities
            await self.hass.services.async_call(
                "tts",
                "speak",
                {
                    "entity_id": tts_entity,
                    "message": message,
                    "media_player_entity_id": tts_entity,
                },
                blocking=False,
            )
            _log.debug("TTS spoken via tts.speak", entity=tts_entity)
        except Exception as err:
            _log.debug("tts.speak failed, trying cloud_say", error=str(err))
            try:
                # Fallback: try tts.cloud_say for cloud TTS
                await self.hass.services.async_call(
                    "tts",
                    "cloud_say",
                    {
                        "entity_id": tts_entity,
                        "message": message,
                    },
                    blocking=False,
                )
                _log.debug("TTS spoken via tts.cloud_say", entity=tts_entity)
            except Exception as err2:
                _log.error(
                    "Failed to speak TTS",
                    entity=tts_entity,
                    error=str(err2),
                )

    async def _speak_browser_mod_tts(self, message: str) -> None:
        """Speak message via browser_mod using Web Speech API.
        
        This works on iOS Safari and any browser with Web Speech API support.
        Requires browser_mod integration to be installed and browsers registered.
        
        Uses the browser's built-in speechSynthesis API to speak text directly
        on the device - perfect for iOS devices viewing HA dashboards.
        """
        if not self._browser_mod_tts_enabled():
            return

        # Check if browser_mod is available
        if not self.hass.services.has_service("browser_mod", "javascript"):
            _log.debug("browser_mod.javascript service not available")
            return

        # Escape the message for JavaScript string
        escaped_message = message.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
        
        # JavaScript code to speak using Web Speech API
        # This works on iOS Safari, Chrome, Firefox, Edge, etc.
        js_code = f"""
            if ('speechSynthesis' in window) {{
                const utterance = new SpeechSynthesisUtterance('{escaped_message}');
                utterance.rate = 1.0;
                utterance.pitch = 1.0;
                utterance.volume = 1.0;
                speechSynthesis.speak(utterance);
            }}
        """

        try:
            # Call browser_mod.javascript on all registered browsers
            await self.hass.services.async_call(
                "browser_mod",
                "javascript",
                {"code": js_code},
                blocking=False,
            )
            _log.debug("browser_mod TTS spoken", message=message[:50])
        except Exception as err:
            _log.error("Failed to speak via browser_mod", error=str(err))

    async def _send_ha_persistent(
        self,
        notification_type: str,
        title: str,
        message: str,
    ) -> None:
        """Send a Home Assistant persistent notification (toast).
        
        This shows a notification in the HA UI sidebar and as a toast message.
        Useful for users who keep HA open on a tablet or browser.
        """
        if not self._ha_persistent_enabled():
            return

        notification_id = f"routinely_{notification_type}"
        
        try:
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": title,
                    "message": message,
                    "notification_id": notification_id,
                },
                blocking=False,
            )
            _log.debug("HA persistent notification sent", notification_id=notification_id)
        except Exception as err:
            _log.error("Failed to send HA persistent notification", error=str(err))

    async def async_send(
        self,
        notification_type: str,
        title: str,
        message: str,
        actions: list[NotificationAction] | None = None,
        data: dict[str, Any] | None = None,
        tts_message: str | None = None,
        critical: bool = False,
        override_targets: str | None = None,
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
            override_targets: Optional comma-separated targets to use instead of global
        """
        # Use override targets if provided, otherwise use global
        if override_targets:
            targets = [t.strip() for t in override_targets.split(",") if t.strip()]
        else:
            targets = self._get_targets()
        
        if not targets:
            _log.debug("No notification targets configured, skipping notification")
            return

        _log.debug(
            "Sending notification",
            type=notification_type,
            targets=targets,
            critical=critical,
        )

        tts_text = tts_message or message

        # Speak via TTS entity if configured (for iOS users and smart speakers)
        if tts_text and self._tts_enabled():
            await self._speak_tts(tts_text)

        # Speak via browser_mod if configured (for iOS Safari and other browsers)
        if tts_text and self._browser_mod_tts_enabled():
            await self._speak_browser_mod_tts(tts_text)

        # Send HA persistent notification (toast) if configured
        if self._ha_persistent_enabled():
            await self._send_ha_persistent(notification_type, title, message)

        for target in targets:
            try:
                # Build platform-specific notification data per target
                notification_data = self._build_notification_data(
                    notification_type=notification_type,
                    actions=actions,
                    tts_message=tts_text,
                    critical=critical,
                    extra_data=data,
                    target=target,
                )
                # For Android TTS, message must be "TTS" to trigger speech
                # See: https://companion.home-assistant.io/docs/notifications/notifications-basic/#text-to-speech-notifications
                effective_message = message
                if self._is_android_target(target) and tts_text:
                    # Use "TTS" to trigger speech mode on Android
                    # The actual text is in data.tts_text
                    effective_message = "TTS"
                    # Store the original message for reference
                    notification_data["message_text"] = message
                
                await self._send_to_target(target, title, effective_message, notification_data)
                _log.debug("Notification sent", target=target, type=notification_type)
            except Exception as err:
                _log.error(
                    "Failed to send notification",
                    target=target,
                    error=str(err),
                )

    @staticmethod
    def _is_android_target(target: str) -> bool:
        """Check if target is likely an Android device.
        
        Android device IDs often contain 'android' or lack 'iphone/ipad'.
        This is heuristic - users can override via settings if needed.
        """
        target_lower = target.lower()
        # Explicit android indicators
        if "android" in target_lower or "pixel" in target_lower or "galaxy" in target_lower:
            return True
        # iOS indicators - if present, it's not Android
        if "iphone" in target_lower or "ipad" in target_lower or "ios" in target_lower:
            return False
        # Default to Android for mobile_app_ targets without iOS indicators
        # (Android is more common and benefits more from TTS critical)
        return target.startswith("mobile_app_")

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
        target: str = "",
    ) -> dict[str, Any]:
        """Build cross-platform notification data with TTS support.
        
        Critical notification implementation based on:
        https://companion.home-assistant.io/docs/notifications/critical-notifications/
        
        iOS (top priority):
        - push.sound.critical: 1 - bypasses DND/mute
        - push.sound.volume: 1.0 - max volume
        - push.interruption-level: "critical" - highest priority
        
        Android (second priority):
        - ttl: 0 - immediate delivery
        - priority: high - high priority FCM
        - media_stream: alarm_stream_max - TTS at max volume, reverts after
        - tts_text: "<message>" - text to speak
        - message: "TTS" - triggers TTS mode (handled in caller)
        """
        is_android = self._is_android_target(target)
        
        data: dict[str, Any] = {
            "tag": f"routinely_{notification_type}",
            "group": "routinely",
        }

        # ============================================================
        # iOS Critical Notifications (TOP PRIORITY)
        # See: https://companion.home-assistant.io/docs/notifications/critical-notifications/#ios
        # ============================================================
        if critical:
            # Critical alert: bypasses DND, plays sound even when muted
            data["push"] = {
                "sound": {
                    "name": "default",
                    "critical": 1,
                    "volume": 1.0,  # Maximum volume
                },
                # Critical interruption level - highest priority on iOS
                # Breaks through all DND/Focus modes
                "interruption-level": "critical",
            }
        else:
            data["push"] = {
                "sound": {
                    "name": "default",
                    "critical": 0,
                    "volume": 0.8,
                },
                # time-sensitive: May break through some Focus modes
                # active: Normal notification
                "interruption-level": "time-sensitive",
            }

        # iOS announcement - Siri speaks this on AirPods/CarPlay/HomePod
        data["apns_headers"] = {
            "apns-push-type": "alert",
        }

        # ============================================================
        # Android Critical Notifications with TTS (SECOND PRIORITY)
        # See: https://companion.home-assistant.io/docs/notifications/critical-notifications/#android
        # ============================================================
        # Base Android settings for high priority delivery
        data["ttl"] = 0  # Immediate delivery, no FCM delay
        data["priority"] = "high"  # High priority FCM message
        
        if critical:
            # Android TTS at maximum volume using alarm stream
            # This will:
            # 1. Play from alarm stream (rings even on vibrate/silent)
            # 2. Set volume to max
            # 3. Speak the tts_text
            # 4. Revert volume to original level after speaking
            data["media_stream"] = "alarm_stream_max"
            data["tts_text"] = tts_message
            data["channel"] = "alarm_stream"  # Use alarm channel
        else:
            # Non-critical: standard TTS on notification stream
            data["tts_text"] = tts_message
            data["channel"] = "routinely"

        # Legacy TTS fields for compatibility
        data["tts"] = tts_message
        data["speak"] = tts_message

        # Persistent notification (stays until dismissed)
        data["persistent"] = notification_type in ("task_started", "routine_paused")
        data["sticky"] = data["persistent"]

        # Actionable notification buttons
        if actions:
            data["actions"] = []
            for action in actions:
                action_data = {
                    "action": action.value,
                    "title": self._get_action_title(action),
                }
                # iOS SF Symbols icon
                icon = self._get_action_icon(action)
                if icon:
                    action_data["icon"] = icon
                # Destructive actions show in red on iOS
                if action in (NotificationAction.CANCEL, NotificationAction.SKIP):
                    action_data["destructive"] = True
                # Auth required actions need device unlock
                if action in (NotificationAction.CANCEL,):
                    action_data["authenticationRequired"] = True
                data["actions"].append(action_data)

        # Merge extra data (allows per-notification overrides)
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

    async def notify_time_until_task(
        self,
        task: Task,
        seconds_until: int,
    ) -> None:
        """Send notification about upcoming task."""
        time_str = self._format_duration_spoken(seconds_until)
        message = f"{time_str} until {task.name}"
        tts = f"{time_str} until {task.name}."

        await self.async_send(
            notification_type="task_upcoming",
            title=f"⏰ {task.name}",
            message=message,
            tts_message=tts,
            critical=False,
            actions=[NotificationAction.PAUSE],
        )

    async def notify_time_remaining(
        self,
        task: Task,
        seconds_remaining: int,
    ) -> None:
        """Send notification about time remaining in task."""
        time_str = self._format_duration_spoken(seconds_remaining)
        message = f"{time_str} remaining in {task.name}"
        tts = f"{time_str} remaining in {task.name}."

        await self.async_send(
            notification_type="task_remaining",
            title=f"⏱️ {task.name}",
            message=message,
            tts_message=tts,
            critical=False,
            actions=[NotificationAction.COMPLETE, NotificationAction.SKIP],
        )

    async def notify_task_overdue(
        self,
        task: Task,
        seconds_overdue: int,
    ) -> None:
        """Send notification that task is overdue."""
        time_str = self._format_duration_spoken(seconds_overdue)
        message = f"{time_str} over on {task.name}"
        tts = f"{time_str} over on {task.name}."

        await self.async_send(
            notification_type="task_overdue",
            title=f"⚠️ {task.name} Overdue",
            message=message,
            tts_message=tts,
            critical=True,
            actions=[NotificationAction.COMPLETE, NotificationAction.SKIP],
        )

    async def notify_task_complete(
        self,
        task: Task,
    ) -> None:
        """Send notification that task has completed."""
        message = f"{task.name} completed"
        tts = f"{task.name} completed."

        await self.async_send(
            notification_type="task_completed",
            title=f"✅ {task.name}",
            message=message,
            tts_message=tts,
            critical=False,
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
