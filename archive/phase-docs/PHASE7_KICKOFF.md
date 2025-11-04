# Phase 7: Recurring Reminders - Kickoff Document

## Quick Start
- Current status: Phase 6 complete (backend), Phase 7 ready to start
- Database: SQLite + D1 (cloud)
- Backend: FastAPI (local) + Cloudflare Workers (cloud)
- Frontend: Vanilla JS/HTML/CSS

## What's Already Done
- Phases 1-6 complete (see TODOS.md)
- Database schema has `recurrence_patterns` table placeholder (not implemented)
- Database has `recurrence_id` field in reminders table

## Phase 7 Goal
Implement recurring reminders with patterns like:
- "Every Tuesday at 3pm"
- "Daily for 30 days"
- "Every other week"
- "Monthly on the 15th"

## Architecture Overview

### Database Schema Needed
**reminders table (existing):**
- Already has: `recurrence_id TEXT` (foreign key to recurrence_patterns)
- Already has: `is_recurring_instance INTEGER DEFAULT 0` (in D1 schema)
- Already has: `original_due_date TEXT` (in D1 schema)

**recurrence_patterns table (needs implementation):**
```sql
CREATE TABLE recurrence_patterns (
    id TEXT PRIMARY KEY,
    frequency TEXT CHECK(frequency IN ('daily', 'weekly', 'monthly', 'yearly')),
    interval INTEGER DEFAULT 1,
    days_of_week TEXT,  -- JSON array like ["monday", "wednesday"]
    day_of_month INTEGER,
    month_of_year INTEGER,
    end_date TEXT,
    end_count INTEGER,
    created_at TEXT NOT NULL
)
```

### Implementation Steps

**1. Database (Start Here)**
- Create migration for local SQLite (server/database.py)
- Create migration for D1 cloud (workers/migrations/004_recurring_patterns.sql)
- Add database functions for CRUD on recurrence_patterns
- Deploy D1 migration: `npx wrangler d1 migrations apply reminders-db`

**2. Backend API**
- Add recurrence models to server/models.py
- Add recurrence endpoints to server/main.py:
  * POST /api/reminders (update to accept recurrence_pattern)
  * GET /api/recurrence-patterns (optional, for UI)
  * Helper function: generate_instances(pattern, start_date, count)
- Add same to workers/src/index.ts

**3. Frontend**
- Add recurrence UI to public/edit.html:
  * Frequency selector (daily/weekly/monthly/yearly)
  * Interval input (every N days/weeks)
  * Days of week checkboxes (for weekly)
  * Day of month selector (for monthly)
  * End conditions (date, count, or never)
- Update public/js/app.js to display recurrence info
- Add instance generation logic

**4. Key Design Decisions**
- **Instance generation:** Server-side on create/edit (not real-time)
- **Editing:** "This instance" vs "All future" vs "Entire series"
- **Deletion:** Same options as editing
- **Sync:** Recurrence patterns sync separately from instances

## Files You'll Need to Modify

**Backend:**
- server/database.py - Add recurrence_patterns table, CRUD functions
- server/models.py - Add RecurrencePattern model
- server/main.py - Add recurrence endpoints

**Cloud:**
- workers/migrations/004_recurring_patterns.sql - New migration
- workers/src/index.ts - Add recurrence endpoints

**Frontend:**
- public/edit.html - Add recurrence UI section
- public/js/app.js - Display recurrence info
- public/css/edit.css - Style recurrence controls

**Tests:**
- tests/test_recurrence.py - Test pattern generation

## Example User Stories

1. **"Remind me to take vitamins every morning at 8am"**
   - frequency: daily, interval: 1, due_time: 08:00, end: never

2. **"Team meeting every Tuesday and Thursday at 2pm"**
   - frequency: weekly, interval: 1, days_of_week: ["tuesday", "thursday"], due_time: 14:00

3. **"Rent due on the 1st of every month"**
   - frequency: monthly, interval: 1, day_of_month: 1

4. **"Dentist appointment every 6 months"**
   - frequency: monthly, interval: 6

## Testing Checklist
- [ ] Can create daily recurring reminder
- [ ] Can create weekly recurring reminder with specific days
- [ ] Can create monthly recurring reminder
- [ ] Generated instances appear in correct date buckets
- [ ] Can edit "this instance only"
- [ ] Can edit "all future instances"
- [ ] Can delete "this instance only"
- [ ] Can delete "entire series"
- [ ] Recurrence syncs to cloud correctly

## Resources
- TODOS.md - Phase 7 detailed checklist
- NEXT_STEPS.md - Phase 7 immediate steps
- Database schema: server/database.py lines 91-113

## Quick Commands

```bash
# Start backend
python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend
cd public && python -m http.server 3000

# Run tests
pytest tests/

# Deploy to Cloudflare Workers
npx wrangler deploy
```

## Success Criteria
- ✅ Can create recurring reminders with various patterns
- ✅ Instances generate correctly
- ✅ Can edit/delete individual instances vs series
- ✅ Recurrence syncs between local/cloud
- ✅ UI displays recurrence info clearly

Estimated time: 8-10 hours

---

**Ready to start? Begin with Step 1: Database Schema Implementation**