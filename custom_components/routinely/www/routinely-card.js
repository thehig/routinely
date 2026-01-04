/**
 * ROUTINELY - Custom Lovelace Card
 * ADHD-friendly routine management for Home Assistant
 * 
 * Version: 1.6.1
 * 
 * Features:
 * - Drag-and-drop task reordering
 * - Pre-start review screen
 * - ADHD-friendly UI/UX
 */

console.log('%c ROUTINELY CARD v1.9.8 ', 'background: #FF6B6B; color: white; font-size: 14px; padding: 4px 8px; border-radius: 4px;');

// All code is bundled inline for HACS compatibility
let modulesLoaded = true;

// =============================================================================
// STYLES
// =============================================================================
const styles = `
    * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    .card { background: var(--ha-card-background, var(--card-background-color, white)); border-radius: 16px; padding: 20px; min-height: 400px; position: relative; }
    .task-icon-large { font-size: 3em; text-align: center; padding: 10px 0 0 0; }
    .task-name { font-size: 2em; font-weight: 700; text-align: center; padding: 10px 20px 20px 20px; color: var(--primary-text-color); }
    .timer { font-size: 5em; font-weight: 700; text-align: center; font-family: 'SF Mono', monospace; padding: 20px 0; color: var(--primary-text-color); }
    .timer.paused { color: #FFA726; animation: pulse 1.5s ease-in-out infinite; }
    .timer.overtime { color: #EF5350; }
    .time-adjust-row { display: flex; justify-content: center; gap: 8px; margin: 10px 0 20px 0; }
    .time-adjust-row .btn-small { padding: 8px 16px; font-size: 0.9em; min-width: 50px; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    .btn { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; border: none; border-radius: 16px; font-size: 1em; font-weight: 600; cursor: pointer; transition: transform 0.1s; min-width: 100px; flex: 1; }
    .btn:active { transform: scale(0.95); }
    .btn-icon { font-size: 2.5em; margin-bottom: 8px; }
    .btn-primary { background: #42A5F5; color: white; }
    .btn-success { background: #66BB6A; color: white; }
    .btn-warning { background: #FFA726; color: white; }
    .btn-danger { background: #EF5350; color: white; }
    .btn-secondary { background: var(--divider-color, #eee); color: var(--primary-text-color); }
    .btn-coral { background: linear-gradient(135deg, #FF6B6B, #FF8E8E); color: white; }
    .btn-small { padding: 8px 16px; min-width: auto; flex: 0; flex-direction: row; gap: 6px; font-size: 0.9em; }
    .btn-small .btn-icon { font-size: 1.2em; margin-bottom: 0; }
    .btn-large { padding: 30px; font-size: 1.2em; }
    .button-row { display: flex; gap: 12px; padding: 10px; justify-content: center; }
    .status-label { text-align: center; font-size: 1.2em; color: var(--secondary-text-color); margin-bottom: 20px; }
    .progress-container { padding: 10px 20px; }
    .progress-bar { height: 12px; background: var(--divider-color, #eee); border-radius: 6px; overflow: hidden; }
    .progress-fill { height: 100%; background: linear-gradient(90deg, #42A5F5, #66BB6A); transition: width 0.5s ease; border-radius: 6px; }
    .progress-text { text-align: center; margin-top: 8px; color: var(--secondary-text-color); font-size: 0.9em; }
    .welcome { text-align: center; padding: 40px 20px; }
    .welcome-icon { font-size: 4em; margin-bottom: 20px; }
    .welcome h2 { margin: 0 0 10px 0; font-weight: 600; color: var(--primary-text-color); }
    .welcome p { margin: 0; color: var(--secondary-text-color); }
    .nav { display: flex; justify-content: center; gap: 8px; padding: 10px; border-top: 1px solid var(--divider-color, #eee); margin-top: auto; }
    .nav-btn { display: flex; flex-direction: column; align-items: center; padding: 12px 20px; border: none; background: transparent; border-radius: 12px; cursor: pointer; color: var(--secondary-text-color); font-size: 0.8em; }
    .nav-btn.active { background: var(--primary-color); color: white; }
    .nav-btn-icon { font-size: 1.5em; margin-bottom: 4px; }
    .routine-list { padding: 10px; }
    .routine-item { display: flex; align-items: center; padding: 20px; margin: 10px 0; background: var(--divider-color, #f5f5f5); border-radius: 12px; cursor: pointer; transition: transform 0.1s, background 0.2s; }
    .routine-item:hover { background: var(--primary-color); color: white; }
    .routine-item:active { transform: scale(0.98); }
    .routine-icon { font-size: 2em; margin-right: 16px; }
    .routine-info { flex: 1; }
    .routine-name { font-size: 1.3em; font-weight: 600; }
    .routine-meta { font-size: 0.9em; opacity: 0.7; }
    .routine-arrow { font-size: 1.5em; opacity: 0.5; }
    .list-header { display: flex; justify-content: space-between; align-items: center; padding: 16px; }
    .list-header h3 { margin: 0; font-size: 1.3em; }
    .item-card { display: flex; align-items: center; padding: 16px; margin: 8px 16px; background: var(--divider-color, #f5f5f5); border-radius: 12px; }
    .item-icon { font-size: 1.5em; margin-right: 12px; width: 40px; text-align: center; }
    .item-info { flex: 1; cursor: pointer; }
    .item-info:hover { opacity: 0.8; }
    .item-name { font-weight: 600; font-size: 1.1em; }
    .item-meta { font-size: 0.85em; color: var(--secondary-text-color); }
    .item-actions { display: flex; gap: 4px; }
    .item-btn { padding: 8px; background: transparent; border: none; cursor: pointer; font-size: 1.1em; opacity: 0.5; border-radius: 8px; }
    .item-btn:hover { opacity: 1; background: var(--divider-color, #eee); }
    .item-btn.delete:hover { background: #EF5350; color: white; }
    .empty { text-align: center; padding: 40px; color: var(--secondary-text-color); }
    .empty-icon { font-size: 3em; margin-bottom: 16px; opacity: 0.5; }
    .form { padding: 20px; }
    .form-title { font-size: 1.5em; font-weight: 600; margin-bottom: 20px; text-align: center; }
    .form-group { margin-bottom: 20px; }
    .form-label { display: block; margin-bottom: 8px; font-weight: 500; color: var(--primary-text-color); }
    .form-input { width: 100%; padding: 16px; border: 2px solid var(--divider-color, #ddd); border-radius: 12px; font-size: 1.1em; background: var(--card-background-color, white); color: var(--primary-text-color); }
    .form-input:focus { outline: none; border-color: var(--primary-color, #42A5F5); }
    .form-select { width: 100%; padding: 16px; border: 2px solid var(--divider-color, #ddd); border-radius: 12px; font-size: 1.1em; background: var(--card-background-color, white); color: var(--primary-text-color); cursor: pointer; }
    .form-hint { font-size: 0.85em; color: var(--secondary-text-color); margin-top: 6px; }
    .form-actions { display: flex; gap: 12px; margin-top: 30px; }
    .duration-quick { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
    .duration-chip { padding: 10px 16px; border: 1px solid var(--divider-color, #ddd); border-radius: 20px; background: transparent; cursor: pointer; font-size: 0.9em; color: var(--primary-text-color); }
    .duration-chip:hover, .duration-chip.selected { background: var(--primary-color); color: white; border-color: var(--primary-color); }
    .emoji-quick { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
    .emoji-chip { padding: 10px 14px; border: 2px solid var(--divider-color, #ddd); border-radius: 10px; background: var(--card-background-color, white); cursor: pointer; font-size: 1.4em; transition: transform 0.1s; }
    .emoji-chip:hover { border-color: var(--primary-color, #42A5F5); transform: scale(1.1); }
    .emoji-chip.selected { border-color: var(--primary-color, #42A5F5); background: rgba(66, 165, 245, 0.2); }
    .task-selector { border: 2px solid var(--divider-color, #ddd); border-radius: 12px; max-height: 250px; overflow-y: auto; background: var(--card-background-color, white); }
    .task-selector-item { display: flex; align-items: center; padding: 14px 16px; cursor: pointer; border-bottom: 1px solid var(--divider-color, #eee); color: var(--primary-text-color); transition: background 0.15s; }
    .task-selector-item:last-child { border-bottom: none; }
    .task-selector-item:hover { background: rgba(66, 165, 245, 0.1); }
    .task-selector-item.selected { background: rgba(66, 165, 245, 0.2); }
    .task-selector-checkbox { width: 28px; height: 28px; margin-right: 12px; border: 2px solid var(--divider-color, #888); border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 0.9em; color: transparent; flex-shrink: 0; }
    .task-selector-item.selected .task-selector-checkbox { background: var(--primary-color, #42A5F5); border-color: var(--primary-color, #42A5F5); color: white; }
    .task-selector-label { flex: 1; display: flex; align-items: center; gap: 8px; }
    .selected-count { text-align: center; padding: 12px; color: var(--secondary-text-color); font-size: 0.95em; font-weight: 500; }
    .review-header { text-align: center; padding: 16px; border-bottom: 1px solid var(--divider-color, #eee); margin-bottom: 16px; }
    .review-header h2 { margin: 0 0 4px 0; font-size: 1.4em; display: flex; align-items: center; justify-content: center; gap: 10px; }
    .review-header .meta { color: var(--secondary-text-color); font-size: 0.95em; }
    .review-task-list { max-height: 350px; overflow-y: auto; padding: 0 8px; }
    .review-task { display: flex; align-items: center; padding: 14px 16px; margin: 8px 0; background: rgba(255, 107, 107, 0.08); border-radius: 12px; border-left: 4px solid #FF6B6B; cursor: pointer; transition: all 0.15s; }
    .review-task:hover { background: rgba(255, 107, 107, 0.15); }
    .review-task.skipped { opacity: 0.5; background: var(--divider-color, #f0f0f0); border-left-color: var(--divider-color, #ccc); text-decoration: line-through; }
    .review-task .task-checkbox { width: 28px; height: 28px; border: 2px solid #FF6B6B; border-radius: 50%; margin-right: 14px; display: flex; align-items: center; justify-content: center; font-size: 14px; color: transparent; flex-shrink: 0; transition: all 0.15s; }
    .review-task.skipped .task-checkbox { background: #66BB6A; border-color: #66BB6A; color: white; }
    .review-task .task-icon { font-size: 1.5em; margin-right: 12px; }
    .review-task .task-details { flex: 1; }
    .review-task .task-name { font-weight: 600; font-size: 1.05em; margin-bottom: 2px; }
    .review-task .task-time { font-size: 0.85em; color: var(--secondary-text-color); }
    .review-task .task-duration { font-size: 0.9em; color: var(--secondary-text-color); margin-left: auto; padding-left: 12px; }
    .review-task .task-mode-badge { font-size: 0.7em; padding: 2px 8px; border-radius: 10px; background: rgba(255, 107, 107, 0.2); color: #FF6B6B; margin-left: 8px; }
    .review-summary { padding: 16px; text-align: center; border-top: 1px solid var(--divider-color, #eee); margin-top: 16px; color: var(--secondary-text-color); }
    .review-summary strong { color: var(--primary-text-color); }
    .review-actions { display: flex; gap: 12px; padding: 16px; position: sticky; bottom: 0; background: var(--ha-card-background, var(--card-background-color, white)); }
    .tag-container { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
    .tag { display: inline-flex; align-items: center; padding: 6px 12px; background: rgba(255, 107, 107, 0.15); color: #FF6B6B; border-radius: 16px; font-size: 0.85em; font-weight: 500; cursor: pointer; transition: all 0.15s; }
    .tag:hover { background: rgba(255, 107, 107, 0.25); }
    .tag.selected { background: #FF6B6B; color: white; }
    .tag-input-row { display: flex; gap: 8px; margin-top: 10px; }
    .tag-input { flex: 1; padding: 10px 14px; border: 2px solid var(--divider-color, #ddd); border-radius: 10px; font-size: 0.95em; background: var(--card-background-color, white); color: var(--primary-text-color); }
    .tag-add-btn { padding: 10px 16px; background: #FF6B6B; color: white; border: none; border-radius: 10px; cursor: pointer; font-weight: 500; }
    .filter-bar { display: flex; gap: 8px; padding: 12px 16px; overflow-x: auto; border-bottom: 1px solid var(--divider-color, #eee); }
    .filter-btn { padding: 8px 14px; border-radius: 20px; border: 1px solid var(--divider-color, #ddd); background: transparent; cursor: pointer; font-size: 0.85em; white-space: nowrap; color: var(--primary-text-color); }
    .filter-btn.active { background: #FF6B6B; border-color: #FF6B6B; color: white; }
    .schedule-section { background: rgba(66, 165, 245, 0.08); border-radius: 12px; padding: 16px; margin-top: 10px; }
    .schedule-section-title { font-size: 0.9em; font-weight: 600; color: var(--secondary-text-color); margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
    .day-picker { display: flex; gap: 6px; justify-content: space-between; }
    .day-btn { width: 40px; height: 40px; border-radius: 50%; border: 2px solid var(--divider-color, #ddd); background: transparent; cursor: pointer; font-size: 0.8em; font-weight: 600; color: var(--primary-text-color); transition: all 0.15s; text-transform: uppercase; }
    .day-btn:hover { border-color: #42A5F5; }
    .day-btn.selected { background: #42A5F5; border-color: #42A5F5; color: white; }
    .time-input-row { display: flex; align-items: center; gap: 12px; margin-top: 12px; }
    .time-input { padding: 10px 14px; border: 2px solid var(--divider-color, #ddd); border-radius: 10px; font-size: 1em; background: var(--card-background-color, white); color: var(--primary-text-color); }
    .notification-settings { background: rgba(102, 187, 106, 0.08); border-radius: 12px; padding: 16px; margin-top: 10px; }
    .notification-toggle { display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--divider-color, #eee); }
    .notification-toggle:last-child { border-bottom: none; }
    .notification-toggle-label { font-size: 0.95em; color: var(--primary-text-color); }
    .notification-toggle-hint { font-size: 0.8em; color: var(--secondary-text-color); margin-top: 2px; }
    .toggle-switch { position: relative; width: 52px; height: 28px; background: var(--divider-color, #ccc); border-radius: 14px; cursor: pointer; transition: background 0.2s; flex-shrink: 0; }
    .toggle-switch.on { background: #66BB6A; }
    .toggle-switch::after { content: ''; position: absolute; width: 22px; height: 22px; background: white; border-radius: 50%; top: 3px; left: 3px; transition: transform 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
    .toggle-switch.on::after { transform: translateX(24px); }
    .notification-time-input { padding: 8px 12px; border: 2px solid var(--divider-color, #ddd); border-radius: 8px; font-size: 0.9em; width: 120px; background: var(--card-background-color, white); color: var(--primary-text-color); }
    .collapsible-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; cursor: pointer; user-select: none; }
    .collapsible-header:hover { opacity: 0.8; }
    .collapsible-icon { font-size: 1.2em; transition: transform 0.2s; }
    .collapsible-icon.open { transform: rotate(90deg); }
    .collapsible-content { max-height: 0; overflow: hidden; transition: max-height 0.3s ease-out; }
    .collapsible-content.open { max-height: 600px; }
    .fab { position: absolute; bottom: 80px; right: 20px; width: 56px; height: 56px; border-radius: 50%; background: #FFD54F; border: none; box-shadow: 0 4px 12px rgba(0,0,0,0.2); cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 1.8em; transition: transform 0.1s; z-index: 10; }
    .fab:hover { transform: scale(1.1); }
    .fab:active { transform: scale(0.95); }
    .reorder-btns { display: flex; flex-direction: column; gap: 2px; margin-right: 10px; }
    .reorder-btn { width: 28px; height: 22px; border: 1px solid var(--divider-color, #ddd); background: var(--card-background-color, white); border-radius: 4px; cursor: pointer; font-size: 0.7em; color: var(--primary-text-color); display: flex; align-items: center; justify-content: center; }
    .reorder-btn:hover:not(.disabled) { background: var(--primary-color, #42A5F5); color: white; border-color: var(--primary-color, #42A5F5); }
    .reorder-btn.disabled { opacity: 0.3; cursor: not-allowed; }
    .reorder-btns-small { display: flex; flex-direction: column; gap: 1px; margin-right: 8px; }
    .reorder-btns-small-placeholder { width: 24px; margin-right: 8px; }
    .reorder-btn-small { width: 22px; height: 18px; border: 1px solid var(--divider-color, #ddd); background: var(--card-background-color, white); border-radius: 3px; cursor: pointer; font-size: 0.6em; color: var(--primary-text-color); display: flex; align-items: center; justify-content: center; padding: 0; }
    .reorder-btn-small:hover:not(.disabled) { background: var(--primary-color, #42A5F5); color: white; border-color: var(--primary-color, #42A5F5); }
    .reorder-btn-small.disabled { opacity: 0.3; cursor: not-allowed; }
`;

