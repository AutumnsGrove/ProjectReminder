# Next Steps - ADHD-Friendly Voice Reminders System

**Session Date:** November 3, 2025
**Current Phase:** Phase 4 - Cloudflare Workers
**Status:** ✅ Phase 1, 2, 3 & 3.5 Complete | 🎉 TESTED & READY FOR CLOUD SYNC!

---

## 🎉 Latest Update: Phase 3.5 Testing & Enhancements COMPLETE!

**Just Completed (November 3, 2025):**
- ✅ **Bug Investigation** - "Reminders don't save" issue was UX gap, not code bug
- ✅ **Race condition already fixed** - Commit 7d686fe resolved 401 errors
- ✅ **Real issue found** - Reminders >7 days out had no view to display them
- ✅ **Future view added** - Third time-horizon page for reminders 8+ days out
- ✅ **Testing infrastructure** - 24 pytest tests with 80% code coverage
  - 18 API tests (all endpoints + auth + filtering)
  - 6 database tests (CRUD operations)
  - test_api.py, test_database.py, conftest.py created
- ✅ **Database cleaned** - Flushed test data, ready for Phase 4
- ✅ **All 3 commits** - 7e9b727 (Future view), ee725da (docs), c85bbd7 (tests)

**How to Run:**
```bash
# Terminal 1: Backend
uv run uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: UI
python serve_ui.py

# Open: http://localhost:3000
# Views: Today (0-1 days), Upcoming (2-7 days), Future (8+ days)

# Run tests
pytest tests/ -v --cov=server
```

**The app now has:**
- Three complete time-horizon views
- 24 automated tests (80% coverage)
- Clean database ready for cloud sync

---

## What Was Just Completed (Phase 2)

✅ **Web UI Implementation**
- Created mobile-first responsive web interface (320px - 768px+)
- Built Today view with overdue, today's tasks, and floating sections
- Built Upcoming view with date-grouped reminders
- Implemented comprehensive edit/create form with all reminder fields
- Added ADHD-friendly design: high contrast, clear typography, priority colors
- Created completion animation (checkbox → fade → slide up)
- Implemented swipe-to-delete gesture for mobile
- Built modular JavaScript architecture (app.js, api.js, storage.js, animations.js)
- Added config.json for settings management
- Stubbed API client to work with localStorage mock data

✅ **Technical Achievements**
- HTML: 3 pages (index.html, upcoming.html, edit.html)
- CSS: 4 stylesheets (main.css, today.css, upcoming.css, edit.css)
- JavaScript: 4 modules with clean separation of concerns
- Priority system: 🟢 Chill (green) / 🟡 Important (yellow) / 🔴 Urgent (red)
- Animations: Smooth completion and swipe gestures
- Mock data: 5 sample reminders persisted in localStorage
- Testing server: serve_ui.py for local development
- All Phase 2 success criteria met and verified

**Previously Completed (Phase 1):**
- ✅ FastAPI REST API server with full CRUD operations
- ✅ SQLite database with complete reminders schema
- ✅ Bearer token authentication
- ✅ Swagger UI at http://localhost:8000/docs

---

## Phase 3: Integration ✅ COMPLETE

**Goal:** Connect the Web UI to the FastAPI backend and replace mock data with real API calls

**What Was Completed:**
- ✅ Implemented real fetch() calls in api.js to FastAPI endpoints
- ✅ Added bearer token authentication headers
- ✅ Replaced localStorage mock data with API responses
- ✅ Added comprehensive error handling with toast notifications
- ✅ Implemented retry logic for network failures
- ✅ Added graceful error messages for all failure modes
- ✅ Created errors.js module with reusable error handling utilities
- ✅ Updated UI to handle API client changes (getTodayReminders structure)
- ✅ Fixed script loading order (storage.js → errors.js → api.js)
- ✅ Created comprehensive integration testing checklist (INTEGRATION_TESTING.md)

**Technical Achievements:**
- Subagent 1 (bd0ee1c): Aligned data model and removed unused fields
- Subagent 2 (bde18c1): Updated UI field references (location_name → location_text)
- Subagent 3 (6111da3): Built error handling infrastructure with toast notifications
- Subagent 4 (0a41caa): Implemented real API client with retry logic
- Subagent 5 (current): Fixed breaking changes, verified integration, documented testing

**Files Modified:**
- `public/js/api.js` - Real API client (~240 insertions, ~180 deletions)
- `public/js/errors.js` - Error handling utilities (~350 lines new)
- `public/css/main.css` - Toast notification styles (~200 lines added)
- `public/js/app.js` - Updated for new API structure
- `public/*.html` - Fixed script loading order (3 files)

