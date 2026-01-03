/**
 * ROUTINELY - Views Module
 * View rendering functions for the card
 */

import { formatTime, formatDuration, formatAdvancementMode, getModeStyle, taskEmojis, routineEmojis } from './utils.js';

/**
 * Render active routine view (timer display)
 */
export function renderActiveRoutine(state, handlers) {
  const { taskName, timeRemaining, isPaused, progress, currentTaskIndex, totalTasks, advancementMode, awaitingInput } = state;
  
  const progressPercent = Math.round(progress * 100);
  
  let actionButtons = '';
  
  if (awaitingInput) {
    actionButtons = `
      <div class="button-row">
        <button class="btn btn-success btn-large" data-action="complete">
          <span class="btn-icon">✅</span>
          Done
        </button>
        <button class="btn btn-warning" data-action="skip">
          <span class="btn-icon">⏭️</span>
          Skip
        </button>
      </div>
    `;
  } else if (isPaused) {
    actionButtons = `
      <div class="button-row">
        <button class="btn btn-primary btn-large" data-action="resume">
          <span class="btn-icon">▶️</span>
          Resume
        </button>
        <button class="btn btn-danger" data-action="stop">
          <span class="btn-icon">⏹️</span>
          Stop
        </button>
      </div>
    `;
  } else {
    const mainAction = advancementMode === 'manual' 
      ? `<button class="btn btn-success btn-large" data-action="complete">
          <span class="btn-icon">✅</span>
          Done
        </button>`
      : `<button class="btn btn-warning btn-large" data-action="pause">
          <span class="btn-icon">⏸️</span>
          Pause
        </button>`;
    
    actionButtons = `
      <div class="button-row">
        ${mainAction}
        <button class="btn btn-secondary" data-action="skip">
          <span class="btn-icon">⏭️</span>
          Skip
        </button>
      </div>
    `;
  }
  
  const timerClass = isPaused ? 'timer paused' : 'timer';
  const statusText = isPaused ? '⏸️ PAUSED' : awaitingInput ? '⏳ WAITING' : '▶️ ACTIVE';
  
  return `
    <div class="card">
      <div class="status-label">${statusText}</div>
      <div class="task-name">${taskName || 'No Task'}</div>
      <div class="${timerClass}">${formatTime(timeRemaining)}</div>
      
      <div class="progress-container">
        <div class="progress-bar">
          <div class="progress-fill" style="width: ${progressPercent}%"></div>
        </div>
        <div class="progress-text">Task ${currentTaskIndex + 1} of ${totalTasks} (${progressPercent}%)</div>
      </div>
      
      ${actionButtons}
    </div>
  `;
}

/**
 * Render routine selection view
 */
export function renderRoutineSelect(routines, allTags, selectedTag, handlers) {
  if (!routines || routines.length === 0) {
    return `
      <div class="card">
        <div class="welcome">
          <div class="welcome-icon">🎯</div>
          <h2>Welcome to Routinely!</h2>
          <p>Create your first routine to get started</p>
        </div>
        <div class="nav">
          <button class="nav-btn" data-tab="tasks"><span class="nav-btn-icon">📋</span>Tasks</button>
          <button class="nav-btn active" data-tab="routines"><span class="nav-btn-icon">🔄</span>Routines</button>
        </div>
      </div>
    `;
  }
  
  // Filter by tag if selected
  let filteredRoutines = routines;
  if (selectedTag) {
    filteredRoutines = routines.filter(r => r.tags && r.tags.includes(selectedTag));
  }
  
  // Build filter bar
  let filterBar = '';
  if (allTags && allTags.length > 0) {
    filterBar = `
      <div class="filter-bar">
        <button class="filter-btn ${!selectedTag ? 'active' : ''}" data-action="filter-tag" data-tag="">All</button>
        ${allTags.map(tag => `
          <button class="filter-btn ${selectedTag === tag ? 'active' : ''}" data-action="filter-tag" data-tag="${tag}">${tag}</button>
        `).join('')}
      </div>
    `;
  }
  
  return `
    <div class="card">
      <div class="welcome">
        <div class="welcome-icon">🎯</div>
        <h2>Ready to Start?</h2>
        <p>Choose a routine to begin</p>
      </div>
      
      ${filterBar}
      
      <div class="routine-list">
        ${filteredRoutines.map(routine => `
          <div class="routine-item" data-action="start-routine" data-routine-id="${routine.id}">
            <span class="routine-icon">${routine.icon || '📋'}</span>
            <div class="routine-info">
              <div class="routine-name">${routine.name}</div>
              <div class="routine-meta">
                ${routine.task_count || 0} tasks • ${formatDuration(routine.total_duration || 0)}
                ${routine.tags && routine.tags.length > 0 ? ` • ${routine.tags.join(', ')}` : ''}
              </div>
            </div>
            <span class="routine-arrow">›</span>
          </div>
        `).join('')}
      </div>
      
      <div class="nav">
        <button class="nav-btn" data-tab="tasks"><span class="nav-btn-icon">📋</span>Tasks</button>
        <button class="nav-btn active" data-tab="routines"><span class="nav-btn-icon">🔄</span>Routines</button>
      </div>
    </div>
  `;
}

