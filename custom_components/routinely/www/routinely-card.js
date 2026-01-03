/**
 * ROUTINELY - ADHD-Friendly Custom Card
 * 
 * Design Principles:
 * - ONE thing at a time (single focus)
 * - BIG touch targets (easy to tap)
 * - Minimal cognitive load (fewer choices)
 * - Clear visual hierarchy (important = big)
 * - Immediate feedback (instant response)
 * - Time awareness (prominent timer)
 * - Calm, not overstimulating
 */

class RoutinelyCard extends HTMLElement {
  static get properties() {
    return {
      hass: {},
      config: {},
    };
  }

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._mode = 'timer'; // timer | routines | tasks | create-task | create-routine | edit-task | edit-routine | review
    this._lastRenderState = null;
    this._selectedTasks = [];
    this._editingId = null;
    this._reviewRoutineId = null;
    this._skippedTaskIds = []; // Tasks to skip in review
    
    // Form state preservation
    this._formState = {
      taskName: '',
      taskDuration: '120',
      taskMode: 'auto',
      taskIcon: '',
      routineName: '',
      routineIcon: '',
    };
  }

  setConfig(config) {
    this.config = config;
  }

  set hass(hass) {
    this._hass = hass;
    
    // Skip re-render if in form/review mode (preserve user input)
    if (this._mode === 'create-task' || this._mode === 'create-routine' || 
        this._mode === 'edit-task' || this._mode === 'edit-routine' || this._mode === 'review') {
      // Only update if routine becomes active (user started one)
      const isActive = this.isActive();
      if (isActive && this._mode !== 'review') {
        this._mode = 'timer';
        this.render();
      } else if (isActive && this._mode === 'review') {
        // Routine started from review, switch to timer
        this._mode = 'timer';
        this._reviewRoutineId = null;
        this._skippedTaskIds = [];
        this.render();
      }
      return;
    }
    
    // For other modes, check if state actually changed
    const newRenderState = this._getRenderState();
    if (this._lastRenderState === newRenderState) {
      return;
    }
    this._lastRenderState = newRenderState;
    this.render();
  }

  _getRenderState() {
    const active = this.getStateValue('binary_sensor.routinely_active');
    const paused = this.getStateValue('binary_sensor.routinely_paused');
    const timeRemaining = this.getStateValue('sensor.routinely_time_remaining');
    const currentTask = this.getStateValue('sensor.routinely_current_task');
    const progress = this.getStateValue('sensor.routinely_progress');
    const taskCount = this.getStateValue('sensor.routinely_tasks');
    const routineCount = this.getStateValue('sensor.routinely_routines');
    
    return `${this._mode}|${active}|${paused}|${timeRemaining}|${currentTask}|${progress}|${taskCount}|${routineCount}`;
  }

  getState(entityId) {
    return this._hass?.states[entityId];
  }

  getStateValue(entityId) {
    return this.getState(entityId)?.state;
  }

  getStateAttr(entityId, attr) {
    return this.getState(entityId)?.attributes?.[attr];
  }

  isActive() {
    return this.getStateValue('binary_sensor.routinely_active') === 'on';
  }

  isPaused() {
    return this.getStateValue('binary_sensor.routinely_paused') === 'on';
  }

  callService(service, data = {}) {
    this._hass.callService('routinely', service, data);
  }

  render() {
    if (!this._hass) return;

    const isActive = this.isActive();
    
    this.shadowRoot.innerHTML = `
      <style>
        ${this.getStyles()}
      </style>
      <div class="card">
        ${isActive ? this.renderActiveRoutine() : this.renderInactiveState()}
      </div>
    `;

    this.attachEventListeners();
  }

  getStyles() {
    return `
      * {
        box-sizing: border-box;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      }

      .card {
        background: var(--ha-card-background, var(--card-background-color, white));
        border-radius: 16px;
        padding: 20px;
        min-height: 400px;
        position: relative;
      }

      /* === TYPOGRAPHY === */
      .task-name {
        font-size: 2em;
        font-weight: 700;
        text-align: center;
        padding: 20px;
        color: var(--primary-text-color);
        line-height: 1.2;
      }

      .timer {
        font-size: 5em;
        font-weight: 700;
        text-align: center;
        font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
        padding: 20px 0;
        color: var(--primary-text-color);
      }

      .timer.paused {
        color: #FFA726;
        animation: pulse 1.5s ease-in-out infinite;
      }

      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
      }

      .status-label {
        text-align: center;
        font-size: 1.2em;
        color: var(--secondary-text-color);
        margin-bottom: 20px;
      }

      .progress-container {
        padding: 10px 20px;
      }

      .progress-bar {
        height: 12px;
        background: var(--divider-color, #eee);
        border-radius: 6px;
        overflow: hidden;
      }

      .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #42A5F5, #66BB6A);
        transition: width 0.5s ease;
        border-radius: 6px;
      }

      .progress-text {
        text-align: center;
        margin-top: 8px;
        color: var(--secondary-text-color);
        font-size: 0.9em;
      }

      /* === BUTTONS === */
      .button-row {
        display: flex;
        gap: 12px;
        padding: 10px;
        justify-content: center;
      }

      .btn {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 20px;
        border: none;
        border-radius: 16px;
        font-size: 1em;
        font-weight: 600;
        cursor: pointer;
        transition: transform 0.1s, box-shadow 0.2s;
        min-width: 100px;
        flex: 1;
      }

      .btn:active {
        transform: scale(0.95);
      }

      .btn-icon {
        font-size: 2.5em;
        margin-bottom: 8px;
      }

      .btn-primary {
        background: #42A5F5;
        color: white;
      }

      .btn-success {
        background: #66BB6A;
        color: white;
      }

      .btn-warning {
        background: #FFA726;
        color: white;
      }

      .btn-danger {
        background: #EF5350;
        color: white;
      }

      .btn-secondary {
        background: var(--divider-color, #eee);
        color: var(--primary-text-color);
      }

      .btn-coral {
        background: linear-gradient(135deg, #FF6B6B, #FF8E8E);
        color: white;
      }

      .btn-large {
        padding: 30px;
        font-size: 1.2em;
      }

      .btn-large .btn-icon {
        font-size: 3em;
      }

      .btn-small {
        padding: 8px 16px;
        min-width: auto;
        flex: 0;
        flex-direction: row;
        gap: 6px;
        font-size: 0.9em;
      }

      .btn-small .btn-icon {
        font-size: 1.2em;
        margin-bottom: 0;
      }

      /* === ROUTINE SELECT === */
      .welcome {
        text-align: center;
        padding: 40px 20px;
      }

      .welcome-icon {
        font-size: 4em;
        margin-bottom: 20px;
      }

      .welcome h2 {
        margin: 0 0 10px 0;
        font-weight: 600;
        color: var(--primary-text-color);
      }

      .welcome p {
        margin: 0;
        color: var(--secondary-text-color);
      }

      .routine-list {
        padding: 10px;
      }

      .routine-item {
        display: flex;
        align-items: center;
        padding: 20px;
        margin: 10px 0;
        background: var(--divider-color, #f5f5f5);
        border-radius: 12px;
        cursor: pointer;
        transition: transform 0.1s, background 0.2s;
      }

      .routine-item:hover {
        background: var(--primary-color);
        color: white;
      }

      .routine-item:active {
        transform: scale(0.98);
      }

      .routine-icon {
        font-size: 2em;
        margin-right: 16px;
      }

      .routine-info {
        flex: 1;
      }

      .routine-name {
        font-size: 1.3em;
        font-weight: 600;
      }

      .routine-meta {
        font-size: 0.9em;
        opacity: 0.7;
      }

      .routine-arrow {
        font-size: 1.5em;
        opacity: 0.5;
      }

      /* === TABS/NAV === */
      .nav {
        display: flex;
        justify-content: center;
        gap: 8px;
        padding: 10px;
        border-top: 1px solid var(--divider-color, #eee);
        margin-top: auto;
      }

      .nav-btn {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 12px 20px;
        border: none;
        background: transparent;
        border-radius: 12px;
        cursor: pointer;
        color: var(--secondary-text-color);
        font-size: 0.8em;
      }

      .nav-btn.active {
        background: var(--primary-color);
        color: white;
      }

      .nav-btn-icon {
        font-size: 1.5em;
        margin-bottom: 4px;
      }

      /* === EMPTY STATE === */
      .empty {
        text-align: center;
        padding: 40px;
        color: var(--secondary-text-color);
      }

      .empty-icon {
        font-size: 3em;
        margin-bottom: 16px;
        opacity: 0.5;
      }

      /* === TASK/ROUTINE LISTS === */
      .list-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px;
      }

      .list-header h3 {
        margin: 0;
        font-size: 1.3em;
      }

      .item-card {
        display: flex;
        align-items: center;
        padding: 16px;
        margin: 8px 16px;
        background: var(--divider-color, #f5f5f5);
        border-radius: 12px;
      }

      .item-icon {
        font-size: 1.5em;
        margin-right: 12px;
        width: 40px;
        text-align: center;
      }

      .item-info {
        flex: 1;
        cursor: pointer;
      }

      .item-info:hover {
        opacity: 0.8;
      }

      .item-name {
        font-weight: 600;
        font-size: 1.1em;
      }

      .item-meta {
        font-size: 0.85em;
        color: var(--secondary-text-color);
      }

      .item-actions {
        display: flex;
        gap: 4px;
      }

      .item-btn {
        padding: 8px;
        background: transparent;
        border: none;
        cursor: pointer;
        font-size: 1.1em;
        opacity: 0.5;
        border-radius: 8px;
      }

      .item-btn:hover {
        opacity: 1;
        background: var(--divider-color, #eee);
      }

      .item-btn.delete:hover {
        background: #EF5350;
        color: white;
      }

      /* === REVIEW SCREEN === */
      .review-header {
        text-align: center;
        padding: 16px;
        border-bottom: 1px solid var(--divider-color, #eee);
        margin-bottom: 16px;
      }

      .review-header h2 {
        margin: 0 0 4px 0;
        font-size: 1.4em;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
      }

      .review-header .meta {
        color: var(--secondary-text-color);
        font-size: 0.95em;
      }

      .review-task-list {
        max-height: 350px;
        overflow-y: auto;
        padding: 0 8px;
      }

      .review-task {
        display: flex;
        align-items: center;
        padding: 14px 16px;
        margin: 8px 0;
        background: rgba(255, 107, 107, 0.08);
        border-radius: 12px;
        border-left: 4px solid #FF6B6B;
        cursor: pointer;
        transition: all 0.15s;
      }

      .review-task:hover {
        background: rgba(255, 107, 107, 0.15);
      }

      .review-task.skipped {
        opacity: 0.5;
        background: var(--divider-color, #f0f0f0);
        border-left-color: var(--divider-color, #ccc);
        text-decoration: line-through;
      }

      .review-task .task-checkbox {
        width: 28px;
        height: 28px;
        border: 2px solid #FF6B6B;
        border-radius: 50%;
        margin-right: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        color: transparent;
        flex-shrink: 0;
        transition: all 0.15s;
      }

      .review-task.skipped .task-checkbox {
        background: #66BB6A;
        border-color: #66BB6A;
        color: white;
      }

      .review-task .task-icon {
        font-size: 1.5em;
        margin-right: 12px;
      }

      .review-task .task-details {
        flex: 1;
      }

      .review-task .task-name {
        font-weight: 600;
        font-size: 1.05em;
        margin-bottom: 2px;
      }

      .review-task .task-time {
        font-size: 0.85em;
        color: var(--secondary-text-color);
      }

      .review-task .task-duration {
        font-size: 0.9em;
        color: var(--secondary-text-color);
        margin-left: auto;
        padding-left: 12px;
      }

      .review-task .task-mode-badge {
        font-size: 0.7em;
        padding: 2px 8px;
        border-radius: 10px;
        background: rgba(255, 107, 107, 0.2);
        color: #FF6B6B;
        margin-left: 8px;
      }

      .review-summary {
        padding: 16px;
        text-align: center;
        border-top: 1px solid var(--divider-color, #eee);
        margin-top: 16px;
        color: var(--secondary-text-color);
      }

      .review-summary strong {
        color: var(--primary-text-color);
      }

      .review-actions {
        display: flex;
        gap: 12px;
        padding: 16px;
        position: sticky;
        bottom: 0;
        background: var(--ha-card-background, var(--card-background-color, white));
      }

      /* === FORMS === */
      .form {
        padding: 20px;
      }

      .form-title {
        font-size: 1.5em;
        font-weight: 600;
        margin-bottom: 20px;
        text-align: center;
      }

      .form-group {
        margin-bottom: 20px;
      }

      .form-label {
        display: block;
        margin-bottom: 8px;
        font-weight: 500;
        color: var(--primary-text-color);
      }

      .form-input {
        width: 100%;
        padding: 16px;
        border: 2px solid var(--divider-color, #ddd);
        border-radius: 12px;
        font-size: 1.1em;
        background: var(--card-background-color, white);
        color: var(--primary-text-color);
      }

      .form-input:focus {
        outline: none;
        border-color: var(--primary-color, #42A5F5);
      }

      .form-select {
        width: 100%;
        padding: 16px;
        border: 2px solid var(--divider-color, #ddd);
        border-radius: 12px;
        font-size: 1.1em;
        background: var(--card-background-color, white);
        color: var(--primary-text-color);
        cursor: pointer;
      }

      .form-hint {
        font-size: 0.85em;
        color: var(--secondary-text-color);
        margin-top: 6px;
      }

      .duration-quick {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 10px;
      }

      .duration-chip {
        padding: 10px 16px;
        border: 1px solid var(--divider-color, #ddd);
        border-radius: 20px;
        background: transparent;
        cursor: pointer;
        font-size: 0.9em;
        color: var(--primary-text-color);
      }

      .duration-chip:hover, .duration-chip.selected {
        background: var(--primary-color);
        color: white;
        border-color: var(--primary-color);
      }

      .form-actions {
        display: flex;
        gap: 12px;
        margin-top: 30px;
      }

      /* === TASK SELECTOR === */
      .task-selector {
        border: 2px solid var(--divider-color, #ddd);
        border-radius: 12px;
        max-height: 250px;
        overflow-y: auto;
        background: var(--card-background-color, white);
      }

      .task-selector-item {
        display: flex;
        align-items: center;
        padding: 14px 16px;
        cursor: pointer;
        border-bottom: 1px solid var(--divider-color, #eee);
        color: var(--primary-text-color);
        transition: background 0.15s;
      }

      .task-selector-item:last-child {
        border-bottom: none;
      }

      .task-selector-item:hover {
        background: rgba(var(--rgb-primary-color, 66, 165, 245), 0.1);
      }

      .task-selector-item.selected {
        background: rgba(var(--rgb-primary-color, 66, 165, 245), 0.2);
      }

      .task-selector-checkbox {
        width: 28px;
        height: 28px;
        margin-right: 12px;
        border: 2px solid var(--divider-color, #888);
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.9em;
        color: transparent;
        flex-shrink: 0;
      }

      .task-selector-item.selected .task-selector-checkbox {
        background: var(--primary-color, #42A5F5);
        border-color: var(--primary-color, #42A5F5);
        color: white;
      }

      .task-selector-label {
        flex: 1;
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .task-selector-label .task-icon {
        font-size: 1.3em;
      }

      .task-selector-label .task-name {
        font-weight: 500;
      }

      .task-selector-label .task-duration {
        opacity: 0.6;
        font-size: 0.9em;
      }

      .selected-count {
        text-align: center;
        padding: 12px;
        color: var(--secondary-text-color);
        font-size: 0.95em;
        font-weight: 500;
      }

      /* === EMOJI PICKER === */
      .emoji-quick {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 10px;
      }

      .emoji-chip {
        padding: 10px 14px;
        border: 2px solid var(--divider-color, #ddd);
        border-radius: 10px;
        background: var(--card-background-color, white);
        cursor: pointer;
        font-size: 1.4em;
        transition: transform 0.1s, border-color 0.15s;
      }

      .emoji-chip:hover {
        border-color: var(--primary-color, #42A5F5);
        transform: scale(1.1);
      }
      
      .emoji-chip.selected {
        border-color: var(--primary-color, #42A5F5);
        background: rgba(var(--rgb-primary-color, 66, 165, 245), 0.2);
      }

      /* === FAB (Floating Action Button) === */
      .fab {
        position: absolute;
        bottom: 80px;
        right: 20px;
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: #FFD54F;
        border: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.8em;
        transition: transform 0.1s, box-shadow 0.2s;
        z-index: 10;
      }

      .fab:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 16px rgba(0,0,0,0.25);
      }

      .fab:active {
        transform: scale(0.95);
      }
    `;
  }

  renderActiveRoutine() {
    const currentTask = this.getStateValue('sensor.routinely_current_task') || 'Current Task';
    const timeRemaining = this.getStateValue('sensor.routinely_time_remaining') || '0:00';
    const progress = parseInt(this.getStateValue('sensor.routinely_progress') || '0');
    const isPaused = this.isPaused();
    const routineName = this.getStateAttr('sensor.routinely_status', 'routine_name') || 'Routine';
    const currentIndex = (this.getStateAttr('sensor.routinely_status', 'current_task_index') || 0) + 1;
    const totalTasks = this.getStateAttr('sensor.routinely_status', 'total_tasks') || 1;

    return `
      <div class="task-name">${this.escapeHtml(currentTask)}</div>
      
      <div class="timer ${isPaused ? 'paused' : ''}">${timeRemaining}</div>
      
      <div class="status-label">
        ${isPaused ? '⏸️ PAUSED' : '⏱️ time remaining'}
      </div>

      <div class="progress-container">
        <div class="progress-bar">
          <div class="progress-fill" style="width: ${progress}%"></div>
        </div>
        <div class="progress-text">
          Task ${currentIndex} of ${totalTasks} · ${progress}% complete
        </div>
      </div>

      <div class="button-row">
        ${isPaused ? `
          <button class="btn btn-success btn-large" data-action="resume">
            <span class="btn-icon">▶️</span>
            RESUME
          </button>
        ` : `
          <button class="btn btn-warning btn-large" data-action="pause">
            <span class="btn-icon">⏸️</span>
            PAUSE
          </button>
        `}
        <button class="btn btn-success btn-large" data-action="complete">
          <span class="btn-icon">✅</span>
          DONE
        </button>
      </div>

      <div class="button-row">
        <button class="btn btn-secondary" data-action="skip">
          <span class="btn-icon">⏭️</span>
          Skip
        </button>
        <button class="btn btn-secondary" data-action="cancel" data-confirm="Stop this routine?">
          <span class="btn-icon">⏹️</span>
          Stop
        </button>
      </div>

      <div class="status-label" style="margin-top: 20px; font-size: 0.9em;">
        ${this.escapeHtml(routineName)}
      </div>
    `;
  }

  renderInactiveState() {
    switch (this._mode) {
      case 'tasks':
        return this.renderTaskList();
      case 'routines':
        return this.renderRoutineList();
      case 'create-task':
        return this.renderTaskForm(false);
      case 'edit-task':
        return this.renderTaskForm(true);
      case 'create-routine':
        return this.renderRoutineForm(false);
      case 'edit-routine':
        return this.renderRoutineForm(true);
      case 'review':
        return this.renderReviewScreen();
      default:
        return this.renderRoutineSelect();
    }
  }

  renderRoutineSelect() {
    const routines = this.getStateAttr('sensor.routinely_routines', 'routines') || [];

    return `
      <div class="welcome">
        <div class="welcome-icon">⏱️</div>
        <h2>Ready to start?</h2>
        <p>Pick a routine below</p>
      </div>

      ${routines.length === 0 ? `
        <div class="empty">
          <div class="empty-icon">📝</div>
          <p>No routines yet</p>
          <p>Create tasks first, then make a routine!</p>
        </div>
        <div class="button-row">
          <button class="btn btn-primary" data-nav="tasks">
            <span class="btn-icon">📋</span>
            Create Tasks
          </button>
        </div>
      ` : `
        <div class="routine-list">
          ${routines.map(r => `
            <div class="routine-item" data-action="review" data-routine-id="${r.id}">
              <span class="routine-icon">${r.icon || '📋'}</span>
              <div class="routine-info">
                <div class="routine-name">${this.escapeHtml(r.name)}</div>
                <div class="routine-meta">${r.task_count} tasks · ${r.duration_formatted}</div>
              </div>
              <span class="routine-arrow">▶️</span>
            </div>
          `).join('')}
        </div>
      `}

      ${this.renderNav('timer')}
    `;
  }

  renderReviewScreen() {
    const routines = this.getStateAttr('sensor.routinely_routines', 'routines') || [];
    const tasks = this.getStateAttr('sensor.routinely_tasks', 'tasks') || [];
    const routine = routines.find(r => r.id === this._reviewRoutineId);
    
    if (!routine) {
      this._mode = 'timer';
      return this.renderRoutineSelect();
    }

    // Get tasks for this routine
    const routineTasks = (routine.task_ids || [])
      .map(tid => tasks.find(t => t.id === tid))
      .filter(Boolean);

    // Calculate times
    let currentTime = new Date();
    const startTime = new Date(currentTime);
    const taskTimes = routineTasks.map(task => {
      const start = new Date(currentTime);
      const end = new Date(currentTime.getTime() + task.duration * 1000);
      currentTime = end;
      return { start, end, task };
    });

    // Calculate total duration excluding skipped
    const totalDuration = routineTasks
      .filter(t => !this._skippedTaskIds.includes(t.id))
      .reduce((sum, t) => sum + t.duration, 0);
    
    const activeTaskCount = routineTasks.length - this._skippedTaskIds.length;
    const endTime = new Date(startTime.getTime() + totalDuration * 1000);

    const formatTime = (date) => date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const formatDuration = (secs) => {
      if (secs < 60) return `${secs}s`;
      const mins = Math.floor(secs / 60);
      if (mins < 60) return `${mins}m`;
      const hours = Math.floor(mins / 60);
      const remMins = mins % 60;
      return remMins > 0 ? `${hours}h ${remMins}m` : `${hours}h`;
    };

    return `
      <div class="review-header">
        <h2>${routine.icon || '📋'} ${this.escapeHtml(routine.name)}</h2>
        <div class="meta">
          ${formatTime(startTime)} → ${formatTime(endTime)} · ${formatDuration(totalDuration)}
        </div>
      </div>

      <div style="padding: 0 16px; margin-bottom: 8px; color: var(--secondary-text-color); font-size: 0.9em;">
        Tap tasks you've already done to skip them:
      </div>

      <div class="review-task-list">
        ${taskTimes.map(({ start, end, task }, index) => {
          const isSkipped = this._skippedTaskIds.includes(task.id);
          const modeLabel = task.mode === 'auto' ? '' : task.mode === 'manual' ? 'Manual' : 'Confirm';
          return `
            <div class="review-task ${isSkipped ? 'skipped' : ''}" data-task-id="${task.id}" data-action="toggle-skip">
              <div class="task-checkbox">✓</div>
              <span class="task-icon">${task.icon || '✅'}</span>
              <div class="task-details">
                <div class="task-name">${this.escapeHtml(task.name)}</div>
                <div class="task-time">${formatTime(start)} - ${formatTime(end)}</div>
              </div>
              ${modeLabel ? `<span class="task-mode-badge">${modeLabel}</span>` : ''}
              <span class="task-duration">${task.duration_formatted}</span>
            </div>
          `;
        }).join('')}
      </div>

      <div class="review-summary">
        ${this._skippedTaskIds.length > 0 
          ? `<strong>${activeTaskCount}</strong> of ${routineTasks.length} tasks · ${this._skippedTaskIds.length} skipped`
          : `<strong>${routineTasks.length}</strong> tasks · ${formatDuration(totalDuration)}`
        }
      </div>

      <div class="review-actions">
        <button class="btn btn-secondary" data-nav="timer" style="flex: 1;">
          ← Back
        </button>
        <button class="btn btn-coral" data-action="start-routine" style="flex: 2;">
          <span class="btn-icon">▶️</span>
          Start Routine
        </button>
      </div>
    `;
  }

  renderTaskList() {
    const tasks = this.getStateAttr('sensor.routinely_tasks', 'tasks') || [];

    return `
      <div class="list-header">
        <h3>📋 Tasks</h3>
        <button class="btn btn-primary btn-small" data-nav="create-task">
          <span class="btn-icon">➕</span>
          New
        </button>
      </div>

      ${tasks.length === 0 ? `
        <div class="empty">
          <div class="empty-icon">📝</div>
          <p>No tasks yet</p>
          <p>Create your first task!</p>
        </div>
      ` : `
        ${tasks.map(t => `
          <div class="item-card">
            <span class="item-icon">${t.icon || '✅'}</span>
            <div class="item-info" data-action="edit-task" data-task-id="${t.id}">
              <div class="item-name">${this.escapeHtml(t.name)}</div>
              <div class="item-meta">${t.duration_formatted} · ${t.mode}</div>
            </div>
            <div class="item-actions">
              <button class="item-btn" data-action="copy-task" data-task-id="${t.id}" title="Copy">📋</button>
              <button class="item-btn" data-action="edit-task" data-task-id="${t.id}" title="Edit">✏️</button>
              <button class="item-btn delete" data-action="delete-task" data-task-id="${t.id}" title="Delete">🗑️</button>
            </div>
          </div>
        `).join('')}
      `}

      ${this.renderNav('tasks')}
    `;
  }

  renderRoutineList() {
    const routines = this.getStateAttr('sensor.routinely_routines', 'routines') || [];

    return `
      <div class="list-header">
        <h3>📚 Routines</h3>
        <button class="btn btn-primary btn-small" data-nav="create-routine">
          <span class="btn-icon">➕</span>
          New
        </button>
      </div>

      ${routines.length === 0 ? `
        <div class="empty">
          <div class="empty-icon">📚</div>
          <p>No routines yet</p>
          <p>Create tasks first, then combine them into a routine!</p>
        </div>
      ` : `
        ${routines.map(r => `
          <div class="item-card">
            <span class="item-icon">${r.icon || '📋'}</span>
            <div class="item-info" data-action="edit-routine" data-routine-id="${r.id}">
              <div class="item-name">${this.escapeHtml(r.name)}</div>
              <div class="item-meta">${r.task_count} tasks · ${r.duration_formatted}</div>
            </div>
            <div class="item-actions">
              <button class="item-btn" data-action="edit-routine" data-routine-id="${r.id}" title="Edit">✏️</button>
              <button class="item-btn delete" data-action="delete-routine" data-routine-id="${r.id}" title="Delete">🗑️</button>
            </div>
          </div>
        `).join('')}
      `}

      ${this.renderNav('routines')}
    `;
  }

  renderTaskForm(isEdit) {
    const f = this._formState;
    const dur = parseInt(f.taskDuration) || 120;
    const title = isEdit ? '✏️ Edit Task' : '➕ New Task';
    const saveLabel = isEdit ? 'Save Changes' : 'Create Task';
    const cancelNav = 'tasks';
    
    return `
      <div class="form">
        <div class="form-title">${title}</div>

        <div class="form-group">
          <label class="form-label">Task Name</label>
          <input type="text" class="form-input" id="task-name" placeholder="e.g. Brush teeth" value="${this.escapeAttr(f.taskName)}">
        </div>

        <div class="form-group">
          <label class="form-label">Duration</label>
          <input type="number" class="form-input" id="task-duration" placeholder="120" value="${dur}">
          <div class="duration-quick">
            <button class="duration-chip ${dur === 30 ? 'selected' : ''}" data-duration="30">30s</button>
            <button class="duration-chip ${dur === 60 ? 'selected' : ''}" data-duration="60">1m</button>
            <button class="duration-chip ${dur === 120 ? 'selected' : ''}" data-duration="120">2m</button>
            <button class="duration-chip ${dur === 300 ? 'selected' : ''}" data-duration="300">5m</button>
            <button class="duration-chip ${dur === 600 ? 'selected' : ''}" data-duration="600">10m</button>
            <button class="duration-chip ${dur === 900 ? 'selected' : ''}" data-duration="900">15m</button>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">When timer ends</label>
          <select class="form-select" id="task-mode">
            <option value="auto" ${f.taskMode === 'auto' ? 'selected' : ''}>Auto → Go to next automatically</option>
            <option value="manual" ${f.taskMode === 'manual' ? 'selected' : ''}>Manual → Must tap DONE</option>
            <option value="confirm" ${f.taskMode === 'confirm' ? 'selected' : ''}>Confirm → Ask, then auto-continue</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Icon</label>
          <input type="text" class="form-input" id="task-icon" placeholder="Pick below or type emoji" value="${this.escapeAttr(f.taskIcon)}">
          <div class="emoji-quick">
            ${['🪥', '🚿', '👕', '☕', '🍳', '💊', '📱', '🧘', '🏃', '📚', '✍️', '🧹'].map(e => `
              <button class="emoji-chip ${f.taskIcon === e ? 'selected' : ''}" data-emoji="${e}">${e}</button>
            `).join('')}
          </div>
        </div>

        <div class="form-actions">
          <button class="btn btn-secondary" data-nav="${cancelNav}" style="flex:1">Cancel</button>
          <button class="btn btn-success" data-action="${isEdit ? 'update-task' : 'save-task'}" style="flex:2">
            <span class="btn-icon">✅</span>
            ${saveLabel}
          </button>
        </div>
      </div>
    `;
  }

  renderRoutineForm(isEdit) {
    const tasks = this.getStateAttr('sensor.routinely_tasks', 'tasks') || [];
    const f = this._formState;
    const title = isEdit ? '✏️ Edit Routine' : '📚 New Routine';
    const saveLabel = isEdit ? 'Save Changes' : 'Create Routine';

    if (tasks.length === 0) {
      return `
        <div class="form">
          <div class="form-title">${title}</div>
          <div class="empty">
            <div class="empty-icon">⚠️</div>
            <p>Create some tasks first!</p>
            <p>Routines are made by combining tasks.</p>
          </div>
          <button class="btn btn-primary" data-nav="create-task" style="width:100%">
            <span class="btn-icon">➕</span>
            Create a Task First
          </button>
        </div>
        ${this.renderNav('routines')}
      `;
    }

    const selectedCount = this._selectedTasks.length;

    return `
      <div class="form">
        <div class="form-title">${title}</div>

        <div class="form-group">
          <label class="form-label">Routine Name</label>
          <input type="text" class="form-input" id="routine-name" placeholder="e.g. Morning Routine" value="${this.escapeAttr(f.routineName)}">
        </div>

        <div class="form-group">
          <label class="form-label">Icon</label>
          <input type="text" class="form-input" id="routine-icon" placeholder="Pick below or type emoji" value="${this.escapeAttr(f.routineIcon)}">
          <div class="emoji-quick">
            ${['🌅', '🌙', '💪', '🧘', '🍽️', '🛁', '🏠', '💼', '📖', '😴'].map(e => `
              <button class="emoji-chip ${f.routineIcon === e ? 'selected' : ''}" data-emoji="${e}">${e}</button>
            `).join('')}
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Select Tasks (tap in order)</label>
          <div class="task-selector" id="task-selector">
            ${tasks.map(t => `
              <div class="task-selector-item ${this._selectedTasks.includes(t.id) ? 'selected' : ''}" data-task-id="${t.id}">
                <div class="task-selector-checkbox">✓</div>
                <div class="task-selector-label">
                  <span class="task-icon">${t.icon || '✅'}</span>
                  <span class="task-name">${this.escapeHtml(t.name)}</span>
                  <span class="task-duration">${t.duration_formatted}</span>
                </div>
              </div>
            `).join('')}
          </div>
          <div class="selected-count" id="selected-count">${selectedCount} task${selectedCount !== 1 ? 's' : ''} selected</div>
        </div>

        <div class="form-actions">
          <button class="btn btn-secondary" data-nav="routines" style="flex:1">Cancel</button>
          <button class="btn btn-success" data-action="${isEdit ? 'update-routine' : 'save-routine'}" style="flex:2">
            <span class="btn-icon">✅</span>
            ${saveLabel}
          </button>
        </div>
      </div>
    `;
  }

  renderNav(activeTab) {
    return `
      <div class="nav">
        <button class="nav-btn ${activeTab === 'timer' ? 'active' : ''}" data-nav="timer">
          <span class="nav-btn-icon">⏱️</span>
          Start
        </button>
        <button class="nav-btn ${activeTab === 'tasks' ? 'active' : ''}" data-nav="tasks">
          <span class="nav-btn-icon">📋</span>
          Tasks
        </button>
        <button class="nav-btn ${activeTab === 'routines' ? 'active' : ''}" data-nav="routines">
          <span class="nav-btn-icon">📚</span>
          Routines
        </button>
      </div>
    `;
  }

  attachEventListeners() {
    // Navigation
    this.shadowRoot.querySelectorAll('[data-nav]').forEach(el => {
      el.addEventListener('click', (e) => {
        const newMode = e.currentTarget.dataset.nav;
        
        // Clear state when leaving create/edit/review
        if ((this._mode.startsWith('create-') || this._mode.startsWith('edit-') || this._mode === 'review') && 
            !newMode.startsWith('create-') && !newMode.startsWith('edit-') && newMode !== 'review') {
          this._clearFormState();
          this._editingId = null;
          this._reviewRoutineId = null;
          this._skippedTaskIds = [];
        }
        
        this._mode = newMode;
        this._lastRenderState = null;
        this.render();
      });
    });

    // Actions
    this.shadowRoot.querySelectorAll('[data-action]').forEach(el => {
      el.addEventListener('click', (e) => {
        const action = e.currentTarget.dataset.action;
        const confirm = e.currentTarget.dataset.confirm;
        
        if (confirm && !window.confirm(confirm)) return;

        switch (action) {
          case 'review':
            this._reviewRoutineId = e.currentTarget.dataset.routineId;
            this._skippedTaskIds = [];
            this._mode = 'review';
            this._lastRenderState = null;
            this.render();
            break;
          case 'toggle-skip':
            const taskId = e.currentTarget.dataset.taskId;
            const idx = this._skippedTaskIds.indexOf(taskId);
            if (idx > -1) {
              this._skippedTaskIds.splice(idx, 1);
            } else {
              this._skippedTaskIds.push(taskId);
            }
            this.render();
            break;
          case 'start-routine':
            const skipIds = this._skippedTaskIds.length > 0 ? this._skippedTaskIds : undefined;
            this.callService('start', { 
              routine_id: this._reviewRoutineId,
              skip_task_ids: skipIds
            });
            break;
          case 'pause':
            this.callService('pause');
            break;
          case 'resume':
            this.callService('resume');
            break;
          case 'complete':
            this.callService('complete_task');
            break;
          case 'skip':
            this.callService('skip');
            break;
          case 'cancel':
            this.callService('cancel');
            break;
          case 'edit-task':
            this.startEditTask(e.currentTarget.dataset.taskId);
            break;
          case 'copy-task':
            this.copyTask(e.currentTarget.dataset.taskId);
            break;
          case 'edit-routine':
            this.startEditRoutine(e.currentTarget.dataset.routineId);
            break;
          case 'delete-task':
            if (window.confirm('Delete this task?')) {
              this.callService('delete_task', { task_id: e.currentTarget.dataset.taskId });
            }
            break;
          case 'delete-routine':
            if (window.confirm('Delete this routine?')) {
              this.callService('delete_routine', { routine_id: e.currentTarget.dataset.routineId });
            }
            break;
          case 'save-task':
            this.saveTask(false);
            break;
          case 'update-task':
            this.saveTask(true);
            break;
          case 'save-routine':
            this.saveRoutine(false);
            break;
          case 'update-routine':
            this.saveRoutine(true);
            break;
        }
      });
    });

    // Form input change tracking
    const taskNameInput = this.shadowRoot.getElementById('task-name');
    const taskDurationInput = this.shadowRoot.getElementById('task-duration');
    const taskModeSelect = this.shadowRoot.getElementById('task-mode');
    const taskIconInput = this.shadowRoot.getElementById('task-icon');
    const routineNameInput = this.shadowRoot.getElementById('routine-name');
    const routineIconInput = this.shadowRoot.getElementById('routine-icon');

    if (taskNameInput) {
      taskNameInput.addEventListener('input', (e) => {
        this._formState.taskName = e.target.value;
      });
    }
    if (taskDurationInput) {
      taskDurationInput.addEventListener('input', (e) => {
        this._formState.taskDuration = e.target.value;
      });
    }
    if (taskModeSelect) {
      taskModeSelect.addEventListener('change', (e) => {
        this._formState.taskMode = e.target.value;
      });
    }
    if (taskIconInput) {
      taskIconInput.addEventListener('input', (e) => {
        this._formState.taskIcon = e.target.value;
      });
    }
    if (routineNameInput) {
      routineNameInput.addEventListener('input', (e) => {
        this._formState.routineName = e.target.value;
      });
    }
    if (routineIconInput) {
      routineIconInput.addEventListener('input', (e) => {
        this._formState.routineIcon = e.target.value;
      });
    }

    // Duration chips
    this.shadowRoot.querySelectorAll('.duration-chip').forEach(el => {
      el.addEventListener('click', (e) => {
        const duration = e.currentTarget.dataset.duration;
        const input = this.shadowRoot.getElementById('task-duration');
        if (input) {
          input.value = duration;
          this._formState.taskDuration = duration;
          this.shadowRoot.querySelectorAll('.duration-chip').forEach(c => c.classList.remove('selected'));
          e.currentTarget.classList.add('selected');
        }
      });
    });

    // Emoji chips
    this.shadowRoot.querySelectorAll('.emoji-chip').forEach(el => {
      el.addEventListener('click', (e) => {
        const emoji = e.currentTarget.dataset.emoji;
        const taskIconInput = this.shadowRoot.getElementById('task-icon');
        const routineIconInput = this.shadowRoot.getElementById('routine-icon');
        
        if (taskIconInput) {
          taskIconInput.value = emoji;
          this._formState.taskIcon = emoji;
        }
        if (routineIconInput) {
          routineIconInput.value = emoji;
          this._formState.routineIcon = emoji;
        }
        
        this.shadowRoot.querySelectorAll('.emoji-chip').forEach(c => c.classList.remove('selected'));
        e.currentTarget.classList.add('selected');
      });
    });

    // Task selector for routine creation
    this.shadowRoot.querySelectorAll('.task-selector-item').forEach(el => {
      el.addEventListener('click', (e) => {
        const taskId = e.currentTarget.dataset.taskId;
        const index = this._selectedTasks.indexOf(taskId);
        
        if (index > -1) {
          this._selectedTasks.splice(index, 1);
          e.currentTarget.classList.remove('selected');
        } else {
          this._selectedTasks.push(taskId);
          e.currentTarget.classList.add('selected');
        }

        const countEl = this.shadowRoot.getElementById('selected-count');
        if (countEl) {
          countEl.textContent = `${this._selectedTasks.length} task${this._selectedTasks.length !== 1 ? 's' : ''} selected`;
        }
      });
    });
  }

  startEditTask(taskId) {
    const tasks = this.getStateAttr('sensor.routinely_tasks', 'tasks') || [];
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;

    this._editingId = taskId;
    this._formState.taskName = task.name;
    this._formState.taskDuration = String(task.duration);
    this._formState.taskMode = task.mode;
    this._formState.taskIcon = task.icon || '';
    
    this._mode = 'edit-task';
    this._lastRenderState = null;
    this.render();
  }

  copyTask(taskId) {
    const tasks = this.getStateAttr('sensor.routinely_tasks', 'tasks') || [];
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;

    const data = {
      task_name: task.name + ' (copy)',
      duration: task.duration,
      advancement_mode: task.mode,
    };
    if (task.icon) data.icon = task.icon;
    
    this.callService('create_task', data);
  }

  startEditRoutine(routineId) {
    const routines = this.getStateAttr('sensor.routinely_routines', 'routines') || [];
    const routine = routines.find(r => r.id === routineId);
    if (!routine) return;

    this._editingId = routineId;
    this._formState.routineName = routine.name;
    this._formState.routineIcon = routine.icon || '';
    this._selectedTasks = routine.task_ids ? [...routine.task_ids] : [];
    
    this._mode = 'edit-routine';
    this._lastRenderState = null;
    this.render();
  }

  saveTask(isUpdate) {
    const name = this._formState.taskName?.trim() || this.shadowRoot.getElementById('task-name')?.value?.trim();
    const duration = parseInt(this._formState.taskDuration) || parseInt(this.shadowRoot.getElementById('task-duration')?.value) || 120;
    const mode = this._formState.taskMode || this.shadowRoot.getElementById('task-mode')?.value || 'auto';
    const icon = this._formState.taskIcon?.trim() || this.shadowRoot.getElementById('task-icon')?.value?.trim();

    if (!name) {
      alert('Please enter a task name');
      return;
    }

    if (isUpdate && this._editingId) {
      const data = {
        task_id: this._editingId,
        task_name: name,
        duration: duration,
        advancement_mode: mode,
      };
      if (icon) data.icon = icon;
      this.callService('update_task', data);
    } else {
      const data = {
        task_name: name,
        duration: duration,
        advancement_mode: mode,
      };
      if (icon) data.icon = icon;
      this.callService('create_task', data);
    }
    
    this._clearFormState();
    this._editingId = null;
    this._mode = 'tasks';
    this._lastRenderState = null;
    
    setTimeout(() => this.render(), 500);
  }

  saveRoutine(isUpdate) {
    const name = this._formState.routineName?.trim() || this.shadowRoot.getElementById('routine-name')?.value?.trim();
    const icon = this._formState.routineIcon?.trim() || this.shadowRoot.getElementById('routine-icon')?.value?.trim();

    if (!name) {
      alert('Please enter a routine name');
      return;
    }

    if (!this._selectedTasks || this._selectedTasks.length === 0) {
      alert('Please select at least one task');
      return;
    }

    if (isUpdate && this._editingId) {
      const data = {
        routine_id: this._editingId,
        routine_name: name,
      };
      if (icon) data.icon = icon;
      this.callService('update_routine', data);
      
      this.callService('reorder_routine', {
        routine_id: this._editingId,
        task_ids: this._selectedTasks,
      });
    } else {
      const data = {
        routine_name: name,
        task_ids: this._selectedTasks,
      };
      if (icon) data.icon = icon;
      this.callService('create_routine', data);
    }
    
    this._clearFormState();
    this._editingId = null;
    this._mode = 'routines';
    this._lastRenderState = null;
    
    setTimeout(() => this.render(), 500);
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  escapeAttr(text) {
    if (!text) return '';
    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  _clearFormState() {
    this._formState = {
      taskName: '',
      taskDuration: '120',
      taskMode: 'auto',
      taskIcon: '',
      routineName: '',
      routineIcon: '',
    };
    this._selectedTasks = [];
  }

  getCardSize() {
    return 6;
  }
}

customElements.define('routinely-card', RoutinelyCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'routinely-card',
  name: 'Routinely Card',
  description: 'ADHD-friendly timer and routine management',
  preview: true,
});

console.log('%c ROUTINELY CARD %c v1.3.0 ', 
  'background: #FF6B6B; color: white; font-weight: bold;',
  'background: #66BB6A; color: white;');
