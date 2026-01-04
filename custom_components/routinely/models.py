"""Data models for the Routinely integration."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid

from .const import AdvancementMode, SessionStatus, TaskStatus


def generate_id() -> str:
    """Generate a unique ID."""
    return uuid.uuid4().hex[:12]


@dataclass
class Task:
    """Represents a single task."""

    id: str
    name: str
    duration: int  # seconds
    icon: str = "mdi:checkbox-marked-circle-outline"
    advancement_mode: AdvancementMode = AdvancementMode.AUTO
    confirm_window: int | None = None
    description: str | None = None
    notification_message: str | None = None  # Custom notification text
    tts_message: str | None = None  # Custom TTS announcement text
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        """Set timestamps if not provided."""
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        """Create Task from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            duration=data["duration"],
            icon=data.get("icon", "mdi:checkbox-marked-circle-outline"),
            advancement_mode=AdvancementMode(data.get("advancement_mode", "auto")),
            confirm_window=data.get("confirm_window"),
            description=data.get("description"),
            notification_message=data.get("notification_message"),
            tts_message=data.get("tts_message"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert Task to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "duration": self.duration,
            "icon": self.icon,
            "advancement_mode": self.advancement_mode.value,
            "confirm_window": self.confirm_window,
            "description": self.description,
            "notification_message": self.notification_message,
            "tts_message": self.tts_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class NotificationSettings:
    """Notification timing settings."""
    
    # Notifications before task starts (seconds)
    notify_before: list[int] = field(default_factory=lambda: [600, 300, 60])
    # Notify when task starts
    notify_on_start: bool = True
    # Notifications for time remaining (seconds)
    notify_remaining: list[int] = field(default_factory=lambda: [300, 60])
    # Notifications when overdue (seconds)
    notify_overdue: list[int] = field(default_factory=lambda: [60, 300, 600])
    # Notify when task completes
    notify_on_complete: bool = False
    # Auto-next specific (different timing for auto-advancing tasks)
    autonext_notify_before: list[int] = field(default_factory=lambda: [300, 60])
    autonext_notify_remaining: list[int] = field(default_factory=lambda: [60])
    # Per-routine notification targets (None = use global targets)
    notification_targets: str | None = None  # Comma-separated targets
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationSettings":
        """Create NotificationSettings from dictionary."""
        return cls(
            notify_before=data.get("notify_before", [600, 300, 60]),
            notify_on_start=data.get("notify_on_start", True),
            notify_remaining=data.get("notify_remaining", [300, 60]),
            notify_overdue=data.get("notify_overdue", [60, 300, 600]),
            notify_on_complete=data.get("notify_on_complete", False),
            autonext_notify_before=data.get("autonext_notify_before", [300, 60]),
            autonext_notify_remaining=data.get("autonext_notify_remaining", [60]),
            notification_targets=data.get("notification_targets"),
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "notify_before": self.notify_before,
            "notify_on_start": self.notify_on_start,
            "notify_remaining": self.notify_remaining,
            "notify_overdue": self.notify_overdue,
            "notify_on_complete": self.notify_on_complete,
            "autonext_notify_before": self.autonext_notify_before,
            "autonext_notify_remaining": self.autonext_notify_remaining,
            "notification_targets": self.notification_targets,
        }


@dataclass
class Routine:
    """Represents a routine (ordered collection of tasks)."""

    id: str
    name: str
    icon: str = "mdi:playlist-check"
    task_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    # Schedule fields (for UI display, actual scheduling via HA automations)
    schedule_time: str | None = None  # e.g., "08:00"
    schedule_days: list[str] = field(default_factory=list)  # e.g., ["mon", "tue", "wed"]
    # Notification settings override (None = use global defaults)
    notification_settings: NotificationSettings | None = None
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        """Set timestamps if not provided."""
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Routine:
        """Create Routine from dictionary."""
        notif_data = data.get("notification_settings")
        notif_settings = NotificationSettings.from_dict(notif_data) if notif_data else None
        return cls(
            id=data["id"],
            name=data["name"],
            icon=data.get("icon", "mdi:playlist-check"),
            task_ids=data.get("task_ids", []),
            tags=data.get("tags", []),
            schedule_time=data.get("schedule_time"),
            schedule_days=data.get("schedule_days", []),
            notification_settings=notif_settings,
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert Routine to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "task_ids": self.task_ids,
            "tags": self.tags,
            "schedule_time": self.schedule_time,
            "schedule_days": self.schedule_days,
            "notification_settings": self.notification_settings.to_dict() if self.notification_settings else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class TaskState:
    """State of a task within an execution session."""

    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    started_at: str | None = None
    completed_at: str | None = None
    skipped_at: str | None = None
    actual_duration: int | None = None
    was_auto_advanced: bool = False
    # Track which notifications have been sent (seconds values)
    sent_before_notifications: list[int] = field(default_factory=list)
    sent_remaining_notifications: list[int] = field(default_factory=list)
    sent_overdue_notifications: list[int] = field(default_factory=list)
    sent_start_notification: bool = False
    sent_complete_notification: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskState":
        """Create TaskState from dictionary."""
        return cls(
            task_id=data["task_id"],
            status=TaskStatus(data.get("status", "pending")),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            skipped_at=data.get("skipped_at"),
            actual_duration=data.get("actual_duration"),
            was_auto_advanced=data.get("was_auto_advanced", False),
            sent_before_notifications=data.get("sent_before_notifications", []),
            sent_remaining_notifications=data.get("sent_remaining_notifications", []),
            sent_overdue_notifications=data.get("sent_overdue_notifications", []),
            sent_start_notification=data.get("sent_start_notification", False),
            sent_complete_notification=data.get("sent_complete_notification", False),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert TaskState to dictionary."""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "skipped_at": self.skipped_at,
            "actual_duration": self.actual_duration,
            "was_auto_advanced": self.was_auto_advanced,
            "sent_before_notifications": self.sent_before_notifications,
            "sent_remaining_notifications": self.sent_remaining_notifications,
            "sent_overdue_notifications": self.sent_overdue_notifications,
            "sent_start_notification": self.sent_start_notification,
            "sent_complete_notification": self.sent_complete_notification,
        }


@dataclass
class ExecutionSession:
    """Represents an active or completed routine execution session."""

    id: str
    routine_id: str
    status: SessionStatus = SessionStatus.IDLE
    current_task_index: int = 0
    task_states: list[TaskState] = field(default_factory=list)
    task_ids: list[str] = field(default_factory=list)  # Ordered task IDs for this session
    started_at: str | None = None
    paused_at: str | None = None
    completed_at: str | None = None
    elapsed_time: int = 0
    task_elapsed_time: int = 0
    confirm_window_active: bool = False
    confirm_window_remaining: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionSession:
        """Create ExecutionSession from dictionary."""
        task_states = [TaskState.from_dict(ts) for ts in data.get("task_states", [])]
        return cls(
            id=data["id"],
            routine_id=data["routine_id"],
            status=SessionStatus(data.get("status", "idle")),
            current_task_index=data.get("current_task_index", 0),
            task_states=task_states,
            task_ids=data.get("task_ids", []),
            started_at=data.get("started_at"),
            paused_at=data.get("paused_at"),
            completed_at=data.get("completed_at"),
            elapsed_time=data.get("elapsed_time", 0),
            task_elapsed_time=data.get("task_elapsed_time", 0),
            confirm_window_active=data.get("confirm_window_active", False),
            confirm_window_remaining=data.get("confirm_window_remaining", 0),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert ExecutionSession to dictionary."""
        return {
            "id": self.id,
            "routine_id": self.routine_id,
            "status": self.status.value,
            "current_task_index": self.current_task_index,
            "task_states": [ts.to_dict() for ts in self.task_states],
            "task_ids": self.task_ids,
            "started_at": self.started_at,
            "paused_at": self.paused_at,
            "completed_at": self.completed_at,
            "elapsed_time": self.elapsed_time,
            "task_elapsed_time": self.task_elapsed_time,
            "confirm_window_active": self.confirm_window_active,
            "confirm_window_remaining": self.confirm_window_remaining,
        }


@dataclass
class SessionHistory:
    """Completed session record for history."""

    id: str
    routine_id: str
    routine_name: str
    status: SessionStatus
    started_at: str
    completed_at: str
    total_duration: int
    tasks_completed: int
    tasks_skipped: int
    total_tasks: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionHistory:
        """Create SessionHistory from dictionary."""
        return cls(
            id=data["id"],
            routine_id=data["routine_id"],
            routine_name=data["routine_name"],
            status=SessionStatus(data["status"]),
            started_at=data["started_at"],
            completed_at=data["completed_at"],
            total_duration=data["total_duration"],
            tasks_completed=data["tasks_completed"],
            tasks_skipped=data["tasks_skipped"],
            total_tasks=data["total_tasks"],
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert SessionHistory to dictionary."""
        return {
            "id": self.id,
            "routine_id": self.routine_id,
            "routine_name": self.routine_name,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_duration": self.total_duration,
            "tasks_completed": self.tasks_completed,
            "tasks_skipped": self.tasks_skipped,
            "total_tasks": self.total_tasks,
        }
