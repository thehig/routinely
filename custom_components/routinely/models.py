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
class Routine:
    """Represents a routine (ordered collection of tasks)."""

    id: str
    name: str
    icon: str = "mdi:playlist-check"
    task_ids: list[str] = field(default_factory=list)
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
        return cls(
            id=data["id"],
            name=data["name"],
            icon=data.get("icon", "mdi:playlist-check"),
            task_ids=data.get("task_ids", []),
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
    actual_duration: int | None = None
    was_auto_advanced: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskState:
        """Create TaskState from dictionary."""
        return cls(
            task_id=data["task_id"],
            status=TaskStatus(data.get("status", "pending")),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            actual_duration=data.get("actual_duration"),
            was_auto_advanced=data.get("was_auto_advanced", False),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert TaskState to dictionary."""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "actual_duration": self.actual_duration,
            "was_auto_advanced": self.was_auto_advanced,
        }


@dataclass
class ExecutionSession:
    """Represents an active or completed routine execution session."""

    id: str
    routine_id: str
    status: SessionStatus = SessionStatus.IDLE
    current_task_index: int = 0
    task_states: list[TaskState] = field(default_factory=list)
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
