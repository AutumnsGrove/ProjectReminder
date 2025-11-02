/**
 * Storage Module - LocalStorage Helpers
 * Handles settings and mock data persistence
 */

const Storage = (function() {
    'use strict';

    const KEYS = {
        CONFIG: 'reminders_config',
        MOCK_DATA: 'reminders_mock_data',
        SETTINGS: 'reminders_settings'
    };

    /**
     * Load configuration from config.json
     */
    async function loadConfig() {
        try {
            const response = await fetch('config.json');
            if (!response.ok) {
                console.warn('Failed to load config.json, using defaults');
                return getDefaultConfig();
            }
            const config = await response.json();
            // Merge with localStorage overrides
            const savedConfig = getItem(KEYS.CONFIG);
            return savedConfig ? { ...config, ...savedConfig } : config;
        } catch (error) {
            console.error('Error loading config:', error);
            return getDefaultConfig();
        }
    }

    /**
     * Get default configuration
     */
    function getDefaultConfig() {
        return {
            api: {
                local_endpoint: 'http://localhost:8000/api',
                cloud_endpoint: '',
                use_cloud: false,
                token: ''
            },
            sync: {
                enabled: false,
                interval_minutes: 5
            },
            ui: {
                theme: 'light',
                animations_enabled: true
            },
            location: {
                enabled: false,
                mapbox_token: ''
            }
        };
    }

    /**
     * Save configuration to localStorage
     */
    function saveConfig(config) {
        return setItem(KEYS.CONFIG, config);
    }

    /**
     * Get item from localStorage
     */
    function getItem(key) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (error) {
            console.error(`Error reading from localStorage (${key}):`, error);
            return null;
        }
    }

    /**
     * Set item in localStorage
     */
    function setItem(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error(`Error writing to localStorage (${key}):`, error);
            return false;
        }
    }

    /**
     * Remove item from localStorage
     */
    function removeItem(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error(`Error removing from localStorage (${key}):`, error);
            return false;
        }
    }

    /**
     * Clear all app data from localStorage
     */
    function clearAll() {
        try {
            Object.values(KEYS).forEach(key => {
                localStorage.removeItem(key);
            });
            return true;
        } catch (error) {
            console.error('Error clearing localStorage:', error);
            return false;
        }
    }

    /**
     * Get mock reminders data
     */
    function getMockData() {
        const saved = getItem(KEYS.MOCK_DATA);
        if (saved && Array.isArray(saved)) {
            return saved;
        }
        // Return default mock data
        return getDefaultMockData();
    }

    /**
     * Save mock reminders data
     */
    function saveMockData(reminders) {
        return setItem(KEYS.MOCK_DATA, reminders);
    }

    /**
     * Get default mock data for Phase 2
     */
    function getDefaultMockData() {
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        const nextWeek = new Date(today);
        nextWeek.setDate(nextWeek.getDate() + 7);

        return [
            {
                id: 'mock-1',
                text: 'Call mom about Thanksgiving',
                due_date: today.toISOString().split('T')[0],
                due_time: '15:00',
                priority: 'important',
                category: 'Calls',
                status: 'pending',
                time_required: 30,
                location_name: null,
                notes: null,
                created_at: now.toISOString(),
                updated_at: now.toISOString()
            },
            {
                id: 'mock-2',
                text: 'Buy groceries',
                due_date: today.toISOString().split('T')[0],
                due_time: null,
                priority: 'chill',
                category: 'Shopping',
                status: 'pending',
                time_required: 60,
                location_name: 'Kroger',
                notes: 'Milk, eggs, bread',
                created_at: now.toISOString(),
                updated_at: now.toISOString()
            },
            {
                id: 'mock-3',
                text: 'Submit project report',
                due_date: tomorrow.toISOString().split('T')[0],
                due_time: '17:00',
                priority: 'urgent',
                category: 'Work',
                status: 'pending',
                time_required: 120,
                location_name: null,
                notes: 'Final deadline - no extensions',
                created_at: now.toISOString(),
                updated_at: now.toISOString()
            },
            {
                id: 'mock-4',
                text: 'Dentist appointment',
                due_date: nextWeek.toISOString().split('T')[0],
                due_time: '10:00',
                priority: 'important',
                category: 'Health',
                status: 'pending',
                time_required: 60,
                location_name: 'Dr. Smith Dental',
                notes: 'Remember to bring insurance card',
                created_at: now.toISOString(),
                updated_at: now.toISOString()
            },
            {
                id: 'mock-5',
                text: 'Review code PR #123',
                due_date: null,
                due_time: null,
                priority: 'chill',
                category: 'Work',
                status: 'pending',
                time_required: 30,
                location_name: null,
                notes: 'Anytime task',
                created_at: now.toISOString(),
                updated_at: now.toISOString()
            }
        ];
    }

    /**
     * Get settings
     */
    function getSettings() {
        return getItem(KEYS.SETTINGS) || {};
    }

    /**
     * Save settings
     */
    function saveSettings(settings) {
        return setItem(KEYS.SETTINGS, settings);
    }

    // Public API
    return {
        loadConfig,
        saveConfig,
        getMockData,
        saveMockData,
        getSettings,
        saveSettings,
        getItem,
        setItem,
        removeItem,
        clearAll,
        KEYS
    };
})();

// Make available globally
window.Storage = Storage;
