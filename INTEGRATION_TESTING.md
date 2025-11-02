# Phase 3 Integration Testing Checklist

**Date:** 2025-11-02
**Phase:** Phase 3 - FastAPI Backend Integration
**Tester:** Manual (User)
**Backend:** FastAPI (localhost:8000)
**Frontend:** UI Server (localhost:3000)

---

## Test Environment Setup

### Prerequisites
- [ ] Backend running: `uv run uvicorn server.main:app --reload --host 0.0.0.0 --port 8000`
- [ ] UI server running: `python serve_ui.py`
- [ ] Browser open: http://localhost:3000
- [ ] `config.json` exists with valid API token
- [ ] `storage.js` loaded before `errors.js` in all HTML files
- [ ] `errors.js` loaded before `api.js` in all HTML files
- [ ] Browser console open (F12) to monitor logs

### Verify Setup
- [ ] Navigate to http://localhost:8000/docs - Swagger UI loads
- [ ] Check backend logs show "Application startup complete"
- [ ] Navigate to http://localhost:3000 - Today view loads without errors
- [ ] Open browser console - No JavaScript errors

---

## 1. Basic CRUD Operations

### Create Reminder
- [ ] Click "+" button → Edit form opens
- [ ] Enter text: "Test reminder"
- [ ] Select priority: "Important"
- [ ] Click "Save" → Redirects to Today view
- [ ] Check green toast: "Reminder created!"
- [ ] Verify reminder appears in list
- [ ] **Backend verification:** Check SQLite database for new record

### Get Single Reminder
- [ ] Click on a reminder card → Edit form loads
- [ ] Verify all fields populated correctly
- [ ] Verify page title changes to "Edit Reminder"
- [ ] Verify "Delete" button appears

### Update Reminder
- [ ] Edit reminder text → Change to "Updated test"
- [ ] Change priority → Select "Urgent"
- [ ] Add category → Select "Work"
- [ ] Click "Save" → Redirects to Today view
- [ ] Check green toast: "Reminder updated!"
- [ ] Verify changes reflected in card
- [ ] **Backend verification:** Check database for updated fields

### Delete Reminder
- [ ] Click on a reminder → Opens edit form
- [ ] Click "Delete" button → Confirmation dialog appears
- [ ] Click "OK" → Redirects to Today view
- [ ] Check green toast: "Reminder deleted!"
- [ ] Verify reminder removed from list
- [ ] **Backend verification:** Check database record marked as deleted

### Complete Reminder
- [ ] Check the checkbox on a reminder card
- [ ] Animation plays (fade out, shrink)
- [ ] Check green toast: "Reminder completed!"
- [ ] Card disappears from view
- [ ] **Backend verification:** Check `status='completed'` and `completed_at` timestamp set

---

## 2. UI Views and Navigation

### Today View (index.html)
- [ ] View loads without errors
- [ ] "Today" tab is active (highlighted)
- [ ] "Refresh" button visible in header

#### Overdue Section
- [ ] Create reminder with past date (e.g., yesterday)
- [ ] Verify "Overdue" section appears
- [ ] Verify red styling applied to overdue cards
- [ ] Verify section title shows "Overdue"

#### Today Section
- [ ] Create reminder with today's date
- [ ] Verify "Today's Tasks" section shows reminder
- [ ] Verify no overdue styling applied
- [ ] If no reminders: Shows empty state "No reminders for today"

#### Floating Section (Anytime)
- [ ] Create reminder with NO due date
- [ ] Verify "Anytime" section appears
- [ ] Verify reminder shows in floating section
- [ ] Verify no date badge shown

### Upcoming View (upcoming.html)
- [ ] Click "Upcoming" tab → View loads
- [ ] "Upcoming" tab becomes active
- [ ] Create reminder for tomorrow
- [ ] Verify date group appears: "Tomorrow"
- [ ] Create reminder for 3 days from now
- [ ] Verify date group appears with formatted date
- [ ] Verify reminders grouped by date
- [ ] Verify reminders sorted by date (earliest first)
- [ ] If no upcoming reminders: Shows empty state

### Edit Form (edit.html)
- [ ] Click "+" → New reminder form loads
- [ ] Page title shows "New Reminder"
- [ ] Delete button hidden
- [ ] All fields empty/default values
- [ ] Click on existing reminder → Edit form loads
- [ ] Page title shows "Edit Reminder"
- [ ] Delete button visible
- [ ] All fields populated from reminder data

---

## 3. Data Field Handling

### Text Field
- [ ] Create reminder with short text (< 50 chars)
- [ ] Create reminder with long text (> 200 chars)
- [ ] Verify text wraps correctly in card
- [ ] Edit reminder → Verify text persists

### Priority Field
- [ ] Create reminder with priority: "Chill" → Green badge shows
- [ ] Create reminder with priority: "Important" → Yellow badge shows
- [ ] Create reminder with priority: "Urgent" → Red badge shows
- [ ] Verify card border color matches priority

