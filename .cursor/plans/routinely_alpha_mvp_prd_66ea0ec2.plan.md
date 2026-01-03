---
name: Routinely Alpha MVP PRD
overview: A focused MVP PRD for Routinely alpha covering task/routine management, notification system, task queuing, and configurable task advancement behaviors.
todos:
  - id: write-alpha-prd
    content: Write Alpha MVP PRD to scripts/prd.txt for Task Master integration
    status: pending
---

# Routinely Alpha MVP - Product Requirements Document

A focused feature set for the initial alpha release of Routinely, a timer-guided routine execution app.---

## 1. Scope Overview

**In Scope (Alpha):**

- Task creation and configuration
- Routine creation with ordered task queues
- Timer-based routine execution
- Configurable task advancement modes
- Comprehensive notification system

**Out of Scope (Future):**

- User accounts/authentication
- Cloud sync/multi-device
- Social features
- Templates/presets library
- Widgets
- Location triggers

---

## 2. Data Models

### 2.1 Task

| Field | Type | Description ||-------|------|-------------|| id | string | Unique identifier || name | string | Display name (e.g., "Brush teeth") || duration | number | Time in seconds || icon | string | Emoji or icon identifier || advancementMode | enum | `auto`, `manual`, `confirm` || confirmWindow | number? | Seconds allowed for confirmation (if mode=confirm) || description | string? | Optional instructions/notes || createdAt | timestamp | Creation time || updatedAt | timestamp | Last modified |**Advancement Modes:**

- `auto` - Task completes automatically when timer expires
- `manual` - User must explicitly mark complete (no auto-advance)
- `confirm` - Auto-advances BUT user can confirm early or snooze; if no action within `confirmWindow`, auto-advances anyway

### 2.2 Routine

| Field | Type | Description ||-------|------|-------------|| id | string | Unique identifier || name | string | Display name (e.g., "Morning Routine") || icon | string | Emoji or icon identifier || taskIds | string[] | Ordered array of task IDs (the queue) || estimatedDuration | number | Calculated sum of task durations || createdAt | timestamp | Creation time || updatedAt | timestamp | Last modified |

### 2.3 Routine Execution (Session)

| Field | Type | Description ||-------|------|-------------|| id | string | Unique session identifier || routineId | string | Reference to routine || status | enum | `pending`, `running`, `paused`, `completed`, `cancelled` || currentTaskIndex | number | Index of active task in queue || taskStates | TaskState[] | State for each task in session || startedAt | timestamp? | When execution began || pausedAt | timestamp? | When paused (if applicable) || completedAt | timestamp? | When finished || elapsedTime | number | Total elapsed seconds (excluding paused time) |

### 2.4 Task State (within session)

| Field | Type | Description ||-------|------|-------------|| taskId | string | Reference to task || status | enum | `pending`, `active`, `completed`, `skipped` || startedAt | timestamp? | When task became active || completedAt | timestamp? | When task finished || actualDuration | number? | Actual time spent || wasAutoAdvanced | boolean | True if advanced by timer vs user action |---

## 3. Task Management

### 3.1 Create Task

**Inputs:**

- name (required, 1-100 chars)
- duration (required, 1-86400 seconds)
- icon (optional, default assigned)
- advancementMode (optional, default: `auto`)
- confirmWindow (required if mode=`confirm`, 5-300 seconds)
- description (optional, max 500 chars)

**Behavior:**

- Validate inputs
- Generate unique ID
- Persist to storage
- Return created task

### 3.2 Edit Task

- All fields editable except ID
- Changes affect future routine executions only (not in-progress)

### 3.3 Delete Task

- Remove from storage
- Remove from any routines containing this task
- Cannot delete during active execution

### 3.4 List Tasks

- Return all user-created tasks
- Support sorting by name, duration, createdAt

---

## 4. Routine Management

### 4.1 Create Routine

**Inputs:**

