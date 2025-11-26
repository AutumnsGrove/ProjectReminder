/**
 * Main Application Logic
 * Phase 2: Using mock data from Storage
 * Handles all view rendering and user interactions
 */

const App = (function() {
    'use strict';

    let config = null;

    /**
     * Initialize the application
     */
    async function init() {
        try {
            // Load configuration
            config = await API.init();
            console.log('App initialized with config:', config);
        } catch (error) {
            console.error('Failed to initialize app:', error);
        }
    }

    /**
     * Initialize Today View
     */
    async function initTodayView() {
        console.log('Initializing Today view...');

        // Check for navigation errors
        const urlParams = new URLSearchParams(window.location.search);
        const errorCode = urlParams.get('error');

        if (errorCode) {
            switch(errorCode) {
                case 'reminderNotFound':
                    showError('The reminder you tried to edit was not found.');
                    break;
                case 'loadFailed':
                    showError('Failed to load the reminder. Please try again.');
                    break;
                default:
                    console.warn('Unknown error code:', errorCode);
            }
            // Clear the error parameter
            window.history.replaceState({}, document.title, window.location.pathname);
        }

        try {
            // Get today's reminders from API (already categorized)
            const {overdue, today, floating} = await API.getTodayReminders();
            console.log('Today reminders:', {overdue, today, floating});

            // Render sections
            renderTodaySection('overdueList', 'overdueSection', overdue, true);
            renderTodaySection('todayList', 'todaySection', today, false);
            renderTodaySection('floatingList', 'floatingSection', floating, false);

        } catch (error) {
            console.error('Error loading today view:', error);
            showError('Failed to load reminders');
        }
    }

    /**
     * Render a section in Today view
     */
    function renderTodaySection(listId, sectionId, reminders, isOverdue) {
        const list = document.getElementById(listId);
        const section = document.getElementById(sectionId);

        if (!list || !section) return;

        if (reminders.length === 0) {
            section.style.display = 'none';
            return;
        }

        section.style.display = 'block';
        list.innerHTML = '';

        reminders.forEach(reminder => {
            const card = createReminderCard(reminder, isOverdue);
            list.appendChild(card);
        });
    }

    /**
     * Create a reminder card element
     */
    function createReminderCard(reminder, isOverdue = false) {
        const card = document.createElement('div');
        card.className = `reminder-card priority-${reminder.priority}`;
        if (isOverdue) {
            card.classList.add('overdue');
        }
        card.dataset.id = reminder.id;

        // Checkbox
        const checkboxContainer = document.createElement('div');
        checkboxContainer.className = 'reminder-checkbox-container';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'reminder-checkbox';
        checkbox.setAttribute('aria-label', 'Complete reminder');

        checkbox.addEventListener('change', async (e) => {
            e.stopPropagation();
            if (checkbox.checked) {
                await handleReminderComplete(reminder.id, card);
            }
        });

        checkboxContainer.appendChild(checkbox);

        // Content
        const content = document.createElement('div');
        content.className = 'reminder-content';

        const text = document.createElement('div');
        text.className = 'reminder-text';
        text.textContent = reminder.text;

        const meta = document.createElement('div');
        meta.className = 'reminder-meta';

        // Add time if present
        if (reminder.due_time) {
            const timeItem = document.createElement('span');
            timeItem.className = 'meta-item time-badge';
            const iconSpan = document.createElement('span');
            iconSpan.className = 'meta-icon';
            iconSpan.textContent = '🕐';
            const timeText = document.createTextNode(formatTime(reminder.due_time));
            timeItem.appendChild(iconSpan);
            timeItem.appendChild(timeText);
            meta.appendChild(timeItem);
        }

        // Add category if present
        if (reminder.category) {
            const categoryItem = document.createElement('span');
            categoryItem.className = 'meta-item category-badge';
            categoryItem.textContent = reminder.category;
            meta.appendChild(categoryItem);
        }

        // Add location if present (Phase 6: Updated to use location_name)
        if (reminder.location_name || reminder.location_address) {
            const locationItem = document.createElement('span');
            locationItem.className = 'meta-item location-badge';
            const locationText = reminder.location_name || reminder.location_address || 'Unknown Location';
            const locIconSpan = document.createElement('span');
            locIconSpan.className = 'meta-icon';
            locIconSpan.textContent = '📍';
            const locTextNode = document.createTextNode(locationText);
            locationItem.appendChild(locIconSpan);
            locationItem.appendChild(locTextNode);
            locationItem.title = reminder.location_address || ''; // Show full address on hover
            meta.appendChild(locationItem);
        }

        // Add time required if present (boolean: true = time-sensitive task)
        if (reminder.time_required) {
            const timeReqItem = document.createElement('span');
            timeReqItem.className = 'meta-item';
            const reqIconSpan = document.createElement('span');
            reqIconSpan.className = 'meta-icon';
            reqIconSpan.textContent = '⏱';
            const reqTextNode = document.createTextNode('Time-sensitive');
            timeReqItem.appendChild(reqIconSpan);
            timeReqItem.appendChild(reqTextNode);
            meta.appendChild(timeReqItem);
        }

        content.appendChild(text);
        content.appendChild(meta);

        // Priority badge
        const priority = document.createElement('div');
        priority.className = 'reminder-priority';
        const priorityBadgeHTML = createPriorityBadge(reminder.priority);
        const priorityTemplate = document.createElement('div');
        priorityTemplate.innerHTML = priorityBadgeHTML;
        priority.appendChild(priorityTemplate.firstChild);

        // Assemble card
        card.appendChild(checkboxContainer);
        card.appendChild(content);
        card.appendChild(priority);

        // Click to edit
        card.addEventListener('click', (e) => {
            if (!e.target.classList.contains('reminder-checkbox')) {
                window.location.href = `edit.html?id=${reminder.id}`;
            }
        });

        // Setup swipe-to-delete on mobile
        Animations.setupSwipeToDelete(card, async () => {
            await handleReminderDelete(reminder.id);
        });

        return card;
    }

    /**
     * Create priority badge HTML
     */
    function createPriorityBadge(priority) {
        const badges = {
            someday: '<span class="priority-badge someday">🔵 Someday</span>',
            chill: '<span class="priority-badge chill">🟢 Chill</span>',
            important: '<span class="priority-badge important">🟡 Important</span>',
            urgent: '<span class="priority-badge urgent">🔴 Urgent</span>',
            waiting: '<span class="priority-badge waiting">🟠 Waiting</span>'
        };
        return badges[priority] || badges.chill;
    }

    /**
     * Format time for display (24h to 12h)
     */
    function formatTime(time24) {
        if (!time24) return '';
        const [hours, minutes] = time24.split(':');
        const hour = parseInt(hours);
        const ampm = hour >= 12 ? 'PM' : 'AM';
        const hour12 = hour % 12 || 12;
        return `${hour12}:${minutes} ${ampm}`;
    }

    /**
     * Handle reminder completion
     */
    async function handleReminderComplete(id, cardElement) {
        try {
            // Animate completion
            await Animations.animateCompletion(cardElement);

            // Update via API
            await API.completeReminder(id);

            console.log('Reminder completed:', id);
        } catch (error) {
            console.error('Error completing reminder:', error);
            showError('Failed to complete reminder');
        }
    }

    /**
     * Handle reminder deletion
     */
    async function handleReminderDelete(id) {
        try {
            await API.deleteReminder(id);
            console.log('Reminder deleted:', id);
        } catch (error) {
            console.error('Error deleting reminder:', error);
            showError('Failed to delete reminder');
        }
    }

    /**
     * Initialize Upcoming View
     */
    async function initUpcomingView() {
        console.log('Initializing Upcoming view...');

        try {
            const reminders = await API.getUpcomingReminders();
            console.log('Upcoming reminders:', reminders);

            const container = document.getElementById('upcomingContainer');
            if (!container) return;

            if (reminders.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <p>No upcoming reminders</p>
                        <p class="empty-subtitle">Tap + to add one</p>
                    </div>
                `;
                return;
            }

            // Group by date
            const groupedByDate = groupRemindersByDate(reminders);

            // Render date groups
            container.innerHTML = '';
            groupedByDate.forEach(group => {
                const dateGroup = createDateGroup(group);
                container.appendChild(dateGroup);
            });

        } catch (error) {
            console.error('Error loading upcoming view:', error);
            showError('Failed to load upcoming reminders');
        }
    }

    /**
     * Initialize Future View
     */
    async function initFutureView() {
        console.log('Initializing Future view...');

        try {
            const reminders = await API.getFutureReminders();
            console.log('Future reminders:', reminders);

            const container = document.getElementById('futureContainer');
            if (!container) return;

            if (reminders.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <p>No future reminders</p>
                        <p class="empty-subtitle">All caught up! 🎉</p>
                    </div>
                `;
                return;
            }

            // Group by date (reuse same logic as upcoming)
            const groupedByDate = groupRemindersByDate(reminders);

            // Render date groups
            container.innerHTML = '';
            groupedByDate.forEach(group => {
                const dateGroup = createDateGroup(group);
                container.appendChild(dateGroup);
            });

        } catch (error) {
            console.error('Error loading future view:', error);
            showError('Failed to load future reminders');
        }
    }

    /**
     * Group reminders by date
     */
    function groupRemindersByDate(reminders) {
        const groups = {};

        reminders.forEach(reminder => {
            const date = reminder.due_date;
            if (!groups[date]) {
                groups[date] = [];
            }
            groups[date].push(reminder);
        });

        // Convert to array and sort by date
        return Object.keys(groups)
            .sort()
            .map(date => ({
                date: date,
                reminders: groups[date]
            }));
    }

    /**
     * Create a date group element
     */
    function createDateGroup(group) {
        const container = document.createElement('div');
        container.className = 'date-group';

        // Date header
        const header = document.createElement('div');
        header.className = 'date-header';

        const title = document.createElement('div');
        title.className = 'date-title';
        title.textContent = formatDate(group.date);

        const subtitle = document.createElement('div');
        subtitle.className = 'date-subtitle';
        subtitle.textContent = formatDateSubtitle(group.date);

        header.appendChild(title);
        header.appendChild(subtitle);

        // Reminders list
        const list = document.createElement('div');
        list.className = 'reminders-list';

        group.reminders.forEach(reminder => {
            const card = createUpcomingReminderCard(reminder);
            list.appendChild(card);
        });

        container.appendChild(header);
        container.appendChild(list);

        return container;
    }

    /**
     * Create upcoming reminder card (without checkbox)
     */
    function createUpcomingReminderCard(reminder) {
        const card = document.createElement('div');
        card.className = `reminder-card priority-${reminder.priority}`;
        card.dataset.id = reminder.id;

        // Content
        const content = document.createElement('div');
        content.className = 'reminder-content';

        const text = document.createElement('div');
        text.className = 'reminder-text';
        text.textContent = reminder.text;

        const meta = document.createElement('div');
        meta.className = 'reminder-meta';

        // Add time if present
        if (reminder.due_time) {
            const timeItem = document.createElement('span');
            timeItem.className = 'meta-item time-badge';
            const iconSpan = document.createElement('span');
            iconSpan.className = 'meta-icon';
            iconSpan.textContent = '🕐';
            const timeText = document.createTextNode(formatTime(reminder.due_time));
            timeItem.appendChild(iconSpan);
            timeItem.appendChild(timeText);
            meta.appendChild(timeItem);
        }

        // Add category if present
        if (reminder.category) {
            const categoryItem = document.createElement('span');
            categoryItem.className = 'meta-item category-badge';
            categoryItem.textContent = reminder.category;
            meta.appendChild(categoryItem);
        }

        // Add location if present (Phase 6: Updated to use location_name)
        if (reminder.location_name || reminder.location_address) {
            const locationItem = document.createElement('span');
            locationItem.className = 'meta-item location-badge';
            const locationText = reminder.location_name || reminder.location_address || 'Unknown Location';
            const locIconSpan = document.createElement('span');
            locIconSpan.className = 'meta-icon';
            locIconSpan.textContent = '📍';
            const locTextNode = document.createTextNode(locationText);
            locationItem.appendChild(locIconSpan);
            locationItem.appendChild(locTextNode);
            locationItem.title = reminder.location_address || ''; // Show full address on hover
            meta.appendChild(locationItem);
        }

        content.appendChild(text);
        content.appendChild(meta);

        // Priority badge
        const priority = document.createElement('div');
        priority.className = 'reminder-priority';
        const priorityBadgeHTML = createPriorityBadge(reminder.priority);
        const priorityTemplate = document.createElement('div');
        priorityTemplate.innerHTML = priorityBadgeHTML;
        priority.appendChild(priorityTemplate.firstChild);

        // Assemble card
        card.appendChild(content);
        card.appendChild(priority);

        // Click to edit
        card.addEventListener('click', () => {
            window.location.href = `edit.html?id=${reminder.id}`;
        });

        return card;
    }

    /**
     * Format date for display
     */
    function formatDate(dateStr) {
        const date = new Date(dateStr + 'T00:00:00');
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);

        if (date.getTime() === tomorrow.getTime()) {
            return 'Tomorrow';
        }

        const dayOfWeek = date.toLocaleDateString('en-US', { weekday: 'long' });
        const month = date.toLocaleDateString('en-US', { month: 'short' });
        const day = date.getDate();

        return `${dayOfWeek}, ${month} ${day}`;
    }

    /**
     * Format date subtitle
     */
    function formatDateSubtitle(dateStr) {
        const date = new Date(dateStr + 'T00:00:00');
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const diffTime = date - today;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays === 1) return 'Tomorrow';
        if (diffDays <= 7) return `In ${diffDays} days`;
        return `${diffDays} days from now`;
    }

    /**
     * Initialize Completed View
     */
    async function initCompletedView() {
        console.log('Initializing Completed view...');

        try {
            const reminders = await API.getCompletedReminders();
            console.log('Completed reminders:', reminders);

            const container = document.getElementById('completedContainer');
            if (!container) return;

            if (reminders.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <p>No completed reminders yet</p>
                        <p class="empty-subtitle">Complete some tasks to see them here</p>
                    </div>
                `;
                return;
            }

            // Group by completion date
            const groupedByDate = groupCompletedByDate(reminders);

            // Render date groups
            container.innerHTML = '';
            groupedByDate.forEach(group => {
                const dateGroup = createCompletedDateGroup(group);
                container.appendChild(dateGroup);
            });

        } catch (error) {
            console.error('Error loading completed view:', error);
            showError('Failed to load completed reminders');
        }
    }

    /**
     * Group completed reminders by completion date
     */
    function groupCompletedByDate(reminders) {
        const groups = {};

        reminders.forEach(reminder => {
            // Use completed_at date, fallback to updated_at
            const dateTime = reminder.completed_at || reminder.updated_at;
            const date = dateTime ? dateTime.split('T')[0] : 'Unknown';

            if (!groups[date]) {
                groups[date] = [];
            }
            groups[date].push(reminder);
        });

        // Convert to array and sort by date (most recent first)
        return Object.keys(groups)
            .sort((a, b) => b.localeCompare(a))
            .map(date => ({
                date: date,
                reminders: groups[date]
            }));
    }

    /**
     * Create a date group element for completed tasks
     */
    function createCompletedDateGroup(group) {
        const container = document.createElement('div');
        container.className = 'date-group';

        // Date header
        const header = document.createElement('div');
        header.className = 'date-header';

        const title = document.createElement('div');
        title.className = 'date-title';
        title.textContent = formatCompletedDate(group.date);

        const subtitle = document.createElement('div');
        subtitle.className = 'date-subtitle';
        subtitle.textContent = `${group.reminders.length} task${group.reminders.length !== 1 ? 's' : ''} completed`;

        header.appendChild(title);
        header.appendChild(subtitle);

        // Reminders list
        const list = document.createElement('div');
        list.className = 'reminders-list';

        group.reminders.forEach(reminder => {
            const card = createCompletedReminderCard(reminder);
            list.appendChild(card);
        });

        container.appendChild(header);
        container.appendChild(list);

        return container;
    }

    /**
     * Create completed reminder card (with checkmark, no checkbox)
     */
    function createCompletedReminderCard(reminder) {
        const card = document.createElement('div');
        card.className = `reminder-card priority-${reminder.priority} completed`;
        card.dataset.id = reminder.id;

        // Checkmark indicator
        const checkmark = document.createElement('div');
        checkmark.className = 'reminder-checkmark';
        checkmark.innerHTML = '<span class="checkmark-icon">&#10003;</span>';

        // Content
        const content = document.createElement('div');
        content.className = 'reminder-content';

        const text = document.createElement('div');
        text.className = 'reminder-text completed-text';
        text.textContent = reminder.text;

        const meta = document.createElement('div');
        meta.className = 'reminder-meta';

        // Add completion time if available
        if (reminder.completed_at) {
            const timeItem = document.createElement('span');
            timeItem.className = 'meta-item';
            const completedTime = new Date(reminder.completed_at);
            const formattedTime = completedTime.toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
            });
            timeItem.textContent = `Completed at ${formattedTime}`;
            meta.appendChild(timeItem);
        }

        // Add category if present
        if (reminder.category) {
            const categoryItem = document.createElement('span');
            categoryItem.className = 'meta-item category-badge';
            categoryItem.textContent = reminder.category;
            meta.appendChild(categoryItem);
        }

        content.appendChild(text);
        content.appendChild(meta);

        // Priority badge
        const priority = document.createElement('div');
        priority.className = 'reminder-priority';
        const priorityBadgeHTML = createPriorityBadge(reminder.priority);
        const priorityTemplate = document.createElement('div');
        priorityTemplate.innerHTML = priorityBadgeHTML;
        priority.appendChild(priorityTemplate.firstChild);

        // Assemble card
        card.appendChild(checkmark);
        card.appendChild(content);
        card.appendChild(priority);

        return card;
    }

    /**
     * Format date for completed view display
     */
    function formatCompletedDate(dateStr) {
        if (dateStr === 'Unknown') return 'Unknown Date';

        const date = new Date(dateStr + 'T00:00:00');
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        if (date.getTime() === today.getTime()) {
            return 'Today';
        }

        if (date.getTime() === yesterday.getTime()) {
            return 'Yesterday';
        }

        const dayOfWeek = date.toLocaleDateString('en-US', { weekday: 'long' });
        const month = date.toLocaleDateString('en-US', { month: 'short' });
        const day = date.getDate();

        return `${dayOfWeek}, ${month} ${day}`;
    }

    /**
     * Initialize Edit View
     */
    async function initEditView() {
        console.log('Initializing Edit view...');

        // Check if editing existing reminder
        const urlParams = new URLSearchParams(window.location.search);
        const reminderId = urlParams.get('id');

        if (reminderId) {
            // Load existing reminder
            await loadReminderForEdit(reminderId);
        }
    }

    /**
     * Load reminder data for editing
     */
    async function loadReminderForEdit(id) {
        try {
            const reminder = await API.getReminder(id);

            if (!reminder) {
                // Navigate away instead of showing an error
                window.location.href = 'index.html?error=reminderNotFound';
                return;
            }

            // Update page title
            document.getElementById('pageTitle').textContent = 'Edit Reminder';

            // Show delete button
            document.getElementById('deleteBtn').style.display = 'flex';

            // Populate form
            document.getElementById('reminderId').value = reminder.id;
            document.getElementById('reminderText').value = reminder.text || '';
            document.getElementById('category').value = reminder.category || '';
            document.getElementById('dueDate').value = reminder.due_date || '';
            document.getElementById('dueTime').value = reminder.due_time || '';
            document.getElementById('timeRequired').checked = reminder.time_required || false;

            // Location handling (updated for Phase 6)
            if (reminder.location_name || reminder.location_address) {
                document.getElementById('locationSearch').value = reminder.location_name || reminder.location_address;
                document.getElementById('locationName').value = reminder.location_name || '';
                document.getElementById('locationAddress').value = reminder.location_address || '';
                document.getElementById('locationLat').value = reminder.location_lat || '';
                document.getElementById('locationLng').value = reminder.location_lng || '';
                document.getElementById('locationRadius').value = reminder.location_radius || '100';
            }

            // TODO: Notes field (Phase 4+)
            // document.getElementById('notes').value = reminder.notes || '';

            // Set priority
            const priorityRadio = document.querySelector(`input[name="priority"][value="${reminder.priority}"]`);
            if (priorityRadio) {
                priorityRadio.checked = true;
            }

        } catch (error) {
            console.error('Error loading reminder:', error);
            window.location.href = 'index.html?error=loadFailed';
        }
    }

    // Track submission state to prevent double-clicks
    let isSubmitting = false;

    /**
     * Handle reminder form submit
     */
    async function handleReminderSubmit(event) {
        event.preventDefault();

        // Prevent double submissions
        if (isSubmitting) {
            console.log('Submission already in progress, ignoring');
            return;
        }

        const form = event.target;
        const saveBtn = document.getElementById('saveBtn');

        // Disable button and set submitting state
        isSubmitting = true;
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.textContent = 'Saving...';
        }

        const formData = new FormData(form);

        const data = {
            text: formData.get('text'),
            priority: formData.get('priority'),
            category: formData.get('category') || null,
            due_date: formData.get('due_date') || null,
            due_time: formData.get('due_time') || null,
            time_required: formData.get('time_required') === 'on' ? true : false,
            location_name: formData.get('location_name') || null,
            location_address: formData.get('location_address') || null,
            location_lat: formData.get('location_lat') ? parseFloat(formData.get('location_lat')) : null,
            location_lng: formData.get('location_lng') ? parseFloat(formData.get('location_lng')) : null,
            location_radius: formData.get('location_radius') ? parseInt(formData.get('location_radius')) : 100
        };

        // Add recurrence pattern if configured (Phase 7)
        if (typeof RecurrenceUI !== 'undefined') {
            const recurrencePattern = RecurrenceUI.getRecurrencePattern();
            if (recurrencePattern) {
                data.recurrence_pattern = recurrencePattern;
            }
        }

        const reminderId = formData.get('id');

        try {
            if (reminderId) {
                // Update existing
                await API.updateReminder(reminderId, data);
                console.log('Reminder updated:', reminderId);
            } else {
                // Create new
                const newReminder = await API.createReminder(data);
                console.log('Reminder created:', newReminder);
            }

            // Redirect to today view
            window.location.href = 'index.html';

        } catch (error) {
            console.error('Error saving reminder:', error);
            showError('Failed to save reminder');
            // Re-enable the button on error so user can retry
            isSubmitting = false;
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.textContent = 'Save';
            }
        }
    }

    /**
     * Handle reminder delete from edit view
     */
    async function handleReminderDelete() {
        const reminderId = document.getElementById('reminderId').value;

        if (!reminderId) return;

        if (!confirm('Are you sure you want to delete this reminder?')) {
            return;
        }

        try {
            await API.deleteReminder(reminderId);
            console.log('Reminder deleted:', reminderId);
            window.location.href = 'index.html';
        } catch (error) {
            console.error('Error deleting reminder:', error);
            showError('Failed to delete reminder');
        }
    }

    /**
     * Show error message
     */
    function showError(message) {
        // Simple alert for now, can be enhanced with custom UI
        alert(message);
    }

    /**
     * Apply confidence indicator styling to form fields (Phase 8.1)
     * @param {HTMLElement} field - The form field element
     * @param {number} confidence - Confidence score (0.0-1.0)
     */
    function applyConfidenceIndicator(field, confidence) {
        // Remove existing confidence classes
        field.classList.remove('confidence-high', 'confidence-medium', 'confidence-low');

        // Apply confidence class based on score
        if (confidence >= 0.8) {
            field.classList.add('confidence-high');  // Green border
        } else if (confidence >= 0.6) {
            field.classList.add('confidence-medium');  // Yellow border
        } else {
            field.classList.add('confidence-low');  // Red border
        }

        // Add tooltip showing confidence
        field.title = `Auto-filled (${Math.round(confidence * 100)}% confidence)`;
    }

    /**
     * Initialize Voice Recorder for the Edit view
     */
    function initVoiceRecorder() {
        // Check if browser supports voice recording
        if (!VoiceRecorder.isSupported()) {
            console.warn('Voice recording not supported in this browser.');
            document.getElementById('voiceRecorderBtn').style.display = 'none';
            return null;
        }

        const reminderText = document.getElementById('reminderText');
        const voiceRecorderBtn = document.getElementById('voiceRecorderBtn');
        const voiceRecorderTimer = document.getElementById('voiceRecorderTimer');
        const formGroup = voiceRecorderBtn.closest('.form-group');

        // Create VoiceRecorder instance
        const voiceRecorder = new VoiceRecorder({
            onRecordingStart: () => {
                // UI updates for recording start
                voiceRecorderBtn.classList.add('recording');
                formGroup.classList.add('recording');
                voiceRecorderTimer.textContent = '0:00';
                voiceRecorderTimer.style.display = 'block';
            },
            onRecordingStop: async (audioBlob) => {
                // Reset UI
                voiceRecorderBtn.classList.remove('recording');
                voiceRecorderBtn.classList.add('processing');
                formGroup.classList.remove('recording');
                formGroup.classList.add('processing');
                voiceRecorderTimer.textContent = '';
                voiceRecorderTimer.style.display = 'none';

                try {
                    // Step 1: Transcribe audio
                    showToast('Transcribing...', 'info');
                    const transcribeResult = await API.transcribeAudio(audioBlob);

                    if (!transcribeResult || !transcribeResult.text) {
                        throw new Error('No transcription text received');
                    }

                    const transcribedText = transcribeResult.text.trim();

                    // Step 2: Parse reminder text with NLP (Phase 8.1)
                    showToast('Analyzing...', 'info');
                    const nlpMode = localStorage.getItem('nlp_mode') || 'auto';
                    const parseResult = await API.parseReminderText(transcribedText, nlpMode);

                    // Step 3: Auto-populate form fields with confidence-based validation
                    reminderText.value = parseResult.text || transcribedText;

                    // Auto-fill date (if confidence > 0.7)
                    if (parseResult.due_date && parseResult.confidence > 0.7) {
                        const dueDateField = document.getElementById('dueDate');
                        if (dueDateField) {
                            dueDateField.value = parseResult.due_date;
                            applyConfidenceIndicator(dueDateField, parseResult.confidence);
                        }
                    }

                    // Auto-fill time (if confidence > 0.7)
                    if (parseResult.due_time && parseResult.confidence > 0.7) {
                        const dueTimeField = document.getElementById('dueTime');
                        const timeRequiredField = document.getElementById('timeRequired');
                        if (dueTimeField) {
                            // Convert HH:MM:SS to HH:MM for HTML input
                            const timeHHMM = parseResult.due_time.substring(0, 5);
                            dueTimeField.value = timeHHMM;
                            applyConfidenceIndicator(dueTimeField, parseResult.confidence);
                        }
                        if (timeRequiredField) {
                            timeRequiredField.checked = parseResult.time_required;
                        }
                    }

                    // Auto-fill priority (if confidence > 0.6)
                    if (parseResult.priority && parseResult.confidence > 0.6) {
                        const priorityRadio = document.querySelector(`input[name="priority"][value="${parseResult.priority}"]`);
                        if (priorityRadio) {
                            priorityRadio.checked = true;
                        }
                    }

                    // Auto-fill category (if provided)
                    if (parseResult.category) {
                        const categoryField = document.getElementById('category');
                        if (categoryField) {
                            categoryField.value = parseResult.category;
                            applyConfidenceIndicator(categoryField, parseResult.confidence);
                        }
                    }

                    // Show success toast with parse mode
                    const modeLabel = parseResult.parse_mode === 'local' ? '🖥️ Local' : '☁️ Cloud';
                    showToast(`Parsed with ${modeLabel} mode (confidence: ${Math.round(parseResult.confidence * 100)}%)`, 'success');

                } catch (error) {
                    // Show error in case of transcription or parse failure
                    console.error('Voice processing error:', error);
                    showToast(error.message, 'error');
                } finally {
                    // Reset button state
                    voiceRecorderBtn.classList.remove('processing');
                    formGroup.classList.remove('processing');
                }
            },
            onRecordingUpdate: (elapsedTime) => {
                // Update timer display
                const minutes = Math.floor(elapsedTime / 60000);
                const seconds = Math.floor((elapsedTime % 60000) / 1000);
                voiceRecorderTimer.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            },
            onError: (errorMessage) => {
                showToast(errorMessage, 'error');
                voiceRecorderBtn.classList.remove('recording', 'processing');
                formGroup.classList.remove('recording', 'processing');
            }
        });

        // Voice recorder button click handler
        voiceRecorderBtn.addEventListener('click', () => {
            if (voiceRecorder.isRecording()) {
                voiceRecorder.stopRecording();
            } else {
                voiceRecorder.startRecording();
            }
        });

        return voiceRecorder;
    }

    // Modify initEditView to include voice recorder
    function initEditView() {
        console.log('Initializing Edit view...');

        // Existing edit view initialization
        const urlParams = new URLSearchParams(window.location.search);
        const reminderId = urlParams.get('id');

        // Initialize voice recorder
        initVoiceRecorder();

        if (reminderId) {
            // Load existing reminder
            loadReminderForEdit(reminderId);
        }
    }

    // Public API
    // Note: init() is now called from HTML files to ensure proper async/await
    return {
        init,
        initTodayView,
        initUpcomingView,
        initFutureView,
        initCompletedView,
        initEditView,
        handleReminderSubmit,
        handleReminderDelete,
        initVoiceRecorder // Expose for testing
    };
})();

// Make available globally
window.App = App;
