/* ========================================
   Error Handling & Toast Notifications
   ADHD-Friendly UI Feedback System
   ======================================== */

/**
 * Toast notification system
 * Displays non-blocking notifications with auto-dismiss
 */
class ToastManager {
    constructor() {
        this.container = null;
        this.toasts = [];
        this.maxToasts = 5; // Maximum visible toasts
        this.init();
    }

    init() {
        // Get or create toast container
        this.container = document.getElementById('toast-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    }

    /**
     * Show a toast notification
     * @param {string} message - Message to display
     * @param {string} type - Toast type (success, error, warning, info)
     * @param {number} duration - Auto-dismiss duration in ms (0 = no auto-dismiss)
     */
    show(message, type = 'info', duration = 4000) {
        // Trim message to avoid overly long toasts
        const trimmedMessage = message.length > 150
            ? message.substring(0, 147) + '...'
            : message;

        // Remove oldest toast if at max capacity
        if (this.toasts.length >= this.maxToasts) {
            const oldestToast = this.toasts[0];
            this.remove(oldestToast);
        }

        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'polite');

        // Create toast content
        const icon = this.getIcon(type);
        const messageSpan = document.createElement('span');
        messageSpan.className = 'toast-message';
        messageSpan.textContent = trimmedMessage;

        const closeButton = document.createElement('button');
        closeButton.className = 'toast-close';
        closeButton.innerHTML = '×';
        closeButton.setAttribute('aria-label', 'Close notification');
        closeButton.onclick = () => this.remove(toast);

        // Assemble toast
        toast.appendChild(icon);
        toast.appendChild(messageSpan);
        toast.appendChild(closeButton);

        // Add to container
        this.container.appendChild(toast);
        this.toasts.push(toast);

        // Trigger animation
        setTimeout(() => toast.classList.add('toast-visible'), 10);

        // Auto-dismiss
        if (duration > 0) {
            setTimeout(() => this.remove(toast), duration);
        }

        // Log to console for debugging
        console.log(`[Toast ${type.toUpperCase()}]`, trimmedMessage);

        return toast;
    }

    /**
     * Remove a toast notification
     * @param {HTMLElement} toast - Toast element to remove
     */
    remove(toast) {
        if (!toast || !toast.parentElement) return;

        // Fade out animation
        toast.classList.remove('toast-visible');
        toast.classList.add('toast-hiding');

        setTimeout(() => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
            }
            this.toasts = this.toasts.filter(t => t !== toast);
        }, 300); // Match CSS transition duration
    }

    /**
     * Get icon element for toast type
     * @param {string} type - Toast type
     * @returns {HTMLElement} Icon element
     */
    getIcon(type) {
        const iconSpan = document.createElement('span');
        iconSpan.className = 'toast-icon';
        iconSpan.setAttribute('aria-hidden', 'true');

        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };

        iconSpan.textContent = icons[type] || icons.info;
        return iconSpan;
    }

    /**
     * Clear all toasts
     */
    clearAll() {
        this.toasts.forEach(toast => this.remove(toast));
    }
}

// Create global toast manager instance
const toastManager = new ToastManager();

/**
 * Show toast notification (public API)
 * @param {string} message - Message to display
 * @param {string} type - Toast type (success, error, warning, info)
 * @param {number} duration - Auto-dismiss duration in ms
 */
function showToast(message, type = 'info', duration = 4000) {
    return toastManager.show(message, type, duration);
}

/**
 * Show error toast
 * @param {string} message - Error message
 */
function showError(message) {
    console.error('[Error]', message);
    return showToast(message, 'error', 5000); // Longer duration for errors
}

/**
 * Show success toast
 * @param {string} message - Success message
 */
function showSuccess(message) {
    return showToast(message, 'success', 3000); // Shorter for success
}

/**
 * Show warning toast
 * @param {string} message - Warning message
 */
function showWarning(message) {
    return showToast(message, 'warning', 4000);
}

/**
 * Show info toast
 * @param {string} message - Info message
 */
function showInfo(message) {
    return showToast(message, 'info', 4000);
}

/**
 * Format error messages from various sources
 * @param {Error|Object|string} error - Error to format
 * @returns {string} Formatted error message
 */
