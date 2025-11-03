# TODOs - ADHD-Friendly Voice Reminders System

**Project Status:** ✅ Phase 1-7 Complete | 🚀 Phase 8 Next (Voice Input)
**Last Updated:** November 3, 2025 (Recurring Reminders Complete!)
**Worker URL:** https://reminders-api.m7jv4v7npb.workers.dev

---

## ✅ Completed Phases (Summary)

<details>
<summary><strong>Phase 1: Core Backend ✅</strong> - FastAPI + SQLite + CRUD endpoints</summary>

- FastAPI REST API with bearer token auth
- SQLite database with full schema
- All CRUD endpoints (health, create, read, update, delete)
- Pydantic models and validation
- Auto-generated Swagger docs
- CORS configured for web UI

**Files:** `server/database.py`, `server/main.py`, `server/models.py`, `server/config.py`
</details>

<details>
<summary><strong>Phase 2: Web UI ✅</strong> - HTML/CSS/JS frontend</summary>

- Today, Upcoming, Future views
- Create/Edit form
- Mobile-first responsive design
- 5-level priority colors (someday/chill/important/urgent/waiting)
- Completion animations
- Toast notifications

**Files:** `public/*.html`, `public/css/*.css`, `public/js/app.js`
</details>

<details>
<summary><strong>Phase 3: Integration ✅</strong> - Full stack connection</summary>

- API client with fetch() calls
- Error handling with retry logic
- Loading states
- Full CRUD integration
- Offline state handling

**Files:** `public/js/api.js`, `public/js/errors.js`
</details>

<details>
<summary><strong>Phase 3.5: Testing Infrastructure ✅</strong> - Pytest test suite</summary>

- 24 passing tests (80% coverage)
- Database, API endpoints, models tested
- Test fixtures and utilities
- CI-ready test suite

**Files:** `tests/test_*.py`, `pytest.ini`
</details>

<details>
<summary><strong>Phase 3.6: 5-Level Priority System ✅</strong> - Enhanced priority model</summary>

- someday (blue) - Dreams/aspirations
- chill (green) - Low priority
- important (yellow) - Medium priority
- urgent (red) - High priority
- waiting (orange) - Blocked/waiting on others

**Files:** Schema updated, UI updated with new colors
</details>

<details>
<summary><strong>Phase 4: Cloudflare Workers ✅</strong> - Production cloud deployment</summary>

- Hono-based TypeScript API
- D1 SQLite database (cloud)
- All 6 endpoints deployed
- Bearer token auth
- CORS configured
- 81-112ms performance
- Production URL: https://reminders-api.m7jv4v7npb.workers.dev

**Files:** `workers/src/index.ts`, `workers/wrangler.toml`, `workers/migrations/*.sql`
</details>

<details>
<summary><strong>Phase 5: Sync Logic ✅</strong> - Bidirectional synchronization</summary>

- Offline-first architecture
- Auto-sync every 5 minutes
- Manual sync button
- Conflict resolution (last-write-wins)
- Change queue with localStorage
- Retry logic (3 attempts)
- Sync status UI (5 states: offline/online/syncing/synced/error)
- D1 migration deployed

**Backend:**
- `POST /api/sync` (FastAPI + Workers)
- 4 sync models (SyncRequest, SyncResponse, SyncChange, ConflictInfo)
- 4 database functions (get_changes_since, apply_sync_change, etc.)

**Frontend:**
- `public/js/sync.js` (459 lines)
- Sync UI in all HTML pages
- CSS animations and styles

**Files:** `server/database.py`, `server/main.py`, `server/models.py`, `workers/src/index.ts`, `workers/migrations/003_add_synced_at.sql`, `public/js/sync.js`, `public/css/main.css`
</details>

**Total Completed:**
- 7 backend modules
- 15 frontend files
- 24 passing tests
- 3 D1 migrations deployed
- ~3,500+ lines of code

---

## Phase 6: Location Features (Day 3-4) 📅 NEXT

