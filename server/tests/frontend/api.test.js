/**
 * Frontend API Client Tests
 * Tests for public/js/api.js
 */

// Mock global fetch
global.fetch = jest.fn();

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

// Mock window.SyncManager
global.window = {
  SyncManager: {
    queueChange: jest.fn()
  }
};

// Mock error handlers (from errors.js)
global.showError = jest.fn();
global.showSuccess = jest.fn();
global.formatErrorMessage = jest.fn((error) => {
  if (typeof error === 'string') return error;
  if (error.message) return error.message;
  return 'Unknown error';
});
global.fetchWithRetry = jest.fn((url, options) => fetch(url, options));
global.safeJsonParse = jest.fn((response) => response.json());

// Mock Storage module
global.Storage = {
  loadConfig: jest.fn(() => Promise.resolve({
    api: {
      local_endpoint: 'http://localhost:8000/api',
      cloud_endpoint: 'https://example.com/api',
      use_cloud: false,
      token: 'test-token-123'
    }
  }))
};

// Import the API module (as IIFE)
const fs = require('fs');
const path = require('path');
const apiCode = fs.readFileSync(
  path.join(__dirname, '../../public/js/api.js'),
  'utf-8'
);
eval(apiCode);

describe('API Client', () => {
  beforeEach(() => {
    fetch.mockClear();
    for (const key in localStorageMock) {
      if (typeof localStorageMock[key] === 'function') {
        localStorageMock[key].mockClear?.();
      }
    }
    localStorageMock.clear();
    showError.mockClear();
    showSuccess.mockClear();
    formatErrorMessage.mockClear();
    fetchWithRetry.mockClear();
    safeJsonParse.mockClear();
    window.SyncManager.queueChange.mockClear();

    // Reset fetch mock to pass through to fetchWithRetry
    fetchWithRetry.mockImplementation((url, options) => fetch(url, options));
    safeJsonParse.mockImplementation((response) => response.json());
  });

  describe('init()', () => {
    test('should initialize API with config from Storage', async () => {
      await API.init();
      expect(Storage.loadConfig).toHaveBeenCalled();
    });
  });

  describe('getEndpoint()', () => {
    test('should return local endpoint when use_cloud is false', async () => {
      await API.init();
      const endpoint = API.getEndpoint();
      expect(endpoint).toBe('http://localhost:8000/api');
    });

    test('should fallback to localStorage config if not initialized', () => {
      localStorage.getItem.mockReturnValue(JSON.stringify({
        api: {
          local_endpoint: 'http://fallback:8000/api',
          use_cloud: false
        }
      }));

      const endpoint = API.getEndpoint();
      expect(endpoint).toBe('http://fallback:8000/api');
    });
  });

  describe('getReminders()', () => {
    test('should return array of reminders on success', async () => {
      const mockReminders = [
        { id: '1', text: 'Test reminder 1' },
        { id: '2', text: 'Test reminder 2' }
      ];

      fetchWithRetry.mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: async () => ({ data: mockReminders })
      });

      await API.init();
      const result = await API.getReminders();

      expect(result).toEqual(mockReminders);
      expect(fetchWithRetry).toHaveBeenCalledWith(
        'http://localhost:8000/api/reminders',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token-123'
          })
        })
      );
    });

    test('should handle network error', async () => {
      fetchWithRetry.mockRejectedValueOnce(new Error('Network error'));
      formatErrorMessage.mockReturnValue('Network error');

      await API.init();

      await expect(API.getReminders()).rejects.toThrow('Network error');
      expect(showError).toHaveBeenCalledWith('Failed to load reminders: Network error');
    });

    test('should include filters in query string', async () => {
      fetchWithRetry.mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: async () => ({ data: [] })
      });

      await API.init();
      await API.getReminders({ status: 'pending', priority: 'urgent' });

      expect(fetchWithRetry).toHaveBeenCalledWith(
        'http://localhost:8000/api/reminders?status=pending&priority=urgent',
        expect.any(Object)
      );
    });

    test('should return empty array when data is missing', async () => {
      fetchWithRetry.mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: async () => ({})
      });

      await API.init();
      const result = await API.getReminders();

      expect(result).toEqual([]);
    });
  });

  describe('getReminder()', () => {
    test('should return reminder by ID', async () => {
      const mockReminder = { id: '123', text: 'Test reminder' };

      fetchWithRetry.mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: async () => mockReminder
      });

      await API.init();
      const result = await API.getReminder('123');

      expect(result).toEqual(mockReminder);
      expect(fetchWithRetry).toHaveBeenCalledWith(
        'http://localhost:8000/api/reminders/123',
        expect.any(Object)
      );
    });

    test('should return null for 404 errors', async () => {
      const error = new Error('Not found');
      error.status = 404;
      fetchWithRetry.mockRejectedValueOnce(error);

      await API.init();
      const result = await API.getReminder('nonexistent');

      expect(result).toBeNull();
    });
  });

  describe('createReminder()', () => {
    test('should send correct payload and include auth header', async () => {
      const mockReminder = {
        id: '123',
        text: 'New reminder',
        priority: 'important'
      };

      fetchWithRetry.mockResolvedValueOnce({
        status: 201,
        ok: true,
        json: async () => mockReminder
      });

      await API.init();
      const result = await API.createReminder({
        text: 'New reminder',
        priority: 'important'
      });

      expect(result).toEqual(mockReminder);
      expect(fetchWithRetry).toHaveBeenCalledWith(
        'http://localhost:8000/api/reminders',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token-123'
          }),
          body: expect.any(String)
        })
      );
      expect(showSuccess).toHaveBeenCalledWith('Reminder created!');
      expect(window.SyncManager.queueChange).toHaveBeenCalledWith(
        '123',
        'create',
        mockReminder
      );
    });

    test('should normalize time format (HH:MM -> HH:MM:SS)', async () => {
      fetchWithRetry.mockResolvedValueOnce({
        status: 201,
        ok: true,
        json: async () => ({ id: '123' })
      });

      await API.init();
      await API.createReminder({
        text: 'Test',
        due_time: '14:30'
      });

      const callArgs = fetchWithRetry.mock.calls[0];
      const body = JSON.parse(callArgs[1].body);
      expect(body.due_time).toBe('14:30:00');
    });
  });

  describe('updateReminder()', () => {
    test('should update existing reminder', async () => {
      const mockUpdated = {
        id: '123',
        text: 'Updated reminder',
        priority: 'urgent'
      };

      fetchWithRetry.mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: async () => mockUpdated
      });

      await API.init();
      const result = await API.updateReminder('123', {
        text: 'Updated reminder',
        priority: 'urgent'
      });

      expect(result).toEqual(mockUpdated);
      expect(fetchWithRetry).toHaveBeenCalledWith(
        'http://localhost:8000/api/reminders/123',
        expect.objectContaining({
          method: 'PATCH'
        })
      );
      expect(showSuccess).toHaveBeenCalledWith('Reminder updated!');
    });
  });

  describe('deleteReminder()', () => {
    test('should delete reminder and return null', async () => {
      fetchWithRetry.mockResolvedValueOnce({
        status: 204,
        ok: true
      });
      safeJsonParse.mockResolvedValueOnce(null);

      await API.init();
      const result = await API.deleteReminder('123');

      expect(result).toBeNull();
      expect(fetchWithRetry).toHaveBeenCalledWith(
        'http://localhost:8000/api/reminders/123',
        expect.objectContaining({
          method: 'DELETE'
        })
      );
      expect(showSuccess).toHaveBeenCalledWith('Reminder deleted!');
      expect(window.SyncManager.queueChange).toHaveBeenCalledWith(
        '123',
        'delete',
        null
      );
    });
  });

  describe('completeReminder()', () => {
    test('should update status to completed', async () => {
      const mockCompleted = {
        id: '123',
        status: 'completed',
        completed_at: '2025-11-04T12:00:00Z'
      };

      fetchWithRetry.mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: async () => mockCompleted
      });

      await API.init();
      const result = await API.completeReminder('123');

      expect(result).toEqual(mockCompleted);
      const callArgs = fetchWithRetry.mock.calls[0];
      const body = JSON.parse(callArgs[1].body);
      expect(body).toEqual({ status: 'completed' });
      expect(showSuccess).toHaveBeenCalledWith('Reminder completed!');
    });
  });

  describe('getNearbyReminders()', () => {
    test('should query location endpoint with coordinates', async () => {
      const mockNearby = [
        { id: '1', text: 'Grocery store', location_lat: 40.0, location_lng: -74.0 }
      ];

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: mockNearby })
      });

      await API.init();
      const result = await API.getNearbyReminders(40.0, -74.0, 500);

      expect(result).toEqual(mockNearby);
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/reminders/near-location?lat=40&lng=-74&radius=500',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token-123'
          })
        })
      );
    });
  });

  describe('healthCheck()', () => {
    test('should return health status', async () => {
      const mockHealth = {
        status: 'healthy',
        database: 'connected',
        timestamp: '2025-11-04T12:00:00Z'
      };

      fetchWithRetry.mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: async () => mockHealth
      });

      await API.init();
      const result = await API.healthCheck();

      expect(result).toEqual(mockHealth);
      expect(fetchWithRetry).toHaveBeenCalledWith(
        'http://localhost:8000/api/health',
        expect.any(Object)
      );
    });
  });

  describe('Error handling', () => {
    test('should handle 401 Unauthorized', async () => {
      const error = new Error('Unauthorized');
      error.status = 401;
      fetchWithRetry.mockRejectedValueOnce(error);
      formatErrorMessage.mockReturnValue('Unauthorized');

      await API.init();

      await expect(API.getReminders()).rejects.toThrow();
      expect(showError).toHaveBeenCalled();
    });

    test('should handle 500 Internal Server Error', async () => {
      const error = new Error('Internal Server Error');
      error.status = 500;
      fetchWithRetry.mockRejectedValueOnce(error);
      formatErrorMessage.mockReturnValue('Internal Server Error');

      await API.init();

      await expect(API.getReminders()).rejects.toThrow();
      expect(showError).toHaveBeenCalled();
    });
  });
});