- name (required, 1-100 chars)
- icon (optional)
- taskIds (optional, empty array default)

**Behavior:**

- Validate inputs
- Calculate estimatedDuration from tasks
- Persist to storage

### 4.2 Edit Routine

- Modify name, icon
- Cannot edit during active execution

### 4.3 Task Queue Operations

| Operation | Description ||-----------|-------------|| Add Task | Append task ID to end of queue || Insert Task | Insert task ID at specific index || Remove Task | Remove task ID from queue || Reorder Tasks | Move task from one index to another || Duplicate Task | Add same task ID again (allows repeats) |**Constraints:**

- A task can appear multiple times in a routine
- Queue changes recalculate estimatedDuration
- Cannot modify queue during active execution

### 4.4 Delete Routine

- Remove routine from storage
- Cannot delete during active execution

---

## 5. Routine Execution Engine

### 5.1 State Machine

```javascript
[idle] --start--> [running] --pause--> [paused]
                     |                    |
                     |  <----resume-------+
                     |
                     +--complete--> [completed]
                     +--cancel--> [cancelled]
```



### 5.2 Start Routine

**Preconditions:**

- Routine exists
- Routine has at least 1 task
- No other routine currently executing (single active session)

**Behavior:**

1. Create new execution session
2. Initialize all task states as `pending`
3. Set currentTaskIndex = 0
4. Mark first task as `active`
5. Start task timer
6. Send "routine started" notification
7. Send "task started" notification for first task

### 5.3 Task Timer Logic

**On Timer Tick (every second):**

1. Decrement remaining time for current task
2. Update UI with remaining time
3. Check if task should auto-advance

**On Task Timer Complete:**| Mode | Behavior ||------|----------|| `auto` | Immediately advance to next task || `manual` | Remain on task, show "Mark Complete" prompt, send notification || `confirm` | Start confirm window timer, send confirmation prompt |**Confirm Window Logic:**

- Window timer starts after main task timer expires
- User can: Confirm (advance), Snooze (+30s), or do nothing
- If window expires with no action: auto-advance
- Track `wasAutoAdvanced = true` if no user action

### 5.4 Advance to Next Task

1. Mark current task as `completed`
2. Record actualDuration
3. Increment currentTaskIndex
4. If more tasks exist:

- Mark next task as `active`
- Start task timer
- Send "task started" notification

5. If no more tasks:

- Mark session as `completed`
- Send "routine completed" notification

### 5.5 Pause Routine

**Behavior:**

1. Pause current task timer (preserve remaining time)
2. Record pausedAt timestamp
3. Set session status to `paused`
4. Send "routine paused" notification

### 5.6 Resume Routine

**Behavior:**

1. Calculate paused duration
2. Resume task timer from where it left off
3. Clear pausedAt
4. Set session status to `running`
5. Send "routine resumed" notification

### 5.7 Skip Task

**Behavior:**

1. Mark current task as `skipped`
2. Record actualDuration (time spent before skip)
3. Advance to next task (or complete routine)
4. Send "task skipped" notification

### 5.8 Cancel Routine

**Behavior:**

1. Stop all timers
2. Mark session as `cancelled`
3. Preserve task states as-is for history
4. Send "routine cancelled" notification

---

## 6. Notification System

### 6.1 Notification Types

| Type | Trigger | Content ||------|---------|---------|| `routine_reminder` | Scheduled time before routine | "Time to start [Routine Name]" || `routine_started` | Routine execution begins | "[Routine Name] started - [X] tasks, ~[Y] min" || `task_started` | New task becomes active | "Now: [Task Name] ([Duration])" || `task_ending_soon` | Configurable time before task ends | "[Task Name] ending in [X] seconds" || `task_complete_auto` | Auto-advanced task | "Completed: [Task Name]. Next: [Next Task]" || `task_awaiting_input` | Manual/confirm task needs action | "[Task Name] complete - tap to continue" || `routine_paused` | User pauses routine | "[Routine Name] paused" || `routine_resumed` | User resumes routine | "[Routine Name] resumed - [Current Task]" || `routine_completed` | All tasks finished | "[Routine Name] complete! [X] tasks in [Y] min" || `routine_cancelled` | User cancels routine | "[Routine Name] cancelled" || `streak_at_risk` | No routine completed today (evening) | "Don't break your streak! Start a routine" |