**Quick Start Commands:**
```bash
# Terminal 1: Start the FastAPI server
uv run uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start the UI server
python serve_ui.py

# API Server: http://localhost:8000
# UI Server: http://localhost:3000
# Swagger docs: http://localhost:8000/docs
# API token: (stored in secrets.json and config.json)
```

**Testing:**
See `INTEGRATION_TESTING.md` for comprehensive manual test checklist covering:
- CRUD operations
- All UI views
- Error handling scenarios
- Toast notifications
- Data integrity
- Edge cases

---

## Priority System Enhancement (Next Session) ✅ DECISION MADE

**Current Priority Levels (3):**
- 🟢 **Chill** (Green) - Low priority, no time pressure
- 🟡 **Important** (Yellow) - Medium priority, should be done
- 🔴 **Urgent** (Red) - High priority, time-sensitive

**NEW Priority Levels to Add (2):**
- 🔵 **Someday** (Blue) - Future ideas, no timeline, lower than Chill
- 🟠 **Waiting** (Orange) - Blocked by external dependency, special state

**Final Priority System (5 levels):**
1. 🔵 Someday - Backlog, ideas, no rush
2. 🟢 Chill - Low priority
3. 🟡 Important - Medium priority
4. 🔴 Urgent - High priority
5. 🟠 Waiting - Blocked/on hold

**Rationale:**
- Simple: Only 5 levels, avoids decision paralysis (ADHD-friendly)
- "Someday" captures future ideas without cluttering Today/Upcoming
- "Waiting" acknowledges external blockers (reduces mental load)
- Color palette: Blue/Green/Yellow/Red/Orange (distinct, accessible)

**Implementation Tasks for Next Session:**
1. **Database Schema** (`server/database.py`, `server/models.py`)
   - Update priority CHECK constraint: Add 'someday' and 'waiting'
   - Migration: ALTER TABLE (or recreate for SQLite)

2. **Backend** (`server/main.py`)
   - Update Pydantic models priority Literal type
   - Test API with new priority values

3. **Frontend** (`public/edit.html`, `public/css/*.css`)
   - Add 2 new radio buttons to priority selector
   - Add blue/orange color classes
   - Update priority badge CSS

4. **Tests** (`tests/test_api.py`)
   - Add test cases for new priority levels
   - Verify filtering works with all 5 levels

**Estimated Time:** 45-60 minutes

---

## Phase 4: Cloudflare Workers + D1 - READY TO START

**Goal:** Deploy serverless cloud sync layer for multi-device support

**Key Deliverables:**
- Create Cloudflare Worker for cloud API
- Set up D1 database (SQLite at the edge)
- Implement bidirectional sync logic
- Add conflict resolution (last-write-wins for MVP)
- Update frontend to switch local ↔ cloud
- Test offline-first behavior

**Estimated Time:** 3-4 hours

**Prerequisites:**
- ✅ Local FastAPI backend working (Phase 1)
- ✅ Web UI complete (Phase 2)
- ✅ Integration tested (Phase 3)
- ✅ Testing infrastructure in place (Phase 3.5)
- ✅ Database cleaned and ready
- ✅ All 3 time-horizon views functional
- [ ] Cloudflare account created
- [ ] Wrangler CLI installed

**Current System Status:**
- Local API: Stable and tested
- UI: 3 views (Today/Upcoming/Future)
- Database: Clean, schema verified
- Tests: 24 passing, 80% coverage
- Ready for cloud deployment

**Quick Start:**
```bash
# Install Wrangler
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Create D1 database
wrangler d1 create reminders-prod

# Deploy Worker
wrangler deploy
```

**See TODOS.md Phase 4 section for detailed implementation steps.**

---

## Important Configuration Notes

### MapBox Token Setup (For Phase 6 - Location Features)

When creating your MapBox token, use these URL restrictions:
```
http://localhost:8000
http://localhost:3000
http://127.0.0.1:8000
http://127.0.0.1:3000
```

Or select **"No restrictions"** for development (public tokens are safe for client-side use).

Once obtained, update `secrets.json`:
```json
{
  "api_token": "YOUR_GENERATED_TOKEN_HERE",
  "mapbox_access_token": "pk.YOUR_MAPBOX_TOKEN_HERE"
}
```

**Generate your api_token with:** `openssl rand -hex 32` or `python3 -c "import secrets; print(secrets.token_hex(32))"`

---

## Phase 1 Reference (For New Sessions)

### Pre-Flight Checklist

Before starting Phase 1, ensure these are ready:

