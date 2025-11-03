# Priority Enhancement Requirements Analysis

**Phase:** 3.6 Research
**Subagent:** Requirements Analysis
**Date:** November 3, 2025

---

## Executive Summary

Expanding priority system from 3 levels to 5 levels for better ADHD task management:
- **Add:** 🔵 Someday (Blue) - Future ideas, no timeline
- **Add:** 🟠 Waiting (Orange) - Blocked/on hold
- **Keep:** 🟢 Chill, 🟡 Important, 🔴 Urgent

**Scope:** 7 files to modify, 4 new test cases
**Estimated Time:** 45-60 minutes (3 subagents)
**Risk:** Low - backward compatible, database can be safely recreated

---

## Current Implementation

### Backend
- **Database Schema** (`server/database.py` line 72):
  ```sql
  priority TEXT CHECK(priority IN ('chill', 'important', 'urgent')) DEFAULT 'chill'
  ```

- **API Models** (`server/models.py`):
  - Line 30: `Literal["chill", "important", "urgent"]` (ReminderCreate)
  - Line 70: `Optional[Literal["chill", "important", "urgent"]]` (ReminderUpdate)

### Frontend
- **HTML Form** (`public/edit.html` lines 47-60): 3 radio buttons
- **CSS Variables** (`public/css/main.css` lines 16-21):
  - `--color-chill: #4CAF50` (Green)
  - `--color-important: #FFC107` (Yellow)
  - `--color-urgent: #F44336` (Red)
- **CSS Badge Classes** (`public/css/main.css` lines 292-305): 3 badge styles
- **JavaScript Display** (`public/js/app.js` lines 173-180): 3 badge mappings
- **JavaScript Sorting** (`public/js/api.js` lines 302, 350): Priority order

### Tests
- **Test Coverage** (`tests/test_api.py`): Tests for 3 priorities

---

## Proposed Enhancement

### New Priority Levels

| Priority | Color | Hex | Emoji | Use Case |
|----------|-------|-----|-------|----------|
| Someday | Blue | #2196F3 | 🔵 | Future ideas, no timeline, lower than Chill |
| Chill | Green | #4CAF50 | 🟢 | Low priority [EXISTING] |
| Important | Yellow | #FFC107 | 🟡 | Medium priority [EXISTING] |
| Urgent | Red | #F44336 | 🔴 | High priority [EXISTING] |
| Waiting | Orange | #FF9800 | 🟠 | Blocked by external dependency |

**ADHD-Friendly Rationale:**
- **Someday** - Captures ideas without cluttering urgent views
- **Waiting** - Acknowledges blockers, reduces mental load

---

## Required Changes

### 1. Backend: server/database.py

**Line 72:**
```python
# BEFORE:
priority TEXT CHECK(priority IN ('chill', 'important', 'urgent')) DEFAULT 'chill',

# AFTER:
priority TEXT CHECK(priority IN ('someday', 'chill', 'important', 'urgent', 'waiting')) DEFAULT 'chill',
```

**Migration Strategy:** SQLite doesn't support ALTER COLUMN with CHECK. Use `python server/database.py --force` to recreate (safe - database was cleaned in Phase 3.5).

---

### 2. Backend: server/models.py

**Line 30 (ReminderCreate):**
```python
# BEFORE:
priority: Literal["chill", "important", "urgent"] = Field("chill", ...)

# AFTER:
priority: Literal["someday", "chill", "important", "urgent", "waiting"] = Field("chill", ...)
```

**Line 70 (ReminderUpdate):**
```python
# BEFORE:
priority: Optional[Literal["chill", "important", "urgent"]] = None

# AFTER:
priority: Optional[Literal["someday", "chill", "important", "urgent", "waiting"]] = None
```

---

### 3. Frontend: public/edit.html

**Lines 47-60 (Add 2 radio buttons):**
```html
<!-- Add at beginning (before chill): -->
<label class="priority-option">
    <input type="radio" name="priority" value="someday">
    <span class="priority-badge someday">🔵 Someday</span>
</label>

<!-- Add at end (after urgent): -->
<label class="priority-option">
    <input type="radio" name="priority" value="waiting">
    <span class="priority-badge waiting">🟠 Waiting</span>
</label>
```

---

### 4. Frontend: public/css/main.css

**Add after line 21 (Color Variables):**
```css
--color-someday: #2196F3;         /* Blue */
--color-someday-light: #E3F2FD;
--color-waiting: #FF9800;         /* Orange */
--color-waiting-light: #FFF3E0;
```

**Add after line 305 (Badge Classes):**
```css
.priority-badge.someday {
    background-color: var(--color-someday-light);
    color: var(--color-someday);
}

.priority-badge.waiting {
    background-color: var(--color-waiting-light);
    color: #E65100; /* Darker orange for readability */
}
```

