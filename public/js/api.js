/**
 * API Client Module
 * Phase 3: Real API calls to FastAPI backend with error handling
 */

const API = (function() {
    'use strict';

    let config = null;

    /**
     * Initialize API with configuration
     */
    async function init() {
        config = await Storage.loadConfig();
        return config;
    }

    /**
     * Get API endpoint (local or cloud based on config)
     */
    function getEndpoint() {
        if (!config) {
            // Try to load config synchronously from localStorage as fallback
            const savedConfig = localStorage.getItem('reminders_config');
            if (savedConfig) {
                const parsedConfig = JSON.parse(savedConfig);
                return parsedConfig.api.use_cloud ? parsedConfig.api.cloud_endpoint : parsedConfig.api.local_endpoint;
            }
            console.warn('API not initialized and no saved config, using default endpoint');
            return 'http://100.114.120.17:8000/api'; // Match current deployment
        }
        return config.api.use_cloud ? config.api.cloud_endpoint : config.api.local_endpoint;
    }

    /**
     * Get authorization headers
     */
    function getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        if (config && config.api.token) {
            headers['Authorization'] = `Bearer ${config.api.token}`;
        }
        return headers;
    }

    /**
     * Normalize time format for backend (HH:MM -> HH:MM:SS)
     * @param {string|null} time - Time string in HH:MM or HH:MM:SS format
     * @returns {string|null} Normalized time string
     */
    function normalizeTimeFormat(time) {
        if (!time) return null;

        // If time is HH:MM, add :00
        if (time.match(/^\d{2}:\d{2}$/)) {
            return `${time}:00`;
        }

        return time;
    }

    /**
     * Make API request with retry logic
     * @param {string} method - HTTP method (GET, POST, PATCH, DELETE)
     * @param {string} path - API path (e.g., '/reminders')
     * @param {Object|null} data - Request body data
     * @returns {Promise<any>} Parsed JSON response
     */
    async function request(method, path, data = null) {
        const url = `${getEndpoint()}${path}`;
        const options = {
            method: method,
            headers: getHeaders()
        };

        if (data !== null) {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetchWithRetry(url, options);

            // Handle 204 No Content (DELETE responses)
            if (response.status === 204) {
                return null;
            }

            // Parse JSON response
            const jsonData = await safeJsonParse(response);
            return jsonData;

        } catch (error) {
            const message = formatErrorMessage(error);
            console.error('[API Error]', method, path, message);
            throw error; // Re-throw for caller to handle
        }
    }

    /**
     * Get all reminders with optional filters
     * @param {Object} filters - Filter options (status, category, priority)
     * @returns {Promise<Array>} Array of reminder objects
     */
    async function getReminders(filters = {}) {
        try {
            // Build query string from filters
            const params = new URLSearchParams();
            if (filters.status) params.append('status', filters.status);
            if (filters.category) params.append('category', filters.category);
            if (filters.priority) params.append('priority', filters.priority);

            const queryString = params.toString();
            const path = queryString ? `/reminders?${queryString}` : '/reminders';

            const response = await request('GET', path);

            // Backend returns {data: [...], pagination: {...}}
            // Extract just the data array
            return response.data || [];

        } catch (error) {
            const message = formatErrorMessage(error);
            showError(`Failed to load reminders: ${message}`);
            throw error;
        }
    }

    /**
     * Get reminder by ID
     * @param {string} id - Reminder ID
     * @returns {Promise<Object|null>} Reminder object or null if not found
     */
    async function getReminder(id) {
        try {
            const response = await request('GET', `/reminders/${id}`);
            return response;
        } catch (error) {
            // Handle 404 gracefully
            if (error.status === 404) {
                return null;
            }

            const message = formatErrorMessage(error);
            showError(`Failed to load reminder: ${message}`);
            throw error;
        }
    }

    /**
     * Create a new reminder
     * @param {Object} data - Reminder data
     * @returns {Promise<Object>} Created reminder object
     */
    async function createReminder(data) {
        try {
            // Normalize time format if present
            const normalizedData = {
                ...data,
                due_time: normalizeTimeFormat(data.due_time)
            };

            const response = await request('POST', '/reminders', normalizedData);

            // Queue change for sync (Phase 5)
            if (window.SyncManager && response.id) {
                window.SyncManager.queueChange(response.id, 'create', response);
            }

            showSuccess('Reminder created!');
            return response;

        } catch (error) {
            const message = formatErrorMessage(error);
            showError(`Failed to create reminder: ${message}`);
            throw error;
        }
    }

    /**
     * Update a reminder
     * @param {string} id - Reminder ID
     * @param {Object} data - Partial reminder data to update
     * @returns {Promise<Object>} Updated reminder object
     */
    async function updateReminder(id, data) {
        try {
            // Normalize time format if present
            const normalizedData = {
                ...data,
                due_time: data.due_time ? normalizeTimeFormat(data.due_time) : data.due_time
            };

            const response = await request('PATCH', `/reminders/${id}`, normalizedData);

            // Queue change for sync (Phase 5)
            if (window.SyncManager && response.id) {
                window.SyncManager.queueChange(response.id, 'update', normalizedData);
            }

            showSuccess('Reminder updated!');
            return response;

        } catch (error) {
            const message = formatErrorMessage(error);
            showError(`Failed to update reminder: ${message}`);
            throw error;
        }
    }

    /**
     * Delete a reminder
     * @param {string} id - Reminder ID
     * @returns {Promise<null>} Returns null on success
     */
    async function deleteReminder(id) {
        try {
            await request('DELETE', `/reminders/${id}`);

            // Queue change for sync (Phase 5)
            if (window.SyncManager) {
                window.SyncManager.queueChange(id, 'delete', null);
            }

            showSuccess('Reminder deleted!');
            return null;

        } catch (error) {
            const message = formatErrorMessage(error);
            showError(`Failed to delete reminder: ${message}`);
            throw error;
        }
    }

    /**
     * Complete a reminder (update status to completed)
     * Backend automatically sets completed_at timestamp
     * @param {string} id - Reminder ID
     * @returns {Promise<Object>} Updated reminder object
     */
    async function completeReminder(id) {
        try {
            // Backend will set completed_at automatically
            const response = await request('PATCH', `/reminders/${id}`, { status: 'completed' });
            showSuccess('Reminder completed!');
            return response;

        } catch (error) {
            const message = formatErrorMessage(error);
            showError(`Failed to complete reminder: ${message}`);
            throw error;
        }
    }

    /**
     * Get today's reminders (overdue, today, and floating)
     * @returns {Promise<Object>} Object with {overdue: [], today: [], floating: []}
     */
    async function getTodayReminders() {
        try {
            // Fetch all pending reminders
            const response = await request('GET', '/reminders?status=pending');
            const reminders = response.data || [];

            const today = new Date().toISOString().split('T')[0];

            // Categorize reminders
            const overdue = [];
            const todayReminders = [];
            const floating = [];

            reminders.forEach(r => {
                if (!r.due_date) {
                    floating.push(r);
                } else if (r.due_date < today) {
                    overdue.push(r);
                } else if (r.due_date === today) {
                    todayReminders.push(r);
                }
            });

            return {
                overdue,
                today: todayReminders,
                floating
            };

        } catch (error) {
            const message = formatErrorMessage(error);
            showError(`Failed to load today's reminders: ${message}`);
            throw error;
        }
    }

    /**
     * Get upcoming reminders (next 7 days, excluding today)
     * @returns {Promise<Array>} Array of reminders sorted by date
     */
    async function getUpcomingReminders() {
        try {
            // Fetch all pending reminders
            const response = await request('GET', '/reminders?status=pending');
            const reminders = response.data || [];

            const today = new Date().toISOString().split('T')[0];
            const nextWeek = new Date();
            nextWeek.setDate(nextWeek.getDate() + 7);
            const nextWeekStr = nextWeek.toISOString().split('T')[0];

            // Filter for upcoming (after today, within 7 days)
            const upcoming = reminders.filter(r => {
                if (!r.due_date) return false; // Exclude floating tasks
                if (r.due_date <= today) return false; // Exclude today and overdue
                if (r.due_date <= nextWeekStr) return true; // Include next 7 days
                return false;
            });

            // Sort by due_date ascending
            upcoming.sort((a, b) => {
                const dateDiff = a.due_date.localeCompare(b.due_date);
                if (dateDiff !== 0) return dateDiff;

                // Then by priority
                const priorityOrder = { urgent: 0, important: 1, chill: 2, someday: 3, waiting: 4 };
                const priorityDiff = priorityOrder[a.priority] - priorityOrder[b.priority];
                if (priorityDiff !== 0) return priorityDiff;

                // Then by time
                if (a.due_time && b.due_time) {
                    return a.due_time.localeCompare(b.due_time);
                }

                return 0;
            });

            return upcoming;

        } catch (error) {
            const message = formatErrorMessage(error);
            showError(`Failed to load upcoming reminders: ${message}`);
            throw error;
        }
    }

    /**
     * Get future reminders (8+ days from now)
     * @returns {Promise<Array>} Array of reminders sorted by date
     */
    async function getFutureReminders() {
        try {
            // Fetch all pending reminders
            const response = await request('GET', '/reminders?status=pending');
            const reminders = response.data || [];

            const today = new Date().toISOString().split('T')[0];
            const nextWeek = new Date();
            nextWeek.setDate(nextWeek.getDate() + 7);
            const nextWeekStr = nextWeek.toISOString().split('T')[0];

            // Filter for future (beyond next 7 days)
            const future = reminders.filter(r => {
                if (!r.due_date) return false; // Exclude floating tasks
                if (r.due_date <= nextWeekStr) return false; // Exclude upcoming/today
                return true; // Include everything beyond 7 days
            });

            // Sort by due_date ascending, then priority
            future.sort((a, b) => {
                const dateDiff = a.due_date.localeCompare(b.due_date);
                if (dateDiff !== 0) return dateDiff;

                const priorityOrder = { urgent: 0, important: 1, chill: 2, someday: 3, waiting: 4 };
                return priorityOrder[a.priority] - priorityOrder[b.priority];
            });

            return future;

        } catch (error) {
            const message = formatErrorMessage(error);
            showError(`Failed to load future reminders: ${message}`);
            throw error;
        }
    }

    /**
     * Health check endpoint
     * @returns {Promise<Object>} Health status object
     */
    async function healthCheck() {
        try {
            const response = await request('GET', '/health');
            return response;
        } catch (error) {
            const message = formatErrorMessage(error);
            showError(`Health check failed: ${message}`);
            throw error;
        }
    }

    /**
     * Get reminders near a location (Phase 6)
     * @param {number} lat - Latitude
     * @param {number} lng - Longitude
     * @param {number} radius - Search radius in meters (default: 1000)
     * @returns {Promise<Array>} Array of reminders within radius
     */
    async function getNearbyReminders(lat, lng, radius = 1000) {
        const endpoint = getEndpoint();
        const url = `${endpoint}/reminders/near-location?lat=${lat}&lng=${lng}&radius=${radius}`;

        const response = await fetch(url, {
            method: 'GET',
            headers: getHeaders()
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get nearby reminders');
        }

        const result = await response.json();
        return result.data || [];
    }

    // Public API
    return {
        init,
        getEndpoint,
        getReminders,
        getReminder,
        createReminder,
        updateReminder,
        deleteReminder,
        completeReminder,
        getTodayReminders,
        getUpcomingReminders,
        getFutureReminders,
        getNearbyReminders,
        healthCheck
    };
})();

// Make available globally
window.API = API;