/**
 * Render review screen before starting routine
 */
export function renderReviewScreen(routine, tasks, skippedIds, startTime, handlers) {
  const includedTasks = tasks.filter(t => !skippedIds.has(t.id));
  const totalDuration = includedTasks.reduce((sum, t) => sum + (t.duration || 0), 0);
  
  // Calculate times for each task
  let runningTime = 0;
  const taskItems = tasks.map(task => {
    const isSkipped = skippedIds.has(task.id);
    const startOffset = runningTime;
    const endOffset = runningTime + (task.duration || 0);
    
    if (!isSkipped) {
      runningTime += (task.duration || 0);
    }
    
    const startTimeStr = calculateDisplayTime(startTime, startOffset);
    const endTimeStr = calculateDisplayTime(startTime, endOffset);
    
    return `
      <div class="review-task ${isSkipped ? 'skipped' : ''} draggable-item" 
           data-action="toggle-skip" data-task-id="${task.id}" data-id="${task.id}">
        <span class="drag-handle">⋮⋮</span>
        <div class="task-checkbox">${isSkipped ? '✓' : ''}</div>
        <span class="task-icon">${task.icon || '📋'}</span>
        <div class="task-details">
          <div class="task-name">${task.name}</div>
          <div class="task-time">${startTimeStr} - ${endTimeStr}</div>
        </div>
        <div class="task-duration">${formatDuration(task.duration)}</div>
        <span class="task-mode-badge" style="${getModeStyle(task.advancement_mode)}">${formatAdvancementMode(task.advancement_mode)}</span>
      </div>
    `;
  });
  
  const endTime = calculateDisplayTime(startTime, totalDuration);
  const startTimeStr = calculateDisplayTime(startTime, 0);
  
  return `
    <div class="card">
      <div class="review-header">
        <h2><span>${routine.icon || '📋'}</span> ${routine.name}</h2>
        <div class="meta">${startTimeStr} → ${endTime} (${formatDuration(totalDuration)})</div>
      </div>
      
      <div class="review-task-list" id="review-task-list">
        ${taskItems.join('')}
      </div>
      
      <div class="review-summary">
        <strong>${includedTasks.length}</strong> of ${tasks.length} tasks • Total: <strong>${formatDuration(totalDuration)}</strong>
      </div>
      
      <div class="review-actions">
        <button class="btn btn-secondary" data-action="cancel-review" style="flex: 1;">
          <span class="btn-icon">←</span> Back
        </button>
        <button class="btn btn-coral" data-action="confirm-start" style="flex: 2;">
          <span class="btn-icon">▶️</span> Start Routine
        </button>
      </div>
    </div>
  `;
}

/**
 * Render task list view
 */