function formatErrorMessage(error) {
    // Handle null/undefined
    if (!error) {
        return 'An unknown error occurred';
    }

    // Handle string errors
    if (typeof error === 'string') {
        return error;
    }

    // Handle backend API errors with detail field
    if (error.detail) {
        return error.detail;
    }

    // Handle Response objects from fetch
    if (error instanceof Response) {
        return `Server error: ${error.status} ${error.statusText}`;
    }

    // Handle network errors
    if (error.message === 'Failed to fetch') {
        return 'Network error: Unable to connect to server. Check your connection.';
    }

    // Handle timeout errors
    if (error.name === 'AbortError' || error.message?.includes('timeout')) {
        return 'Request timeout: The server took too long to respond.';
    }

    // Handle JavaScript Error objects
    if (error instanceof Error) {
        return error.message || 'An unexpected error occurred';
    }

    // Handle objects with message property
    if (error.message) {
        return error.message;
    }

    // Handle objects with error property
    if (error.error) {
        return formatErrorMessage(error.error);
    }

    // Last resort: stringify
    try {
        const stringified = JSON.stringify(error);
        if (stringified !== '{}') {
            return stringified;
        }
    } catch (e) {
        // Circular reference or non-serializable
    }

    return 'An unexpected error occurred';
}

/**
 * Retry a function with exponential backoff
 * @param {Function} fn - Async function to retry
 * @param {Object} options - Retry options
 * @returns {Promise} Result of function
 */
async function withRetry(fn, options = {}) {
    const {
        maxAttempts = 3,
        initialDelay = 500,
        maxDelay = 5000,
        backoffFactor = 2,
        onRetry = null,
        retryOn = null // Function to determine if should retry: (error) => boolean
    } = options;

    let lastError;
    let delay = initialDelay;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            const result = await fn();

            // Success - reset toast if this was a retry
            if (attempt > 1) {
                console.log(`[Retry] Succeeded on attempt ${attempt}`);
            }

            return result;
        } catch (error) {
            lastError = error;

            // Log the error
            console.error(`[Retry] Attempt ${attempt}/${maxAttempts} failed:`, error);

            // Check if we should retry this error
            if (retryOn && !retryOn(error)) {
                console.log('[Retry] Error is not retryable, failing immediately');
                throw error;
            }

            // If this was the last attempt, throw
            if (attempt === maxAttempts) {
                console.error(`[Retry] All ${maxAttempts} attempts failed`);
                break;
            }

            // Show retry notification
            if (onRetry) {
                onRetry(attempt, maxAttempts, error);
            } else {
                showWarning(`Connection issue. Retrying (${attempt}/${maxAttempts})...`);
            }

            // Wait before next attempt (exponential backoff)
            const currentDelay = Math.min(delay, maxDelay);
            console.log(`[Retry] Waiting ${currentDelay}ms before attempt ${attempt + 1}`);
            await sleep(currentDelay);

            // Increase delay for next iteration
            delay *= backoffFactor;
        }
    }

    // All attempts failed
    const errorMessage = formatErrorMessage(lastError);
    showError(`Operation failed: ${errorMessage}`);
    throw lastError;
}

/**
 * Sleep for specified milliseconds
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise} Promise that resolves after delay
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Wrapper for fetch with retry logic
 * @param {string} url - URL to fetch
 * @param {Object} options - Fetch options
 * @param {Object} retryOptions - Retry options
 * @returns {Promise<Response>} Fetch response
 */
async function fetchWithRetry(url, options = {}, retryOptions = {}) {
    return withRetry(
        async () => {
            const response = await fetch(url, options);

            // Check if response is OK
            if (!response.ok) {
                // Try to parse error message from response
                let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    if (errorData.detail) {
                        errorMessage = errorData.detail;
                    }
                } catch (e) {
                    // Response wasn't JSON, use status text
                }

                const error = new Error(errorMessage);
                error.response = response;
                error.status = response.status;
                throw error;
            }

            return response;
        },
        {
            maxAttempts: 3,
            initialDelay: 500,
            maxDelay: 5000,
            backoffFactor: 2,
            // Only retry on network errors or 5xx server errors
            retryOn: (error) => {
                if (error.message === 'Failed to fetch') return true; // Network error
                if (error.status >= 500 && error.status < 600) return true; // Server error
                return false; // Don't retry client errors (4xx)
            },
            ...retryOptions
        }
    );
}

/**
 * Safe JSON parse with error handling
 * @param {Response} response - Fetch response
 * @returns {Promise<any>} Parsed JSON or throws formatted error
 */
async function safeJsonParse(response) {
    try {
        return await response.json();
    } catch (error) {
        console.error('[JSON Parse Error]', error);
        throw new Error('Invalid response from server');
    }
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        showToast,
        showError,
        showSuccess,
        showWarning,
        showInfo,
        formatErrorMessage,
        withRetry,
        fetchWithRetry,
        safeJsonParse,
        sleep
    };
}
