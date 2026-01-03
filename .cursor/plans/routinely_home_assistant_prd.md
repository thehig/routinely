---
name: Routinely Home Assistant Integration PRD
overview: Implementation guide for Routinely as a Home Assistant custom integration, using timers, automations, scripts, and optional Node-RED flows for timer-guided routine execution.
---

# Routinely Home Assistant Integration - Product Requirements Document

Implementation of Routinely timer-guided routine execution within the Home Assistant ecosystem.

---

## 1. Architecture Overview

### 1.1 Recommended Approach: Custom Integration + HACS

**Primary Implementation:** Custom Home Assistant Integration (Python)

| Component | Implementation |
|-----------|----------------|
| Core Logic | Custom integration (`custom_components/routinely/`) |
| Data Storage | Home Assistant config entries + JSON storage |
| Timer Engine | HA Timer entities + integration coordinator |
| Notifications | HA notify services (mobile app, TTS, persistent) |
| UI | Lovelace dashboard cards + optional custom card |
| Automation Bridge | Fire events for external automation hooks |

### 1.2 Alternative Approaches

| Approach | Pros | Cons |
|----------|------|------|
| **Custom Integration** | Full control, clean UX, maintainable | Requires Python development |
| **Node-RED** | Visual flows, rapid prototyping | Complex state management, harder to share |
| **Scripts + Helpers** | Native HA, no code | Limited logic, verbose YAML |
| **AppDaemon** | Python + HA events | Additional dependency |

**Recommendation:** Custom Integration for production, Node-RED for prototyping.

---

## 2. Entity Design

### 2.1 Core Entities

```yaml
# Per-Routine Entities (created dynamically)
sensor.routinely_{routine_id}_status        # pending|running|paused|completed|cancelled
sensor.routinely_{routine_id}_current_task  # Current task name
sensor.routinely_{routine_id}_progress      # X/Y tasks complete
timer.routinely_{routine_id}_task           # Active task countdown
sensor.routinely_{routine_id}_time_remaining # MM:SS formatted

# Global Entities
binary_sensor.routinely_active              # True if any routine running
sensor.routinely_active_routine             # ID of active routine (or 'none')
```

### 2.2 Entity Attributes

**Routine Status Sensor Attributes:**
```yaml
attributes:
  routine_id: "morning_routine"
  routine_name: "Morning Routine"
  total_tasks: 5
  completed_tasks: 2
  skipped_tasks: 0
  current_task_index: 2
  current_task_name: "Brush teeth"
  current_task_duration: 120
  estimated_total_duration: 900
  elapsed_time: 340
  started_at: "2026-01-03T07:00:00"
  advancement_mode: "auto"  # current task's mode
```

### 2.3 Input Helpers (for Manual Control)

```yaml
input_select.routinely_action:
  options:
    - none
    - start
    - pause
    - resume
    - skip
    - complete
    - cancel

input_text.routinely_target_routine:
  max: 50
```

---

## 3. Custom Integration Structure

### 3.1 File Structure

```
custom_components/routinely/
├── __init__.py           # Integration setup
├── manifest.json         # HACS/HA metadata
├── const.py              # Constants, defaults
├── coordinator.py        # DataUpdateCoordinator
├── config_flow.py        # UI configuration
├── sensor.py             # Status/progress sensors
├── timer.py              # Timer entity platform
├── binary_sensor.py      # Active routine sensor
├── services.yaml         # Service definitions
├── services.py           # Service handlers
├── models.py             # Task, Routine, Session dataclasses
├── engine.py             # Execution engine logic
├── storage.py            # JSON storage handler
└── translations/
    └── en.json           # UI strings
```

### 3.2 Services

| Service | Parameters | Description |
|---------|------------|-------------|
| `routinely.create_task` | name, duration, icon, advancement_mode, confirm_window, description | Create new task |
| `routinely.update_task` | task_id, [fields] | Update existing task |
| `routinely.delete_task` | task_id | Remove task |
| `routinely.create_routine` | name, icon, task_ids | Create routine |
| `routinely.update_routine` | routine_id, [fields] | Update routine |
| `routinely.delete_routine` | routine_id | Remove routine |
| `routinely.add_task_to_routine` | routine_id, task_id, position | Add task to queue |
| `routinely.remove_task_from_routine` | routine_id, position | Remove from queue |
| `routinely.reorder_routine` | routine_id, task_ids | Set new task order |
| `routinely.start` | routine_id | Start routine execution |
| `routinely.pause` | | Pause active routine |
| `routinely.resume` | | Resume paused routine |
| `routinely.skip` | | Skip current task |
| `routinely.complete_task` | | Mark current task complete (manual mode) |
| `routinely.cancel` | | Cancel active routine |
| `routinely.confirm` | | Confirm task (confirm mode) |
| `routinely.snooze` | seconds (default: 30) | Snooze confirm window |

