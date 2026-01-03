# Routinely - Home Assistant Integration

Timer-guided routine execution for Home Assistant. Create tasks, build routines, and execute them with timed steps.

## Features

- **Task Management**: Create reusable tasks with configurable durations
- **Routine Builder**: Combine tasks into ordered routines
- **Timer Execution**: Run routines with countdown timers per task
- **Advancement Modes**: Auto, Manual, or Confirm modes for task completion
- **TTS Notifications**: Notifications read aloud via iOS/Android platform TTS
- **Actionable Notifications**: Pause, Resume, Skip, Complete buttons in notifications
- **Events**: Home Assistant events fired for automation hooks
- **Sensors**: Track status, current task, time remaining, and progress

## Installation

### HACS (Recommended)

1. Add this repository as a custom repository in HACS
2. Install "Routinely" from HACS
3. Restart Home Assistant
4. Add integration via Settings → Devices & Services → Add Integration → Routinely

### Manual

1. Copy `custom_components/routinely` to your `config/custom_components/` directory
2. Restart Home Assistant
3. Add integration via Settings → Devices & Services → Add Integration → Routinely

## Usage

### Creating Tasks

```yaml
service: routinely.create_task
data:
  task_name: "Brush teeth"
  duration: 120
  icon: "mdi:toothbrush"
  advancement_mode: "auto"
```

### Creating Routines

```yaml
service: routinely.create_routine
data:
  routine_name: "Morning Routine"
  icon: "mdi:weather-sunny"
  task_ids:
    - "abc123def456"
    - "xyz789uvw012"
```

### Starting a Routine

```yaml
service: routinely.start
data:
  routine_id: "morning_routine_id"
```

### Control Services

| Service | Description |
|---------|-------------|
| `routinely.start` | Start a routine |
| `routinely.pause` | Pause active routine |
| `routinely.resume` | Resume paused routine |
| `routinely.skip` | Skip current task |
| `routinely.complete_task` | Manually complete task |
| `routinely.confirm` | Confirm during confirm window |
| `routinely.snooze` | Snooze confirm window |
| `routinely.cancel` | Cancel active routine |

## Entities

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.routinely_status` | Sensor | Current status (idle/running/paused/completed/cancelled) |
| `sensor.routinely_current_task` | Sensor | Name of current task |
| `sensor.routinely_time_remaining` | Sensor | Formatted time remaining (MM:SS) |
| `sensor.routinely_progress` | Sensor | Progress percentage |
| `binary_sensor.routinely_active` | Binary Sensor | True if routine is active |
| `binary_sensor.routinely_paused` | Binary Sensor | True if routine is paused |
| `binary_sensor.routinely_awaiting_input` | Binary Sensor | True if waiting for user action |

## Events

Listen for these events in automations:

| Event | Description |
|-------|-------------|
| `routinely_routine_started` | Routine execution began |
| `routinely_routine_paused` | Routine paused |
| `routinely_routine_resumed` | Routine resumed |
| `routinely_routine_completed` | Routine finished |
| `routinely_routine_cancelled` | Routine cancelled |
| `routinely_task_started` | New task began |
| `routinely_task_ending_soon` | Task ending warning |
| `routinely_task_completed` | Task completed |
| `routinely_task_skipped` | Task skipped |
| `routinely_task_awaiting_input` | Task needs user input |

## Advancement Modes

| Mode | Behavior |
|------|----------|
| `auto` | Task completes automatically when timer expires |
| `manual` | User must explicitly mark complete |
| `confirm` | Shows confirm window after timer; auto-advances if no action |

## Notifications & TTS

Routinely sends rich notifications with **text-to-speech** announcements. Notifications are read aloud by your device's platform TTS (iOS Siri, Android TTS).

### Setup

1. Go to Settings → Devices & Services → Routinely → Configure
2. Enable notifications
3. Enter notification targets (e.g., `mobile_app_iphone, mobile_app_pixel`)

### iOS Setup for Spoken Notifications

For iOS devices to read notifications aloud:

1. Open iOS Settings → Notifications → Announce Notifications
2. Enable "Announce Notifications"
3. Select "Headphones" or "CarPlay" (or both)
4. Optionally enable "Reply Without Confirmation"

The Home Assistant app notifications will be spoken by Siri when:
- You're wearing AirPods/Beats
- Connected to CarPlay
- Using "Hey Siri" enabled devices

### Android Setup

Android will use TTS when:
- Notification channels are configured for spoken announcements
- You're using Android Auto
- Accessibility TTS is enabled

### Custom TTS Messages

You can customize what's spoken for each task:

```yaml
service: routinely.create_task
data:
  task_name: "Brush teeth"
  duration: 120
  tts_message: "Time to brush your teeth! 2 minutes starting now."
  notification_message: "🦷 Brush teeth - 2:00"
```

### Notification Actions

All notifications include actionable buttons:

| Notification | Actions Available |
|--------------|-------------------|
| Task Started | Skip, Pause, Done* |
| Task Ending Soon | Skip, Done |
| Awaiting Input | Continue, Snooze / Done, Skip |
| Routine Paused | Resume, Cancel |
| Routine Complete | (informational) |

*Done button only shown for manual/confirm mode tasks

### Notification Events

Notifications are automatically handled - tapping action buttons triggers the corresponding service. No automations needed!

## Example Automation

```yaml
automation:
  - alias: "Notify on task start"
    trigger:
      - platform: event
        event_type: routinely_task_started
    action:
      - service: notify.mobile_app
        data:
          title: "{{ trigger.event.data.task_name }}"
          message: "Starting task ({{ trigger.event.data.duration }}s)"
```

## Lovelace Card Example

```yaml
type: vertical-stack
cards:
  - type: entity
    entity: sensor.routinely_status
  - type: entity
    entity: sensor.routinely_current_task
  - type: entity
    entity: sensor.routinely_time_remaining
  - type: gauge
    entity: sensor.routinely_progress
    min: 0
    max: 100
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
        name: Cancel
        icon: mdi:stop
        tap_action:
          action: call-service
          service: routinely.cancel
```

## Logging & Debugging

Routinely includes comprehensive logging to help diagnose issues.

### Log Levels

| Level | Description |
|-------|-------------|
| `debug` | Detailed diagnostics - timer ticks, state changes, all method calls |
| `info` | Routine/task lifecycle events, service calls |
| `warning` | Recoverable issues, deprecated usage |
| `error` | Failures that prevent operations |

### Configuration

**Via Integration Options:**

1. Settings → Devices & Services → Routinely → Configure
2. Select desired log level from dropdown

**Via configuration.yaml:**

```yaml
logger:
  default: warning
  logs:
    custom_components.routinely: debug
    custom_components.routinely.engine: debug
    custom_components.routinely.notifications: info
```

### Log Output

Logs appear in:
- Home Assistant logs (Settings → System → Logs)
- `home-assistant.log` file
- Docker container logs (`docker logs homeassistant`)

### Example Debug Output

```
[custom_components.routinely.engine] Routine started [routine_id=abc123 | name=Morning Routine | total_tasks=5]
[custom_components.routinely.engine] Task started [task_id=xyz789 | task_name=Brush teeth | duration=120 | mode=auto]
[custom_components.routinely.notifications] Sending notification [type=task_started | targets=['mobile_app_iphone']]
```

## License

MIT
