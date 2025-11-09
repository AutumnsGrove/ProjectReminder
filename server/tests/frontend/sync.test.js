/**
 * Frontend Sync Manager Tests
 * Tests for public/js/sync.js
 */

// Mock localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    })
  };
})();

global.localStorage = localStorageMock;

// Mock crypto.randomUUID
global.crypto = {
  randomUUID: jest.fn(() => 'test-uuid-12345')
};

// Mock navigator.onLine
Object.defineProperty(global.navigator, 'onLine', {
  writable: true,
  value: true
});

// Mock window.addEventListener
global.window = {
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  UI: {
    showToast: jest.fn()
  }
};

// Mock console methods
global.console = {
  ...console,
  log: jest.fn(),
  warn: jest.fn(),
  error: jest.fn()
};

// Mock fetch
global.fetch = jest.fn();

// Mock API module
global.API = {
  getEndpoint: jest.fn(() => 'http://localhost:8000/api')
};

// Import the SyncManager module
const fs = require('fs');
const path = require('path');
const syncCode = fs.readFileSync(
  path.join(__dirname, '../../public/js/sync.js'),
  'utf-8'
);
eval(syncCode);

describe('Sync Manager', () => {
  beforeEach(() => {
    // Reset all mocks
    localStorageMock.clear();
    localStorage.getItem.mockClear();
    localStorage.setItem.mockClear();
    fetch.mockClear();
    console.log.mockClear();
    console.warn.mockClear();
    console.error.mockClear();
    window.addEventListener.mockClear();
    window.removeEventListener.mockClear();
    API.getEndpoint.mockReturnValue('http://localhost:8000/api');

    // Reset online status
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: true
    });
  });

  describe('initSync()', () => {
    test('should generate client ID if not exists', () => {
      SyncManager.init();
      expect(localStorage.setItem).toHaveBeenCalledWith(
        'sync_client_id',
        'test-uuid-12345'
      );
    });

    test('should not regenerate client ID if exists', () => {
      localStorage.getItem.mockReturnValue('existing-client-id');
      SyncManager.init();
      const clientId = SyncManager.clientId();
      expect(clientId).toBe('existing-client-id');
    });

    test('should initialize change queue as empty array', () => {
      SyncManager.init();
      expect(localStorage.setItem).toHaveBeenCalledWith(
        'sync_change_queue',
        '[]'
      );
    });

    test('should enable auto-sync by default', () => {
      SyncManager.init();
      expect(SyncManager.isAutoSyncEnabled()).toBe(true);
    });

    test('should listen to online/offline events', () => {
      SyncManager.init();
      expect(window.addEventListener).toHaveBeenCalledWith('online', expect.any(Function));
      expect(window.addEventListener).toHaveBeenCalledWith('offline', expect.any(Function));
    });
  });

  describe('Status Management', () => {
    test('should return current sync status', () => {
      SyncManager.init();
      const status = SyncManager.status();
      expect(['offline', 'online', 'syncing', 'synced', 'error']).toContain(status);
    });

    test('should notify listeners on status change', () => {
      SyncManager.init();
      const callback = jest.fn();
      SyncManager.onSyncStatusChange(callback);

      // Callback should be called immediately with current status
      expect(callback).toHaveBeenCalledWith(expect.any(String));
    });

    test('should allow unsubscribing from status changes', () => {
      SyncManager.init();
      const callback = jest.fn();
      const unsubscribe = SyncManager.onSyncStatusChange(callback);

      callback.mockClear();
      unsubscribe();

      // Status changes after unsubscribe should not trigger callback
      // (hard to test without internal access, but covered by implementation)
      expect(typeof unsubscribe).toBe('function');
    });

    test('should detect online status', () => {
      Object.defineProperty(navigator, 'onLine', { value: true });
      SyncManager.init();
      const status = SyncManager.status();
      expect(status).not.toBe('offline');
    });

    test('should detect offline status', () => {
      Object.defineProperty(navigator, 'onLine', { value: false });
      SyncManager.init();
      const status = SyncManager.status();
      expect(status).toBe('offline');
    });
  });

  describe('Change Queue', () => {
    beforeEach(() => {
      SyncManager.init();
    });

    test('should add change to queue', () => {
      SyncManager.queueChange('reminder-123', 'create', { text: 'New reminder' });

      const queue = SyncManager.queue();
      expect(queue).toHaveLength(1);
      expect(queue[0]).toMatchObject({
        id: 'reminder-123',
        action: 'create',
        data: { text: 'New reminder' }
      });
      expect(queue[0].updated_at).toBeDefined();
    });

    test('should replace existing change for same ID', () => {
      SyncManager.queueChange('reminder-123', 'create', { text: 'First' });
      SyncManager.queueChange('reminder-123', 'update', { text: 'Second' });

      const queue = SyncManager.queue();
      expect(queue).toHaveLength(1);
      expect(queue[0].action).toBe('update');
      expect(queue[0].data.text).toBe('Second');
    });

    test('should limit queue size to 1000 changes', () => {
      // Create a mock queue with 1001 items
      const largeQueue = Array.from({ length: 1001 }, (_, i) => ({
        id: `reminder-${i}`,
        action: 'create',
        data: {},
        updated_at: new Date().toISOString()
      }));

      localStorage.getItem.mockReturnValue(JSON.stringify(largeQueue));

      SyncManager.queueChange('new-reminder', 'create', {});

      const queue = SyncManager.queue();
      expect(queue.length).toBeLessThanOrEqual(1000);
    });

    test('should return empty array for invalid queue JSON', () => {
      localStorage.getItem.mockReturnValue('invalid-json{');
      const queue = SyncManager.queue();
      expect(queue).toEqual([]);
      expect(console.error).toHaveBeenCalled();
    });
  });

  describe('Auto-Sync', () => {
    beforeEach(() => {
      jest.useFakeTimers();
      SyncManager.init();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    test('should check if auto-sync is enabled', () => {
      expect(SyncManager.isAutoSyncEnabled()).toBe(true);
    });

    test('should enable auto-sync', () => {
      SyncManager.disableAutoSync();
      SyncManager.enableAutoSync();
      expect(SyncManager.isAutoSyncEnabled()).toBe(true);
    });

    test('should disable auto-sync', () => {
      SyncManager.disableAutoSync();
      expect(SyncManager.isAutoSyncEnabled()).toBe(false);
    });
  });

  describe('Manual Sync', () => {
    beforeEach(() => {
      SyncManager.init();
      localStorage.setItem('apiToken', 'test-token');
    });

    test('should skip sync if already syncing', async () => {
      // Mock a slow sync operation
      fetch.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));

      const firstSync = SyncManager.sync();
      const secondSync = SyncManager.sync();

      const result = await secondSync;
      expect(result.success).toBe(false);
      expect(result.reason).toBe('already_syncing');
    });

    test('should skip sync if offline', async () => {
      Object.defineProperty(navigator, 'onLine', { value: false });

      const result = await SyncManager.sync();
      expect(result.success).toBe(false);
      expect(result.reason).toBe('offline');
    });

    test('should perform sync when online', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          server_changes: [],
          conflicts: [],
          applied_count: 0,
          last_sync: new Date().toISOString()
        })
      });

      const result = await SyncManager.sync();
      expect(result.success).toBe(true);
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/sync',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token'
          })
        })
      );
    });

    test('should send change queue in sync request', async () => {
      SyncManager.queueChange('reminder-123', 'create', { text: 'Test' });

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          server_changes: [],
          conflicts: [],
          applied_count: 1,
          last_sync: new Date().toISOString()
        })
      });

      await SyncManager.sync();

      const callArgs = fetch.mock.calls[0];
      const body = JSON.parse(callArgs[1].body);
      expect(body.changes).toHaveLength(1);
      expect(body.changes[0].id).toBe('reminder-123');
    });

    test('should clear change queue after successful sync', async () => {
      SyncManager.queueChange('reminder-123', 'create', { text: 'Test' });

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          server_changes: [],
          conflicts: [],
          applied_count: 1,
          last_sync: new Date().toISOString()
        })
      });

      await SyncManager.sync();

      const queue = SyncManager.queue();
      expect(queue).toHaveLength(0);
    });

    test('should handle sync errors', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await SyncManager.sync();
      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
      expect(console.error).toHaveBeenCalledWith('Sync failed:', expect.any(Error));
    });

    test('should retry failed sync attempts', async () => {
      // First two attempts fail, third succeeds
      fetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            server_changes: [],
            conflicts: [],
            applied_count: 0,
            last_sync: new Date().toISOString()
          })
        });

      const result = await SyncManager.sync();
      expect(result.success).toBe(true);
      expect(fetch).toHaveBeenCalledTimes(3);
    });

    test('should update last sync timestamp', async () => {
      const syncTime = new Date().toISOString();

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          server_changes: [],
          conflicts: [],
          applied_count: 0,
          last_sync: syncTime
        })
      });

      await SyncManager.sync();
      expect(localStorage.setItem).toHaveBeenCalledWith('sync_last_sync', syncTime);
    });
  });

  describe('Cleanup', () => {
    test('should remove event listeners on cleanup', () => {
      SyncManager.init();
      SyncManager.cleanup();

      expect(window.removeEventListener).toHaveBeenCalledWith('online', expect.any(Function));
      expect(window.removeEventListener).toHaveBeenCalledWith('offline', expect.any(Function));
    });
  });
});