### Category Field
- [ ] Create reminder with category: "Personal"
- [ ] Verify category badge appears in meta section
- [ ] Create reminder with no category → No badge shown
- [ ] Change category in edit form → Updates correctly

### Due Date Field
- [ ] Create reminder with today's date
- [ ] Create reminder with future date
- [ ] Create reminder with past date (overdue)
- [ ] Create reminder with NO date (floating)
- [ ] Verify date format displays correctly

### Due Time Field
- [ ] Create reminder with time: "14:00" (2:00 PM)
- [ ] Verify time badge shows "2:00 PM" (12-hour format)
- [ ] Verify time icon (🕐) appears
- [ ] Create reminder with NO time → No time badge shown
- [ ] **Backend verification:** Time stored as "14:00:00" (HH:MM:SS format)

### Location Field (location_text)
- [ ] Create reminder with location: "Home Depot"
- [ ] Verify location badge shows with pin icon (📍)
- [ ] Create reminder with NO location → No badge shown
- [ ] Edit reminder → Location persists correctly

### Time Required Field (boolean)
- [ ] Create reminder with "Time-sensitive task" checked
- [ ] Verify "Time-sensitive" badge shows with timer icon (⏱)
- [ ] Create reminder with checkbox unchecked
- [ ] Verify no time-sensitive badge shown
- [ ] **Backend verification:** Stored as `true`/`false` boolean

---

## 4. Error Handling & Validation

### Invalid Token (401)
- [ ] Edit `config.json` → Change token to invalid value
- [ ] Refresh page → Try to load reminders
- [ ] Verify red error toast: "Failed to load reminders: Unauthorized"
- [ ] Check console for "[API Error] 401" log
- [ ] **Fix:** Restore valid token in config.json

### Network Down (Offline)
- [ ] Stop backend server (Ctrl+C)
- [ ] Try to create reminder
- [ ] Verify yellow warning toast: "Retrying... (attempt X/3)"
- [ ] After 3 retries → Red error toast: "Failed to create reminder: Network error"
- [ ] **Fix:** Restart backend server

### Missing Reminder (404)
- [ ] Navigate to edit.html?id=nonexistent-uuid
- [ ] Verify error toast: "Reminder not found"
- [ ] No JavaScript errors in console

### Validation Error (400)
- [ ] Try to create reminder with empty text field
- [ ] Browser validation prevents submit
- [ ] **Backend test (manual):** Send POST with invalid priority
- [ ] Verify error toast shows validation message

### Malformed Response
- [ ] **Backend test (optional):** Temporarily break API response
- [ ] Verify error toast shows graceful error message
- [ ] No unhandled exceptions in console

---

## 5. Toast Notification System

### Success Toasts (Green)
- [ ] Create reminder → "Reminder created!" (3 sec auto-dismiss)
- [ ] Update reminder → "Reminder updated!" (3 sec)
- [ ] Delete reminder → "Reminder deleted!" (3 sec)
- [ ] Complete reminder → "Reminder completed!" (3 sec)
- [ ] Verify green background color
- [ ] Verify auto-dismiss after 3 seconds

### Error Toasts (Red)
- [ ] Trigger error (e.g., invalid token)
- [ ] Verify red error toast appears
- [ ] Verify error message is descriptive
- [ ] Verify auto-dismiss after 5 seconds
- [ ] Verify red background color

### Warning Toasts (Yellow)
- [ ] Trigger network retry (stop backend)
- [ ] Verify yellow warning toast: "Retrying..."
- [ ] Verify retry count shown
- [ ] Verify toast updates on each retry

### Toast Stacking
- [ ] Trigger multiple toasts quickly
- [ ] Verify toasts stack vertically
- [ ] Verify older toasts auto-dismiss
- [ ] No overlapping or layout issues

---

## 6. API Integration Tests

### Endpoint: GET /reminders
- [ ] Filter by status: `?status=pending`
- [ ] Filter by category: `?category=Work`
- [ ] Filter by priority: `?priority=urgent`
- [ ] Verify pagination object returned
- [ ] Verify `data` array contains reminders

### Endpoint: GET /reminders/:id
- [ ] Valid ID → Returns reminder object
- [ ] Invalid ID → Returns 404
- [ ] Verify all fields present in response

### Endpoint: POST /reminders
- [ ] Create with all fields → Success (201)
- [ ] Create with only text → Success (defaults applied)
- [ ] Create with invalid priority → Error (400)
- [ ] Verify `created_at` and `updated_at` timestamps set

### Endpoint: PATCH /reminders/:id
- [ ] Update single field → Only that field changes
- [ ] Update multiple fields → All changes persist
- [ ] Update with invalid data → Error (400)
- [ ] Verify `updated_at` timestamp changes

### Endpoint: DELETE /reminders/:id
- [ ] Delete existing reminder → Success (204)
- [ ] Delete nonexistent reminder → Error (404)
- [ ] Verify soft delete (status='deleted', deleted_at set)