### 1. Environment Setup
```bash
# Check Python version (need 3.11+)
python3 --version

# Check if UV is installed
uv --version
# If not: pip install uv

# Verify git is configured
git config user.name
git config user.email
```

### 2. API Keys
- [ ] Get MapBox access token from https://account.mapbox.com/ (free tier)
- [ ] Generate strong random API token for bearer auth (use: `openssl rand -hex 32`)
- [ ] Create `secrets.json` from `ClaudeUsage/templates/secrets_template.json`
- [ ] Verify `secrets.json` is in `.gitignore`

### 3. Review Key Documents
- [ ] Read `reminders-project-spec.md` - Database Schema section (lines 150-230)
- [ ] Read `reminders-project-spec.md` - API Specification section (lines 269-540)
- [ ] Read `ClaudeUsage/db_usage.md` - Database.py template and patterns
- [ ] Read `ClaudeUsage/uv_usage.md` - Python dependency management

---

## Phase 1: Core Backend - Implementation Order

### Step 1: Project Setup (15 minutes)

**Goal:** Initialize Python environment and project structure

**Tasks:**
1. Initialize UV project
   ```bash
   uv init
   ```

2. Add FastAPI dependencies
   ```bash
   uv add fastapi uvicorn sqlalchemy pydantic python-multipart
   ```

3. Create directory structure
   ```bash
   mkdir -p server
   touch server/__init__.py
   touch server/main.py
   touch server/database.py
   touch server/models.py
   touch server/config.py
   ```

4. Create secrets.json
   ```bash
   cp ClaudeUsage/templates/secrets_template.json secrets.json
   # Then edit with real tokens
   ```

5. Verify `.gitignore` includes:
   - `secrets.json`
   - `reminders.db`
   - `__pycache__/`
   - `.venv/`
   - `*.pyc`

**Reference:** `ClaudeUsage/uv_usage.md`, `README.md` (Getting Started section)

---

### Step 2: Database Layer (30-45 minutes)

**Goal:** Create SQLite database with full schema

**Create `server/database.py`:**
- Follow template in `ClaudeUsage/db_usage.md`
- Implement full reminders table schema from spec (lines 158-201)
- Include all fields: id, text, due_date, due_time, time_required, location fields, priority, category, status, timestamps, etc.
- Add indexes: `idx_reminders_due_date`, `idx_reminders_status`, `idx_reminders_category`, `idx_reminders_priority`, `idx_reminders_location`
- Create seed data function with default categories: ["Personal", "Work", "Errands", "Home", "Health", "Calls", "Shopping", "Projects"]
- Add initialization script that runs when executed directly

**Key Points:**
- Use SQLite TEXT for dates/times (ISO 8601 format: "2025-11-03T15:00:00Z")
- Use TEXT PRIMARY KEY for UUID v4 IDs
- Use CHECK constraints for status ('pending', 'completed', 'snoozed') and priority ('chill', 'important', 'urgent')
- Follow database.py pattern: all SQL isolated, function-based interface

**Test:**
```bash
python server/database.py  # Should create reminders.db
sqlite3 reminders.db ".schema"  # Verify schema
sqlite3 reminders.db "SELECT * FROM reminders;"  # Should be empty initially
```

**Reference:** `reminders-project-spec.md` (Database Schema section, lines 150-267)

---

### Step 3: Configuration & Models (30 minutes)

**Create `server/config.py`:**
```python
import os
import json
from pathlib import Path

# Load secrets
def load_secrets():
    secrets_path = Path(__file__).parent.parent / "secrets.json"
    try:
        with open(secrets_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: secrets.json not found. Using env vars.")
        return {}

SECRETS = load_secrets()

# Database
DB_PATH = Path(__file__).parent.parent / "reminders.db"

# Authentication
API_TOKEN = SECRETS.get("api_token", os.getenv("API_TOKEN", ""))

# CORS (allow local development)
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
    "null"  # For file:// protocol during development
]

# Server
HOST = "0.0.0.0"
PORT = 8000
DEBUG = True
```

**Create `server/models.py`:**
- Create Pydantic models for:
  - `ReminderCreate` (request body for POST)
  - `ReminderUpdate` (request body for PATCH)
  - `ReminderResponse` (response model)
  - `ReminderListResponse` (list with pagination metadata)
  - `HealthResponse` (health check)
- Use Optional for nullable fields
- Add Field validators for priority, status
- Match database schema exactly

**Reference:** `reminders-project-spec.md` (API Specification section, lines 269-420), FastAPI docs for Pydantic models

---

### Step 4: FastAPI Application (45-60 minutes)

**Create `server/main.py`:**

