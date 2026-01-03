/**
 * ROUTINELY - Drag and Drop Module
 * Provides touch-friendly drag and drop reordering
 */

/**
 * DragDropManager - Handles drag and drop interactions
 * Supports both mouse and touch events for mobile compatibility
 */
export class DragDropManager {
  constructor(options = {}) {
    this.container = null;
    this.items = [];
    this.draggedItem = null;
    this.draggedIndex = -1;
    this.placeholder = null;
    this.onReorder = options.onReorder || (() => {});
    this.itemSelector = options.itemSelector || '.draggable-item';
    this.handleSelector = options.handleSelector || '.drag-handle';
    
    // Touch handling
    this.touchStartY = 0;
    this.touchCurrentY = 0;
    this.touchStartX = 0;
    this.scrollContainer = null;
    this.autoScrollInterval = null;
    this.isDragging = false;
    
    // Clone element for visual feedback
    this.dragClone = null;
    
    // Bind methods
    this._onMouseDown = this._onMouseDown.bind(this);
    this._onMouseMove = this._onMouseMove.bind(this);
    this._onMouseUp = this._onMouseUp.bind(this);
    this._onTouchStart = this._onTouchStart.bind(this);
    this._onTouchMove = this._onTouchMove.bind(this);
    this._onTouchEnd = this._onTouchEnd.bind(this);
  }

  /**
   * Initialize drag and drop on a container
   */
  init(container, scrollContainer = null) {
    this.container = container;
    this.scrollContainer = scrollContainer || container;
    
    if (!container) return;

    // Remove existing listeners
    this.destroy();

    // Add event listeners to drag handles
    const handles = container.querySelectorAll(this.handleSelector);
    handles.forEach((handle, index) => {
      handle.addEventListener('mousedown', (e) => this._onMouseDown(e, index));
      handle.addEventListener('touchstart', (e) => this._onTouchStart(e, index), { passive: false });
    });

    // Global listeners for move/end
    document.addEventListener('mousemove', this._onMouseMove);
    document.addEventListener('mouseup', this._onMouseUp);
    document.addEventListener('touchmove', this._onTouchMove, { passive: false });
    document.addEventListener('touchend', this._onTouchEnd);
  }

  /**
   * Clean up event listeners
   */
  destroy() {
    document.removeEventListener('mousemove', this._onMouseMove);
    document.removeEventListener('mouseup', this._onMouseUp);
    document.removeEventListener('touchmove', this._onTouchMove);
    document.removeEventListener('touchend', this._onTouchEnd);
    this._stopAutoScroll();
    this._removeDragClone();
  }

  /**
   * Get current order of items by their data-id attributes
   */
  getOrder() {
    if (!this.container) return [];
    const items = this.container.querySelectorAll(this.itemSelector);
    return Array.from(items).map(item => item.dataset.id);
  }

  // === MOUSE HANDLERS ===

  _onMouseDown(e, index) {
    e.preventDefault();
    this._startDrag(index, e.clientY, e.clientX);
  }

  _onMouseMove(e) {
    if (!this.isDragging) return;
    this._updateDrag(e.clientY, e.clientX);
  }

  _onMouseUp(e) {
    if (!this.isDragging) return;
    this._endDrag();
  }

  // === TOUCH HANDLERS ===

  _onTouchStart(e, index) {
    if (e.touches.length !== 1) return;
    
    const touch = e.touches[0];
    this.touchStartY = touch.clientY;
    this.touchStartX = touch.clientX;
    
    // Delay to distinguish from scroll
    this._touchTimeout = setTimeout(() => {
      e.preventDefault();
      this._startDrag(index, touch.clientY, touch.clientX);
      
      // Vibrate on mobile if supported
      if (navigator.vibrate) {
        navigator.vibrate(50);
      }
    }, 150);
  }

  _onTouchMove(e) {
    if (!this.isDragging) {
      // Cancel drag start if user scrolls
      const touch = e.touches[0];
      const deltaY = Math.abs(touch.clientY - this.touchStartY);
      const deltaX = Math.abs(touch.clientX - this.touchStartX);
      
      if (deltaY > 10 || deltaX > 10) {
        clearTimeout(this._touchTimeout);
      }
      return;
    }
    
    e.preventDefault();
    const touch = e.touches[0];
    this._updateDrag(touch.clientY, touch.clientX);
  }

  _onTouchEnd(e) {
    clearTimeout(this._touchTimeout);
    if (!this.isDragging) return;
    this._endDrag();
  }

  // === DRAG LOGIC ===