### Endpoint: GET /health
- [ ] Navigate to http://localhost:8000/api/health
- [ ] Verify JSON response: `{"status": "ok", "database": "connected"}`

---

## 7. Data Integrity & Timestamps

### Timestamps (Backend-generated)
- [ ] Create reminder → Check `created_at` is set
- [ ] Create reminder → Check `updated_at` is set
- [ ] Create reminder → Verify `created_at` == `updated_at`
- [ ] Update reminder → Verify `updated_at` changes
- [ ] Update reminder → Verify `created_at` unchanged
- [ ] Complete reminder → Verify `completed_at` is set
- [ ] Delete reminder → Verify `deleted_at` is set

### Time Format Normalization
- [ ] Enter time "14:00" in form (HH:MM)
- [ ] **Backend verification:** Check database shows "14:00:00" (HH:MM:SS)
- [ ] Edit reminder → Time displays as "14:00" (HH:MM in form)
- [ ] Card shows "2:00 PM" (12-hour format)

### Boolean Fields
- [ ] `time_required` checkbox checked → Stored as `true` (or 1 in SQLite)
- [ ] `time_required` checkbox unchecked → Stored as `false` (or 0 in SQLite)
- [ ] Verify no string "on" or "off" stored

### Null Handling
- [ ] Create reminder with no category → `category: null` in database
- [ ] Create reminder with no location → `location_text: null` in database
- [ ] Create reminder with no time → `due_time: null` in database

---

## 8. Mobile UI & Animations

### Swipe-to-Delete (Mobile)
- [ ] **Mobile test:** Swipe reminder card left
- [ ] Verify red delete overlay appears
- [ ] Complete swipe → Reminder deleted
- [ ] Check green toast: "Reminder deleted!"

### Completion Animation
- [ ] Check reminder checkbox
- [ ] Verify completion animation plays:
  - [ ] Fade out effect
  - [ ] Shrink scale effect
  - [ ] Smooth transition
- [ ] Card disappears after animation completes

### Touch Interactions
- [ ] **Mobile test:** Tap reminder card → Opens edit form
- [ ] **Mobile test:** Tap checkbox → Completes reminder
- [ ] **Mobile test:** Tap FAB "+" button → Opens new form
- [ ] No accidental triggers or double-taps

### Responsive Layout
- [ ] Resize browser to mobile width (< 600px)
- [ ] Verify layout stacks vertically
- [ ] Verify buttons remain tappable
- [ ] Verify text wraps correctly

---

## 9. Performance & User Experience

### Page Load Time
- [ ] Today view loads in < 1 second
- [ ] Upcoming view loads in < 1 second
- [ ] Edit form loads in < 500ms

### API Response Time
- [ ] Create reminder completes in < 500ms
- [ ] Update reminder completes in < 500ms
- [ ] Delete reminder completes in < 500ms
- [ ] List reminders completes in < 1 second

### Smooth Interactions
- [ ] No lag when clicking cards
- [ ] No lag when checking checkboxes
- [ ] Form inputs respond immediately
- [ ] Animations play smoothly (60fps)

### Browser Console
- [ ] No JavaScript errors logged
- [ ] No unhandled promise rejections
- [ ] API calls logged clearly
- [ ] Error messages are helpful

---

## 10. Edge Cases & Stress Tests

### Large Data Sets
- [ ] Create 50+ reminders
- [ ] Verify Today view renders all correctly
- [ ] Verify Upcoming view groups properly
- [ ] No performance degradation

### Long Text Content
- [ ] Create reminder with 500+ character text
- [ ] Verify card renders without breaking layout
- [ ] Verify edit form handles long text

### Date Edge Cases
- [ ] Create reminder for today at 23:59
- [ ] Create reminder for tomorrow at 00:01
- [ ] Create reminder for 1 year in future
- [ ] Verify all dates handled correctly

### Empty States
- [ ] Delete all reminders
- [ ] Verify Today view shows empty state
- [ ] Verify Upcoming view shows empty state
- [ ] Empty states have helpful text

### Browser Compatibility
- [ ] Test in Chrome (latest)
- [ ] Test in Firefox (latest)
- [ ] Test in Safari (latest)
- [ ] Test in mobile Safari (iOS)
- [ ] Test in Chrome mobile (Android)

---

## Known Issues

**Document any bugs or issues found during testing:**

1. [Issue description]
   - **Steps to reproduce:** [...]
   - **Expected:** [...]
   - **Actual:** [...]
   - **Severity:** Critical / Major / Minor

---

## Testing Notes

**Record observations, suggestions, and any additional findings:**

---

## Sign-Off

- [ ] All critical tests passed
- [ ] All known issues documented
- [ ] Phase 3 integration verified
- [ ] Ready for Phase 4 (Cloudflare Workers deployment)

**Tester Signature:** ___________________
**Date Completed:** ___________________

---

**Phase 3 Status:** ✅ READY FOR USER TESTING
**Next Phase:** Phase 4 - Cloudflare Workers + D1 (Cloud Sync)