**Implement:**
1. FastAPI app initialization
2. CORS middleware (using config.CORS_ORIGINS)
3. Bearer token authentication dependency
   ```python
   from fastapi import Depends, HTTPException, Header

   async def verify_token(authorization: str = Header(None)):
       if not authorization or not authorization.startswith("Bearer "):
           raise HTTPException(status_code=401, detail="Missing or invalid token")
       token = authorization.replace("Bearer ", "")
       if token != config.API_TOKEN:
           raise HTTPException(status_code=401, detail="Invalid token")
       return token
   ```

4. Health check endpoint:
   - `GET /api/health`
   - Returns: status, version, database connectivity, timestamp

5. CRUD endpoints (all require authentication):
   - `POST /api/reminders` - Create reminder (generate UUID, set created_at/updated_at)
   - `GET /api/reminders` - List with filters (status, category, priority, limit, offset)
   - `GET /api/reminders/{id}` - Get single reminder (404 if not found)
   - `PATCH /api/reminders/{id}` - Update reminder (update updated_at timestamp)
   - `DELETE /api/reminders/{id}` - Delete reminder (204 on success)

**Important Details:**
- Generate UUIDs server-side: `import uuid; str(uuid.uuid4())`
- ISO 8601 timestamps: `from datetime import datetime, timezone; datetime.now(timezone.utc).isoformat()`
- When completing reminder: set `status='completed'` and `completed_at=<timestamp>`
- Handle 404s for missing reminders
- Return proper HTTP status codes (200, 201, 204, 400, 401, 404)

**Reference:** `reminders-project-spec.md` (API Specification, lines 269-420), `ClaudeUsage/db_usage.md`

---

### Step 5: Testing & Validation (30 minutes)

**Start the server:**
```bash
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

**Test via Swagger UI:**
1. Open http://localhost:8000/docs
2. Test `/api/health` endpoint (should work without auth)
3. Click "Authorize" button, enter: `Bearer YOUR_TOKEN` (from secrets.json)
4. Test creating a reminder:
   ```json
   {
     "text": "Test reminder",
     "priority": "chill",
     "category": "Personal"
   }
   ```
5. Test listing reminders
6. Test getting single reminder by ID
7. Test updating reminder (change text or priority)
8. Test deleting reminder

**Test via curl:**
```bash
# Health check (no auth)
curl http://localhost:8000/api/health

# Create reminder (with auth)
curl -X POST http://localhost:8000/api/reminders \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Call mom about Thanksgiving",
    "due_date": "2025-11-03",
    "priority": "important",
    "category": "Calls"
  }'

# List reminders
curl http://localhost:8000/api/reminders \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Validate:**
- ✅ Can create reminders with all fields
- ✅ Can list reminders (pagination works)
- ✅ Can get single reminder by ID
- ✅ Can update reminder (text, priority, status)
- ✅ Can delete reminder
- ✅ Authentication blocks unauthorized requests
- ✅ Database persists data between server restarts
- ✅ Swagger docs are complete and accurate

---

## Phase 1 Success Criteria

Before moving to Phase 2, ensure:

- ✅ API running on localhost:8000
- ✅ Swagger docs accessible at /docs
- ✅ Can create/read/update/delete reminders via API
- ✅ Authentication works (valid token = access, invalid = 401)
- ✅ Database persists data (check reminders.db file)
- ✅ All fields from spec are implemented (especially location fields, timestamps)
- ✅ ISO 8601 date/time formatting is correct
- ✅ Priority and status enums work correctly
- ✅ Error handling returns proper status codes

---

## Smart Views (Phase 1 Extension - Optional)

If Phase 1 completes quickly, implement these smart view endpoints:

### `/api/reminders/today`
**Logic:**
- Return reminders where:
  - `due_date = today's date` OR
  - `due_date < today's date AND status = 'pending'` (overdue) OR
  - `due_date IS NULL AND status = 'pending'` (floating tasks)
- Sort by: priority (urgent → important → chill), then time, then created_at

### `/api/reminders/upcoming`
**Logic:**
- Return reminders where:
  - `due_date BETWEEN tomorrow AND 7 days from now`
- Sort by: due_date (ascending), then priority, then time

**Reference:** `reminders-project-spec.md` (Smart Views section, lines 423-460)

---

## Common Issues & Solutions

### Issue: UV not found
```bash
pip install uv
# or
pip3 install uv
```

### Issue: Port 8000 already in use
```bash
# Find process using port 8000
lsof -i :8000
# Kill it
kill -9 <PID>
# Or use different port
uvicorn server.main:app --reload --host 0.0.0.0 --port 8001
```