// =============================================================================
// UTILITIES
// =============================================================================
const utils = {
  formatTime: (seconds, showSign = false) => {
    if (seconds === null || seconds === undefined) return '--:--';
    const isNegative = seconds < 0;
    const absSeconds = Math.abs(seconds);
    const hrs = Math.floor(absSeconds / 3600);
    const mins = Math.floor((absSeconds % 3600) / 60);
    const secs = absSeconds % 60;
    const prefix = isNegative ? '+' : (showSign ? '-' : '');
    if (hrs > 0) return `${prefix}${hrs}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    return `${prefix}${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  },
  formatDuration: (seconds) => {
    if (!seconds || seconds <= 0) return '0m';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins === 0) return `${secs}s`;
    if (secs === 0) return `${mins}m`;
    return `${mins}m ${secs}s`;
  },
  formatAdvancementMode: (mode) => {
    const modes = { 'manual': 'Manual', 'auto': 'Auto', 'confirm': 'Confirm' };
    return modes[mode] || mode;
  },
  getModeStyle: (mode) => {
    const styles = {
      'manual': 'background: rgba(255, 152, 0, 0.2); color: #FF9800;',
      'auto': 'background: rgba(66, 165, 245, 0.2); color: #42A5F5;',
      'confirm': 'background: rgba(171, 71, 188, 0.2); color: #AB47BC;'
    };
    return styles[mode] || '';
  },
  parseMinutesToArray: (str) => {
    if (!str || typeof str !== 'string') return [];
    return str.split(',').map(s => parseInt(s.trim(), 10)).filter(n => !isNaN(n) && n > 0);
  },
  taskEmojis: ['📋', '✅', '⏰', '🔔', '📝', '🎯', '💪', '🧘', '🚿', '🦷', '💊', '🍳', '☕', '📚', '💻', '🏃'],
  routineEmojis: ['🌅', '🌙', '☀️', '🏠', '💼', '🧹', '🛏️', '🍽️', '💪', '🧘', '📚', '🎮', '🚗', '✈️', '🎉', '❤️']
};