### MapBox Setup
- [x] Get MapBox access token (free tier: 50k requests/month)
- [x] Add MapBox GL JS to project
- [x] Configure MapBox in secrets.json

### Location Picker
- [x] Create location picker component in edit form
- [x] Implement geocoding (address → lat/lng)
- [x] Add map visualization
- [x] Enable pin dragging to adjust location
- [x] Add radius configuration (default: 100m, adjustable 10m-10km)

### Location Endpoints
- [x] Implement `GET /api/reminders/near-location` (FastAPI)
- [x] Implement `GET /api/reminders/near-location` (Workers)
- [x] Add Haversine distance calculation
- [x] Test location-based filtering

### Geolocation
- [x] Integrate browser Geolocation API
- [x] Add "Use my location" button
- [x] Handle permission denied gracefully
- [x] Display location reminders on map (optional view)

**Success Criteria:**
- ✅ Can set reminder location via text or map
- ✅ Can query reminders near current location
- ✅ Location-based filtering works
- ✅ Geocoding is accurate

**Estimated Time:** 6-8 hours (Completed)

---

## Phase 7: Recurring Reminders ✅ COMPLETED

### Database ✅
- [x] Create `recurrence_patterns` table (already existed in schema)
- [x] Add foreign key relationship to reminders (already existed)
- [x] Implement recurrence pattern CRUD functions
- [x] Implement instance generation function (90-day horizon)

### Backend API ✅
- [x] Add RecurrencePatternCreate and RecurrencePatternResponse models
- [x] Update POST /api/reminders to accept embedded recurrence_pattern
- [x] Implement server-side instance generation (FastAPI)
- [x] Mirror all changes to Cloudflare Workers TypeScript

### Recurrence UI ✅
- [x] Add recurrence section to edit form (5 frequencies: none/daily/weekly/monthly/yearly)
- [x] Create UI for pattern selection with visual badges
- [x] Add interval configuration (every N days/weeks/months/years)
- [x] Add days of week selector (for weekly)
- [x] Add day of month selector (for monthly)
- [x] Add end conditions (never/on date/after N occurrences)
- [x] Add live preview showing next 3 occurrences

### Frontend Logic ✅
- [x] Create recurrence.js module for UI state management
- [x] Implement frequency change handlers
- [x] Implement preview generation logic
- [x] Integrate with form submission (app.js)
- [x] Add recurrence pattern extraction

### Implementation Details
- **Instance Horizon:** 90 days ahead
- **Supported Frequencies:** daily, weekly, monthly, yearly
- **Weekly:** Select specific days (Mon-Sun)
- **Monthly:** Select day of month (1-31)
- **End Conditions:** Never, specific date, or after N occurrences
- **MVP Editing:** All future instances affected (no "this instance only" yet)

**Files Modified:**
1. `server/database.py` - Added 5 recurrence functions (~350 lines)
2. `server/models.py` - Added 2 recurrence models (~60 lines)
3. `server/main.py` - Updated POST endpoint with instance generation (~40 lines modified)
4. `workers/src/index.ts` - Mirrored backend logic (~200 lines)
5. `public/edit.html` - Added recurrence UI section (~150 lines)
6. `public/css/edit.css` - Added recurrence styles (~260 lines)
7. `public/js/recurrence.js` - New file for recurrence logic (~350 lines)
8. `public/js/app.js` - Updated form submission (~20 lines modified)

**Total New/Modified Code:** ~1,430 lines

**Success Criteria:**
- ✅ Can create "every day" reminder
- ✅ Can create "every Tuesday" reminder (weekly with specific days)
- ✅ Can create "15th of every month" reminder
- ✅ Can set end conditions (never, date, count)
- ✅ Preview shows next 3 occurrences
- ✅ Instances generated server-side on creation
- ⚠️ Edit/delete single instance vs series (deferred to Phase 7.1)
- ⚠️ Display recurrence info in reminder list (deferred to Phase 7.1)

**Testing Status:** ⏳ Ready for manual testing

**Completed:** November 3, 2025 (Evening Session)
**Estimated Time:** 8-10 hours → **Actual:** ~6 hours (autonomous execution)