### 3.3 Events

```yaml
# Fired events for automation hooks
routinely_routine_started:
  routine_id: "morning_routine"
  routine_name: "Morning Routine"
  total_tasks: 5

routinely_task_started:
  routine_id: "morning_routine"
  task_id: "brush_teeth"
  task_name: "Brush teeth"
  task_index: 2
  duration: 120
  advancement_mode: "auto"

routinely_task_ending_soon:
  routine_id: "morning_routine"
  task_id: "brush_teeth"
  seconds_remaining: 10

routinely_task_completed:
  routine_id: "morning_routine"
  task_id: "brush_teeth"
  was_auto_advanced: true
  actual_duration: 120

routinely_task_skipped:
  routine_id: "morning_routine"
  task_id: "brush_teeth"

routinely_task_awaiting_input:
  routine_id: "morning_routine"
  task_id: "meditation"
  mode: "manual"  # or "confirm"

routinely_routine_paused:
  routine_id: "morning_routine"

routinely_routine_resumed:
  routine_id: "morning_routine"

routinely_routine_completed:
  routine_id: "morning_routine"
  total_time: 892
  tasks_completed: 5
  tasks_skipped: 0

routinely_routine_cancelled:
  routine_id: "morning_routine"
```

---

## 4. Data Storage

### 4.1 Storage Schema

**Location:** `.storage/routinely`

```json
{
  "version": 1,
  "data": {
    "tasks": {
      "task_001": {
        "id": "task_001",
        "name": "Brush teeth",
        "duration": 120,
        "icon": "mdi:toothbrush",
        "advancement_mode": "auto",
        "confirm_window": null,
        "description": "Use electric toothbrush",
        "created_at": "2026-01-03T10:00:00Z",
        "updated_at": "2026-01-03T10:00:00Z"
      }
    },
    "routines": {
      "morning_routine": {
        "id": "morning_routine",
        "name": "Morning Routine",
        "icon": "mdi:weather-sunny",
        "task_ids": ["task_001", "task_002", "task_003"],
        "created_at": "2026-01-03T10:00:00Z",
        "updated_at": "2026-01-03T10:00:00Z"
      }
    },
    "history": [],
    "settings": {
      "task_ending_warning": 10,
      "default_advancement_mode": "auto",
      "notification_targets": ["mobile_app_phone"]
    }
  }
}
```

---

## 5. Execution Engine

### 5.1 State Machine (Python)

```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

class SessionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    SKIPPED = "skipped"

@dataclass
class TaskState:
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    actual_duration: Optional[int] = None
    was_auto_advanced: bool = False

@dataclass
class ExecutionSession:
    id: str
    routine_id: str
    status: SessionStatus = SessionStatus.PENDING
    current_task_index: int = 0
    task_states: list[TaskState] = None
    started_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    elapsed_time: int = 0
    paused_elapsed: int = 0
```

### 5.2 Timer Handling

```python
async def start_task_timer(self, task_id: str, duration: int):
    """Start HA timer for current task."""
    await self.hass.services.async_call(
        "timer", "start",
        {"entity_id": f"timer.routinely_{self.routine_id}_task", "duration": duration}
    )

async def handle_timer_finished(self, event):
    """Called when task timer expires."""
    task = self.current_task
    match task.advancement_mode:
        case "auto":
            await self.advance_to_next_task(auto_advanced=True)
        case "manual":
            await self.fire_awaiting_input_event()
            await self.send_notification("task_awaiting_input")
        case "confirm":
            await self.start_confirm_window()
```

### 5.3 Coordinator Pattern

```python
class RoutinelyCoordinator(DataUpdateCoordinator):
    """Manages routine execution state and timer events."""
    
    def __init__(self, hass: HomeAssistant, storage: RoutinelyStorage):
        super().__init__(hass, _LOGGER, name="routinely", update_interval=timedelta(seconds=1))
        self.storage = storage
        self.session: Optional[ExecutionSession] = None
        
    async def _async_update_data(self):
        """Update sensor data every second during execution."""
        if self.session and self.session.status == SessionStatus.RUNNING:
            return {
                "status": self.session.status.value,
                "current_task": self.get_current_task_name(),
                "time_remaining": self.get_time_remaining(),
                "progress": f"{self.completed_count}/{self.total_tasks}",
            }
        return {"status": "idle"}
```