---

### 5. Frontend: public/js/app.js

**Lines 173-180 (Badge Display Function):**
```javascript
// Add two new entries:
someday: '<span class="priority-badge someday">🔵 Someday</span>',
waiting: '<span class="priority-badge waiting">🟠 Waiting</span>'
```

---

### 6. Frontend: public/js/api.js

**Line 302 (Today View Sorting):**
```javascript
// BEFORE:
const priorityOrder = { urgent: 0, important: 1, chill: 2 };

// AFTER:
const priorityOrder = { urgent: 0, important: 1, chill: 2, someday: 3, waiting: 4 };
```

**Line 350 (Upcoming View Sorting):**
```javascript
// Same change as above
```

**Sorting Logic:** Urgent → Important → Chill → Someday → Waiting
(Blocked items sort last to avoid clutter)

---

### 7. Tests: tests/test_api.py

**Add 4 New Test Cases:**
1. `test_create_reminder_with_someday_priority()` - Verify API accepts 'someday'
2. `test_create_reminder_with_waiting_priority()` - Verify API accepts 'waiting'
3. `test_list_reminders_filter_by_someday()` - Test filtering by 'someday'
4. `test_list_reminders_filter_by_waiting()` - Test filtering by 'waiting'

---

## Affected Components

### Files to Modify (7):
1. ✅ `server/database.py` - CHECK constraint
2. ✅ `server/models.py` - Pydantic Literals (2 locations)
3. ✅ `public/edit.html` - Radio buttons
4. ✅ `public/css/main.css` - Colors and badge styles
5. ✅ `public/js/app.js` - Badge display
6. ✅ `public/js/api.js` - Sorting logic (2 locations)
7. ✅ `tests/test_api.py` - New test cases

### Files That DON'T Need Changes:
- `public/index.html` - Renders via JavaScript
- `public/upcoming.html` - Renders via JavaScript
- `public/future.html` - Renders via JavaScript
- `public/js/storage.js` - Mock data (optional)

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Database migration fails | Low | Database clean, use --force flag safely |
| Backward compatibility broken | Low | Default stays 'chill', existing data unaffected |
| UI layout breaks with 5 buttons | Low | Flexbox adapts, test on mobile |
| Color accessibility issues | Medium | Test with colorblind simulator later |
| Test coverage drops | Low | Add 4 tests to maintain 80%+ |

---

## Implementation Sequence

### Subagent 2: Backend (15-20 min)
- Update `server/database.py` CHECK constraint
- Update `server/models.py` Literal types (2 locations)
- Recreate database: `python server/database.py --force`
- Test via Swagger UI: Create reminders with 'someday' and 'waiting'
- **Commit:** `feat: Expand backend priority system to 5 levels (someday, waiting)`

### Subagent 3: Frontend (15-20 min)
- Update `public/edit.html` - Add 2 radio buttons
- Update `public/css/main.css` - Add colors and badge styles
- Update `public/js/app.js` - Add badge mappings
- Update `public/js/api.js` - Update sort order (2 locations)
- Manual test: Create reminders with all 5 priorities
- **Commit:** `feat: Add someday and waiting priority options to UI`

### Subagent 4: Testing (10-15 min)
- Add 4 test cases to `tests/test_api.py`
- Run: `pytest tests/ -v --cov=server`
- Verify 80%+ coverage maintained
- Manual UI testing across all 3 views
- **Commit:** `test: Add coverage for 5-level priority system`

---

## Success Criteria

- ✅ Database accepts all 5 priority values
- ✅ API validates all 5 priority values
- ✅ UI displays all 5 priority badges with correct colors
- ✅ Sorting logic works with new priorities
- ✅ Tests pass (80%+ coverage)
- ✅ Manual testing successful (create/view/filter)
- ✅ 3 atomic commits in git history

---

## Color Accessibility Reference

**Contrast Ratios (WCAG AA):**
- Blue (#2196F3) on white: 3.1:1 ⚠️ (use dark text on light background)
- Orange (#FF9800) on white: 2.3:1 ⚠️ (use darker #E65100 for text)
- Green (#4CAF50) on white: 3.0:1 ✅ (existing, acceptable)
- Yellow (#FFC107) on white: 1.8:1 ⚠️ (existing, use dark text)
- Red (#F44336) on white: 3.9:1 ✅ (existing, acceptable)

**Implementation:** All priorities use light backgrounds with dark text for accessibility.

---

## Next Steps

**Ready for Subagent 2:** Backend implementation
**Context to Pass:** This analysis document + file paths
**Estimated Time:** 15-20 minutes
**Commit Type:** `feat:`

---

*Analysis completed by Subagent 1*
*Phase: Research*
*Generated: November 3, 2025*
