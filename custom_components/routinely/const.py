"""Constants for the Routinely integration."""
from enum import StrEnum
from typing import Final

DOMAIN: Final = "routinely"
STORAGE_VERSION: Final = 1
STORAGE_KEY: Final = f"{DOMAIN}.storage"

# Defaults
DEFAULT_TASK_ENDING_WARNING: Final = 10
DEFAULT_ADVANCEMENT_MODE: Final = "auto"
DEFAULT_CONFIRM_WINDOW: Final = 30
DEFAULT_SNOOZE_DURATION: Final = 30

# Limits
MIN_TASK_DURATION: Final = 1
MAX_TASK_DURATION: Final = 86400
MIN_CONFIRM_WINDOW: Final = 5
MAX_CONFIRM_WINDOW: Final = 300
MAX_NAME_LENGTH: Final = 100
MAX_DESCRIPTION_LENGTH: Final = 500


class AdvancementMode(StrEnum):
    """Task advancement modes."""

    AUTO = "auto"
    MANUAL = "manual"
    CONFIRM = "confirm"


class SessionStatus(StrEnum):
    """Routine execution session status."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskStatus(StrEnum):
    """Task status within a session."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class NotificationAction(StrEnum):
    """Notification action button identifiers."""

    PAUSE = "ROUTINELY_PAUSE"
    RESUME = "ROUTINELY_RESUME"
    SKIP = "ROUTINELY_SKIP"
    COMPLETE = "ROUTINELY_COMPLETE"
    CONFIRM = "ROUTINELY_CONFIRM"
    SNOOZE = "ROUTINELY_SNOOZE"
    CANCEL = "ROUTINELY_CANCEL"


# Events
EVENT_ROUTINE_STARTED: Final = f"{DOMAIN}_routine_started"
EVENT_ROUTINE_PAUSED: Final = f"{DOMAIN}_routine_paused"
EVENT_ROUTINE_RESUMED: Final = f"{DOMAIN}_routine_resumed"
EVENT_ROUTINE_COMPLETED: Final = f"{DOMAIN}_routine_completed"
EVENT_ROUTINE_CANCELLED: Final = f"{DOMAIN}_routine_cancelled"
EVENT_TASK_STARTED: Final = f"{DOMAIN}_task_started"
EVENT_TASK_ENDING_SOON: Final = f"{DOMAIN}_task_ending_soon"
EVENT_TASK_COMPLETED: Final = f"{DOMAIN}_task_completed"
EVENT_TASK_SKIPPED: Final = f"{DOMAIN}_task_skipped"
EVENT_TASK_AWAITING_INPUT: Final = f"{DOMAIN}_task_awaiting_input"

# Services
SERVICE_CREATE_TASK: Final = "create_task"
SERVICE_UPDATE_TASK: Final = "update_task"
SERVICE_DELETE_TASK: Final = "delete_task"
SERVICE_CREATE_ROUTINE: Final = "create_routine"
SERVICE_UPDATE_ROUTINE: Final = "update_routine"
SERVICE_DELETE_ROUTINE: Final = "delete_routine"
SERVICE_ADD_TASK_TO_ROUTINE: Final = "add_task_to_routine"
SERVICE_REMOVE_TASK_FROM_ROUTINE: Final = "remove_task_from_routine"
SERVICE_REORDER_ROUTINE: Final = "reorder_routine"
SERVICE_START: Final = "start"
SERVICE_PAUSE: Final = "pause"
SERVICE_RESUME: Final = "resume"
SERVICE_SKIP: Final = "skip"
SERVICE_COMPLETE_TASK: Final = "complete_task"
SERVICE_CANCEL: Final = "cancel"
SERVICE_CONFIRM: Final = "confirm"
SERVICE_SNOOZE: Final = "snooze"
SERVICE_ADJUST_TIME: Final = "adjust_time"
SERVICE_TEST_NOTIFICATION: Final = "test_notification"