---

## 6. Notification Integration

### 6.1 Notification Service Calls

```yaml
# Mobile App Actionable Notification
service: notify.mobile_app_phone
data:
  title: "Routinely"
  message: "Now: Brush teeth (2:00)"
  data:
    tag: "routinely_active"
    persistent: true
    sticky: true
    channel: "routinely_timer"
    importance: high
    actions:
      - action: "ROUTINELY_SKIP"
        title: "Skip"
      - action: "ROUTINELY_PAUSE"
        title: "Pause"
      - action: "ROUTINELY_COMPLETE"
        title: "Done"
```

### 6.2 Notification Templates

```python
NOTIFICATIONS = {
    "routine_started": {
        "title": "Routinely",
        "message": "{routine_name} started - {total_tasks} tasks, ~{duration_min} min"
    },
    "task_started": {
        "title": "Now: {task_name}",
        "message": "{duration_formatted} | {progress}"
    },
    "task_ending_soon": {
        "title": "{task_name}",
        "message": "Ending in {seconds} seconds"
    },
    "task_awaiting_input": {
        "title": "{task_name} complete",
        "message": "Tap to continue to next task"
    },
    "routine_completed": {
        "title": "Routine Complete! 🎉",
        "message": "{routine_name}: {tasks_completed} tasks in {duration_formatted}"
    }
}
```

### 6.3 TTS Announcements (Optional)

```yaml
# Announce task changes via smart speakers
service: tts.speak
target:
  entity_id: media_player.living_room_speaker
data:
  message: "Starting task: Brush teeth. Two minutes."
  cache: true
```

---

## 7. Lovelace Dashboard

### 7.1 Routine Execution Card

```yaml
type: vertical-stack
cards:
  # Active Routine Header
  - type: conditional
    conditions:
      - entity: binary_sensor.routinely_active
        state: "on"
    card:
      type: custom:mushroom-template-card
      primary: "{{ state_attr('sensor.routinely_morning_routine_status', 'current_task_name') }}"
      secondary: "{{ states('sensor.routinely_morning_routine_time_remaining') }}"
      icon: "{{ state_attr('sensor.routinely_morning_routine_status', 'icon') }}"
      icon_color: blue
      
  # Timer Display
  - type: custom:timer-bar-card
    entity: timer.routinely_morning_routine_task
    
  # Progress
  - type: custom:bar-card
    entity: sensor.routinely_morning_routine_progress
    
  # Control Buttons
  - type: horizontal-stack
    cards:
      - type: button
        name: Pause
        icon: mdi:pause
        tap_action:
          action: call-service
          service: routinely.pause
      - type: button
        name: Skip
        icon: mdi:skip-next
        tap_action:
          action: call-service
          service: routinely.skip
      - type: button
        name: Done
        icon: mdi:check
        tap_action:
          action: call-service
          service: routinely.complete_task
```

### 7.2 Routine List Card

```yaml
type: custom:auto-entities
card:
  type: entities
  title: My Routines
filter:
  include:
    - entity_id: sensor.routinely_*_status
      options:
        tap_action:
          action: call-service
          service: routinely.start
          service_data:
            routine_id: "{{ state_attr(entity, 'routine_id') }}"
```

---

## 8. Node-RED Alternative

### 8.1 Flow Structure

For rapid prototyping, Node-RED can implement the execution engine:

```
[HA Events In] --> [State Machine] --> [Timer Control]
                        |
                        +--> [Notification Node]
                        +--> [HA Service Call]
                        +--> [HA Events Out]
```

### 8.2 Key Nodes

| Node | Purpose |
|------|---------|
| `events: all` | Listen for routinely.* service calls |
| `stoptimer` | node-red-contrib-stoptimer for task timing |
| `flow context` | Store session state |
| `call service` | Send notifications, update entities |
| `ha-entity` | Expose sensors to HA |

### 8.3 Sample Flow (JSON)

```json
[
  {
    "id": "routinely_start",
    "type": "server-events",
    "name": "Routinely Start",
    "event_type": "call_service",
    "filter": "domain: routinely, service: start"
  },
  {
    "id": "task_timer",
    "type": "stoptimer",
    "name": "Task Timer",
    "payloadtype": "num",
    "wires": [["timer_complete"], ["timer_tick"]]
  }
]
```