  _startDrag(index, clientY, clientX) {
    const items = this.container.querySelectorAll(this.itemSelector);
    if (index >= items.length) return;

    this.isDragging = true;
    this.draggedIndex = index;
    this.draggedItem = items[index];
    this.items = Array.from(items);
    
    // Create visual clone for dragging
    this._createDragClone(this.draggedItem, clientY, clientX);
    
    // Mark original as dragging
    this.draggedItem.classList.add('dragging');
    
    // Create placeholder
    this._createPlaceholder();
    
    // Start auto-scroll check
    this._startAutoScroll();
  }

  _updateDrag(clientY, clientX) {
    if (!this.dragClone) return;

    // Update clone position
    this.dragClone.style.top = `${clientY - this.dragClone.offsetHeight / 2}px`;
    this.dragClone.style.left = `${clientX - this.dragClone.offsetWidth / 2}px`;

    // Find drop target
    const targetIndex = this._getDropIndex(clientY);
    
    if (targetIndex !== -1 && targetIndex !== this.draggedIndex) {
      this._moveToPosition(targetIndex);
    }

    // Update auto-scroll
    this.touchCurrentY = clientY;
  }

  _endDrag() {
    this.isDragging = false;
    this._stopAutoScroll();
    
    // Remove visual elements
    this._removeDragClone();
    this._removePlaceholder();
    
    if (this.draggedItem) {
      this.draggedItem.classList.remove('dragging');
    }

    // Get new order and fire callback
    const newOrder = this.getOrder();
    this.onReorder(newOrder);

    // Reset state
    this.draggedItem = null;
    this.draggedIndex = -1;
    this.items = [];
  }

  _getDropIndex(clientY) {
    const items = this.container.querySelectorAll(this.itemSelector);
    
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item === this.draggedItem) continue;
      
      const rect = item.getBoundingClientRect();
      const midY = rect.top + rect.height / 2;
      
      if (clientY < midY) {
        return i;
      }
    }
    
    return items.length - 1;
  }

  _moveToPosition(newIndex) {
    if (newIndex === this.draggedIndex) return;

    const items = Array.from(this.container.querySelectorAll(this.itemSelector));
    const targetItem = items[newIndex];
    
    if (!targetItem || !this.draggedItem) return;

    // Move DOM element
    if (newIndex < this.draggedIndex) {
      this.container.insertBefore(this.draggedItem, targetItem);
    } else {
      const nextSibling = targetItem.nextSibling;
      if (nextSibling) {
        this.container.insertBefore(this.draggedItem, nextSibling);
      } else {
        this.container.appendChild(this.draggedItem);
      }
    }

    this.draggedIndex = newIndex;
  }

  // === VISUAL HELPERS ===

  _createDragClone(element, clientY, clientX) {
    this.dragClone = element.cloneNode(true);
    this.dragClone.style.cssText = `
      position: fixed;
      top: ${clientY - element.offsetHeight / 2}px;
      left: ${clientX - element.offsetWidth / 2}px;
      width: ${element.offsetWidth}px;
      z-index: 10000;
      pointer-events: none;
      opacity: 0.9;
      transform: scale(1.02);
      box-shadow: 0 8px 24px rgba(0,0,0,0.2);
      border-radius: 12px;
      background: var(--ha-card-background, var(--card-background-color, white));
    `;
    document.body.appendChild(this.dragClone);
  }

  _removeDragClone() {
    if (this.dragClone && this.dragClone.parentNode) {
      this.dragClone.parentNode.removeChild(this.dragClone);
    }
    this.dragClone = null;
  }

  _createPlaceholder() {
    // The dragged item becomes its own placeholder via opacity
  }

  _removePlaceholder() {
    // Cleanup if needed
  }

  // === AUTO-SCROLL ===

  _startAutoScroll() {
    this._stopAutoScroll();
    this.autoScrollInterval = setInterval(() => {
      if (!this.isDragging || !this.scrollContainer) return;

      const containerRect = this.scrollContainer.getBoundingClientRect();
      const scrollSpeed = 8;
      const threshold = 60;

      if (this.touchCurrentY < containerRect.top + threshold) {
        this.scrollContainer.scrollTop -= scrollSpeed;
      } else if (this.touchCurrentY > containerRect.bottom - threshold) {
        this.scrollContainer.scrollTop += scrollSpeed;
      }
    }, 16);
  }

  _stopAutoScroll() {
    if (this.autoScrollInterval) {
      clearInterval(this.autoScrollInterval);
      this.autoScrollInterval = null;
    }
  }
}

/**
 * Create a reorderable list with drag handles
 * Returns HTML for items with drag handles included
 */
export function createDraggableItem(content, id, extraClasses = '') {
  return `
    <div class="draggable-item ${extraClasses}" data-id="${id}">
      <span class="drag-handle">⋮⋮</span>
      ${content}
    </div>
  `;
}