export function renderTaskList(tasks) {
  return `
    <div class="card">
      <div class="list-header">
        <h3>📋 Tasks</h3>
        <button class="btn btn-small btn-primary" data-action="create-task">
          <span class="btn-icon">+</span> New
        </button>
      </div>
      
      ${tasks.length === 0 ? `
        <div class="empty">
          <div class="empty-icon">📋</div>
          <p>No tasks yet. Create your first task!</p>
        </div>
      ` : tasks.map(task => `
        <div class="item-card">
          <span class="item-icon">${task.icon || '📋'}</span>
          <div class="item-info" data-action="edit-task" data-task-id="${task.id}">
            <div class="item-name">${task.name}</div>
            <div class="item-meta">${formatDuration(task.duration)} • ${formatAdvancementMode(task.advancement_mode)}</div>
          </div>
          <div class="item-actions">
            <button class="item-btn" data-action="copy-task" data-task-id="${task.id}" title="Copy">📋</button>
            <button class="item-btn" data-action="edit-task" data-task-id="${task.id}" title="Edit">✏️</button>
            <button class="item-btn delete" data-action="delete-task" data-task-id="${task.id}" title="Delete">🗑️</button>
          </div>
        </div>
      `).join('')}
      
      <div class="nav">
        <button class="nav-btn active" data-tab="tasks"><span class="nav-btn-icon">📋</span>Tasks</button>
        <button class="nav-btn" data-tab="routines"><span class="nav-btn-icon">🔄</span>Routines</button>
      </div>
    </div>
  `;
}

/**
 * Render routine list view
 */
export function renderRoutineList(routines) {
  return `
    <div class="card">
      <div class="list-header">
        <h3>🔄 Routines</h3>
        <button class="btn btn-small btn-primary" data-action="create-routine">
          <span class="btn-icon">+</span> New
        </button>
      </div>
      
      ${routines.length === 0 ? `
        <div class="empty">
          <div class="empty-icon">🔄</div>
          <p>No routines yet. Create your first routine!</p>
        </div>
      ` : routines.map(routine => `
        <div class="item-card">
          <span class="item-icon">${routine.icon || '📋'}</span>
          <div class="item-info" data-action="edit-routine" data-routine-id="${routine.id}">
            <div class="item-name">${routine.name}</div>
            <div class="item-meta">
              ${routine.task_count || 0} tasks • ${formatDuration(routine.total_duration || 0)}
              ${routine.tags && routine.tags.length > 0 ? ` • ${routine.tags.join(', ')}` : ''}
            </div>
          </div>
          <div class="item-actions">
            <button class="item-btn" data-action="edit-routine" data-routine-id="${routine.id}" title="Edit">✏️</button>
            <button class="item-btn delete" data-action="delete-routine" data-routine-id="${routine.id}" title="Delete">🗑️</button>
          </div>
        </div>
      `).join('')}
      
      <div class="nav">
        <button class="nav-btn" data-tab="tasks"><span class="nav-btn-icon">📋</span>Tasks</button>
        <button class="nav-btn active" data-tab="routines"><span class="nav-btn-icon">🔄</span>Routines</button>
      </div>
    </div>
  `;
}

/**
 * Render task form (create/edit)
 */
export function renderTaskForm(formState, isEdit) {
  const title = isEdit ? 'Edit Task' : 'New Task';
  const saveAction = isEdit ? 'save-edit-task' : 'save-task';
  
  return `
    <div class="card">
      <div class="form">
        <div class="form-title">${title}</div>
        
        <div class="form-group">
          <label class="form-label">Name</label>
          <input type="text" class="form-input" id="task-name" 
                 value="${formState.name || ''}" 
                 placeholder="e.g., Brush Teeth">
        </div>
        
        <div class="form-group">
          <label class="form-label">Icon</label>
          <input type="text" class="form-input" id="task-icon" 
                 value="${formState.icon || ''}" 
                 placeholder="Choose below or paste emoji">
          <div class="emoji-quick">
            ${taskEmojis.map(e => `
              <button class="emoji-chip ${formState.icon === e ? 'selected' : ''}" 
                      data-action="select-emoji" data-emoji="${e}" data-target="task-icon">${e}</button>
            `).join('')}
          </div>
        </div>
        
        <div class="form-group">
          <label class="form-label">Duration (minutes)</label>
          <input type="number" class="form-input" id="task-duration" 
                 value="${formState.duration || 5}" min="1" max="120">
          <div class="duration-quick">
            ${[1, 2, 5, 10, 15, 30].map(d => `
              <button class="duration-chip ${formState.duration === d ? 'selected' : ''}" 
                      data-action="select-duration" data-duration="${d}">${d}m</button>
            `).join('')}
          </div>
        </div>
        
        <div class="form-group">
          <label class="form-label">Advancement Mode</label>
          <select class="form-select" id="task-mode">
            <option value="manual" ${formState.mode === 'manual' ? 'selected' : ''}>Manual - Tap to complete</option>
            <option value="auto_next" ${formState.mode === 'auto_next' ? 'selected' : ''}>Auto Next - Auto advance when timer ends</option>
            <option value="confirm_next" ${formState.mode === 'confirm_next' ? 'selected' : ''}>Confirm - Ask before advancing</option>
          </select>
          <div class="form-hint">How should the routine advance after this task?</div>
        </div>
        
        <div class="form-actions">
          <button class="btn btn-secondary" data-action="cancel-form" style="flex: 1;">Cancel</button>
          <button class="btn btn-success" data-action="${saveAction}" style="flex: 2;">
            <span class="btn-icon">💾</span> Save
          </button>
        </div>
      </div>
    </div>
  `;
}