---

## Phase 8: Voice Input (MVP - Voice-to-Text Only) 📅 NEXT

**Tech Stack Decided:**
- ✅ STT: Whisper.cpp (local, offline)
- ✅ LLM: Llama 3.2 1B (deferred to Phase 8.1)

**MVP Scope:** Voice transcription only (manual field completion)
**Architecture:** See `docs/phase8_architecture.md` for full plan

### Research & Selection
- [x] Research local STT options (Whisper.cpp chosen)
- [x] Research small LLMs (Llama 3.2 1B chosen, deferred)
- [x] Architecture plan created with house-planner
- [x] Choose final stack (Whisper.cpp for MVP)

### Whisper.cpp Integration
- [ ] Install and configure Whisper.cpp (base.en model)
- [ ] Create Python wrapper for Whisper.cpp (`server/voice/whisper.py`)
- [ ] Add voice recording endpoint (`POST /api/voice/transcribe`)
- [ ] Test transcription accuracy

### UI Integration
- [ ] Add voice button (🎤) to edit form with 3 states
- [ ] Implement audio recording in browser (`public/js/voice-recorder.js`)
- [ ] Send audio to backend for transcription
- [ ] Display transcription in text field
- [ ] Add comprehensive error handling (permissions, failures)

### NLP Parsing (Phase 8.1 - Deferred)
- [ ] Install and configure Llama 3.2 1B
- [ ] Create prompt for reminder parsing
- [ ] Implement parsing pipeline (text → structured data)
- [ ] Add fallback to manual edit if parse fails
- [ ] Add `POST /api/voice/parse` endpoint

**Phase 8 MVP Success Criteria:**
- ✅ Voice transcription to text (>85% accuracy)
- ✅ Runs locally (privacy preserved)
- ✅ Fast enough (<8 seconds end-to-end)
- ✅ User manually fills date, time, priority
- ✅ Graceful error handling

**Phase 8.1 Success Criteria (Future):**
- ✅ Auto-extract date: "tomorrow" → "2025-11-04"
- ✅ Auto-extract time: "at 3pm" → "15:00:00"
- ✅ Auto-extract priority: "urgent" → "urgent"
- ✅ Auto-extract location: "at Kroger" → geocoded

**Estimated Time:**
- Phase 8 MVP: 12-15 hours
- Phase 8.1: 8-10 hours (future)

---

## Future Features (Post-MVP) 🔮

### E-ink Display Clients
- [ ] Research Android e-ink app development
- [ ] Create read-only view for car dashboard
- [ ] Implement tap-to-complete
- [ ] Optimize for e-ink refresh

### Smart Features
- [ ] Auto-categorization via LLM
- [ ] Priority suggestion based on keywords
- [ ] Duplicate detection
- [ ] Reminder templates

### Receipt Printer
- [ ] Research thermal printer APIs
- [ ] Create daily task list formatter
- [ ] Schedule morning prints

### Analytics
- [ ] Track completion rates
- [ ] Generate productivity insights
- [ ] Identify time-of-day patterns

---

## MVP Roadmap

**Completed (✅):**
- Phase 1: Core Backend
- Phase 2: Web UI
- Phase 3: Integration
- Phase 3.5: Testing
- Phase 3.6: 5-Level Priority
- Phase 4: Cloud Deployment
- Phase 5: Sync Logic
- Phase 6: Location Features
- Phase 7: Recurring Reminders

**Remaining for MVP (📅):**
- Phase 8: Voice Input (12-15 hours)

**Total Time to MVP:** ~12-15 hours remaining (~2 days)

---

## Notes

- Phases 1-7 provide full offline-first multi-device functionality with recurring reminders ✅
- Phase 8 completes the MVP feature set (voice input)
- Future features are v1.1+ enhancements
- All completed phases have passing tests (Phase 7 needs manual testing)
- Production deployment is live and operational

---

*Generated by Claude Sonnet 4.5*
*Last Updated: November 3, 2025 (Evening Session)*