// =============================================================================
// ROUTINELY CARD CLASS
// =============================================================================

class RoutinelyCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = null;
    this._config = {};
    
    // UI State
    this._mode = 'home'; // home, tasks, routines, create-task, create-routine, edit-task, edit-routine, review
    this._lastRenderState = null;
    this._selectedTag = null;
    this._notificationSettingsOpen = false;
    
    // Form state preservation
    this._formState = {};
    this._selectedTasks = new Set();
    this._editingId = null;
    
    // Review state
    this._reviewRoutine = null;
    this._reviewTasks = [];
    this._skippedTaskIds = new Set();
    this._reviewTaskOrder = []; // Track reordered task IDs
    
    // Routine form task order
    this._routineTaskOrder = [];
    
    // Initialize
    this._init();
  }

  _init() {
    this._render();
  }

  setConfig(config) {
    this._config = config;
  }

  set hass(hass) {
    const oldHass = this._hass;
    this._hass = hass;
    
    // Determine if we should re-render
    const currentState = this._getRenderState();
    const shouldRender = !this._lastRenderState || 
                         JSON.stringify(currentState) !== JSON.stringify(this._lastRenderState);
    
    // Don't re-render during form input (except for active routine changes)
    const inForm = ['create-task', 'edit-task', 'create-routine', 'edit-routine'].includes(this._mode);
    
    if (shouldRender && (!inForm || currentState.isActive !== this._lastRenderState?.isActive)) {
      this._lastRenderState = currentState;
      this._render();
    }
  }

  _getRenderState() {
    if (!this._hass) return null;
    
    const statusEntity = this._hass.states['sensor.routinely_status'];
    const currentTaskEntity = this._hass.states['sensor.routinely_current_task'];
    const timeEntity = this._hass.states['sensor.routinely_time_remaining'];
    const progressEntity = this._hass.states['sensor.routinely_progress'];
    const tasksEntity = this._hass.states['sensor.routinely_tasks'];
    const routinesEntity = this._hass.states['sensor.routinely_routines'];
    
    return {
      status: statusEntity?.state,
      isActive: statusEntity?.state !== 'idle',
      currentTask: currentTaskEntity?.state,
      timeRemaining: timeEntity?.attributes?.seconds,
      progress: progressEntity?.state,
      taskCount: tasksEntity?.state,
      routineCount: routinesEntity?.state,
      mode: this._mode
    };
  }

  _render() {
    if (!this._hass || !modulesLoaded) return;
    
    const statusEntity = this._hass.states['sensor.routinely_status'];
    const currentTaskEntity = this._hass.states['sensor.routinely_current_task'];
    const timeEntity = this._hass.states['sensor.routinely_time_remaining'];
    const progressEntity = this._hass.states['sensor.routinely_progress'];
    const activeEntity = this._hass.states['binary_sensor.routinely_active'];
    const pausedEntity = this._hass.states['binary_sensor.routinely_paused'];
    const awaitingEntity = this._hass.states['binary_sensor.routinely_awaiting_input'];
    const tasksEntity = this._hass.states['sensor.routinely_tasks'];
    const routinesEntity = this._hass.states['sensor.routinely_routines'];
    
    const isActive = activeEntity?.state === 'on';
    const isPaused = pausedEntity?.state === 'on';
    const awaitingInput = awaitingEntity?.state === 'on';
    
    let content = '';
    
    if (isActive) {
      // Active routine view
      const taskName = currentTaskEntity?.state || 'Unknown Task';
      const taskIcon = currentTaskEntity?.attributes?.icon || '📋';
      const timeRemaining = parseInt(timeEntity?.attributes?.seconds) || 0;
      const progressPercent = parseInt(progressEntity?.state) || 0;
      const currentTaskIndex = currentTaskEntity?.attributes?.task_index || 0;
      const totalTasks = progressEntity?.attributes?.total_tasks || 1;
      const advancementMode = currentTaskEntity?.attributes?.advancement_mode || 'manual';
      const taskDuration = currentTaskEntity?.attributes?.duration || 0;
      const taskElapsed = currentTaskEntity?.attributes?.task_elapsed_time || 0;
      
      content = this._renderActiveRoutine({
        taskName,
        taskIcon,
        timeRemaining,
        isPaused,
        progressPercent,
        currentTaskIndex,
        totalTasks,
        advancementMode,
        taskDuration,
        taskElapsed
      });
    } else {
      // Inactive views based on mode
      switch (this._mode) {
        case 'tasks':
          content = this._renderTaskList();
          break;
        case 'routines':
          content = this._renderRoutineList();
          break;
        case 'create-task':
        case 'edit-task':
          content = this._renderTaskForm();
          break;
        case 'create-routine':
        case 'edit-routine':
          content = this._renderRoutineForm();
          break;
        case 'review':
          content = this._renderReviewScreen();
          break;
        default:
          content = this._renderRoutineSelect();
      }
    }
    
    this.shadowRoot.innerHTML = `
      <style>${styles}</style>
      ${content}
    `;
    
    this._attachEventListeners();
  }

  // ==========================================================================
  // VIEW RENDERERS
  // ==========================================================================

  _renderActiveRoutine(state) {
    const { taskName, taskIcon, timeRemaining, isPaused, progressPercent, currentTaskIndex, totalTasks, advancementMode, taskDuration, taskElapsed } = state;
    
    const isOvertime = timeRemaining < 0;
    const isManualMode = advancementMode === 'manual' || advancementMode === 'confirm';
    
    let actionButtons = '';
    
    if (isPaused) {
      actionButtons = `
        <div class="button-row">
          <button class="btn btn-primary btn-large" data-action="resume">
            <span class="btn-icon">▶️</span>Resume
          </button>
          <button class="btn btn-danger" data-action="stop">
            <span class="btn-icon">⏹️</span>Stop
          </button>
        </div>
      `;
    } else {
      // Always show Pause + Skip (Done and Skip are synonymous)
      actionButtons = `
        <div class="button-row">
          <button class="btn btn-warning btn-large" data-action="pause">
            <span class="btn-icon">⏸️</span>Pause
          </button>
          <button class="btn btn-secondary" data-action="skip">
            <span class="btn-icon">⏭️</span>Skip
          </button>
        </div>
      `;
    }
    
    // Time adjustment buttons (only when not paused)
    const canSubtract5 = timeRemaining > 300;
    const canSubtract1 = timeRemaining > 60;
    const canAdd = !isOvertime;
    
    const timeAdjustButtons = !isPaused ? `
      <div class="time-adjust-row">
        <button class="btn btn-small ${canSubtract5 ? '' : 'disabled'}" data-action="adjust-time" data-seconds="-300" ${canSubtract5 ? '' : 'disabled'}>-5m</button>
        <button class="btn btn-small ${canSubtract1 ? '' : 'disabled'}" data-action="adjust-time" data-seconds="-60" ${canSubtract1 ? '' : 'disabled'}>-1m</button>
        <button class="btn btn-small ${canAdd ? '' : 'disabled'}" data-action="adjust-time" data-seconds="60" ${canAdd ? '' : 'disabled'}>+1m</button>
        <button class="btn btn-small ${canAdd ? '' : 'disabled'}" data-action="adjust-time" data-seconds="300" ${canAdd ? '' : 'disabled'}>+5m</button>
      </div>
    ` : '';
    
    const timerClass = isPaused ? 'timer paused' : (isOvertime ? 'timer overtime' : 'timer');
    const statusText = isPaused ? '⏸️ PAUSED' : (isOvertime ? '⏰ OVERTIME' : '▶️ ACTIVE');
    
    const clampedProgress = Math.min(100, Math.max(0, progressPercent));
    
    return `
      <div class="card">
        <div class="status-label">${statusText}</div>
        <div class="task-icon-large">${taskIcon}</div>
        <div class="task-name">${taskName || 'No Task'}</div>
        <div class="${timerClass}">${utils.formatTime(timeRemaining)}</div>
        ${timeAdjustButtons}
        <div class="progress-container">
          <div class="progress-bar">
            <div class="progress-fill" style="width: ${clampedProgress}%"></div>
          </div>
          <div class="progress-text">Task ${currentTaskIndex + 1} of ${totalTasks} (${clampedProgress}%)</div>
        </div>
        ${actionButtons}
      </div>
    `;
  }

  _renderRoutineSelect() {
    const routinesEntity = this._hass.states['sensor.routinely_routines'];
    const routines = routinesEntity?.attributes?.routines || [];
    const allTags = routinesEntity?.attributes?.all_tags || [];
    
    if (!routines || routines.length === 0) {
      return `
        <div class="card">
          <div class="welcome">
            <div class="welcome-icon">🎯</div>
            <h2>Welcome to Routinely!</h2>
            <p>Create your first routine to get started</p>
          </div>
          ${this._renderNav('home')}
        </div>
      `;
    }
    
    let filteredRoutines = routines;
    if (this._selectedTag) {
      filteredRoutines = routines.filter(r => r.tags && r.tags.includes(this._selectedTag));
    }
    
    let filterBar = '';
    if (allTags && allTags.length > 0) {
      filterBar = `
        <div class="filter-bar">
          <button class="filter-btn ${!this._selectedTag ? 'active' : ''}" data-action="filter-tag" data-tag="">All</button>
          ${allTags.map(tag => `
            <button class="filter-btn ${this._selectedTag === tag ? 'active' : ''}" data-action="filter-tag" data-tag="${tag}">${tag}</button>
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
                  ${routine.task_count || 0} tasks • ${utils.formatDuration(routine.duration || 0)}
                  ${routine.tags && routine.tags.length > 0 ? ` • ${routine.tags.join(', ')}` : ''}
                </div>
              </div>
              <span class="routine-arrow">›</span>
            </div>
          `).join('')}
        </div>
        ${this._renderNav('home')}
      </div>
    `;
  }
  
  _renderNav(active) {
    return `
      <div class="nav">
        <button class="nav-btn ${active === 'home' ? 'active' : ''}" data-action="nav-home">
          <span class="nav-btn-icon">▶️</span>Start
        </button>
        <button class="nav-btn ${active === 'tasks' ? 'active' : ''}" data-action="nav-tasks">
          <span class="nav-btn-icon">📋</span>Tasks
        </button>
        <button class="nav-btn ${active === 'routines' ? 'active' : ''}" data-action="nav-routines">
          <span class="nav-btn-icon">🔄</span>Routines
        </button>
        <button class="nav-btn" data-action="test-notification" title="Send test notification">
          <span class="nav-btn-icon">🔔</span>Test
        </button>
      </div>
    `;
  }

  _renderReviewScreen() {
    if (!this._reviewRoutine || !this._reviewTasks) {
      this._mode = 'home';
      return this._renderRoutineSelect();
    }
    
    const routine = this._reviewRoutine;
    const tasks = this._reviewTasks;
    const skippedIds = this._skippedTaskIds;
    
    // Calculate times
    const now = new Date();
    const startTime = { hour: now.getHours(), min: now.getMinutes() };
    
    const includedTasks = tasks.filter(t => !skippedIds.has(t.id));
    const totalDuration = includedTasks.reduce((sum, t) => sum + (t.duration || 0), 0);
    
    let runningTime = 0;
    const taskItems = tasks.map((task, index) => {
      const isSkipped = skippedIds.has(task.id);
      const startOffset = runningTime;
      const endOffset = runningTime + (task.duration || 0);
      
      if (!isSkipped) {
        runningTime += (task.duration || 0);
      }
      
      const startTimeStr = this._calcDisplayTime(startTime, startOffset);
      const endTimeStr = this._calcDisplayTime(startTime, endOffset);
      const isFirst = index === 0;
      const isLast = index === tasks.length - 1;
      
      return `
        <div class="review-task ${isSkipped ? 'skipped' : ''}">
          <div class="reorder-btns">
            <button class="reorder-btn ${isFirst ? 'disabled' : ''}" data-action="move-up" data-task-id="${task.id}" ${isFirst ? 'disabled' : ''}>▲</button>
            <button class="reorder-btn ${isLast ? 'disabled' : ''}" data-action="move-down" data-task-id="${task.id}" ${isLast ? 'disabled' : ''}>▼</button>
          </div>
          <div class="task-checkbox" data-action="toggle-skip" data-task-id="${task.id}">${isSkipped ? '✓' : ''}</div>
          <span class="task-icon">${task.icon || '📋'}</span>
          <div class="task-details" data-action="toggle-skip" data-task-id="${task.id}">
            <div class="task-name">${task.name}</div>
            <div class="task-time">${startTimeStr} - ${endTimeStr}</div>
          </div>
          <div class="task-duration">${utils.formatDuration(task.duration)}</div>
          <span class="task-mode-badge" style="${utils.getModeStyle(task.advancement_mode || task.mode)}">${utils.formatAdvancementMode(task.advancement_mode || task.mode)}</span>
        </div>
      `;
    });
    
    const endTimeStr = this._calcDisplayTime(startTime, totalDuration);
    const startTimeStr = this._calcDisplayTime(startTime, 0);
    
    return `
      <div class="card">
        <div class="review-header">
          <h2><span>${routine.icon || '📋'}</span> ${routine.name}</h2>
          <div class="meta">${startTimeStr} → ${endTimeStr} (${utils.formatDuration(totalDuration)})</div>
        </div>
        <div class="review-task-list" id="review-task-list">
          ${taskItems.join('')}
        </div>
        <div class="review-summary">
          <strong>${includedTasks.length}</strong> of ${tasks.length} tasks • Total: <strong>${utils.formatDuration(totalDuration)}</strong>
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

  _calcDisplayTime(startTime, offsetSeconds) {
    const totalMins = startTime.hour * 60 + startTime.min + Math.floor(offsetSeconds / 60);
    const h = Math.floor(totalMins / 60) % 24;
    const m = totalMins % 60;
    const ampm = h >= 12 ? 'PM' : 'AM';
    const h12 = h % 12 || 12;
    return `${h12}:${String(m).padStart(2, '0')} ${ampm}`;
  }

  _renderTaskList() {
    const tasksEntity = this._hass.states['sensor.routinely_tasks'];
    const tasks = tasksEntity?.attributes?.tasks || [];
    
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
              <div class="item-meta">${utils.formatDuration(task.duration)} • ${utils.formatAdvancementMode(task.advancement_mode || task.mode)}</div>
            </div>
            <div class="item-actions">
              <button class="item-btn" data-action="copy-task" data-task-id="${task.id}" title="Copy">📋</button>
              <button class="item-btn" data-action="edit-task" data-task-id="${task.id}" title="Edit">✏️</button>
              <button class="item-btn delete" data-action="delete-task" data-task-id="${task.id}" title="Delete">🗑️</button>
            </div>
          </div>
        `).join('')}
        ${this._renderNav('tasks')}
      </div>
    `;
  }

  _renderRoutineList() {
    const routinesEntity = this._hass.states['sensor.routinely_routines'];
    const routines = routinesEntity?.attributes?.routines || [];
    
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
                ${routine.task_count || 0} tasks • ${utils.formatDuration(routine.duration || 0)}
                ${routine.tags && routine.tags.length > 0 ? ` • ${routine.tags.join(', ')}` : ''}
              </div>
            </div>
            <div class="item-actions">
              <button class="item-btn" data-action="edit-routine" data-routine-id="${routine.id}" title="Edit">✏️</button>
              <button class="item-btn delete" data-action="delete-routine" data-routine-id="${routine.id}" title="Delete">🗑️</button>
            </div>
          </div>
        `).join('')}
        ${this._renderNav('routines')}
      </div>
    `;
  }

  _renderTaskForm() {
    const isEdit = this._mode === 'edit-task';
    const title = isEdit ? 'Edit Task' : 'New Task';
    const saveAction = isEdit ? 'save-edit-task' : 'save-task';
    
    return `
      <div class="card">
        <div class="form">
          <div class="form-title">${title}</div>
          
          <div class="form-group">
            <label class="form-label">Name</label>
            <input type="text" class="form-input" id="task-name" 
                   value="${this._formState.name || ''}" 
                   placeholder="e.g., Brush Teeth">
          </div>
          
          <div class="form-group">
            <label class="form-label">Icon</label>
            <input type="text" class="form-input" id="task-icon" 
                   value="${this._formState.icon || ''}" 
                   placeholder="Paste an emoji (e.g. 🦷)">
          </div>
          
          <div class="form-group">
            <label class="form-label">Duration (minutes)</label>
            <input type="number" class="form-input" id="task-duration" 
                   value="${this._formState.duration || 5}" min="1" max="120">
            <div class="duration-quick">
              ${[1, 2, 5, 10, 15, 30].map(d => `
                <button class="duration-chip ${this._formState.duration === d ? 'selected' : ''}" 
                        data-action="select-duration" data-duration="${d}">${d}m</button>
              `).join('')}
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">Advancement Mode</label>
            <select class="form-select" id="task-mode">
              <option value="manual" ${this._formState.mode === 'manual' ? 'selected' : ''}>Manual - Tap to complete</option>
              <option value="auto" ${this._formState.mode === 'auto' ? 'selected' : ''}>Auto - Auto advance when timer ends</option>
              <option value="confirm" ${this._formState.mode === 'confirm' ? 'selected' : ''}>Confirm - Ask before advancing</option>
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

  _renderRoutineForm() {
    const isEdit = this._mode === 'edit-routine';
    const title = isEdit ? 'Edit Routine' : 'New Routine';
    const saveAction = isEdit ? 'save-edit-routine' : 'save-routine';
    
    const tasksEntity = this._hass.states['sensor.routinely_tasks'];
    let tasks = tasksEntity?.attributes?.tasks || [];
    
    // Apply custom order if we have one
    if (this._routineTaskOrder.length > 0) {
      const taskMap = new Map(tasks.map(t => [t.id, t]));
      const orderedTasks = this._routineTaskOrder.map(id => taskMap.get(id)).filter(t => t);
      // Add any tasks not in the order at the end
      const orderedIds = new Set(this._routineTaskOrder);
      const remainingTasks = tasks.filter(t => !orderedIds.has(t.id));
      tasks = [...orderedTasks, ...remainingTasks];
    }
    
    const selectedDuration = tasks
      .filter(t => this._formState.selectedTasks?.has(t.id))
      .reduce((sum, t) => sum + (t.duration || 0), 0);
    
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
                   value="${this._formState.name || ''}" 
                   placeholder="e.g., Morning Routine">
          </div>
          
          <div class="form-group">
            <label class="form-label">Icon</label>
            <input type="text" class="form-input" id="routine-icon" 
                   value="${this._formState.icon || ''}" 
                   placeholder="Paste an emoji (e.g. 🌅)">
          </div>
          
          <div class="form-group">
            <label class="form-label">Tags</label>
            <div class="tag-input-row">
              <input type="text" class="tag-input" id="tag-input" placeholder="Add a tag...">
              <button class="tag-add-btn" data-action="add-tag">Add</button>
            </div>
            ${this._formState.tags?.length > 0 ? `
              <div class="tag-container">
                ${this._formState.tags.map(tag => `
                  <span class="tag" data-action="remove-tag" data-tag="${tag}">${tag} ×</span>
                `).join('')}
              </div>
            ` : ''}
          </div>
          
          <div class="form-group">
            <label class="form-label">Tasks</label>
            <div class="task-selector" id="task-selector">
              ${tasks.map((task) => {
                const isSelected = this._formState.selectedTasks?.has(task.id);
                const orderIdx = this._routineTaskOrder.indexOf(task.id);
                const isFirst = orderIdx === 0;
                const isLast = orderIdx === this._routineTaskOrder.length - 1;
                return `
                  <div class="task-selector-item ${isSelected ? 'selected' : ''}">
                    ${isSelected ? `
                      <div class="reorder-btns-small">
                        <button class="reorder-btn-small ${isFirst ? 'disabled' : ''}" data-action="move-up" data-task-id="${task.id}" ${isFirst ? 'disabled' : ''}>▲</button>
                        <button class="reorder-btn-small ${isLast ? 'disabled' : ''}" data-action="move-down" data-task-id="${task.id}" ${isLast ? 'disabled' : ''}>▼</button>
                      </div>
                    ` : '<div class="reorder-btns-small-placeholder"></div>'}
                    <div class="task-selector-checkbox" data-action="toggle-task" data-task-id="${task.id}">${isSelected ? '✓' : ''}</div>
                    <div class="task-selector-label" data-action="toggle-task" data-task-id="${task.id}">
                      <span class="task-icon">${task.icon || '📋'}</span>
                      <span class="task-name">${task.name}</span>
                      <span class="task-duration">(${utils.formatDuration(task.duration)})</span>
                    </div>
                  </div>
                `;
              }).join('')}
            </div>
            ${tasks.length > 0 ? `
              <div class="selected-count">
                ${this._formState.selectedTasks?.size || 0} tasks selected • ${utils.formatDuration(selectedDuration)}
              </div>
            ` : ''}
          </div>
          
          <div class="form-group">
            <label class="form-label">Schedule (optional)</label>
            <div class="schedule-section">
              <div class="schedule-section-title">Days</div>
              <div class="day-picker">
                ${days.map(d => `
                  <button class="day-btn ${this._formState.scheduleDays?.includes(d.key) ? 'selected' : ''}" 
                          data-action="toggle-day" data-day="${d.key}">${d.label}</button>
                `).join('')}
              </div>
              <div class="time-input-row">
                <span>Time:</span>
                <input type="time" class="time-input" id="schedule-time" 
                       value="${this._formState.scheduleTime || ''}">
              </div>
              <div class="form-hint">Use Home Assistant automations for scheduled triggers</div>
            </div>
          </div>
          
          <div class="form-group">
            <div class="collapsible-header" data-action="toggle-notification-settings">
              <label class="form-label" style="margin-bottom: 0; cursor: pointer;">🔔 Notification Settings</label>
              <span class="collapsible-icon ${this._notificationSettingsOpen ? 'open' : ''}">›</span>
            </div>
            <div class="collapsible-content ${this._notificationSettingsOpen ? 'open' : ''}">
              <div class="notification-settings">
                <div class="notification-toggle">
                  <div>
                    <div class="notification-toggle-label">Custom notifications</div>
                    <div class="notification-toggle-hint">Override global defaults for this routine</div>
                  </div>
                  <div class="toggle-switch ${this._formState.useCustomNotifications ? 'on' : ''}" 
                       data-action="toggle-custom-notifications"></div>
                </div>
                
                ${this._formState.useCustomNotifications ? `
                  <div class="notification-toggle">
                    <div>
                      <div class="notification-toggle-label">Before task starts (mins)</div>
                      <div class="notification-toggle-hint">e.g., 10,5,1</div>
                    </div>
                    <input type="text" class="notification-time-input" id="notify-before" 
                           value="${this._formState.notifyBefore || ''}" placeholder="10,5,1">
                  </div>
                  
                  <div class="notification-toggle">
                    <div>
                      <div class="notification-toggle-label">On task start</div>
                    </div>
                    <div class="toggle-switch ${this._formState.notifyOnStart ? 'on' : ''}" 
                         data-action="toggle-notify-start"></div>
                  </div>
                  
                  <div class="notification-toggle">
                    <div>
                      <div class="notification-toggle-label">Time remaining (mins)</div>
                      <div class="notification-toggle-hint">e.g., 5,1</div>
                    </div>
                    <input type="text" class="notification-time-input" id="notify-remaining" 
                           value="${this._formState.notifyRemaining || ''}" placeholder="5,1">
                  </div>
                  
                  <div class="notification-toggle">
                    <div>
                      <div class="notification-toggle-label">Overdue alerts (mins)</div>
                      <div class="notification-toggle-hint">e.g., 1,5,10</div>
                    </div>
                    <input type="text" class="notification-time-input" id="notify-overdue" 
                           value="${this._formState.notifyOverdue || ''}" placeholder="1,5,10">
                  </div>
                  
                  <div class="notification-toggle">
                    <div>
                      <div class="notification-toggle-label">On task complete</div>
                    </div>
                    <div class="toggle-switch ${this._formState.notifyOnComplete ? 'on' : ''}" 
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
        
        <button class="fab" data-action="create-task" title="New Task">+</button>
      </div>
    `;
  }

  // ==========================================================================
  // EVENT HANDLING
  // ==========================================================================

  _attachEventListeners() {
    this.shadowRoot.querySelectorAll('[data-action]').forEach(el => {
      el.addEventListener('click', (e) => this._handleAction(e));
    });
    
    // Form input listeners
    this._attachFormInputListeners();
  }

  _attachFormInputListeners() {
    const inputs = ['task-name', 'task-icon', 'task-duration', 'task-mode', 
                    'routine-name', 'routine-icon', 'schedule-time', 'tag-input',
                    'notify-before', 'notify-remaining', 'notify-overdue'];
    
    inputs.forEach(id => {
      const el = this.shadowRoot.getElementById(id);
      if (el) {
        el.addEventListener('input', (e) => this._handleInputChange(e, id));
        el.addEventListener('change', (e) => this._handleInputChange(e, id));
      }
    });
  }

  _handleInputChange(e, id) {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    
    switch(id) {
      case 'task-name': this._formState.name = value; break;
      case 'task-icon': this._formState.icon = value; break;
      case 'task-duration': this._formState.duration = parseInt(value) || 5; break;
      case 'task-mode': this._formState.mode = value; break;
      case 'routine-name': this._formState.name = value; break;
      case 'routine-icon': this._formState.icon = value; break;
      case 'schedule-time': this._formState.scheduleTime = value; break;
      case 'notify-before': this._formState.notifyBefore = value; break;
      case 'notify-remaining': this._formState.notifyRemaining = value; break;
      case 'notify-overdue': this._formState.notifyOverdue = value; break;
    }
  }

  async _handleAction(e) {
    const action = e.target.closest('[data-action]')?.dataset.action;
    if (!action) return;
    
    const target = e.target.closest('[data-action]');
    
    switch(action) {
      // Navigation
      case 'nav-home':
        this._mode = 'home';
        this._clearFormState();
        this._render();
        break;
      
      case 'nav-tasks':
        this._mode = 'tasks';
        this._clearFormState();
        this._render();
        break;
      
      case 'nav-routines':
        this._mode = 'routines';
        this._clearFormState();
        this._render();
        break;
      
      case 'test-notification':
        await this._callService('test_notification', { message: 'Test notification from Routinely card' });
        // Show brief visual feedback
        const testBtn = this.shadowRoot.querySelector('[data-action="test-notification"]');
        if (testBtn) {
          testBtn.style.background = 'var(--success-color, #66BB6A)';
          testBtn.style.color = 'white';
          setTimeout(() => {
            testBtn.style.background = '';
            testBtn.style.color = '';
          }, 1000);
        }
        break;
      
      // Routine actions
      case 'start-routine':
        await this._startReview(target.dataset.routineId);
        break;
      
      case 'cancel-review':
        this._mode = 'home';
        this._reviewRoutine = null;
        this._reviewTasks = [];
        this._skippedTaskIds = new Set();
        this._reviewTaskOrder = [];
        this._render();
        break;
      
      case 'toggle-skip':
        const skipTaskId = target.dataset.taskId;
        if (this._skippedTaskIds.has(skipTaskId)) {
          this._skippedTaskIds.delete(skipTaskId);
        } else {
          this._skippedTaskIds.add(skipTaskId);
        }
        // Save scroll position before render
        const reviewList = this.shadowRoot.getElementById('review-task-list');
        const reviewScrollTop = reviewList ? reviewList.scrollTop : 0;
        this._render();
        // Restore scroll position after render
        const newReviewList = this.shadowRoot.getElementById('review-task-list');
        if (newReviewList) newReviewList.scrollTop = reviewScrollTop;
        break;
      
      case 'confirm-start':
        await this._confirmStartRoutine();
        break;
      
      // Active routine controls
      case 'complete':
        await this._callService('complete_task');
        break;
      case 'skip':
        await this._callService('skip');
        break;
      case 'pause':
        await this._callService('pause');
        break;
      case 'resume':
        await this._callService('resume');
        break;
      case 'stop':
        await this._callService('cancel');
        break;
      case 'adjust-time':
        const adjustSeconds = parseInt(target.dataset.seconds) || 0;
        await this._callService('adjust_time', { seconds: adjustSeconds });
        break;
      
      // Task CRUD
      case 'create-task':
        this._mode = 'create-task';
        this._clearFormState();
        this._formState = { name: '', icon: '', duration: 5, mode: 'manual' };
        this._render();
        break;
      
      case 'edit-task':
        await this._startEditTask(target.dataset.taskId);
        break;
      
      case 'copy-task':
        await this._copyTask(target.dataset.taskId);
        break;
      
      case 'save-task':
        await this._saveTask();
        break;
      
      case 'save-edit-task':
        await this._saveEditTask();
        break;
      
      case 'delete-task':
        await this._deleteTask(target.dataset.taskId);
        break;
      
      // Routine CRUD
      case 'create-routine':
        this._mode = 'create-routine';
        this._clearFormState();
        this._formState = { name: '', icon: '', selectedTasks: new Set(), tags: [], scheduleDays: [] };
        this._routineTaskOrder = [];
        this._render();
        break;
      
      case 'edit-routine':
        await this._startEditRoutine(target.dataset.routineId);
        break;
      
      case 'save-routine':
        await this._saveRoutine();
        break;
      
      case 'save-edit-routine':
        await this._saveEditRoutine();
        break;
      
      case 'delete-routine':
        await this._deleteRoutine(target.dataset.routineId);
        break;
      
      // Form helpers
      case 'cancel-form':
        this._mode = this._mode.includes('task') ? 'tasks' : 'routines';
        this._clearFormState();
        this._routineTaskOrder = [];
        this._render();
        break;
      
      case 'select-duration':
        const durationInput = this.shadowRoot.getElementById('task-duration');
        if (durationInput) {
          durationInput.value = target.dataset.duration;
          this._formState.duration = parseInt(target.dataset.duration);
          this._render();
        }
        break;
      
      case 'toggle-task':
        const taskId = target.dataset.taskId;
        if (!this._formState.selectedTasks) {
          this._formState.selectedTasks = new Set();
        }
        if (this._formState.selectedTasks.has(taskId)) {
          this._formState.selectedTasks.delete(taskId);
          // Remove from order list when unchecked
          const orderIdx = this._routineTaskOrder.indexOf(taskId);
          if (orderIdx !== -1) this._routineTaskOrder.splice(orderIdx, 1);
        } else {
          this._formState.selectedTasks.add(taskId);
          // Add to order list when checked (if not already present)
          if (!this._routineTaskOrder.includes(taskId)) {
            this._routineTaskOrder.push(taskId);
          }
        }
        // Save scroll position before render
        const taskSelector = this.shadowRoot.getElementById('task-selector');
        const scrollTop = taskSelector ? taskSelector.scrollTop : 0;
        this._render();
        // Restore scroll position after render
        const newTaskSelector = this.shadowRoot.getElementById('task-selector');
        if (newTaskSelector) newTaskSelector.scrollTop = scrollTop;
        break;
      
      // Tags
      case 'add-tag':
        const tagInput = this.shadowRoot.getElementById('tag-input');
        if (tagInput && tagInput.value.trim()) {
          if (!this._formState.tags) this._formState.tags = [];
          const newTag = tagInput.value.trim();
          if (!this._formState.tags.includes(newTag)) {
            this._formState.tags.push(newTag);
          }
          tagInput.value = '';
          this._render();
        }
        break;
      
      case 'remove-tag':
        const tagToRemove = target.dataset.tag;
        if (this._formState.tags) {
          this._formState.tags = this._formState.tags.filter(t => t !== tagToRemove);
          this._render();
        }
        break;
      
      case 'filter-tag':
        this._selectedTag = target.dataset.tag || null;
        this._render();
        break;
      
      // Schedule
      case 'toggle-day':
        const day = target.dataset.day;
        if (!this._formState.scheduleDays) this._formState.scheduleDays = [];
        const idx = this._formState.scheduleDays.indexOf(day);
        if (idx >= 0) {
          this._formState.scheduleDays.splice(idx, 1);
        } else {
          this._formState.scheduleDays.push(day);
        }
        this._render();
        break;
      
      // Notification settings
      case 'toggle-notification-settings':
        this._notificationSettingsOpen = !this._notificationSettingsOpen;
        this._render();
        break;
      
      case 'toggle-custom-notifications':
        this._formState.useCustomNotifications = !this._formState.useCustomNotifications;
        this._render();
        break;
      
      case 'toggle-notify-start':
        this._formState.notifyOnStart = !this._formState.notifyOnStart;
        this._render();
        break;
      
      case 'toggle-notify-complete':
        this._formState.notifyOnComplete = !this._formState.notifyOnComplete;
        this._render();
        break;
      
      // Move up/down in review and routine editor
      case 'move-up':
        this._moveTask(target.dataset.taskId, -1);
        break;
      
      case 'move-down':
        this._moveTask(target.dataset.taskId, 1);
        break;
    }
  }
  
  _moveTask(taskId, direction) {
    // Handle review screen
    if (this._mode === 'review' && this._reviewTasks) {
      const idx = this._reviewTasks.findIndex(t => t.id === taskId);
      if (idx === -1) return;
      const newIdx = idx + direction;
      if (newIdx < 0 || newIdx >= this._reviewTasks.length) return;
      
      // Swap
      const temp = this._reviewTasks[idx];
      this._reviewTasks[idx] = this._reviewTasks[newIdx];
      this._reviewTasks[newIdx] = temp;
      
      // Save scroll position
      const reviewList = this.shadowRoot.getElementById('review-task-list');
      const scrollTop = reviewList ? reviewList.scrollTop : 0;
      this._render();
      // Restore scroll position
      const newReviewList = this.shadowRoot.getElementById('review-task-list');
      if (newReviewList) newReviewList.scrollTop = scrollTop;
      return;
    }
    
    // Handle routine editor
    if ((this._mode === 'create-routine' || this._mode === 'edit-routine') && this._routineTaskOrder.length > 0) {
      const idx = this._routineTaskOrder.indexOf(taskId);
      if (idx === -1) return;
      const newIdx = idx + direction;
      if (newIdx < 0 || newIdx >= this._routineTaskOrder.length) return;
      
      // Swap
      const temp = this._routineTaskOrder[idx];
      this._routineTaskOrder[idx] = this._routineTaskOrder[newIdx];
      this._routineTaskOrder[newIdx] = temp;
      
      // Save scroll position
      const taskSelector = this.shadowRoot.getElementById('task-selector');
      const selectorScrollTop = taskSelector ? taskSelector.scrollTop : 0;
      this._render();
      // Restore scroll position
      const newTaskSelector = this.shadowRoot.getElementById('task-selector');
      if (newTaskSelector) newTaskSelector.scrollTop = selectorScrollTop;
    }
  }

  _clearFormState() {
    this._formState = {};
    this._editingId = null;
    this._notificationSettingsOpen = false;
    this._routineTaskOrder = [];
  }

  // ==========================================================================
  // SERVICE CALLS
  // ==========================================================================

  async _callService(service, data = {}) {
    try {
      await this._hass.callService('routinely', service, data);
    } catch (e) {
      console.error(`Failed to call routinely.${service}:`, e);
    }
  }

  async _startReview(routineId) {
    const routinesEntity = this._hass.states['sensor.routinely_routines'];
    const routines = routinesEntity?.attributes?.routines || [];
    const routine = routines.find(r => r.id === routineId);
    
    if (!routine) return;
    
    const tasksEntity = this._hass.states['sensor.routinely_tasks'];
    const allTasks = tasksEntity?.attributes?.tasks || [];
    
    // Get tasks for this routine in order
    const taskIds = routine.task_ids || [];
    const tasks = taskIds.map(id => allTasks.find(t => t.id === id)).filter(t => t);
    
    this._reviewRoutine = routine;
    this._reviewTasks = tasks;
    this._skippedTaskIds = new Set();
    this._reviewTaskOrder = tasks.map(t => t.id);
    this._mode = 'review';
    this._render();
  }

  async _confirmStartRoutine() {
    if (!this._reviewRoutine) return;
    
    // Build full task order (reordered tasks including skipped)
    const taskOrder = this._reviewTasks.map(t => t.id);
    
    const skipTaskIds = Array.from(this._skippedTaskIds);
    
    await this._callService('start', {
      routine_id: this._reviewRoutine.id,
      skip_task_ids: skipTaskIds,
      task_order: taskOrder
    });
    
    // Clear review state
    this._reviewRoutine = null;
    this._reviewTasks = [];
    this._skippedTaskIds = new Set();
    this._reviewTaskOrder = [];
    this._mode = 'home';
  }

  async _startEditTask(taskId) {
    const tasksEntity = this._hass.states['sensor.routinely_tasks'];
    const tasks = tasksEntity?.attributes?.tasks || [];
    const task = tasks.find(t => t.id === taskId);
    
    if (!task) return;
    
    this._editingId = taskId;
    this._formState = {
      name: task.name,
      icon: task.icon || '',
      duration: Math.floor(task.duration / 60), // seconds to minutes
      mode: task.advancement_mode || task.mode || 'manual'
    };
    this._mode = 'edit-task';
    this._render();
  }

  async _copyTask(taskId) {
    const tasksEntity = this._hass.states['sensor.routinely_tasks'];
    const tasks = tasksEntity?.attributes?.tasks || [];
    const task = tasks.find(t => t.id === taskId);
    
    if (!task) return;
    
    await this._callService('create_task', {
      task_name: `${task.name} (copy)`,
      duration: task.duration,
      icon: task.icon || '📋',
      advancement_mode: task.advancement_mode || task.mode || 'manual'
    });
  }

  async _saveTask() {
    const name = this._formState.name?.trim();
    const icon = this._formState.icon || '📋';
    const duration = (this._formState.duration || 5) * 60;
    const mode = this._formState.mode || 'manual';
    
    if (!name) return;
    
    await this._callService('create_task', {
      task_name: name,
      duration,
      icon,
      advancement_mode: mode
    });
    
    this._mode = 'tasks';
    this._clearFormState();
    this._render();
  }

  async _saveEditTask() {
    if (!this._editingId) return;
    
    const name = this._formState.name?.trim();
    const icon = this._formState.icon || '📋';
    const duration = (this._formState.duration || 5) * 60;
    const mode = this._formState.mode || 'manual';
    
    if (!name) return;
    
    await this._callService('update_task', {
      task_id: this._editingId,
      task_name: name,
      duration,
      icon,
      advancement_mode: mode
    });
    
    this._mode = 'tasks';
    this._clearFormState();
    this._render();
  }

  async _deleteTask(taskId) {
    if (confirm('Delete this task?')) {
      await this._callService('delete_task', { task_id: taskId });
    }
  }

  async _startEditRoutine(routineId) {
    const routinesEntity = this._hass.states['sensor.routinely_routines'];
    const routines = routinesEntity?.attributes?.routines || [];
    const routine = routines.find(r => r.id === routineId);
    
    if (!routine) return;
    
    // Get task IDs
    const taskIds = routine.task_ids || [];
    
    this._editingId = routineId;
    this._formState = {
      name: routine.name,
      icon: routine.icon || '',
      selectedTasks: new Set(taskIds),
      tags: routine.tags || [],
      scheduleDays: routine.schedule_days || [],
      scheduleTime: routine.schedule_time || '',
      useCustomNotifications: !!routine.notification_settings,
      notifyBefore: routine.notification_settings?.notify_before?.join(',') || '',
      notifyOnStart: routine.notification_settings?.notify_on_start ?? true,
      notifyRemaining: routine.notification_settings?.notify_remaining?.join(',') || '',
      notifyOverdue: routine.notification_settings?.notify_overdue?.join(',') || '',
      notifyOnComplete: routine.notification_settings?.notify_on_complete ?? false
    };
    this._routineTaskOrder = [...taskIds];
    this._mode = 'edit-routine';
    this._notificationSettingsOpen = !!routine.notification_settings;
    this._render();
  }

  async _saveRoutine() {
    const name = this._formState.name?.trim();
    const icon = this._formState.icon || '📋';
    
    if (!name) return;
    
    // Get task IDs in order (use routineTaskOrder if we have it, filtered by selection)
    let taskIds;
    if (this._routineTaskOrder.length > 0) {
      taskIds = this._routineTaskOrder.filter(id => this._formState.selectedTasks?.has(id));
    } else {
      taskIds = Array.from(this._formState.selectedTasks || []);
    }
    
    const serviceData = {
      routine_name: name,
      icon,
      task_ids: taskIds,
      tags: this._formState.tags || [],
      schedule_time: this._formState.scheduleTime || null,
      schedule_days: this._formState.scheduleDays || []
    };
    
    // Add notification settings if custom
    if (this._formState.useCustomNotifications) {
      serviceData.notification_settings = {
        notify_before: utils.parseMinutesToArray(this._formState.notifyBefore || ''),
        notify_on_start: this._formState.notifyOnStart ?? true,
        notify_remaining: utils.parseMinutesToArray(this._formState.notifyRemaining || ''),
        notify_overdue: utils.parseMinutesToArray(this._formState.notifyOverdue || ''),
        notify_on_complete: this._formState.notifyOnComplete ?? false
      };
    }
    
    await this._callService('create_routine', serviceData);
    
    this._mode = 'routines';
    this._clearFormState();
    this._render();
  }

  async _saveEditRoutine() {
    if (!this._editingId) return;
    
    const name = this._formState.name?.trim();
    const icon = this._formState.icon || '📋';
    
    if (!name) return;
    
    // Get task IDs in order
    let taskIds;
    if (this._routineTaskOrder.length > 0) {
      taskIds = this._routineTaskOrder.filter(id => this._formState.selectedTasks?.has(id));
    } else {
      taskIds = Array.from(this._formState.selectedTasks || []);
    }
    
    const serviceData = {
      routine_id: this._editingId,
      routine_name: name,
      icon,
      task_ids: taskIds,
      tags: this._formState.tags || [],
      schedule_time: this._formState.scheduleTime || null,
      schedule_days: this._formState.scheduleDays || []
    };
    
    // Add notification settings if custom, or null to clear
    if (this._formState.useCustomNotifications) {
      serviceData.notification_settings = {
        notify_before: utils.parseMinutesToArray(this._formState.notifyBefore || ''),
        notify_on_start: this._formState.notifyOnStart ?? true,
        notify_remaining: utils.parseMinutesToArray(this._formState.notifyRemaining || ''),
        notify_overdue: utils.parseMinutesToArray(this._formState.notifyOverdue || ''),
        notify_on_complete: this._formState.notifyOnComplete ?? false
      };
    } else {
      serviceData.notification_settings = null;
    }
    
    await this._callService('update_routine', serviceData);
    
    this._mode = 'routines';
    this._clearFormState();
    this._render();
  }

  async _deleteRoutine(routineId) {
    if (confirm('Delete this routine?')) {
      await this._callService('delete_routine', { routine_id: routineId });
    }
  }

  // ==========================================================================
  // STATIC CONFIG
  // ==========================================================================

  static getConfigElement() {
    return document.createElement('routinely-card-editor');
  }

  static getStubConfig() {
    return {};
  }
}

// Register the card
customElements.define('routinely-card', RoutinelyCard);

// Register with Lovelace
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'routinely-card',
  name: 'Routinely Card',
  description: 'ADHD-friendly routine management card with drag-and-drop reordering'
});