### 6.2 Notification Settings

| Setting | Type | Default ||---------|------|---------|| enableNotifications | boolean | true || soundEnabled | boolean | true || vibrationEnabled | boolean | true || taskEndingWarning | number | 10 (seconds before) || showInLockScreen | boolean | true || persistentTimerNotification | boolean | true (shows ongoing timer) |

### 6.3 Persistent Timer Notification

During active routine execution:

- Show ongoing/sticky notification
- Display: Current task name, remaining time, progress (X of Y tasks)
- Actions: Pause/Resume, Skip, Cancel
- Update every second with remaining time

---

## 7. User Interface Requirements

### 7.1 Screens

| Screen | Purpose ||--------|---------|| Home | List routines, quick start, today's progress || Task Library | List/create/edit tasks || Routine Editor | Create/edit routine, manage task queue || Execution View | Active timer, current task, controls || Session Summary | Post-routine stats || Settings | Notification preferences, app settings |

### 7.2 Execution View Components

- **Timer Display**: Large countdown (MM:SS), circular progress
- **Task Info**: Current task name, icon, description
- **Progress Bar**: Visual indicator of routine progress (tasks completed)
- **Queue Preview**: Upcoming 2-3 tasks visible
- **Controls**: Pause/Resume, Skip, Mark Complete (for manual tasks), Cancel
- **Confirm Dialog**: For confirm-mode tasks after timer expires

### 7.3 Task Queue Editor

- Drag-and-drop reordering
- Swipe to remove
- Add task button (opens task picker)
- Total duration display (auto-calculated)
- Preview of full queue

---

## 8. Persistence Requirements

### 8.1 Local Storage

All data persisted locally:

- Tasks
- Routines
- Execution history (last N sessions)
- User settings/preferences

### 8.2 Data Operations

- CRUD for tasks and routines
- Session history with pagination
- Settings read/write
- Export data (JSON format)
- Import data (JSON format)

---

## 9. Edge Cases & Error Handling

| Scenario | Handling ||----------|----------|| App killed during execution | Restore session state on reopen, resume from last known position || Task deleted while in routine | Remove from routine queue, recalculate duration || Empty routine started | Prevent start, show error || Device sleeps during execution | Use background timer/service, maintain notifications || Notification permissions denied | Warn user, allow execution without notifications || Very long task (>1 hour) | Support with periodic "still running" notifications |---

## 10. Success Metrics (Alpha)

| Metric | Target ||--------|--------|| Routine completion rate | Track % of started routines completed || Average tasks per routine | Track routine complexity || Skip rate | Track % of tasks skipped || Auto-advance vs manual | Ratio of advancement modes used || Session duration accuracy | Actual vs estimated time |---

## 11. Technical Considerations

### 11.1 Timer Accuracy

- Use system clock for elapsed time (not interval counting)
- Handle device sleep/wake properly
- Background execution support required

### 11.2 Notification Reliability

- Schedule notifications in advance where possible
- Handle notification permission changes gracefully
- Support notification channels/categories for user control

### 11.3 State Recovery

- Persist execution state on every significant change
- Recover gracefully from app termination
- Handle timer drift on resume

---

## 12. Implementation Priority

| Phase | Features ||-------|----------|| Phase 1 | Task CRUD, Routine CRUD, Queue management || Phase 2 | Execution engine, Timer logic, State machine || Phase 3 | Notification system (all types) || Phase 4 | Persistence, State recovery, Settings |