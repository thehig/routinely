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
    this._mode = 'timer'; // timer | routines | tasks | create-task | create-routine
  }

  setConfig(config) {
    this.config = config;
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
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

      .btn-large {
        padding: 30px;
        font-size: 1.2em;
      }

      .btn-large .btn-icon {
        font-size: 3em;
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
      }

      .item-name {
        font-weight: 600;
        font-size: 1.1em;
      }

      .item-meta {
        font-size: 0.85em;
        color: var(--secondary-text-color);
      }

      .item-delete {
        padding: 10px;
        background: transparent;
        border: none;
        cursor: pointer;
        font-size: 1.2em;
        opacity: 0.5;
        border-radius: 8px;
      }

      .item-delete:hover {
        opacity: 1;
        background: #EF5350;
        color: white;
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
        max-height: 200px;
        overflow-y: auto;
      }

      .task-selector-item {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        cursor: pointer;
        border-bottom: 1px solid var(--divider-color, #eee);
      }

      .task-selector-item:last-child {
        border-bottom: none;
      }

      .task-selector-item:hover {
        background: var(--divider-color, #f5f5f5);
      }

      .task-selector-item.selected {
        background: #E3F2FD;
      }

      .task-selector-checkbox {
        width: 24px;
        height: 24px;
        margin-right: 12px;
        border: 2px solid var(--divider-color, #ddd);
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .task-selector-item.selected .task-selector-checkbox {
        background: var(--primary-color);
        border-color: var(--primary-color);
        color: white;
      }

      .selected-count {
        text-align: center;
        padding: 10px;
        color: var(--secondary-text-color);
        font-size: 0.9em;
      }

      /* === ALERTS === */
      .alert {
        padding: 16px;
        border-radius: 12px;
        margin: 16px;
        text-align: center;
      }

      .alert-success {
        background: #E8F5E9;
        color: #2E7D32;
      }

      .alert-error {
        background: #FFEBEE;
        color: #C62828;
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
        return this.renderCreateTask();
      case 'create-routine':
        return this.renderCreateRoutine();
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
            <div class="routine-item" data-action="start" data-routine-id="${r.id}">
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

  renderTaskList() {
    const tasks = this.getStateAttr('sensor.routinely_tasks', 'tasks') || [];

    return `
      <div class="list-header">
        <h3>📋 Tasks</h3>
        <button class="btn btn-primary" data-nav="create-task">
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
            <span class="item-icon">${t.icon || '✓'}</span>
            <div class="item-info">
              <div class="item-name">${this.escapeHtml(t.name)}</div>
              <div class="item-meta">${t.duration_formatted} · ${t.mode}</div>
            </div>
            <button class="item-delete" data-action="delete-task" data-task-id="${t.id}" title="Delete">🗑️</button>
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
        <button class="btn btn-primary" data-nav="create-routine">
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
            <div class="item-info">
              <div class="item-name">${this.escapeHtml(r.name)}</div>
              <div class="item-meta">${r.task_count} tasks · ${r.duration_formatted}</div>
            </div>
            <button class="item-delete" data-action="delete-routine" data-routine-id="${r.id}" title="Delete">🗑️</button>
          </div>
        `).join('')}
      `}

      ${this.renderNav('routines')}
    `;
  }

  renderCreateTask() {
    return `
      <div class="form">
        <div class="form-title">➕ New Task</div>

        <div class="form-group">
          <label class="form-label">Task Name</label>
          <input type="text" class="form-input" id="task-name" placeholder="e.g. Brush teeth">
        </div>

        <div class="form-group">
          <label class="form-label">Duration (seconds)</label>
          <input type="number" class="form-input" id="task-duration" placeholder="120" value="120">
          <div class="duration-quick">
            <button class="duration-chip" data-duration="60">1 min</button>
            <button class="duration-chip selected" data-duration="120">2 min</button>
            <button class="duration-chip" data-duration="300">5 min</button>
            <button class="duration-chip" data-duration="600">10 min</button>
            <button class="duration-chip" data-duration="900">15 min</button>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">When timer ends</label>
          <select class="form-select" id="task-mode">
            <option value="auto">Auto → Go to next automatically</option>
            <option value="manual">Manual → Must tap DONE</option>
            <option value="confirm">Confirm → Ask, then auto-continue</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Icon (optional)</label>
          <input type="text" class="form-input" id="task-icon" placeholder="mdi:toothbrush or emoji 🪥">
          <div class="form-hint">Use mdi:icon-name or emoji</div>
        </div>

        <div class="form-actions">
          <button class="btn btn-secondary" data-nav="tasks" style="flex:1">Cancel</button>
          <button class="btn btn-success" data-action="save-task" style="flex:2">
            <span class="btn-icon">✅</span>
            Create Task
          </button>
        </div>
      </div>
    `;
  }

  renderCreateRoutine() {
    const tasks = this.getStateAttr('sensor.routinely_tasks', 'tasks') || [];

    if (tasks.length === 0) {
      return `
        <div class="form">
          <div class="form-title">📚 New Routine</div>
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

    return `
      <div class="form">
        <div class="form-title">📚 New Routine</div>

        <div class="form-group">
          <label class="form-label">Routine Name</label>
          <input type="text" class="form-input" id="routine-name" placeholder="e.g. Morning Routine">
        </div>

        <div class="form-group">
          <label class="form-label">Icon (optional)</label>
          <input type="text" class="form-input" id="routine-icon" placeholder="mdi:weather-sunny or emoji 🌅">
        </div>

        <div class="form-group">
          <label class="form-label">Select Tasks (in order)</label>
          <div class="task-selector" id="task-selector">
            ${tasks.map(t => `
              <div class="task-selector-item" data-task-id="${t.id}">
                <div class="task-selector-checkbox">✓</div>
                <span>${t.icon || '✓'}</span>
                <span style="margin-left:8px">${this.escapeHtml(t.name)} (${t.duration_formatted})</span>
              </div>
            `).join('')}
          </div>
          <div class="selected-count" id="selected-count">0 tasks selected</div>
        </div>

        <div class="form-actions">
          <button class="btn btn-secondary" data-nav="routines" style="flex:1">Cancel</button>
          <button class="btn btn-success" data-action="save-routine" style="flex:2">
            <span class="btn-icon">✅</span>
            Create Routine
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
        this._mode = e.currentTarget.dataset.nav;
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
          case 'start':
            this.callService('start', { routine_id: e.currentTarget.dataset.routineId });
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
            this.saveTask();
            break;
          case 'save-routine':
            this.saveRoutine();
            break;
        }
      });
    });

    // Duration chips
    this.shadowRoot.querySelectorAll('.duration-chip').forEach(el => {
      el.addEventListener('click', (e) => {
        const duration = e.currentTarget.dataset.duration;
        const input = this.shadowRoot.getElementById('task-duration');
        if (input) {
          input.value = duration;
          this.shadowRoot.querySelectorAll('.duration-chip').forEach(c => c.classList.remove('selected'));
          e.currentTarget.classList.add('selected');
        }
      });
    });

    // Task selector for routine creation
    this._selectedTasks = [];
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

  saveTask() {
    const name = this.shadowRoot.getElementById('task-name')?.value?.trim();
    const duration = parseInt(this.shadowRoot.getElementById('task-duration')?.value) || 120;
    const mode = this.shadowRoot.getElementById('task-mode')?.value || 'auto';
    const icon = this.shadowRoot.getElementById('task-icon')?.value?.trim();

    if (!name) {
      alert('Please enter a task name');
      return;
    }

    const data = {
      task_name: name,
      duration: duration,
      advancement_mode: mode,
    };

    if (icon) {
      data.icon = icon;
    }

    this.callService('create_task', data);
    this._mode = 'tasks';
    
    // Give a moment for the service to complete
    setTimeout(() => this.render(), 500);
  }

  saveRoutine() {
    const name = this.shadowRoot.getElementById('routine-name')?.value?.trim();
    const icon = this.shadowRoot.getElementById('routine-icon')?.value?.trim();

    if (!name) {
      alert('Please enter a routine name');
      return;
    }

    if (!this._selectedTasks || this._selectedTasks.length === 0) {
      alert('Please select at least one task');
      return;
    }

    const data = {
      routine_name: name,
      task_ids: this._selectedTasks,
    };

    if (icon) {
      data.icon = icon;
    }

    this.callService('create_routine', data);
    this._selectedTasks = [];
    this._mode = 'routines';
    
    setTimeout(() => this.render(), 500);
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  getCardSize() {
    return 6;
  }
}

customElements.define('routinely-card', RoutinelyCard);

// Register with HACS frontend
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'routinely-card',
  name: 'Routinely Card',
  description: 'ADHD-friendly timer and routine management',
  preview: true,
});

console.log('%c ROUTINELY CARD %c Loaded ', 
  'background: #42A5F5; color: white; font-weight: bold;',
  'background: #66BB6A; color: white;');
