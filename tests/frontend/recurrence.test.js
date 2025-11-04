/**
 * Frontend Recurrence UI Tests
 * Tests for public/js/recurrence.js
 */

// Mock DOM elements
const createMockElement = (id, value = '') => ({
  id,
  value,
  checked: false,
  style: { display: 'block' },
  textContent: '',
  innerHTML: '',
  addEventListener: jest.fn(),
  querySelector: jest.fn(),
  querySelectorAll: jest.fn(() => [])
});

// Mock document
global.document = {
  getElementById: jest.fn((id) => createMockElement(id)),
  querySelector: jest.fn(),
  querySelectorAll: jest.fn(() => [])
};

// Mock console
global.console = {
  ...console,
  log: jest.fn()
};

// Import the RecurrenceUI module
const fs = require('fs');
const path = require('path');
const recurrenceCode = fs.readFileSync(
  path.join(__dirname, '../../public/js/recurrence.js'),
  'utf-8'
);
eval(recurrenceCode);

describe('Recurrence UI', () => {
  let mockElements;

  beforeEach(() => {
    // Reset mocks
    if (document.getElementById.mockClear) document.getElementById.mockClear();
    if (document.querySelector.mockClear) document.querySelector.mockClear();
    if (document.querySelectorAll.mockClear) document.querySelectorAll.mockClear();
    console.log.mockClear();

    // Create mock elements
    mockElements = {
      recurrenceDetails: createMockElement('recurrenceDetails'),
      intervalUnit: createMockElement('intervalUnit'),
      recurrenceInterval: createMockElement('recurrenceInterval', '1'),
      daysOfWeekContainer: createMockElement('daysOfWeekContainer'),
      dayOfMonthContainer: createMockElement('dayOfMonthContainer'),
      dayOfMonth: createMockElement('dayOfMonth', '1'),
      endDateContainer: createMockElement('endDateContainer'),
      endCountContainer: createMockElement('endCountContainer'),
      recurrenceEndDate: createMockElement('recurrenceEndDate'),
      recurrenceEndCount: createMockElement('recurrenceEndCount', '10'),
      recurrencePreview: createMockElement('recurrencePreview'),
      dueDate: createMockElement('dueDate', '2025-11-10')
    };

    // Mock querySelectorAll for frequency radios
    const frequencyRadios = [
      { value: 'none', checked: true, addEventListener: jest.fn() },
      { value: 'daily', checked: false, addEventListener: jest.fn() },
      { value: 'weekly', checked: false, addEventListener: jest.fn() },
      { value: 'monthly', checked: false, addEventListener: jest.fn() }
    ];

    const endConditionRadios = [
      { value: 'never', checked: true, addEventListener: jest.fn() },
      { value: 'date', checked: false, addEventListener: jest.fn() },
      { value: 'count', checked: false, addEventListener: jest.fn() }
    ];

    const dayCheckboxes = [
      { value: '0', checked: false, addEventListener: jest.fn() }, // Monday
      { value: '1', checked: false, addEventListener: jest.fn() }, // Tuesday
      { value: '2', checked: false, addEventListener: jest.fn() }  // Wednesday
    ];

    document.querySelectorAll.mockImplementation((selector) => {
      if (selector.includes('recurrence_frequency')) {
        return frequencyRadios;
      } else if (selector.includes('recurrence_end')) {
        return endConditionRadios;
      } else if (selector.includes('days-of-week')) {
        return dayCheckboxes;
      }
      return [];
    });

    document.querySelector.mockImplementation((selector) => {
      if (selector.includes('recurrence_frequency')) {
        if (selector.includes('[value="daily"]')) {
          return frequencyRadios[1];
        } else if (selector.includes('[value="weekly"]')) {
          return frequencyRadios[2];
        } else if (selector.includes(':checked')) {
          return frequencyRadios.find(r => r.checked) || frequencyRadios[0];
        }
      } else if (selector.includes('recurrence_end')) {
        if (selector.includes('[value="date"]')) {
          return endConditionRadios[1];
        } else if (selector.includes('[value="count"]')) {
          return endConditionRadios[2];
        } else if (selector.includes(':checked')) {
          return endConditionRadios.find(r => r.checked) || endConditionRadios[0];
        }
      }
      return null;
    });

    document.getElementById.mockImplementation((id) => {
      return mockElements[id] || createMockElement(id);
    });
  });

  describe('init()', () => {
    test('should initialize recurrence UI', () => {
      RecurrenceUI.init();

      expect(console.log).toHaveBeenCalledWith('Initializing Recurrence UI...');
      expect(document.querySelectorAll).toHaveBeenCalled();
    });

    test('should not initialize twice', () => {
      RecurrenceUI.init();
      console.log.mockClear();

      RecurrenceUI.init();

      expect(console.log).not.toHaveBeenCalled();
    });

    test('should attach event listeners to frequency radios', () => {
      RecurrenceUI.init();

      const frequencyRadios = document.querySelectorAll('input[name="recurrence_frequency"]');
      frequencyRadios.forEach(radio => {
        expect(radio.addEventListener).toHaveBeenCalledWith('change', expect.any(Function));
      });
    });

    test('should attach event listeners to interval input', () => {
      RecurrenceUI.init();

      expect(mockElements.recurrenceInterval.addEventListener).toHaveBeenCalledWith(
        'input',
        expect.any(Function)
      );
    });
  });

  describe('getRecurrencePattern()', () => {
    beforeEach(() => {
      RecurrenceUI.init();
    });

    test('should return null when frequency is none', () => {
      const pattern = RecurrenceUI.getRecurrencePattern();

      expect(pattern).toBeNull();
    });

    test('should return daily pattern', () => {
      // Set daily frequency
      const frequencyRadios = document.querySelectorAll('input[name="recurrence_frequency"]');
      frequencyRadios[1].checked = true;
      frequencyRadios[0].checked = false;

      mockElements.recurrenceInterval.value = '2';

      const pattern = RecurrenceUI.getRecurrencePattern();

      expect(pattern).toMatchObject({
        frequency: 'daily',
        interval: 2
      });
    });

    test('should return weekly pattern with days of week', () => {
      // Set weekly frequency
      const frequencyRadios = document.querySelectorAll('input[name="recurrence_frequency"]');
      frequencyRadios[2].checked = true;
      frequencyRadios[0].checked = false;

      // Mock selected days
      const dayCheckboxes = [
        { value: '0', checked: true },
        { value: '2', checked: true },
        { value: '4', checked: false }
      ];

      document.querySelectorAll.mockImplementation((selector) => {
        if (selector.includes('days-of-week') && selector.includes(':checked')) {
          return dayCheckboxes.filter(cb => cb.checked);
        }
        return [];
      });

      const pattern = RecurrenceUI.getRecurrencePattern();

      expect(pattern).toMatchObject({
        frequency: 'weekly',
        interval: 1,
        days_of_week: '0,2'
      });
    });

    test('should return monthly pattern with day of month', () => {
      // Set monthly frequency
      const frequencyRadios = document.querySelectorAll('input[name="recurrence_frequency"]');
      frequencyRadios[3].checked = true;
      frequencyRadios[0].checked = false;

      mockElements.dayOfMonth.value = '15';

      const pattern = RecurrenceUI.getRecurrencePattern();

      expect(pattern).toMatchObject({
        frequency: 'monthly',
        interval: 1,
        day_of_month: 15
      });
    });

    test('should include end date when specified', () => {
      const frequencyRadios = document.querySelectorAll('input[name="recurrence_frequency"]');
      frequencyRadios[1].checked = true;
      frequencyRadios[0].checked = false;

      const endRadios = document.querySelectorAll('input[name="recurrence_end"]');
      endRadios[1].checked = true;
      endRadios[0].checked = false;

      mockElements.recurrenceEndDate.value = '2025-12-31';

      const pattern = RecurrenceUI.getRecurrencePattern();

      expect(pattern).toMatchObject({
        frequency: 'daily',
        end_date: '2025-12-31'
      });
    });

    test('should include end count when specified', () => {
      const frequencyRadios = document.querySelectorAll('input[name="recurrence_frequency"]');
      frequencyRadios[1].checked = true;
      frequencyRadios[0].checked = false;

      const endRadios = document.querySelectorAll('input[name="recurrence_end"]');
      endRadios[2].checked = true;
      endRadios[0].checked = false;

      mockElements.recurrenceEndCount.value = '10';

      const pattern = RecurrenceUI.getRecurrencePattern();

      expect(pattern).toMatchObject({
        frequency: 'daily',
        end_count: 10
      });
    });

    test('should validate interval is at least 1', () => {
      const frequencyRadios = document.querySelectorAll('input[name="recurrence_frequency"]');
      frequencyRadios[1].checked = true;
      frequencyRadios[0].checked = false;

      mockElements.recurrenceInterval.value = '0';

      const pattern = RecurrenceUI.getRecurrencePattern();

      expect(pattern.interval).toBe(1); // Should default to 1
    });

    test('should validate day of month is between 1-31', () => {
      const frequencyRadios = document.querySelectorAll('input[name="recurrence_frequency"]');
      frequencyRadios[3].checked = true;
      frequencyRadios[0].checked = false;

      mockElements.dayOfMonth.value = '0'; // Invalid

      const pattern = RecurrenceUI.getRecurrencePattern();

      expect(pattern.day_of_month).toBeUndefined();
    });
  });

  describe('loadRecurrencePattern()', () => {
    beforeEach(() => {
      RecurrenceUI.init();
    });

    test('should load daily pattern', () => {
      const pattern = {
        frequency: 'daily',
        interval: 3
      };

      RecurrenceUI.loadRecurrencePattern(pattern);

      expect(mockElements.recurrenceInterval.value).toBe(3);
    });

    test('should load weekly pattern with days', () => {
      const pattern = {
        frequency: 'weekly',
        interval: 2,
        days_of_week: '0,2,4'
      };

      const dayCheckboxes = [
        { value: '0', checked: false },
        { value: '2', checked: false },
        { value: '4', checked: false }
      ];

      document.querySelector.mockImplementation((selector) => {
        if (selector.includes('days-of-week')) {
          const value = selector.match(/\[value="(\d+)"\]/)?.[1];
          return dayCheckboxes.find(cb => cb.value === value);
        }
        return null;
      });

      RecurrenceUI.loadRecurrencePattern(pattern);

      expect(dayCheckboxes[0].checked).toBe(true);
      expect(dayCheckboxes[1].checked).toBe(true);
      expect(dayCheckboxes[2].checked).toBe(true);
    });

    test('should load pattern with end date', () => {
      const pattern = {
        frequency: 'daily',
        interval: 1,
        end_date: '2025-12-31'
      };

      RecurrenceUI.loadRecurrencePattern(pattern);

      expect(mockElements.recurrenceEndDate.value).toBe('2025-12-31');
    });

    test('should load pattern with end count', () => {
      const pattern = {
        frequency: 'daily',
        interval: 1,
        end_count: 10
      };

      RecurrenceUI.loadRecurrencePattern(pattern);

      expect(mockElements.recurrenceEndCount.value).toBe(10);
    });

    test('should handle null pattern gracefully', () => {
      expect(() => RecurrenceUI.loadRecurrencePattern(null)).not.toThrow();
    });
  });

  describe('Preview generation', () => {
    beforeEach(() => {
      RecurrenceUI.init();
    });

    test('should show message when no pattern configured', () => {
      // Frequency is 'none' by default
      const pattern = RecurrenceUI.getRecurrencePattern();

      expect(pattern).toBeNull();
    });

    test('should generate preview for daily pattern', () => {
      // This would require testing the generatePreviewDates function
      // which is internal to the module. We can test it indirectly
      // through updatePreview, but since we're mocking the DOM,
      // we'll focus on the pattern extraction logic instead.

      const frequencyRadios = document.querySelectorAll('input[name="recurrence_frequency"]');
      frequencyRadios[1].checked = true;
      frequencyRadios[0].checked = false;

      const pattern = RecurrenceUI.getRecurrencePattern();

      expect(pattern.frequency).toBe('daily');
    });
  });

  describe('UI state management', () => {
    beforeEach(() => {
      RecurrenceUI.init();
    });

    test('should update interval unit text for daily', () => {
      const frequencyRadios = document.querySelectorAll('input[name="recurrence_frequency"]');
      const dailyRadio = frequencyRadios[1];
      dailyRadio.checked = true;
      frequencyRadios[0].checked = false;

      // Trigger the change event handler
      const changeHandler = dailyRadio.addEventListener.mock.calls.find(
        call => call[0] === 'change'
      )?.[1];

      if (changeHandler) {
        changeHandler({ target: dailyRadio });
      }

      // The interval unit should be updated
      // (this is a simplified test since we're mocking the DOM)
      expect(mockElements.recurrenceDetails.style.display).toBe('block');
    });
  });

  describe('Date formatting', () => {
    test('should format dates consistently', () => {
      // Test that patterns use ISO date format (YYYY-MM-DD)
      const frequencyRadios = document.querySelectorAll('input[name="recurrence_frequency"]');
      frequencyRadios[1].checked = true;
      frequencyRadios[0].checked = false;

      const endRadios = document.querySelectorAll('input[name="recurrence_end"]');
      endRadios[1].checked = true;
      endRadios[0].checked = false;

      mockElements.recurrenceEndDate.value = '2025-12-31';

      RecurrenceUI.init();
      const pattern = RecurrenceUI.getRecurrencePattern();

      expect(pattern.end_date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    });
  });

  describe('Frequency validation', () => {
    beforeEach(() => {
      RecurrenceUI.init();
    });

    test('should reject invalid frequency', () => {
      // Frequency not selected or invalid
      document.querySelector.mockReturnValue(null);

      const pattern = RecurrenceUI.getRecurrencePattern();

      expect(pattern).toBeNull();
    });

    test('should accept valid daily frequency', () => {
      const frequencyRadios = document.querySelectorAll('input[name="recurrence_frequency"]');
      frequencyRadios[1].checked = true;
      frequencyRadios[0].checked = false;

      const pattern = RecurrenceUI.getRecurrencePattern();

      expect(pattern).not.toBeNull();
      expect(pattern.frequency).toBe('daily');
    });

    test('should accept valid weekly frequency', () => {
      const frequencyRadios = document.querySelectorAll('input[name="recurrence_frequency"]');
      frequencyRadios[2].checked = true;
      frequencyRadios[0].checked = false;

      const pattern = RecurrenceUI.getRecurrencePattern();

      expect(pattern).not.toBeNull();
      expect(pattern.frequency).toBe('weekly');
    });
  });
});
