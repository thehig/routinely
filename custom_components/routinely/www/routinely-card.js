/**
 * Routinely Card - Custom Lovelace card for managing routines
 */
class RoutinelyCard extends HTMLElement {
  static get properties() {
    return {
      hass: {},
      config: {},
    };
  }

  setConfig(config) {
    this.config = config;
    this._view = config.view || 'dashboard'; // dashboard, tasks, routines
  }

  set hass(hass) {
    this._hass = hass;
    if (!this.content) {
      this._createCard();
    }
    this._updateCard();
  }

  _createCard() {
    this.innerHTML = `
      <ha-card>
        <style>
          .routinely-container {
            padding: 16px;
          }
          .routinely-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
          }
          .routinely-title {
            font-size: 1.5em;
            font-weight: 500;
          }
          .routinely-tabs {
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
            border-bottom: 1px solid var(--divider-color);
            padding-bottom: 8px;
          }
          .routinely-tab {
            padding: 8px 16px;
            cursor: pointer;
            border-radius: 4px;
            background: none;
            border: none;
            color: var(--primary-text-color);
            font-size: 14px;
          }
          .routinely-tab.active {
            background: var(--primary-color);
            color: var(--text-primary-color);
          }
          .routinely-tab:hover:not(.active) {
            background: var(--secondary-background-color);
          }
          
          /* Active Routine Display */
          .active-routine {
            background: var(--primary-color);
            color: var(--text-primary-color);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
          }
          .active-routine.paused {
            background: var(--warning-color);
          }
          .active-routine-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          .active-routine-name {
            font-size: 1.2em;
            font-weight: 500;
          }
          .active-routine-status {
            font-size: 0.9em;
            opacity: 0.9;
          }
          .active-task {
            margin-top: 16px;
            text-align: center;
          }
          .active-task-name {
            font-size: 1.4em;
            margin-bottom: 8px;
          }
          .active-task-timer {
            font-size: 3em;
            font-weight: bold;
            font-family: monospace;
          }
          .active-task-progress {
            margin-top: 8px;
            font-size: 0.9em;
            opacity: 0.9;
          }
          .active-controls {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-top: 16px;
          }
          .control-btn {
            padding: 10px 20px;
            border-radius: 8px;
            border: 2px solid currentColor;
            background: transparent;
            color: inherit;
            cursor: pointer;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 6px;
          }
          .control-btn:hover {
            background: rgba(255,255,255,0.2);
          }
          .control-btn.primary {
            background: rgba(255,255,255,0.2);
          }
          
          /* No Active Routine */
          .no-active {
            text-align: center;
            padding: 40px 20px;
            color: var(--secondary-text-color);
          }
          .no-active-icon {
            font-size: 48px;
            margin-bottom: 16px;
          }
          
          /* Lists */
          .item-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
          }
          .item-card {
            background: var(--card-background-color);
            border: 1px solid var(--divider-color);
            border-radius: 8px;
            padding: 12px 16px;
            display: flex;
            align-items: center;
            gap: 12px;
            cursor: pointer;
            transition: background 0.2s;
          }
          .item-card:hover {
            background: var(--secondary-background-color);
          }
          .item-icon {
            font-size: 24px;
            width: 40px;
            text-align: center;
          }
          .item-info {
            flex: 1;
          }
          .item-name {
            font-weight: 500;
          }
          .item-meta {
            font-size: 0.85em;
            color: var(--secondary-text-color);
          }
          .item-actions {
            display: flex;
            gap: 8px;
          }
          .item-btn {
            padding: 6px 12px;
            border-radius: 4px;
            border: 1px solid var(--divider-color);
            background: transparent;
            color: var(--primary-text-color);
            cursor: pointer;
            font-size: 12px;
          }
          .item-btn.primary {
            background: var(--primary-color);
            color: var(--text-primary-color);
            border-color: var(--primary-color);
          }
          .item-btn:hover {
            opacity: 0.8;
          }
          
          /* Add Button */
          .add-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            width: 100%;
            padding: 12px;
            margin-top: 16px;
            border: 2px dashed var(--divider-color);
            border-radius: 8px;
            background: transparent;
            color: var(--primary-color);
            cursor: pointer;
            font-size: 14px;
          }
          .add-btn:hover {
            background: var(--secondary-background-color);
          }

          /* Forms */
          .form-group {
            margin-bottom: 16px;
          }
          .form-label {
            display: block;
            margin-bottom: 4px;
            font-size: 0.9em;
            color: var(--secondary-text-color);
          }
          .form-input {
            width: 100%;
            padding: 10px;
            border: 1px solid var(--divider-color);
            border-radius: 4px;
            background: var(--card-background-color);
            color: var(--primary-text-color);
            font-size: 14px;
            box-sizing: border-box;
          }
          .form-select {
            width: 100%;
            padding: 10px;
            border: 1px solid var(--divider-color);
            border-radius: 4px;
            background: var(--card-background-color);
            color: var(--primary-text-color);
            font-size: 14px;
          }
          .form-row {
            display: flex;
            gap: 12px;
          }
          .form-row > * {
            flex: 1;
          }
          .form-actions {
            display: flex;
            gap: 8px;
            justify-content: flex-end;
            margin-top: 16px;
          }
          .btn {
            padding: 10px 20px;
            border-radius: 4px;
            border: none;
            cursor: pointer;
            font-size: 14px;
          }
          .btn-primary {
            background: var(--primary-color);
            color: var(--text-primary-color);
          }
          .btn-secondary {
            background: var(--secondary-background-color);
            color: var(--primary-text-color);
          }
          
          /* Empty State */
          .empty-state {
            text-align: center;
            padding: 40px;
            color: var(--secondary-text-color);
          }
        </style>
        <div class="routinely-container">
          <div class="routinely-header">
            <div class="routinely-title">⏱️ Routinely</div>
          </div>
          <div class="routinely-tabs">
            <button class="routinely-tab active" data-view="dashboard">Dashboard</button>
            <button class="routinely-tab" data-view="tasks">Tasks</button>
            <button class="routinely-tab" data-view="routines">Routines</button>
          </div>
          <div class="routinely-content" id="routinely-content">
            Loading...
          </div>
        </div>
      </ha-card>
    `;
    
    this.content = this.querySelector('#routinely-content');
    
    // Tab switching
    this.querySelectorAll('.routinely-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        this.querySelectorAll('.routinely-tab').forEach(t => t.classList.remove('active'));
        e.target.classList.add('active');
        this._view = e.target.dataset.view;
        this._updateCard();
      });
    });
  }

  _updateCard() {
    if (!this._hass || !this.content) return;
    
    switch(this._view) {
      case 'tasks':
        this._renderTasks();
        break;
      case 'routines':
        this._renderRoutines();
        break;
      default:
        this._renderDashboard();
    }
  }

  _renderDashboard() {
    const status = this._hass.states['sensor.routinely_status'];
    const currentTask = this._hass.states['sensor.routinely_current_task'];
    const timeRemaining = this._hass.states['sensor.routinely_time_remaining'];
    const progress = this._hass.states['sensor.routinely_progress'];
    const isActive = this._hass.states['binary_sensor.routinely_active'];
    const isPaused = this._hass.states['binary_sensor.routinely_paused'];
    
    if (isActive && isActive.state === 'on') {
      const routineName = status?.attributes?.routine_name || 'Routine';
      const taskName = currentTask?.state || 'Task';
      const time = timeRemaining?.state || '0:00';
      const progressPct = progress?.state || 0;
      const completedTasks = status?.attributes?.completed_tasks || 0;
      const totalTasks = status?.attributes?.total_tasks || 0;
      const paused = isPaused?.state === 'on';
      
      this.content.innerHTML = `
        <div class="active-routine ${paused ? 'paused' : ''}">
          <div class="active-routine-header">
            <div class="active-routine-name">${routineName}</div>
            <div class="active-routine-status">${paused ? '⏸️ Paused' : '▶️ Running'}</div>
          </div>
          <div class="active-task">
            <div class="active-task-name">${taskName}</div>
            <div class="active-task-timer">${time}</div>
            <div class="active-task-progress">Task ${completedTasks + 1} of ${totalTasks} • ${progressPct}% complete</div>
          </div>
          <div class="active-controls">
            ${paused ? 
              `<button class="control-btn primary" data-action="resume">▶️ Resume</button>` :
              `<button class="control-btn" data-action="pause">⏸️ Pause</button>`
            }
            <button class="control-btn" data-action="skip">⏭️ Skip</button>
            <button class="control-btn" data-action="complete">✅ Done</button>
            <button class="control-btn" data-action="cancel">⏹️ Cancel</button>
          </div>
        </div>
      `;
      
      // Add event listeners
      this.content.querySelectorAll('[data-action]').forEach(btn => {
        btn.addEventListener('click', (e) => this._handleAction(e.target.dataset.action));
      });
    } else {
      // Show routine selection
      this.content.innerHTML = `
        <div class="no-active">
          <div class="no-active-icon">⏱️</div>
          <div>No routine running</div>
          <div style="margin-top: 16px; font-size: 0.9em;">Select a routine to start:</div>
        </div>
        <div class="item-list" id="routine-start-list">
          <div class="empty-state">Loading routines...</div>
        </div>
      `;
      
      this._loadRoutinesForStart();
    }
  }

  async _loadRoutinesForStart() {
    // We need to get routines from storage - for now show a message
    const listEl = this.querySelector('#routine-start-list');
    if (!listEl) return;
    
    listEl.innerHTML = `
      <div class="empty-state">
        <p>Create routines in the <strong>Routines</strong> tab</p>
        <p style="font-size: 0.85em; margin-top: 8px;">Or use Developer Tools → Services → routinely.start</p>
      </div>
    `;
  }

  _renderTasks() {
    this.content.innerHTML = `
      <div id="task-form" style="display: none; margin-bottom: 20px; padding: 16px; background: var(--secondary-background-color); border-radius: 8px;">
        <h3 style="margin: 0 0 16px 0;">Create Task</h3>
        <div class="form-group">
          <label class="form-label">Task Name *</label>
          <input type="text" class="form-input" id="task-name" placeholder="e.g., Brush teeth">
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Duration (seconds) *</label>
            <input type="number" class="form-input" id="task-duration" placeholder="120" min="1" max="86400">
          </div>
          <div class="form-group">
            <label class="form-label">Icon</label>
            <input type="text" class="form-input" id="task-icon" placeholder="mdi:toothbrush">
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Advancement Mode</label>
          <select class="form-select" id="task-mode">
            <option value="auto">Auto - advances automatically when timer ends</option>
            <option value="manual">Manual - must tap "Done" to advance</option>
            <option value="confirm">Confirm - prompts after timer, auto-advances if no response</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Description (optional)</label>
          <input type="text" class="form-input" id="task-description" placeholder="Optional notes or instructions">
        </div>
        <div class="form-actions">
          <button class="btn btn-secondary" id="cancel-task">Cancel</button>
          <button class="btn btn-primary" id="save-task">Create Task</button>
        </div>
      </div>
      
      <div class="item-list" id="task-list">
        <div class="empty-state">Loading tasks...</div>
      </div>
      
      <button class="add-btn" id="add-task-btn">
        <span>➕</span> Create New Task
      </button>
    `;
    
    // Event listeners
    this.querySelector('#add-task-btn').addEventListener('click', () => {
      this.querySelector('#task-form').style.display = 'block';
      this.querySelector('#add-task-btn').style.display = 'none';
    });
    
    this.querySelector('#cancel-task').addEventListener('click', () => {
      this.querySelector('#task-form').style.display = 'none';
      this.querySelector('#add-task-btn').style.display = 'flex';
      this._clearTaskForm();
    });
    
    this.querySelector('#save-task').addEventListener('click', () => this._saveTask());
    
    this._loadTasks();
  }

  _clearTaskForm() {
    this.querySelector('#task-name').value = '';
    this.querySelector('#task-duration').value = '';
    this.querySelector('#task-icon').value = '';
    this.querySelector('#task-mode').value = 'auto';
    this.querySelector('#task-description').value = '';
  }

  async _saveTask() {
    const name = this.querySelector('#task-name').value.trim();
    const duration = parseInt(this.querySelector('#task-duration').value);
    const icon = this.querySelector('#task-icon').value.trim() || 'mdi:checkbox-marked-circle-outline';
    const mode = this.querySelector('#task-mode').value;
    const description = this.querySelector('#task-description').value.trim();
    
    if (!name) {
      alert('Please enter a task name');
      return;
    }
    if (!duration || duration < 1) {
      alert('Please enter a valid duration (1-86400 seconds)');
      return;
    }
    
    try {
      await this._hass.callService('routinely', 'create_task', {
        task_name: name,
        duration: duration,
        icon: icon,
        advancement_mode: mode,
        description: description || undefined,
      });
      
      this.querySelector('#task-form').style.display = 'none';
      this.querySelector('#add-task-btn').style.display = 'flex';
      this._clearTaskForm();
      
      // Refresh task list
      setTimeout(() => this._loadTasks(), 500);
    } catch (err) {
      alert('Error creating task: ' + err.message);
    }
  }

  async _loadTasks() {
    const listEl = this.querySelector('#task-list');
    if (!listEl) return;
    
    // Tasks are stored in .storage/routinely.storage - we can't directly access it
    // Show instructions for now
    listEl.innerHTML = `
      <div class="empty-state">
        <p>Tasks are stored internally.</p>
        <p style="font-size: 0.85em; margin-top: 8px;">
          Use the form above to create tasks.<br>
          Task IDs will appear in Home Assistant logs.
        </p>
      </div>
    `;
  }

  _renderRoutines() {
    this.content.innerHTML = `
      <div id="routine-form" style="display: none; margin-bottom: 20px; padding: 16px; background: var(--secondary-background-color); border-radius: 8px;">
        <h3 style="margin: 0 0 16px 0;">Create Routine</h3>
        <div class="form-group">
          <label class="form-label">Routine Name *</label>
          <input type="text" class="form-input" id="routine-name" placeholder="e.g., Morning Routine">
        </div>
        <div class="form-group">
          <label class="form-label">Icon</label>
          <input type="text" class="form-input" id="routine-icon" placeholder="mdi:weather-sunny">
        </div>
        <div class="form-group">
          <label class="form-label">Task IDs (comma-separated)</label>
          <input type="text" class="form-input" id="routine-tasks" placeholder="task_id_1, task_id_2, task_id_3">
          <div style="font-size: 0.8em; color: var(--secondary-text-color); margin-top: 4px;">
            Find task IDs in logs after creating tasks
          </div>
        </div>
        <div class="form-actions">
          <button class="btn btn-secondary" id="cancel-routine">Cancel</button>
          <button class="btn btn-primary" id="save-routine">Create Routine</button>
        </div>
      </div>
      
      <div class="item-list" id="routine-list">
        <div class="empty-state">Loading routines...</div>
      </div>
      
      <button class="add-btn" id="add-routine-btn">
        <span>➕</span> Create New Routine
      </button>
    `;
    
    // Event listeners
    this.querySelector('#add-routine-btn').addEventListener('click', () => {
      this.querySelector('#routine-form').style.display = 'block';
      this.querySelector('#add-routine-btn').style.display = 'none';
    });
    
    this.querySelector('#cancel-routine').addEventListener('click', () => {
      this.querySelector('#routine-form').style.display = 'none';
      this.querySelector('#add-routine-btn').style.display = 'flex';
    });
    
    this.querySelector('#save-routine').addEventListener('click', () => this._saveRoutine());
    
    this._loadRoutines();
  }

  async _saveRoutine() {
    const name = this.querySelector('#routine-name').value.trim();
    const icon = this.querySelector('#routine-icon').value.trim() || 'mdi:playlist-check';
    const tasksStr = this.querySelector('#routine-tasks').value.trim();
    
    if (!name) {
      alert('Please enter a routine name');
      return;
    }
    
    const taskIds = tasksStr ? tasksStr.split(',').map(t => t.trim()).filter(t => t) : [];
    
    try {
      await this._hass.callService('routinely', 'create_routine', {
        routine_name: name,
        icon: icon,
        task_ids: taskIds,
      });
      
      this.querySelector('#routine-form').style.display = 'none';
      this.querySelector('#add-routine-btn').style.display = 'flex';
      this.querySelector('#routine-name').value = '';
      this.querySelector('#routine-icon').value = '';
      this.querySelector('#routine-tasks').value = '';
      
      setTimeout(() => this._loadRoutines(), 500);
    } catch (err) {
      alert('Error creating routine: ' + err.message);
    }
  }

  async _loadRoutines() {
    const listEl = this.querySelector('#routine-list');
    if (!listEl) return;
    
    listEl.innerHTML = `
      <div class="empty-state">
        <p>Routines are stored internally.</p>
        <p style="font-size: 0.85em; margin-top: 8px;">
          Use the form above to create routines.<br>
          Routine IDs will appear in Home Assistant logs.
        </p>
      </div>
    `;
  }

  async _handleAction(action) {
    try {
      switch(action) {
        case 'pause':
          await this._hass.callService('routinely', 'pause', {});
          break;
        case 'resume':
          await this._hass.callService('routinely', 'resume', {});
          break;
        case 'skip':
          await this._hass.callService('routinely', 'skip', {});
          break;
        case 'complete':
          await this._hass.callService('routinely', 'complete_task', {});
          break;
        case 'cancel':
          if (confirm('Cancel the current routine?')) {
            await this._hass.callService('routinely', 'cancel', {});
          }
          break;
      }
    } catch (err) {
      console.error('Action failed:', err);
    }
  }

  getCardSize() {
    return 4;
  }
}

customElements.define('routinely-card', RoutinelyCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'routinely-card',
  name: 'Routinely Card',
  description: 'Manage and control your Routinely timers',
});
