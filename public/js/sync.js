/**
 * Sync Manager Module
 *
 * Handles bidirectional synchronization between local and cloud storage.
 *
 * Features:
 * - Local change tracking with queue
 * - Background auto-sync (every 5 minutes)
 * - Manual sync trigger
 * - Last-write-wins conflict resolution
 * - Network error handling with retry logic
 * - Sync status management
 *
 * Phase 5: Sync Logic Implementation
 */

const SyncManager = (function() {
    'use strict';

    // =============================================================================
    // Constants
    // =============================================================================

    const SYNC_INTERVAL = 5 * 60 * 1000; // 5 minutes
    const MAX_RETRY_ATTEMPTS = 3;
    const RETRY_DELAY = 2000; // 2 seconds
    const STORAGE_KEYS = {
        CLIENT_ID: 'sync_client_id',
        LAST_SYNC: 'sync_last_sync',
        CHANGE_QUEUE: 'sync_change_queue',
        SYNC_STATUS: 'sync_status',
        AUTO_SYNC_ENABLED: 'sync_auto_enabled'
    };

    // =============================================================================
    // State
    // =============================================================================

    let syncTimer = null;
    let isSyncing = false;
    let statusCallbacks = [];

    // Sync status: 'offline', 'online', 'syncing', 'synced', 'error'
    let currentStatus = 'offline';

    // =============================================================================
    // Initialization
    // =============================================================================

    /**
     * Initialize sync manager
     */
    function initSync() {
        // Generate or retrieve client ID
        if (!localStorage.getItem(STORAGE_KEYS.CLIENT_ID)) {
            localStorage.setItem(STORAGE_KEYS.CLIENT_ID, crypto.randomUUID());
        }

        // Initialize change queue if not exists
        if (!localStorage.getItem(STORAGE_KEYS.CHANGE_QUEUE)) {
            localStorage.setItem(STORAGE_KEYS.CHANGE_QUEUE, JSON.stringify([]));
        }

        // Enable auto-sync by default
        if (localStorage.getItem(STORAGE_KEYS.AUTO_SYNC_ENABLED) === null) {
            localStorage.setItem(STORAGE_KEYS.AUTO_SYNC_ENABLED, 'true');
        }

        // Detect online/offline status
        updateConnectionStatus();

        // Listen to online/offline events
        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        // Start auto-sync if enabled
        if (isAutoSyncEnabled()) {
            startAutoSync();
        }

        console.log('Sync manager initialized', {
            clientId: getClientId(),
            autoSync: isAutoSyncEnabled(),
            status: currentStatus
        });
    }

    /**
     * Cleanup sync manager
     */
    function cleanupSync() {
        stopAutoSync();
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
    }

    // =============================================================================
    // Status Management
    // =============================================================================

    /**
     * Get current sync status
     */
    function getSyncStatus() {
        return currentStatus;
    }

    /**
     * Subscribe to sync status changes
     */
    function onSyncStatusChange(callback) {
        statusCallbacks.push(callback);
        // Immediately call with current status
        callback(currentStatus);

        // Return unsubscribe function
        return () => {
            statusCallbacks = statusCallbacks.filter(cb => cb !== callback);
        };
    }

    /**
     * Update sync status and notify listeners
     */
    function setStatus(newStatus) {
        if (currentStatus !== newStatus) {
            currentStatus = newStatus;
            localStorage.setItem(STORAGE_KEYS.SYNC_STATUS, newStatus);

            // Notify all listeners
            statusCallbacks.forEach(callback => callback(newStatus));

            console.log('Sync status changed:', newStatus);
        }
    }

    /**
     * Update connection status based on navigator.onLine
     */
    function updateConnectionStatus() {
        if (navigator.onLine) {
            if (currentStatus === 'offline') {
                setStatus('online');
            }
        } else {
            setStatus('offline');
        }
    }

    /**
     * Handle online event
     */
    function handleOnline() {
        console.log('Network online detected');
        setStatus('online');

        // Trigger immediate sync
        if (isAutoSyncEnabled()) {
            syncNow();
        }
    }

    /**
     * Handle offline event
     */
    function handleOffline() {
        console.log('Network offline detected');
        setStatus('offline');
    }

    // =============================================================================
    // Auto-Sync Management
    // =============================================================================

    /**
     * Check if auto-sync is enabled
     */
    function isAutoSyncEnabled() {
        return localStorage.getItem(STORAGE_KEYS.AUTO_SYNC_ENABLED) === 'true';
    }

    /**
     * Enable auto-sync
     */
    function enableAutoSync() {
        localStorage.setItem(STORAGE_KEYS.AUTO_SYNC_ENABLED, 'true');
        startAutoSync();
    }

    /**
     * Disable auto-sync
     */
    function disableAutoSync() {
        localStorage.setItem(STORAGE_KEYS.AUTO_SYNC_ENABLED, 'false');
        stopAutoSync();
    }

    /**
     * Start auto-sync timer
     */
    function startAutoSync() {
        if (syncTimer) return; // Already running

        console.log('Starting auto-sync timer (5 min intervals)');

        syncTimer = setInterval(() => {
            if (navigator.onLine && !isSyncing) {
                syncNow();
            }
        }, SYNC_INTERVAL);

        // Initial sync after 10 seconds
        setTimeout(() => {
            if (navigator.onLine && !isSyncing) {
                syncNow();
            }
        }, 10000);
    }

    /**
     * Stop auto-sync timer
     */
    function stopAutoSync() {
        if (syncTimer) {
            clearInterval(syncTimer);
            syncTimer = null;
            console.log('Auto-sync timer stopped');
        }
    }

    // =============================================================================
    // Change Queue Management
    // =============================================================================

    /**
     * Get client ID
     */
    function getClientId() {
        return localStorage.getItem(STORAGE_KEYS.CLIENT_ID);
    }

    /**
     * Get last sync timestamp
     */
    function getLastSync() {
        return localStorage.getItem(STORAGE_KEYS.LAST_SYNC);
    }

    /**
     * Set last sync timestamp
     */
    function setLastSync(timestamp) {
        localStorage.setItem(STORAGE_KEYS.LAST_SYNC, timestamp);
    }

    /**
     * Get change queue
     */
    function getChangeQueue() {
        try {
            const queue = localStorage.getItem(STORAGE_KEYS.CHANGE_QUEUE);
            return queue ? JSON.parse(queue) : [];
        } catch (error) {
            console.error('Failed to parse change queue:', error);
            return [];
        }
    }

    /**
     * Set change queue
     */
    function setChangeQueue(queue) {
        // Limit queue size to 1000 changes
        if (queue.length > 1000) {
            console.warn('Change queue size limit reached, keeping latest 1000 changes');
            queue = queue.slice(-1000);
        }

        localStorage.setItem(STORAGE_KEYS.CHANGE_QUEUE, JSON.stringify(queue));
    }

    /**
     * Add change to queue
     */
    function queueChange(id, action, data = null) {
        const queue = getChangeQueue();

        // Remove any existing changes for this ID
        const filteredQueue = queue.filter(change => change.id !== id);

        // Add new change
        const change = {
            id,
            action,
            data,
            updated_at: new Date().toISOString()
        };

        filteredQueue.push(change);
        setChangeQueue(filteredQueue);

        console.log('Change queued:', change);
    }

    /**
     * Clear change queue
     */
    function clearChangeQueue() {
        setChangeQueue([]);
    }

    // =============================================================================
    // Manual Sync Trigger
    // =============================================================================

    /**
     * Trigger sync manually
     * Returns Promise that resolves when sync is complete
     */
    async function syncNow() {
        // Check if already syncing
        if (isSyncing) {
            console.log('Sync already in progress, skipping');
            return { success: false, reason: 'already_syncing' };
        }

        // Check if online
        if (!navigator.onLine) {
            console.log('Cannot sync: offline');
            setStatus('offline');
            return { success: false, reason: 'offline' };
        }

        // Start sync
        isSyncing = true;
        setStatus('syncing');

        try {
            const result = await performSync();
            setStatus('synced');

            // Update last synced timestamp display
            setLastSync(result.last_sync);

            return { success: true, result };
        } catch (error) {
            console.error('Sync failed:', error);
            setStatus('error');
            return { success: false, error: error.message };
        } finally {
            isSyncing = false;
        }
    }

    // =============================================================================
    // Sync Logic
    // =============================================================================

    /**
     * Perform bidirectional sync with retry logic
     */
    async function performSync(retryAttempt = 0) {
        try {
            console.log('Starting sync...', {
                clientId: getClientId(),
                lastSync: getLastSync(),
                queuedChanges: getChangeQueue().length
            });

            // Build sync request
            const syncRequest = {
                client_id: getClientId(),
                last_sync: getLastSync(),
                changes: getChangeQueue()
            };

            // Call sync API endpoint
            const apiUrl = API.getEndpoint().replace('/api', '');

            // Get token from API module's getAuthToken function
            const apiToken = API.getAuthToken ? API.getAuthToken() : null;

            if (!apiToken) {
                throw new Error('API token not configured');
            }

            const response = await fetch(`${apiUrl}/api/sync`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiToken}`
                },
                body: JSON.stringify(syncRequest)
            });

            if (!response.ok) {
                throw new Error(`Sync API returned ${response.status}: ${response.statusText}`);
            }

            const syncResponse = await response.json();

            console.log('Sync response received:', {
                serverChanges: syncResponse.server_changes.length,
                conflicts: syncResponse.conflicts.length,
                appliedCount: syncResponse.applied_count
            });

            // Apply server changes to local display (refresh page)
            if (syncResponse.server_changes.length > 0) {
                console.log('Server changes detected, page will refresh automatically');
                // The UI will reload reminders from API automatically on next render
            }

            // Clear change queue (all changes have been applied)
            clearChangeQueue();

            // Report conflicts to user (if any)
            if (syncResponse.conflicts.length > 0) {
                console.warn('Sync conflicts detected:', syncResponse.conflicts);
                // Show toast notification
                if (window.UI && window.UI.showToast) {
                    window.UI.showToast(`${syncResponse.conflicts.length} sync conflicts resolved`, 'warning');
                }
            }

            return syncResponse;

        } catch (error) {
            // Retry logic
            if (retryAttempt < MAX_RETRY_ATTEMPTS) {
                console.warn(`Sync attempt ${retryAttempt + 1} failed, retrying in ${RETRY_DELAY}ms...`);
                await new Promise(resolve => setTimeout(resolve, RETRY_DELAY * (retryAttempt + 1)));
                return performSync(retryAttempt + 1);
            }

            throw error;
        }
    }

    // =============================================================================
    // Public API
    // =============================================================================

    return {
        init: initSync,
        cleanup: cleanupSync,
        status: getSyncStatus,
        sync: syncNow,
        queueChange: queueChange,
        queue: getChangeQueue,
        lastSync: getLastSync,
        clientId: getClientId,
        enableAutoSync,
        disableAutoSync,
        isAutoSyncEnabled,
        onSyncStatusChange
    };
})();

// Make available globally
window.SyncManager = SyncManager;