# Attributes
ATTR_TASK_ID: Final = "task_id"
ATTR_TASK_NAME: Final = "task_name"
ATTR_ROUTINE_ID: Final = "routine_id"
ATTR_ROUTINE_NAME: Final = "routine_name"
ATTR_DURATION: Final = "duration"
ATTR_ICON: Final = "icon"
ATTR_DESCRIPTION: Final = "description"
ATTR_ADVANCEMENT_MODE: Final = "advancement_mode"
ATTR_CONFIRM_WINDOW: Final = "confirm_window"
ATTR_TASK_IDS: Final = "task_ids"
ATTR_POSITION: Final = "position"
ATTR_SECONDS: Final = "seconds"
ATTR_TOTAL_TASKS: Final = "total_tasks"
ATTR_COMPLETED_TASKS: Final = "completed_tasks"
ATTR_SKIPPED_TASKS: Final = "skipped_tasks"
ATTR_CURRENT_TASK_INDEX: Final = "current_task_index"
ATTR_CURRENT_TASK_NAME: Final = "current_task_name"
ATTR_CURRENT_TASK_DURATION: Final = "current_task_duration"
ATTR_ESTIMATED_DURATION: Final = "estimated_duration"
ATTR_ELAPSED_TIME: Final = "elapsed_time"
ATTR_TIME_REMAINING: Final = "time_remaining"
ATTR_STARTED_AT: Final = "started_at"
ATTR_WAS_AUTO_ADVANCED: Final = "was_auto_advanced"
ATTR_ACTUAL_DURATION: Final = "actual_duration"
ATTR_PROGRESS: Final = "progress"

# Config
CONF_NOTIFICATION_TARGETS: Final = "notification_targets"
CONF_TASK_ENDING_WARNING: Final = "task_ending_warning"
CONF_DEFAULT_ADVANCEMENT_MODE: Final = "default_advancement_mode"
CONF_ENABLE_TTS: Final = "enable_tts"
CONF_TTS_ENTITY: Final = "tts_entity"
CONF_ENABLE_BROWSER_MOD_TTS: Final = "enable_browser_mod_tts"
CONF_ENABLE_HA_PERSISTENT: Final = "enable_ha_persistent"
CONF_ENABLE_NOTIFICATIONS: Final = "enable_notifications"
CONF_LOG_LEVEL: Final = "log_level"

# Log levels
LOG_LEVEL_DEBUG: Final = "debug"
LOG_LEVEL_INFO: Final = "info"
LOG_LEVEL_WARNING: Final = "warning"
LOG_LEVEL_ERROR: Final = "error"
DEFAULT_LOG_LEVEL: Final = LOG_LEVEL_INFO

# Task notification attributes
ATTR_NOTIFICATION_MESSAGE: Final = "notification_message"
ATTR_TTS_MESSAGE: Final = "tts_message"

# Notification timing settings
CONF_NOTIFY_BEFORE: Final = "notify_before"  # List of seconds before task starts
CONF_NOTIFY_ON_START: Final = "notify_on_start"
CONF_NOTIFY_REMAINING: Final = "notify_remaining"  # List of seconds remaining
CONF_NOTIFY_OVERDUE: Final = "notify_overdue"  # List of seconds overdue
CONF_NOTIFY_ON_COMPLETE: Final = "notify_on_complete"

# Default notification timings (in seconds)
DEFAULT_NOTIFY_BEFORE: Final = [600, 300, 60]  # 10, 5, 1 min before
DEFAULT_NOTIFY_REMAINING: Final = [300, 60]  # 5, 1 min remaining  
DEFAULT_NOTIFY_OVERDUE: Final = [60, 300, 600]  # 1, 5, 10 min overdue
DEFAULT_NOTIFY_ON_START: Final = True
DEFAULT_NOTIFY_ON_COMPLETE: Final = False

# Auto-next specific notification timings
CONF_AUTONEXT_NOTIFY_BEFORE: Final = "autonext_notify_before"
CONF_AUTONEXT_NOTIFY_REMAINING: Final = "autonext_notify_remaining"
DEFAULT_AUTONEXT_NOTIFY_BEFORE: Final = [300, 60]  # 5, 1 min before
DEFAULT_AUTONEXT_NOTIFY_REMAINING: Final = [60]  # 1 min remaining