/**
 * Render routine form (create/edit)
 */
export function renderRoutineForm(formState, tasks, isEdit, notificationSettingsOpen) {
  const title = isEdit ? 'Edit Routine' : 'New Routine';
  const saveAction = isEdit ? 'save-edit-routine' : 'save-routine';
  
  // Calculate selected tasks duration
  const selectedDuration = tasks
    .filter(t => formState.selectedTasks && formState.selectedTasks.has(t.id))
    .reduce((sum, t) => sum + (t.duration || 0), 0);
  
  // Days of week
  const days = [
    { key: 'mon', label: 'M' },
    { key: 'tue', label: 'T' },
    { key: 'wed', label: 'W' },
    { key: 'thu', label: 'T' },
    { key: 'fri', label: 'F' },
    { key: 'sat', label: 'S' },
    { key: 'sun', label: 'S' }
  ];
  
  return `
    <div class="card">
      <div class="form">
        <div class="form-title">${title}</div>
        
        <div class="form-group">
          <label class="form-label">Name</label>
          <input type="text" class="form-input" id="routine-name" 
                 value="${formState.name || ''}" 
                 placeholder="e.g., Morning Routine">
        </div>
        
        <div class="form-group">
          <label class="form-label">Icon</label>
          <input type="text" class="form-input" id="routine-icon" 
                 value="${formState.icon || ''}" 
                 placeholder="Choose below or paste emoji">
          <div class="emoji-quick">
            ${routineEmojis.map(e => `
              <button class="emoji-chip ${formState.icon === e ? 'selected' : ''}" 
                      data-action="select-emoji" data-emoji="${e}" data-target="routine-icon">${e}</button>
            `).join('')}
          </div>
        </div>
        
        <div class="form-group">
          <label class="form-label">Tags</label>
          <div class="tag-input-row">
            <input type="text" class="tag-input" id="tag-input" placeholder="Add a tag...">
            <button class="tag-add-btn" data-action="add-tag">Add</button>
          </div>
          ${formState.tags && formState.tags.length > 0 ? `
            <div class="tag-container">
              ${formState.tags.map(tag => `
                <span class="tag" data-action="remove-tag" data-tag="${tag}">${tag} ×</span>
              `).join('')}
            </div>
          ` : ''}
        </div>
        
        <div class="form-group">
          <label class="form-label">Tasks (drag to reorder)</label>
          <div class="task-selector" id="task-selector">
            ${tasks.map(task => {
              const isSelected = formState.selectedTasks && formState.selectedTasks.has(task.id);
              return `
                <div class="task-selector-item draggable-item ${isSelected ? 'selected' : ''}" 
                     data-action="toggle-task" data-task-id="${task.id}" data-id="${task.id}">
                  <span class="drag-handle">⋮⋮</span>
                  <div class="task-selector-checkbox">${isSelected ? '✓' : ''}</div>
                  <div class="task-selector-label">
                    <span class="task-icon">${task.icon || '📋'}</span>
                    <span class="task-name">${task.name}</span>
                    <span class="task-duration">(${formatDuration(task.duration)})</span>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
          ${tasks.length > 0 ? `
            <div class="selected-count">
              ${formState.selectedTasks ? formState.selectedTasks.size : 0} tasks selected • ${formatDuration(selectedDuration)}
            </div>
          ` : ''}
        </div>
        
        <div class="form-group">
          <label class="form-label">Schedule (optional)</label>
          <div class="schedule-section">
            <div class="schedule-section-title">Days</div>
            <div class="day-picker">
              ${days.map(d => `
                <button class="day-btn ${formState.scheduleDays && formState.scheduleDays.includes(d.key) ? 'selected' : ''}" 
                        data-action="toggle-day" data-day="${d.key}">${d.label}</button>
              `).join('')}
            </div>
            <div class="time-input-row">
              <span>Time:</span>
              <input type="time" class="time-input" id="schedule-time" 
                     value="${formState.scheduleTime || ''}">
            </div>
            <div class="form-hint">Use Home Assistant automations for scheduled triggers</div>
          </div>
        </div>
        
        <!-- Notification Settings Collapsible -->
        <div class="form-group">
          <div class="collapsible-header" data-action="toggle-notification-settings">
            <label class="form-label" style="margin-bottom: 0; cursor: pointer;">🔔 Notification Settings</label>
            <span class="collapsible-icon ${notificationSettingsOpen ? 'open' : ''}">›</span>
          </div>
          <div class="collapsible-content ${notificationSettingsOpen ? 'open' : ''}">
            <div class="notification-settings">
              <div class="notification-toggle">
                <div>
                  <div class="notification-toggle-label">Custom notifications</div>
                  <div class="notification-toggle-hint">Override global defaults for this routine</div>
                </div>
                <div class="toggle-switch ${formState.useCustomNotifications ? 'on' : ''}" 
                     data-action="toggle-custom-notifications"></div>
              </div>
              
              ${formState.useCustomNotifications ? `
                <div class="notification-toggle">
                  <div>
                    <div class="notification-toggle-label">Before task starts (mins)</div>
                    <div class="notification-toggle-hint">e.g., 10,5,1</div>
                  </div>
                  <input type="text" class="notification-time-input" id="notify-before" 
                         value="${formState.notifyBefore || ''}" placeholder="10,5,1">
                </div>
                
                <div class="notification-toggle">
                  <div>
                    <div class="notification-toggle-label">On task start</div>
                  </div>
                  <div class="toggle-switch ${formState.notifyOnStart ? 'on' : ''}" 
                       data-action="toggle-notify-start"></div>
                </div>
                
                <div class="notification-toggle">
                  <div>
                    <div class="notification-toggle-label">Time remaining (mins)</div>
                    <div class="notification-toggle-hint">e.g., 5,1</div>
                  </div>
                  <input type="text" class="notification-time-input" id="notify-remaining" 
                         value="${formState.notifyRemaining || ''}" placeholder="5,1">
                </div>
                
                <div class="notification-toggle">
                  <div>
                    <div class="notification-toggle-label">Overdue alerts (mins)</div>
                    <div class="notification-toggle-hint">e.g., 1,5,10</div>
                  </div>
                  <input type="text" class="notification-time-input" id="notify-overdue" 
                         value="${formState.notifyOverdue || ''}" placeholder="1,5,10">
                </div>
                
                <div class="notification-toggle">
                  <div>
                    <div class="notification-toggle-label">On task complete</div>
                  </div>
                  <div class="toggle-switch ${formState.notifyOnComplete ? 'on' : ''}" 
                       data-action="toggle-notify-complete"></div>
                </div>
              ` : ''}
            </div>
          </div>
        </div>
        
        <div class="form-actions">
          <button class="btn btn-secondary" data-action="cancel-form" style="flex: 1;">Cancel</button>
          <button class="btn btn-success" data-action="${saveAction}" style="flex: 2;">
            <span class="btn-icon">💾</span> Save
          </button>
        </div>
      </div>
      
      <!-- FAB to quickly add a task -->
      <button class="fab" data-action="create-task" title="New Task">+</button>
    </div>
  `;
}

// Helper function
function calculateDisplayTime(startTime, offsetSeconds) {
  const totalMins = startTime.hour * 60 + startTime.min + Math.floor(offsetSeconds / 60);
  const h = Math.floor(totalMins / 60) % 24;
  const m = totalMins % 60;
  const ampm = h >= 12 ? 'PM' : 'AM';
  const h12 = h % 12 || 12;
  return `${h12}:${String(m).padStart(2, '0')} ${ampm}`;
}
