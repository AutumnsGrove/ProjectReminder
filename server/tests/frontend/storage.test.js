/**
 * Frontend Storage Module Tests
 * Tests for public/js/storage.js
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

// Mock fetch for config.json
global.fetch = jest.fn();

// Mock console
global.console = {
  ...console,
  log: jest.fn(),
  warn: jest.fn(),
  error: jest.fn()
};

// Import the Storage module
const fs = require('fs');
const path = require('path');
const storageCode = fs.readFileSync(
  path.join(__dirname, '../../public/js/storage.js'),
  'utf-8'
);
eval(storageCode);

describe('Storage Module', () => {
  beforeEach(() => {
    // Clear the storage
    for (const key in localStorageMock) {
      if (typeof localStorageMock[key] === 'function') {
        localStorageMock[key].mockClear?.();
      }
    }
    localStorageMock.clear();
    fetch.mockClear();
    console.warn.mockClear();
    console.error.mockClear();
  });

  describe('loadConfig()', () => {
    test('should load config from config.json', async () => {
      const mockConfig = {
        api: {
          local_endpoint: 'http://localhost:8000/api',
          cloud_endpoint: 'https://example.com/api',
          use_cloud: false,
          token: 'test-token'
        },
        sync: {
          enabled: true,
          interval_minutes: 5
        }
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig
      });

      const config = await Storage.loadConfig();

      expect(config).toEqual(mockConfig);
      expect(fetch).toHaveBeenCalledWith('config.json');
    });

    test('should merge with localStorage overrides', async () => {
      const mockConfig = {
        api: {
          local_endpoint: 'http://localhost:8000/api',
          use_cloud: false
        }
      };

      const savedOverrides = {
        api: {
          use_cloud: true
        }
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig
      });

      localStorage.getItem.mockReturnValue(JSON.stringify(savedOverrides));

      const config = await Storage.loadConfig();

      expect(config.api.use_cloud).toBe(true);
      expect(config.api.local_endpoint).toBe('http://localhost:8000/api');
    });

    test('should use defaults when config.json fails to load', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 404
      });

      const config = await Storage.loadConfig();

      expect(config).toMatchObject({
        api: expect.objectContaining({
          local_endpoint: expect.any(String),
          use_cloud: false
        })
      });
      expect(console.warn).toHaveBeenCalledWith(
        'Failed to load config.json, using defaults'
      );
    });

    test('should handle network errors', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      const config = await Storage.loadConfig();

      expect(config).toBeDefined();
      expect(console.error).toHaveBeenCalledWith(
        'Error loading config:',
        expect.any(Error)
      );
    });
  });

  describe('saveConfig()', () => {
    test('should save config to localStorage', () => {
      const config = {
        api: {
          local_endpoint: 'http://localhost:8000/api',
          use_cloud: false
        }
      };

      const result = Storage.saveConfig(config);

      expect(result).toBe(true);
      expect(localStorage.setItem).toHaveBeenCalledWith(
        'reminders_config',
        JSON.stringify(config)
      );
    });
  });

  describe('getItem()', () => {
    test('should retrieve and parse JSON from localStorage', () => {
      const mockData = { key: 'value' };
      localStorage.getItem.mockReturnValue(JSON.stringify(mockData));

      const result = Storage.getItem('test_key');

      expect(result).toEqual(mockData);
      expect(localStorage.getItem).toHaveBeenCalledWith('test_key');
    });

    test('should return null when item does not exist', () => {
      localStorage.getItem.mockReturnValue(null);

      const result = Storage.getItem('nonexistent');

      expect(result).toBeNull();
    });

    test('should return null and log error for invalid JSON', () => {
      localStorage.getItem.mockReturnValue('invalid-json{');

      const result = Storage.getItem('invalid_key');

      expect(result).toBeNull();
      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining('Error reading from localStorage'),
        expect.any(Error)
      );
    });
  });

  describe('setItem()', () => {
    test('should store JSON in localStorage', () => {
      const data = { key: 'value' };

      const result = Storage.setItem('test_key', data);

      expect(result).toBe(true);
      expect(localStorage.setItem).toHaveBeenCalledWith(
        'test_key',
        JSON.stringify(data)
      );
    });

    test('should handle localStorage errors', () => {
      localStorage.setItem.mockImplementation(() => {
        throw new Error('QuotaExceededError');
      });

      const result = Storage.setItem('test_key', { data: 'test' });

      expect(result).toBe(false);
      expect(console.error).toHaveBeenCalled();
    });
  });

  describe('removeItem()', () => {
    test('should remove item from localStorage', () => {
      const result = Storage.removeItem('test_key');

      expect(result).toBe(true);
      expect(localStorage.removeItem).toHaveBeenCalledWith('test_key');
    });

    test('should handle removal errors', () => {
      localStorage.removeItem.mockImplementation(() => {
        throw new Error('Storage error');
      });

      const result = Storage.removeItem('test_key');

      expect(result).toBe(false);
      expect(console.error).toHaveBeenCalled();
    });
  });

  describe('clearAll()', () => {
    test('should clear all app data from localStorage', () => {
      const result = Storage.clearAll();

      expect(result).toBe(true);
      expect(localStorage.removeItem).toHaveBeenCalledWith('reminders_config');
      expect(localStorage.removeItem).toHaveBeenCalledWith('reminders_mock_data');
      expect(localStorage.removeItem).toHaveBeenCalledWith('reminders_settings');
    });

    test('should handle clear errors', () => {
      localStorage.removeItem.mockImplementation(() => {
        throw new Error('Storage error');
      });

      const result = Storage.clearAll();

      expect(result).toBe(false);
      expect(console.error).toHaveBeenCalled();
    });
  });

  describe('getMockData()', () => {
    test('should return saved mock data if exists', () => {
      const mockData = [
        { id: '1', text: 'Test reminder 1' },
        { id: '2', text: 'Test reminder 2' }
      ];

      localStorage.getItem.mockReturnValue(JSON.stringify(mockData));

      const result = Storage.getMockData();

      expect(result).toEqual(mockData);
    });

    test('should return default mock data if none saved', () => {
      localStorage.getItem.mockReturnValue(null);

      const result = Storage.getMockData();

      expect(Array.isArray(result)).toBe(true);
      expect(result.length).toBeGreaterThan(0);
      expect(result[0]).toMatchObject({
        id: expect.any(String),
        text: expect.any(String),
        status: 'pending'
      });
    });

    test('should return default if saved data is not an array', () => {
      localStorage.getItem.mockReturnValue(JSON.stringify({ not: 'array' }));

      const result = Storage.getMockData();

      expect(Array.isArray(result)).toBe(true);
      expect(result.length).toBeGreaterThan(0);
    });
  });

  describe('saveMockData()', () => {
    test('should save mock data to localStorage', () => {
      const mockData = [
        { id: '1', text: 'Test reminder' }
      ];

      const result = Storage.saveMockData(mockData);

      expect(result).toBe(true);
      expect(localStorage.setItem).toHaveBeenCalledWith(
        'reminders_mock_data',
        JSON.stringify(mockData)
      );
    });
  });

  describe('getSettings()', () => {
    test('should return saved settings', () => {
      const settings = {
        theme: 'dark',
        notifications: true
      };

      localStorage.getItem.mockReturnValue(JSON.stringify(settings));

      const result = Storage.getSettings();

      expect(result).toEqual(settings);
    });

    test('should return empty object if no settings', () => {
      localStorage.getItem.mockReturnValue(null);

      const result = Storage.getSettings();

      expect(result).toEqual({});
    });
  });

  describe('saveSettings()', () => {
    test('should save settings to localStorage', () => {
      const settings = {
        theme: 'dark',
        notifications: true
      };

      const result = Storage.saveSettings(settings);

      expect(result).toBe(true);
      expect(localStorage.setItem).toHaveBeenCalledWith(
        'reminders_settings',
        JSON.stringify(settings)
      );
    });
  });

  describe('Storage quota handling', () => {
    test('should handle QuotaExceededError gracefully', () => {
      localStorage.setItem.mockImplementation(() => {
        const error = new Error('QuotaExceededError');
        error.name = 'QuotaExceededError';
        throw error;
      });

      const largeData = { data: 'x'.repeat(10000000) }; // Large object
      const result = Storage.setItem('large_key', largeData);

      expect(result).toBe(false);
      expect(console.error).toHaveBeenCalled();
    });
  });
});
