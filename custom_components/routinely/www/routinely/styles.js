/**
 * ROUTINELY - Styles Module
 * All CSS styles for the Routinely card
 */

export const styles = `
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

  .btn-primary { background: #42A5F5; color: white; }
  .btn-success { background: #66BB6A; color: white; }
  .btn-warning { background: #FFA726; color: white; }
  .btn-danger { background: #EF5350; color: white; }
  .btn-secondary { background: var(--divider-color, #eee); color: var(--primary-text-color); }
  .btn-coral { background: linear-gradient(135deg, #FF6B6B, #FF8E8E); color: white; }

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

  /* === TAGS === */
  .tag-container {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 10px;
  }

  .tag {
    display: inline-flex;
    align-items: center;
    padding: 6px 12px;
    background: rgba(255, 107, 107, 0.15);
    color: #FF6B6B;
    border-radius: 16px;
    font-size: 0.85em;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s;
  }

  .tag:hover {
    background: rgba(255, 107, 107, 0.25);
  }

  .tag.selected {
    background: #FF6B6B;
    color: white;
  }

  .tag-input-row {
    display: flex;
    gap: 8px;
    margin-top: 10px;
  }

  .tag-input {
    flex: 1;
    padding: 10px 14px;
    border: 2px solid var(--divider-color, #ddd);
    border-radius: 10px;
    font-size: 0.95em;
    background: var(--card-background-color, white);
    color: var(--primary-text-color);
  }

  .tag-add-btn {
    padding: 10px 16px;
    background: #FF6B6B;
    color: white;
    border: none;
    border-radius: 10px;
    cursor: pointer;
    font-weight: 500;
  }

  /* === SCHEDULE === */
  .schedule-section {
    background: rgba(66, 165, 245, 0.08);
    border-radius: 12px;
    padding: 16px;
    margin-top: 10px;
  }

  .schedule-section-title {
    font-size: 0.9em;
    font-weight: 600;
    color: var(--secondary-text-color);
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .day-picker {
    display: flex;
    gap: 6px;
    justify-content: space-between;
  }

  .day-btn {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 2px solid var(--divider-color, #ddd);
    background: transparent;
    cursor: pointer;
    font-size: 0.8em;
    font-weight: 600;
    color: var(--primary-text-color);
    transition: all 0.15s;
    text-transform: uppercase;
  }

  .day-btn:hover {
    border-color: #42A5F5;
  }

  .day-btn.selected {
    background: #42A5F5;
    border-color: #42A5F5;
    color: white;
  }

  .time-input-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 12px;
  }

  .time-input {
    padding: 10px 14px;
    border: 2px solid var(--divider-color, #ddd);
    border-radius: 10px;
    font-size: 1em;
    background: var(--card-background-color, white);
    color: var(--primary-text-color);
  }

  /* === FILTER BAR === */
  .filter-bar {
    display: flex;
    gap: 8px;
    padding: 12px 16px;
    overflow-x: auto;
    border-bottom: 1px solid var(--divider-color, #eee);
  }

  .filter-btn {
    padding: 8px 14px;
    border-radius: 20px;
    border: 1px solid var(--divider-color, #ddd);
    background: transparent;
    cursor: pointer;
    font-size: 0.85em;
    white-space: nowrap;
    color: var(--primary-text-color);
  }

  .filter-btn.active {
    background: #FF6B6B;
    border-color: #FF6B6B;
    color: white;
  }

  /* === NOTIFICATION SETTINGS === */
  .notification-settings {
    background: rgba(102, 187, 106, 0.08);
    border-radius: 12px;
    padding: 16px;
    margin-top: 10px;
  }

  .notification-toggle {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid var(--divider-color, #eee);
  }

  .notification-toggle:last-child {
    border-bottom: none;
  }

  .notification-toggle-label {
    font-size: 0.95em;
    color: var(--primary-text-color);
  }

  .notification-toggle-hint {
    font-size: 0.8em;
    color: var(--secondary-text-color);
    margin-top: 2px;
  }

  .toggle-switch {
    position: relative;
    width: 52px;
    height: 28px;
    background: var(--divider-color, #ccc);
    border-radius: 14px;
    cursor: pointer;
    transition: background 0.2s;
    flex-shrink: 0;
  }

  .toggle-switch.on {
    background: #66BB6A;
  }

  .toggle-switch::after {
    content: '';
    position: absolute;
    width: 22px;
    height: 22px;
    background: white;
    border-radius: 50%;
    top: 3px;
    left: 3px;
    transition: transform 0.2s;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  }

  .toggle-switch.on::after {
    transform: translateX(24px);
  }

  .notification-time-input {
    padding: 8px 12px;
    border: 2px solid var(--divider-color, #ddd);
    border-radius: 8px;
    font-size: 0.9em;
    width: 120px;
    background: var(--card-background-color, white);
    color: var(--primary-text-color);
  }

  .collapsible-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 0;
    cursor: pointer;
    user-select: none;
  }

  .collapsible-header:hover {
    opacity: 0.8;
  }

  .collapsible-icon {
    font-size: 1.2em;
    transition: transform 0.2s;
  }

  .collapsible-icon.open {
    transform: rotate(90deg);
  }

  .collapsible-content {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease-out;
  }

  .collapsible-content.open {
    max-height: 600px;
  }

  /* === DRAG AND DROP === */
  .draggable {
    cursor: grab;
    touch-action: none;
  }

  .draggable:active {
    cursor: grabbing;
  }

  .draggable.dragging {
    opacity: 0.5;
    transform: scale(1.02);
    box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    z-index: 100;
  }

  .drag-handle {
    cursor: grab;
    padding: 8px;
    margin-right: 8px;
    opacity: 0.4;
    font-size: 1.2em;
    touch-action: none;
  }

  .drag-handle:hover {
    opacity: 0.8;
  }

  .drop-zone {
    transition: all 0.2s;
  }

  .drop-zone.drag-over {
    background: rgba(66, 165, 245, 0.2);
    border-color: #42A5F5;
  }

  .drop-indicator {
    height: 4px;
    background: #42A5F5;
    border-radius: 2px;
    margin: 4px 0;
    opacity: 0;
    transition: opacity 0.2s;
  }

  .drop-indicator.visible {
    opacity: 1;
  }

  .sortable-ghost {
    opacity: 0.4;
  }

  .sortable-chosen {
    background: rgba(66, 165, 245, 0.1);
  }
`;
