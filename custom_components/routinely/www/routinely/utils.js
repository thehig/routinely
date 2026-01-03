/**
 * ROUTINELY - Utilities Module
 * Helper functions and utilities
 */

/**
 * Format seconds as MM:SS or HH:MM:SS
 */
export function formatTime(seconds) {
  if (seconds === null || seconds === undefined || seconds < 0) return '--:--';
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  if (hrs > 0) {
    return `${hrs}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

/**
 * Format seconds as human readable duration
 */
export function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return '0m';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  if (mins === 0) return `${secs}s`;
  if (secs === 0) return `${mins}m`;
  return `${mins}m ${secs}s`;
}

/**
 * Format advancement mode for display
 */
export function formatAdvancementMode(mode) {
  const modes = {
    'manual': 'Manual',
    'auto_next': 'Auto',
    'auto_complete': 'Auto-Complete',
    'confirm_next': 'Confirm'
  };
  return modes[mode] || mode;
}

/**
 * Get badge style class for advancement mode
 */
export function getModeStyle(mode) {
  const styles = {
    'manual': 'background: rgba(255, 152, 0, 0.2); color: #FF9800;',
    'auto_next': 'background: rgba(66, 165, 245, 0.2); color: #42A5F5;',
    'auto_complete': 'background: rgba(102, 187, 106, 0.2); color: #66BB6A;',
    'confirm_next': 'background: rgba(171, 71, 188, 0.2); color: #AB47BC;'
  };
  return styles[mode] || '';
}

/**
 * Convert minutes input string to array of integers
 */
export function parseMinutesToArray(str) {
  if (!str || typeof str !== 'string') return [];
  return str.split(',')
    .map(s => parseInt(s.trim(), 10))
    .filter(n => !isNaN(n) && n > 0);
}

/**
 * Calculate time string from start time and offset
 */
export function calculateTimeString(startHour, startMin, offsetSeconds) {
  const totalMins = startHour * 60 + startMin + Math.floor(offsetSeconds / 60);
  const h = Math.floor(totalMins / 60) % 24;
  const m = totalMins % 60;
  const ampm = h >= 12 ? 'PM' : 'AM';
  const h12 = h % 12 || 12;
  return `${h12}:${String(m).padStart(2, '0')} ${ampm}`;
}

/**
 * Get current time as start time object
 */
export function getCurrentStartTime() {
  const now = new Date();
  return {
    hour: now.getHours(),
    min: now.getMinutes()
  };
}

/**
 * Common emoji sets for tasks and routines
 */
export const taskEmojis = ['📋', '✅', '⏰', '🔔', '📝', '🎯', '💪', '🧘', '🚿', '🦷', '💊', '🍳', '☕', '📚', '💻', '🏃'];
export const routineEmojis = ['🌅', '🌙', '☀️', '🏠', '💼', '🧹', '🛏️', '🍽️', '💪', '🧘', '📚', '🎮', '🚗', '✈️', '🎉', '❤️'];
