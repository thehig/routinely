"""Service handlers for the Routinely integration."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.core import ServiceCall, callback
from homeassistant.helpers import config_validation as cv

from .logger import Loggers
from .models import NotificationSettings

from .const import (
    ATTR_ADVANCEMENT_MODE,
    ATTR_CONFIRM_WINDOW,
    ATTR_DESCRIPTION,
    ATTR_DURATION,
    ATTR_ICON,
    ATTR_NOTIFICATION_MESSAGE,
    ATTR_POSITION,
    ATTR_ROUTINE_ID,
    ATTR_ROUTINE_NAME,
    ATTR_SECONDS,
    ATTR_TASK_ID,
    ATTR_TASK_IDS,
    ATTR_TASK_NAME,
    ATTR_TTS_MESSAGE,
    DEFAULT_ADVANCEMENT_MODE,
    DEFAULT_SNOOZE_DURATION,
    DOMAIN,
    MAX_DESCRIPTION_LENGTH,
    MAX_NAME_LENGTH,
    MAX_TASK_DURATION,
    MIN_CONFIRM_WINDOW,
    MIN_TASK_DURATION,
    SERVICE_ADD_TASK_TO_ROUTINE,
    SERVICE_CANCEL,
    SERVICE_COMPLETE_TASK,
    SERVICE_CONFIRM,
    SERVICE_CREATE_ROUTINE,
    SERVICE_CREATE_TASK,
    SERVICE_DELETE_ROUTINE,
    SERVICE_DELETE_TASK,
    SERVICE_PAUSE,
    SERVICE_REMOVE_TASK_FROM_ROUTINE,
    SERVICE_REORDER_ROUTINE,
    SERVICE_RESUME,
    SERVICE_SKIP,
    SERVICE_SNOOZE,
    SERVICE_START,
    SERVICE_UPDATE_ROUTINE,
    SERVICE_UPDATE_TASK,
    AdvancementMode,
    NotificationAction,
)
from .models import Routine, Task, generate_id

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .coordinator import RoutinelyCoordinator
    from .storage import RoutinelyStorage

_log = Loggers.services

# Service schemas
SCHEMA_CREATE_TASK = vol.Schema(
    {
        vol.Required(ATTR_TASK_NAME): cv.string,
        vol.Required(ATTR_DURATION): vol.All(
            vol.Coerce(int), vol.Range(min=MIN_TASK_DURATION, max=MAX_TASK_DURATION)
        ),
        vol.Optional(ATTR_ICON): cv.string,
        vol.Optional(ATTR_ADVANCEMENT_MODE, default=DEFAULT_ADVANCEMENT_MODE): vol.In(
            [m.value for m in AdvancementMode]
        ),
        vol.Optional(ATTR_CONFIRM_WINDOW): vol.All(
            vol.Coerce(int), vol.Range(min=MIN_CONFIRM_WINDOW)
        ),
        vol.Optional(ATTR_DESCRIPTION): vol.All(
            cv.string, vol.Length(max=MAX_DESCRIPTION_LENGTH)
        ),
        vol.Optional(ATTR_NOTIFICATION_MESSAGE): vol.All(
            cv.string, vol.Length(max=MAX_DESCRIPTION_LENGTH)
        ),
        vol.Optional(ATTR_TTS_MESSAGE): vol.All(
            cv.string, vol.Length(max=MAX_DESCRIPTION_LENGTH)
        ),
    }
)

SCHEMA_UPDATE_TASK = vol.Schema(
    {
        vol.Required(ATTR_TASK_ID): cv.string,
        vol.Optional(ATTR_TASK_NAME): vol.All(
            cv.string, vol.Length(max=MAX_NAME_LENGTH)
        ),
        vol.Optional(ATTR_DURATION): vol.All(
            vol.Coerce(int), vol.Range(min=MIN_TASK_DURATION, max=MAX_TASK_DURATION)
        ),
        vol.Optional(ATTR_ICON): cv.string,
        vol.Optional(ATTR_ADVANCEMENT_MODE): vol.In(
            [m.value for m in AdvancementMode]
        ),
        vol.Optional(ATTR_CONFIRM_WINDOW): vol.All(
            vol.Coerce(int), vol.Range(min=MIN_CONFIRM_WINDOW)
        ),
        vol.Optional(ATTR_DESCRIPTION): vol.All(
            cv.string, vol.Length(max=MAX_DESCRIPTION_LENGTH)
        ),
        vol.Optional(ATTR_NOTIFICATION_MESSAGE): vol.All(
            cv.string, vol.Length(max=MAX_DESCRIPTION_LENGTH)
        ),
        vol.Optional(ATTR_TTS_MESSAGE): vol.All(
            cv.string, vol.Length(max=MAX_DESCRIPTION_LENGTH)
        ),
    }
)

SCHEMA_DELETE_TASK = vol.Schema({vol.Required(ATTR_TASK_ID): cv.string})

SCHEMA_CREATE_ROUTINE = vol.Schema(
    {
        vol.Required(ATTR_ROUTINE_NAME): vol.All(
            cv.string, vol.Length(max=MAX_NAME_LENGTH)
        ),
        vol.Optional(ATTR_ICON): cv.string,
        vol.Optional(ATTR_TASK_IDS): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("tags"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("schedule_time"): vol.Any(cv.string, None),
        vol.Optional("schedule_days"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("notification_settings"): vol.Any(dict, None),
    }
)

SCHEMA_UPDATE_ROUTINE = vol.Schema(
    {
        vol.Required(ATTR_ROUTINE_ID): cv.string,
        vol.Optional(ATTR_ROUTINE_NAME): vol.All(
            cv.string, vol.Length(max=MAX_NAME_LENGTH)
        ),
        vol.Optional(ATTR_ICON): cv.string,
        vol.Optional(ATTR_TASK_IDS): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("tags"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("schedule_time"): vol.Any(cv.string, None),
        vol.Optional("schedule_days"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("notification_settings"): vol.Any(dict, None),
    }
)

SCHEMA_DELETE_ROUTINE = vol.Schema({vol.Required(ATTR_ROUTINE_ID): cv.string})

SCHEMA_ADD_TASK_TO_ROUTINE = vol.Schema(
    {
        vol.Required(ATTR_ROUTINE_ID): cv.string,
        vol.Required(ATTR_TASK_ID): cv.string,
        vol.Optional(ATTR_POSITION): vol.Coerce(int),
    }
)

SCHEMA_REMOVE_TASK_FROM_ROUTINE = vol.Schema(
    {
        vol.Required(ATTR_ROUTINE_ID): cv.string,
        vol.Required(ATTR_POSITION): vol.Coerce(int),
    }
)

SCHEMA_REORDER_ROUTINE = vol.Schema(
    {
        vol.Required(ATTR_ROUTINE_ID): cv.string,
        vol.Required(ATTR_TASK_IDS): vol.All(cv.ensure_list, [cv.string]),
    }
)

SCHEMA_START = vol.Schema({
    vol.Required(ATTR_ROUTINE_ID): cv.string,
    vol.Optional("skip_task_ids"): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional("task_order"): vol.All(cv.ensure_list, [cv.string]),
})

SCHEMA_SNOOZE = vol.Schema(
    {vol.Optional(ATTR_SECONDS, default=DEFAULT_SNOOZE_DURATION): vol.Coerce(int)}
)


async def async_setup_services(
    hass: HomeAssistant,
    storage: RoutinelyStorage,
    coordinator: RoutinelyCoordinator,
) -> None:
    """Set up Routinely services."""

    async def handle_create_task(call: ServiceCall) -> None:
        """Handle create_task service call."""
        task = Task(
            id=generate_id(),
            name=call.data[ATTR_TASK_NAME],
            duration=call.data[ATTR_DURATION],
            icon=call.data.get(ATTR_ICON, "mdi:checkbox-marked-circle-outline"),
            advancement_mode=AdvancementMode(
                call.data.get(ATTR_ADVANCEMENT_MODE, DEFAULT_ADVANCEMENT_MODE)
            ),
            confirm_window=call.data.get(ATTR_CONFIRM_WINDOW),
            description=call.data.get(ATTR_DESCRIPTION),
            notification_message=call.data.get(ATTR_NOTIFICATION_MESSAGE),
            tts_message=call.data.get(ATTR_TTS_MESSAGE),
        )
        await storage.async_create_task(task)
        _log.info("Created task", name=task.name, id=task.id)

    async def handle_update_task(call: ServiceCall) -> None:
        """Handle update_task service call."""
        task_id = call.data[ATTR_TASK_ID]
        task = storage.get_task(task_id)
        if not task:
            _log.error("Task not found", task_id=task_id)
            return

        if ATTR_TASK_NAME in call.data:
            task.name = call.data[ATTR_TASK_NAME]
        if ATTR_DURATION in call.data:
            task.duration = call.data[ATTR_DURATION]
        if ATTR_ICON in call.data:
            task.icon = call.data[ATTR_ICON]
        if ATTR_ADVANCEMENT_MODE in call.data:
            task.advancement_mode = AdvancementMode(call.data[ATTR_ADVANCEMENT_MODE])
        if ATTR_CONFIRM_WINDOW in call.data:
            task.confirm_window = call.data[ATTR_CONFIRM_WINDOW]
        if ATTR_DESCRIPTION in call.data:
            task.description = call.data[ATTR_DESCRIPTION]
        if ATTR_NOTIFICATION_MESSAGE in call.data:
            task.notification_message = call.data[ATTR_NOTIFICATION_MESSAGE]
        if ATTR_TTS_MESSAGE in call.data:
            task.tts_message = call.data[ATTR_TTS_MESSAGE]

        task.updated_at = datetime.now().isoformat()
        await storage.async_update_task(task)
        _log.info("Updated task", name=task.name)

    async def handle_delete_task(call: ServiceCall) -> None:
        """Handle delete_task service call."""
        task_id = call.data[ATTR_TASK_ID]
        if coordinator.engine.is_active:
            _log.error("Cannot delete task while routine is active")
            return
        await storage.async_delete_task(task_id)
        _log.info("Deleted task", task_id=task_id)

    async def handle_create_routine(call: ServiceCall) -> None:
        """Handle create_routine service call."""
        task_ids = call.data.get(ATTR_TASK_IDS, [])
        # Validate task IDs exist
        for tid in task_ids:
            if not storage.get_task(tid):
                _log.error("Task not found", task_id=tid)
                return

        # Process notification settings if provided
        notification_settings = None
        ns_data = call.data.get("notification_settings")
        if ns_data:
            notification_settings = NotificationSettings.from_dict(ns_data)

        routine = Routine(
            id=generate_id(),
            name=call.data[ATTR_ROUTINE_NAME],
            icon=call.data.get(ATTR_ICON, "mdi:playlist-check"),
            task_ids=task_ids,
            tags=call.data.get("tags", []),
            schedule_time=call.data.get("schedule_time"),
            schedule_days=call.data.get("schedule_days", []),
            notification_settings=notification_settings,
        )
        await storage.async_create_routine(routine)
        _log.info("Created routine", name=routine.name, id=routine.id)

    async def handle_update_routine(call: ServiceCall) -> None:
        """Handle update_routine service call."""
        routine_id = call.data[ATTR_ROUTINE_ID]
        routine = storage.get_routine(routine_id)
        if not routine:
            _log.error("Routine not found", routine_id=routine_id)
            return

        if coordinator.engine.is_active and coordinator.engine.session.routine_id == routine_id:
            _log.error("Cannot update routine while it is active")
            return

        if ATTR_ROUTINE_NAME in call.data:
            routine.name = call.data[ATTR_ROUTINE_NAME]
        if ATTR_ICON in call.data:
            routine.icon = call.data[ATTR_ICON]
        if ATTR_TASK_IDS in call.data:
            # Validate task IDs exist
            task_ids = call.data[ATTR_TASK_IDS]
            for tid in task_ids:
                if not storage.get_task(tid):
                    _log.error("Task not found", task_id=tid)
                    return
            routine.task_ids = task_ids
        if "tags" in call.data:
            routine.tags = call.data["tags"]
        if "schedule_time" in call.data:
            routine.schedule_time = call.data["schedule_time"]
        if "schedule_days" in call.data:
            routine.schedule_days = call.data["schedule_days"]
        if "notification_settings" in call.data:
            ns_data = call.data["notification_settings"]
            if ns_data:
                routine.notification_settings = NotificationSettings.from_dict(ns_data)
            else:
                routine.notification_settings = None  # Use global defaults

        routine.updated_at = datetime.now().isoformat()
        await storage.async_update_routine(routine)
        _log.info("Updated routine", name=routine.name)

    async def handle_delete_routine(call: ServiceCall) -> None:
        """Handle delete_routine service call."""
        routine_id = call.data[ATTR_ROUTINE_ID]
        if coordinator.engine.is_active and coordinator.engine.session.routine_id == routine_id:
            _log.error("Cannot delete routine while it is active")
            return
        await storage.async_delete_routine(routine_id)
        _log.info("Deleted routine", routine_id=routine_id)

    async def handle_add_task_to_routine(call: ServiceCall) -> None:
        """Handle add_task_to_routine service call."""
        routine_id = call.data[ATTR_ROUTINE_ID]
        task_id = call.data[ATTR_TASK_ID]
        position = call.data.get(ATTR_POSITION)

        routine = storage.get_routine(routine_id)
        if not routine:
            _log.error("Routine not found", routine_id=routine_id)
            return

        if not storage.get_task(task_id):
            _log.error("Task not found", task_id=task_id)
            return

        if coordinator.engine.is_active and coordinator.engine.session.routine_id == routine_id:
            _log.error("Cannot modify routine while it is active")
            return

        if position is not None and 0 <= position <= len(routine.task_ids):
            routine.task_ids.insert(position, task_id)
        else:
            routine.task_ids.append(task_id)

        routine.updated_at = datetime.now().isoformat()
        await storage.async_update_routine(routine)
        _log.info("Added task to routine", task_id=task_id, routine_id=routine_id)

    async def handle_remove_task_from_routine(call: ServiceCall) -> None:
        """Handle remove_task_from_routine service call."""
        routine_id = call.data[ATTR_ROUTINE_ID]
        position = call.data[ATTR_POSITION]

        routine = storage.get_routine(routine_id)
        if not routine:
            _log.error("Routine not found", routine_id=routine_id)
            return

        if coordinator.engine.is_active and coordinator.engine.session.routine_id == routine_id:
            _log.error("Cannot modify routine while it is active")
            return

        if 0 <= position < len(routine.task_ids):
            routine.task_ids.pop(position)
            routine.updated_at = datetime.now().isoformat()
            await storage.async_update_routine(routine)
            _log.info("Removed task from routine", position=position, routine_id=routine_id)
        else:
            _log.error("Invalid position", position=position)

    async def handle_reorder_routine(call: ServiceCall) -> None:
        """Handle reorder_routine service call."""
        routine_id = call.data[ATTR_ROUTINE_ID]
        task_ids = call.data[ATTR_TASK_IDS]

        routine = storage.get_routine(routine_id)
        if not routine:
            _log.error("Routine not found", routine_id=routine_id)
            return

        if coordinator.engine.is_active and coordinator.engine.session.routine_id == routine_id:
            _log.error("Cannot modify routine while it is active")
            return

        # Validate all task IDs exist
        for tid in task_ids:
            if not storage.get_task(tid):
                _log.error("Task not found", task_id=tid)
                return

        routine.task_ids = task_ids
        routine.updated_at = datetime.now().isoformat()
        await storage.async_update_routine(routine)
        _log.info("Reordered routine", routine_id=routine_id)

    async def handle_start(call: ServiceCall) -> None:
        """Handle start service call."""
        routine_id = call.data[ATTR_ROUTINE_ID]
        skip_task_ids = call.data.get("skip_task_ids")
        task_order = call.data.get("task_order")
        success = await coordinator.start_routine(routine_id, skip_task_ids, task_order)
        if not success:
            _log.error("Failed to start routine", routine_id=routine_id)

    async def handle_pause(call: ServiceCall) -> None:
        """Handle pause service call."""
        success = await coordinator.pause()
        if not success:
            _log.warning("No active routine to pause")

    async def handle_resume(call: ServiceCall) -> None:
        """Handle resume service call."""
        success = await coordinator.resume()
        if not success:
            _log.warning("No paused routine to resume")

    async def handle_skip(call: ServiceCall) -> None:
        """Handle skip service call."""
        success = await coordinator.skip_task()
        if not success:
            _log.warning("No active task to skip")

    async def handle_complete_task(call: ServiceCall) -> None:
        """Handle complete_task service call."""
        success = await coordinator.complete_task()
        if not success:
            _log.warning("Cannot complete task (not in manual/confirm mode)")

    async def handle_confirm(call: ServiceCall) -> None:
        """Handle confirm service call."""
        success = await coordinator.confirm()
        if not success:
            _log.warning("No confirm window active")

    async def handle_snooze(call: ServiceCall) -> None:
        """Handle snooze service call."""
        seconds = call.data.get(ATTR_SECONDS, DEFAULT_SNOOZE_DURATION)
        success = await coordinator.snooze(seconds)
        if not success:
            _log.warning("No confirm window to snooze")

    async def handle_cancel(call: ServiceCall) -> None:
        """Handle cancel service call."""
        success = await coordinator.cancel()
        if not success:
            _log.warning("No active routine to cancel")

    # Register services
    hass.services.async_register(DOMAIN, SERVICE_CREATE_TASK, handle_create_task, SCHEMA_CREATE_TASK)
    hass.services.async_register(DOMAIN, SERVICE_UPDATE_TASK, handle_update_task, SCHEMA_UPDATE_TASK)
    hass.services.async_register(DOMAIN, SERVICE_DELETE_TASK, handle_delete_task, SCHEMA_DELETE_TASK)
    hass.services.async_register(DOMAIN, SERVICE_CREATE_ROUTINE, handle_create_routine, SCHEMA_CREATE_ROUTINE)
    hass.services.async_register(DOMAIN, SERVICE_UPDATE_ROUTINE, handle_update_routine, SCHEMA_UPDATE_ROUTINE)
    hass.services.async_register(DOMAIN, SERVICE_DELETE_ROUTINE, handle_delete_routine, SCHEMA_DELETE_ROUTINE)
    hass.services.async_register(DOMAIN, SERVICE_ADD_TASK_TO_ROUTINE, handle_add_task_to_routine, SCHEMA_ADD_TASK_TO_ROUTINE)
    hass.services.async_register(DOMAIN, SERVICE_REMOVE_TASK_FROM_ROUTINE, handle_remove_task_from_routine, SCHEMA_REMOVE_TASK_FROM_ROUTINE)
    hass.services.async_register(DOMAIN, SERVICE_REORDER_ROUTINE, handle_reorder_routine, SCHEMA_REORDER_ROUTINE)
    hass.services.async_register(DOMAIN, SERVICE_START, handle_start, SCHEMA_START)
    hass.services.async_register(DOMAIN, SERVICE_PAUSE, handle_pause)
    hass.services.async_register(DOMAIN, SERVICE_RESUME, handle_resume)
    hass.services.async_register(DOMAIN, SERVICE_SKIP, handle_skip)
    hass.services.async_register(DOMAIN, SERVICE_COMPLETE_TASK, handle_complete_task)
    hass.services.async_register(DOMAIN, SERVICE_CONFIRM, handle_confirm)
    hass.services.async_register(DOMAIN, SERVICE_SNOOZE, handle_snooze, SCHEMA_SNOOZE)
    hass.services.async_register(DOMAIN, SERVICE_CANCEL, handle_cancel)


@callback
def async_unload_services(hass: HomeAssistant) -> None:
    """Unload Routinely services."""
    services = [
        SERVICE_CREATE_TASK,
        SERVICE_UPDATE_TASK,
        SERVICE_DELETE_TASK,
        SERVICE_CREATE_ROUTINE,
        SERVICE_UPDATE_ROUTINE,
        SERVICE_DELETE_ROUTINE,
        SERVICE_ADD_TASK_TO_ROUTINE,
        SERVICE_REMOVE_TASK_FROM_ROUTINE,
        SERVICE_REORDER_ROUTINE,
        SERVICE_START,
        SERVICE_PAUSE,
        SERVICE_RESUME,
        SERVICE_SKIP,
        SERVICE_COMPLETE_TASK,
        SERVICE_CONFIRM,
        SERVICE_SNOOZE,
        SERVICE_CANCEL,
    ]
    for service in services:
        hass.services.async_remove(DOMAIN, service)
