/**
 * recurrence.js - Recurrence Pattern UI Logic (Phase 7)
 *
 * Handles:
 * - Frequency selection and UI state management
 * - Days of week selection
 * - End condition handling
 * - Preview generation
 * - Form data extraction
 */

const RecurrenceUI = (() => {
    'use strict';

    let initialized = false;

    /**
     * Initialize recurrence UI
     */
    function init() {
        if (initialized) return;

        console.log('Initializing Recurrence UI...');

        // Get DOM elements
        const frequencyRadios = document.querySelectorAll('input[name="recurrence_frequency"]');
        const recurrenceDetails = document.getElementById('recurrenceDetails');
        const intervalInput = document.getElementById('recurrenceInterval');
        const intervalUnit = document.getElementById('intervalUnit');
        const daysOfWeekContainer = document.getElementById('daysOfWeekContainer');
        const dayOfMonthContainer = document.getElementById('dayOfMonthContainer');
        const endConditionRadios = document.querySelectorAll('input[name="recurrence_end"]');
        const endDateContainer = document.getElementById('endDateContainer');
        const endCountContainer = document.getElementById('endCountContainer');
        const dayCheckboxes = document.querySelectorAll('.days-of-week input[type="checkbox"]');

        // Frequency change handler
        frequencyRadios.forEach(radio => {
            radio.addEventListener('change', handleFrequencyChange);
        });

        // Interval change handler (for preview update)
        intervalInput.addEventListener('input', updatePreview);

        // Days of week change handler
        dayCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', updatePreview);
        });

        // Day of month change handler
        document.getElementById('dayOfMonth').addEventListener('input', updatePreview);

        // End condition change handlers
        endConditionRadios.forEach(radio => {
            radio.addEventListener('change', handleEndConditionChange);
        });

        document.getElementById('recurrenceEndDate').addEventListener('change', updatePreview);
        document.getElementById('recurrenceEndCount').addEventListener('input', updatePreview);

        initialized = true;
    }

    /**
     * Handle frequency selection change
     */
    function handleFrequencyChange(event) {
        const frequency = event.target.value;
        const recurrenceDetails = document.getElementById('recurrenceDetails');
        const intervalUnit = document.getElementById('intervalUnit');
        const daysOfWeekContainer = document.getElementById('daysOfWeekContainer');
        const dayOfMonthContainer = document.getElementById('dayOfMonthContainer');

        if (frequency === 'none') {
            // Hide details
            recurrenceDetails.style.display = 'none';
            return;
        }

        // Show details
        recurrenceDetails.style.display = 'block';

        // Update interval unit text
        const unitText = {
            daily: 'day(s)',
            weekly: 'week(s)',
            monthly: 'month(s)',
            yearly: 'year(s)'
        };
        intervalUnit.textContent = unitText[frequency] || 'day(s)';

        // Show/hide frequency-specific controls
        daysOfWeekContainer.style.display = frequency === 'weekly' ? 'block' : 'none';
        dayOfMonthContainer.style.display = frequency === 'monthly' ? 'block' : 'none';

        // Update preview
        updatePreview();
    }

    /**
     * Handle end condition change
     */
    function handleEndConditionChange(event) {
        const endCondition = event.target.value;
        const endDateContainer = document.getElementById('endDateContainer');
        const endCountContainer = document.getElementById('endCountContainer');

        endDateContainer.style.display = endCondition === 'date' ? 'block' : 'none';
        endCountContainer.style.display = endCondition === 'count' ? 'block' : 'none';

        updatePreview();
    }

    /**
     * Update recurrence preview
     */
    function updatePreview() {
        const pattern = getRecurrencePattern();

        if (!pattern) {
            document.getElementById('recurrencePreview').innerHTML =
                '<small class="form-hint">Configure recurrence pattern to see preview</small>';
            return;
        }

        // Get due date from form or use today
        const dueDateInput = document.getElementById('dueDate');
        const startDate = dueDateInput.value ? new Date(dueDateInput.value) : new Date();

        // Generate preview dates
        const previewDates = generatePreviewDates(startDate, pattern, 3);

        if (previewDates.length === 0) {
            document.getElementById('recurrencePreview').innerHTML =
                '<small class="form-hint">No future occurrences</small>';
            return;
        }

        // Format dates for display
        const dateList = previewDates.map(date => {
            const options = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' };
            return `<li>${date.toLocaleDateString('en-US', options)}</li>`;
        }).join('');

        document.getElementById('recurrencePreview').innerHTML = `<ul>${dateList}</ul>`;
    }

    /**
     * Generate preview dates based on pattern
     */
    function generatePreviewDates(startDate, pattern, count) {
        const dates = [];
        let currentDate = new Date(startDate);
        const maxIterations = 1000; // Safety limit
        let iterations = 0;

        while (dates.length < count && iterations < maxIterations) {
            iterations++;

            // Check end conditions
            if (pattern.end_date) {
                const endDate = new Date(pattern.end_date);
                if (currentDate > endDate) break;
            }
            if (pattern.end_count && dates.length >= pattern.end_count) break;

            // For weekly, check if day matches
            if (pattern.frequency === 'weekly' && pattern.days_of_week) {
                const allowedDays = pattern.days_of_week.split(',').map(d => parseInt(d));
                const currentDay = (currentDate.getDay() + 6) % 7; // Convert Sun=0 to Mon=0
                if (allowedDays.includes(currentDay)) {
                    dates.push(new Date(currentDate));
                }
                currentDate.setDate(currentDate.getDate() + 1);
                continue;
            }

            // For monthly, check day of month
            if (pattern.frequency === 'monthly' && pattern.day_of_month) {
                if (currentDate.getDate() === pattern.day_of_month) {
                    dates.push(new Date(currentDate));
                }
                currentDate.setDate(currentDate.getDate() + 1);
                continue;
            }

            // For daily and yearly, just add the date
            dates.push(new Date(currentDate));

            // Advance to next occurrence
            if (pattern.frequency === 'daily') {
                currentDate.setDate(currentDate.getDate() + pattern.interval);
            } else if (pattern.frequency === 'weekly') {
                currentDate.setDate(currentDate.getDate() + (pattern.interval * 7));
            } else if (pattern.frequency === 'monthly') {
                currentDate.setMonth(currentDate.getMonth() + pattern.interval);
            } else if (pattern.frequency === 'yearly') {
                currentDate.setFullYear(currentDate.getFullYear() + pattern.interval);
            }
        }

        return dates;
    }

    /**
     * Get recurrence pattern from form
     * Returns null if frequency is 'none', otherwise returns pattern object
     */
    function getRecurrencePattern() {
        const frequency = document.querySelector('input[name="recurrence_frequency"]:checked')?.value;

        if (!frequency || frequency === 'none') {
            return null;
        }

        const interval = parseInt(document.getElementById('recurrenceInterval').value) || 1;
        const endCondition = document.querySelector('input[name="recurrence_end"]:checked')?.value || 'never';

        const pattern = {
            frequency,
            interval
        };

        // Add frequency-specific fields
        if (frequency === 'weekly') {
            const selectedDays = Array.from(document.querySelectorAll('.days-of-week input[type="checkbox"]:checked'))
                .map(cb => cb.value);
            if (selectedDays.length > 0) {
                pattern.days_of_week = selectedDays.join(',');
            }
        }

        if (frequency === 'monthly') {
            const dayOfMonth = parseInt(document.getElementById('dayOfMonth').value);
            if (dayOfMonth >= 1 && dayOfMonth <= 31) {
                pattern.day_of_month = dayOfMonth;
            }
        }

        // Add end conditions
        if (endCondition === 'date') {
            const endDate = document.getElementById('recurrenceEndDate').value;
            if (endDate) {
                pattern.end_date = endDate;
            }
        } else if (endCondition === 'count') {
            const endCount = parseInt(document.getElementById('recurrenceEndCount').value);
            if (endCount >= 1) {
                pattern.end_count = endCount;
            }
        }

        return pattern;
    }

    /**
     * Load recurrence pattern into form (for editing existing reminders)
     */
    function loadRecurrencePattern(pattern) {
        if (!pattern) return;

        // Set frequency
        const frequencyRadio = document.querySelector(`input[name="recurrence_frequency"][value="${pattern.frequency}"]`);
        if (frequencyRadio) {
            frequencyRadio.checked = true;
            handleFrequencyChange({ target: frequencyRadio });
        }

        // Set interval
        if (pattern.interval) {
            document.getElementById('recurrenceInterval').value = pattern.interval;
        }

        // Set days of week (for weekly)
        if (pattern.days_of_week) {
            const days = pattern.days_of_week.split(',');
            days.forEach(day => {
                const checkbox = document.querySelector(`.days-of-week input[value="${day}"]`);
                if (checkbox) checkbox.checked = true;
            });
        }

        // Set day of month (for monthly)
        if (pattern.day_of_month) {
            document.getElementById('dayOfMonth').value = pattern.day_of_month;
        }

        // Set end condition
        if (pattern.end_date) {
            document.querySelector('input[name="recurrence_end"][value="date"]').checked = true;
            document.getElementById('recurrenceEndDate').value = pattern.end_date;
            handleEndConditionChange({ target: { value: 'date' } });
        } else if (pattern.end_count) {
            document.querySelector('input[name="recurrence_end"][value="count"]').checked = true;
            document.getElementById('recurrenceEndCount').value = pattern.end_count;
            handleEndConditionChange({ target: { value: 'count' } });
        }

        updatePreview();
    }

    // Public API
    return {
        init,
        getRecurrencePattern,
        loadRecurrencePattern
    };
})();

// Make available globally
window.RecurrenceUI = RecurrenceUI;
