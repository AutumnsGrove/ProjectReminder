/**
 * API Client Module
 * Phase 2: Stubbed to return mock data from Storage
 * Phase 3: Will implement actual API calls to FastAPI backend
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
            console.warn('API not initialized, using default endpoint');
            return 'http://localhost:8000/api';
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
     * Make API request (stubbed for Phase 2)
     */
    async function request(method, path, data = null) {
        // Phase 2: Return mock data instead of making real API calls
        console.log(`[API STUB] ${method} ${path}`, data);

        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 300));

        // For Phase 2, we'll just work with mock data from Storage
        // Phase 3 will implement actual fetch() calls
        return { success: true, stubbed: true };
    }

    /**
     * Get all reminders (stubbed - returns mock data)
     */
    async function getReminders(filters = {}) {
        console.log('[API STUB] getReminders', filters);
        await new Promise(resolve => setTimeout(resolve, 200));

        const reminders = Storage.getMockData();

        // Apply filters if provided
        let filtered = reminders.filter(r => r.status !== 'completed');

        if (filters.status) {
            filtered = filtered.filter(r => r.status === filters.status);
        }
        if (filters.category) {
            filtered = filtered.filter(r => r.category === filters.category);
        }
        if (filters.priority) {
            filtered = filtered.filter(r => r.priority === filters.priority);
        }

        return filtered;
    }

    /**
     * Get reminder by ID (stubbed - returns from mock data)
     */
    async function getReminder(id) {
        console.log('[API STUB] getReminder', id);
        await new Promise(resolve => setTimeout(resolve, 150));

        const reminders = Storage.getMockData();
        return reminders.find(r => r.id === id) || null;
    }

    /**
     * Create reminder (stubbed - saves to mock data)
     */
    async function createReminder(data) {
        console.log('[API STUB] createReminder', data);
        await new Promise(resolve => setTimeout(resolve, 300));

        const reminders = Storage.getMockData();
        const newReminder = {
            id: `mock-${Date.now()}`,
            text: data.text,
            due_date: data.due_date || null,
            due_time: data.due_time || null,
            priority: data.priority || 'chill',
            category: data.category || null,
            status: 'pending',
            time_required: data.time_required || null,
            location_name: data.location_name || null,
            location_address: data.location_address || null,
            location_lat: data.location_lat || null,
            location_lng: data.location_lng || null,
            location_radius: data.location_radius || null,
            notes: data.notes || null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };

        reminders.push(newReminder);
        Storage.saveMockData(reminders);

        return newReminder;
    }

    /**
     * Update reminder (stubbed - updates mock data)
     */
    async function updateReminder(id, data) {
        console.log('[API STUB] updateReminder', id, data);
        await new Promise(resolve => setTimeout(resolve, 300));

        const reminders = Storage.getMockData();
        const index = reminders.findIndex(r => r.id === id);

        if (index === -1) {
            throw new Error('Reminder not found');
        }

        // Update reminder
        reminders[index] = {
            ...reminders[index],
            ...data,
            updated_at: new Date().toISOString()
        };

        Storage.saveMockData(reminders);
        return reminders[index];
    }

    /**
     * Delete reminder (stubbed - removes from mock data)
     */
    async function deleteReminder(id) {
        console.log('[API STUB] deleteReminder', id);
        await new Promise(resolve => setTimeout(resolve, 200));

        const reminders = Storage.getMockData();
        const filtered = reminders.filter(r => r.id !== id);

        if (filtered.length === reminders.length) {
            throw new Error('Reminder not found');
        }

        Storage.saveMockData(filtered);
        return true;
    }

    /**
     * Complete reminder (update status to completed)
     */
    async function completeReminder(id) {
        console.log('[API STUB] completeReminder', id);
        return updateReminder(id, {
            status: 'completed',
            completed_at: new Date().toISOString()
        });
    }

    /**
     * Get today's reminders (stubbed - filters mock data)
     */
    async function getTodayReminders() {
        console.log('[API STUB] getTodayReminders');
        await new Promise(resolve => setTimeout(resolve, 200));

        const reminders = Storage.getMockData();
        const today = new Date().toISOString().split('T')[0];
        const now = new Date();

        // Return reminders that are:
        // 1. Due today
        // 2. Overdue (due_date < today)
        // 3. No due date (floating tasks)
        // And status is pending

        return reminders.filter(r => {
            if (r.status === 'completed') return false;

            if (!r.due_date) return true; // Floating tasks
            if (r.due_date === today) return true; // Due today
            if (r.due_date < today) return true; // Overdue

            return false;
        }).sort((a, b) => {
            // Sort by priority (urgent > important > chill)
            const priorityOrder = { urgent: 0, important: 1, chill: 2 };
            const priorityDiff = priorityOrder[a.priority] - priorityOrder[b.priority];
            if (priorityDiff !== 0) return priorityDiff;

            // Then by time
            if (a.due_time && b.due_time) {
                return a.due_time.localeCompare(b.due_time);
            }

            // Then by created_at
            return new Date(a.created_at) - new Date(b.created_at);
        });
    }

    /**
     * Get upcoming reminders (next 7 days, stubbed - filters mock data)
     */
    async function getUpcomingReminders() {
        console.log('[API STUB] getUpcomingReminders');
        await new Promise(resolve => setTimeout(resolve, 200));

        const reminders = Storage.getMockData();
        const today = new Date().toISOString().split('T')[0];
        const nextWeek = new Date();
        nextWeek.setDate(nextWeek.getDate() + 7);
        const nextWeekStr = nextWeek.toISOString().split('T')[0];

        return reminders.filter(r => {
            if (r.status === 'completed') return false;
            if (!r.due_date) return false; // Exclude floating tasks
            if (r.due_date <= today) return false; // Exclude today and overdue
            if (r.due_date <= nextWeekStr) return true; // Include next 7 days

            return false;
        }).sort((a, b) => {
            // Sort by due_date first
            const dateDiff = a.due_date.localeCompare(b.due_date);
            if (dateDiff !== 0) return dateDiff;

            // Then by priority
            const priorityOrder = { urgent: 0, important: 1, chill: 2 };
            const priorityDiff = priorityOrder[a.priority] - priorityOrder[b.priority];
            if (priorityDiff !== 0) return priorityDiff;

            // Then by time
            if (a.due_time && b.due_time) {
                return a.due_time.localeCompare(b.due_time);
            }

            return 0;
        });
    }

    /**
     * Health check (stubbed)
     */
    async function healthCheck() {
        console.log('[API STUB] healthCheck');
        await new Promise(resolve => setTimeout(resolve, 100));

        return {
            status: 'ok',
            mode: 'stub',
            message: 'Phase 2: Using mock data from localStorage'
        };
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
        healthCheck
    };
})();

// Make available globally
window.API = API;