---

## 9. Automation Examples

### 9.1 Start Routine on Schedule

```yaml
automation:
  - alias: "Start Morning Routine at 7 AM"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: state
        entity_id: person.user
        state: "home"
      - condition: state
        entity_id: binary_sensor.routinely_active
        state: "off"
    action:
      - service: routinely.start
        data:
          routine_id: "morning_routine"
```

### 9.2 React to Task Events

```yaml
automation:
  - alias: "Turn on bathroom lights for brush teeth task"
    trigger:
      - platform: event
        event_type: routinely_task_started
        event_data:
          task_id: "brush_teeth"
    action:
      - service: light.turn_on
        target:
          entity_id: light.bathroom
        data:
          brightness_pct: 100
```

### 9.3 Handle Mobile App Actions

```yaml
automation:
  - alias: "Handle Routinely Notification Actions"
    trigger:
      - platform: event
        event_type: mobile_app_notification_action
    action:
      - choose:
          - conditions: "{{ trigger.event.data.action == 'ROUTINELY_SKIP' }}"
            sequence:
              - service: routinely.skip
          - conditions: "{{ trigger.event.data.action == 'ROUTINELY_PAUSE' }}"
            sequence:
              - service: routinely.pause
          - conditions: "{{ trigger.event.data.action == 'ROUTINELY_COMPLETE' }}"
            sequence:
              - service: routinely.complete_task
```

---

## 10. Configuration Options

### 10.1 Integration Config Flow

```yaml
# config_flow options
notification_targets:
  - mobile_app_phone
  - tts.living_room
task_ending_warning: 10  # seconds
default_advancement_mode: auto
enable_tts_announcements: false
tts_entity: media_player.living_room
persistent_notification: true
history_retention_days: 30
```

### 10.2 Per-Routine Overrides

```yaml
# Stored per routine
routine_settings:
  morning_routine:
    notification_targets: ["mobile_app_phone"]
    enable_tts: true
    task_ending_warning: 15
```

---

## 11. Implementation Phases

| Phase | Deliverables | Effort |
|-------|--------------|--------|
| **Phase 1** | Integration scaffold, storage, task/routine CRUD services | 2-3 days |
| **Phase 2** | Execution engine, timer integration, state machine | 3-4 days |
| **Phase 3** | Sensors, events, mobile notifications | 2-3 days |
| **Phase 4** | Lovelace cards, config flow UI | 2-3 days |
| **Phase 5** | History, statistics, optional Node-RED export | 2 days |

---

## 12. Dependencies

| Dependency | Purpose | Required |
|------------|---------|----------|
| Home Assistant 2024.1+ | Core platform | Yes |
| Mobile App Integration | Actionable notifications | Recommended |
| Timer Integration | Built-in timer entities | Yes (built-in) |
| Mushroom Cards | Enhanced UI | Optional |
| Timer Bar Card | Visual timer | Optional |
| Node-RED | Alternative flow engine | Optional |

---

## 13. HACS Distribution

### 13.1 Manifest

```json
{
  "domain": "routinely",
  "name": "Routinely",
  "version": "1.0.0",
  "documentation": "https://github.com/user/routinely-ha",
  "issue_tracker": "https://github.com/user/routinely-ha/issues",
  "dependencies": [],
  "codeowners": ["@user"],
  "requirements": [],
  "iot_class": "local_polling",
  "config_flow": true
}
```

### 13.2 HACS Repository Info

```json
{
  "name": "Routinely",
  "render_readme": true,
  "domains": ["sensor", "binary_sensor", "timer"],
  "homeassistant": "2024.1.0"
}
```

---

## 14. Testing Strategy

| Test Type | Scope |
|-----------|-------|
| Unit Tests | Engine logic, state transitions |
| Integration Tests | Service calls, entity updates |
| Manual Testing | Mobile notifications, timer accuracy |
| E2E Testing | Full routine execution flow |

---

## 15. Future Enhancements

- **Voice Control:** "Hey Google, start my morning routine"
- **Wear OS Tile:** Timer display on smartwatch
- **Calendar Integration:** Auto-suggest routines based on calendar events
- **Statistics Dashboard:** Completion rates, time trends
- **Blueprint Generator:** Export routines as shareable HA blueprints