### Issue: secrets.json not loading
- Verify file path is correct (project root)
- Check JSON syntax is valid
- Print debug message in config.py to confirm loading

### Issue: Database errors
- Delete reminders.db and reinitialize: `python server/database.py`
- Check schema matches spec exactly
- Verify SQLite3 is available: `sqlite3 --version`

### Issue: CORS errors in browser
- Ensure CORS_ORIGINS includes your frontend URL
- Add "null" for file:// protocol during development

---

## After Phase 1 Completion

**Document your work:**
1. Update `TODOS.md` - Mark Phase 1 tasks as complete
2. Note any deviations from spec in comments
3. Document any additional endpoints or features added

**Commit your work:**
```bash
git add .
git commit -m "feat: Implement Phase 1 - Core Backend with FastAPI and SQLite

- Initialize Python environment with UV
- Create FastAPI REST API server
- Implement SQLite database with full reminders schema
- Add CRUD endpoints with bearer token auth
- Create Pydantic models for validation
- Add health check endpoint
- Test all endpoints via Swagger UI

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Prepare for Phase 2:**
- Review `TODOS.md` Phase 2 section
- Start thinking about UI design (reference spec lines 578-899)
- Ensure API is stable and well-tested before building frontend

---

## Key Files to Reference

| File | Purpose | When to Read |
|------|---------|--------------|
| `reminders-project-spec.md` | Complete specification | Throughout Phase 1 |
| `TODOS.md` | Task checklist | Before/during/after work |
| `CLAUDE.md` | Project instructions | When unsure about patterns |
| `ClaudeUsage/db_usage.md` | Database patterns | Step 2 (Database Layer) |
| `ClaudeUsage/uv_usage.md` | Python dependencies | Step 1 (Project Setup) |
| `ClaudeUsage/git_guide.md` | Git workflow | When committing |
| `README.md` | Project overview | For context and setup |

---

## Quick Command Reference

```bash
# Setup
uv init
uv add fastapi uvicorn sqlalchemy pydantic

# Database
python server/database.py  # Initialize DB

# Run server
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

# Test
curl http://localhost:8000/api/health
curl http://localhost:8000/docs  # Swagger UI

# Database inspection
sqlite3 reminders.db ".schema"
sqlite3 reminders.db "SELECT * FROM reminders;"

# Git
git status
git add .
git commit -m "feat: descriptive message"
```

---

## Timeline Estimate

| Step | Estimated Time | Priority |
|------|---------------|----------|
| 1. Project Setup | 15 minutes | Must Have |
| 2. Database Layer | 30-45 minutes | Must Have |
| 3. Config & Models | 30 minutes | Must Have |
| 4. FastAPI Application | 45-60 minutes | Must Have |
| 5. Testing & Validation | 30 minutes | Must Have |
| Smart Views (optional) | 30 minutes | Nice to Have |

**Total:** ~2.5-3 hours for core Phase 1

---

## Tips for Success

1. **Follow the spec closely** - Database schema and API endpoints are well-defined
2. **Test incrementally** - Don't wait until everything is built to test
3. **Use Swagger UI** - It's the fastest way to test endpoints
4. **Check TODOS.md frequently** - Mark off tasks as you complete them
5. **Commit often** - After each major step (database, models, endpoints)
6. **Read ClaudeUsage guides** - They have patterns and templates
7. **Don't over-engineer** - This is MVP, keep it simple
8. **Focus on functionality** - Make it work first, optimize later

---

## Questions to Ask If Stuck

1. "Can you show me the database.py implementation following the ClaudeUsage/db_usage.md template?"
2. "Can you implement the Pydantic models based on the spec at lines 158-201?"
3. "Can you show me how to implement bearer token authentication in FastAPI?"
4. "Can you help me test the API endpoints with curl commands?"
5. "Can you review my implementation against the spec and identify missing pieces?"

---

## Final Checklist Before Starting

- [ ] Read this entire document
- [ ] Review `reminders-project-spec.md` sections: Database Schema (lines 150-267) and API Specification (lines 269-420)
- [ ] Check `TODOS.md` Phase 1 section
- [ ] Verify Python 3.11+ is installed
- [ ] Verify UV is installed
- [ ] Have MapBox token ready (or plan to get it during setup)
- [ ] Have strong random API token ready (or generate during setup)
- [ ] Git is configured with name and email
- [ ] Understand offline-first, ADHD-optimized design principles

---

**Ready to begin? Start with Step 1: Project Setup!**

Good luck! 🚀

---

*Generated by Claude Sonnet 4.5*
*Created: November 2, 2025*
*Next Session: Phase 1 - Core Backend Implementation*
