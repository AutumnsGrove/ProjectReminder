# Comprehensive Testing Session - Next Claude Prompt

**Date Created:** November 8, 2025
**Purpose:** Full end-to-end testing of ADHD-Friendly Voice Reminders System
**Context:** All features complete (Phases 1-8.1), ready for comprehensive testing

---

## 📋 SESSION OVERVIEW

You are starting a comprehensive testing session for a voice-first reminders app. All development is complete (100% MVP features), but systematic testing is needed to verify everything works end-to-end.

**Current State:**
- ✅ Backend FastAPI server ready (runs on port 8000)
- ✅ Frontend UI ready (runs on port 3077 via `python serve_ui.py`)
- ✅ 138 tests exist (pytest)
- ✅ Database initialized (SQLite)
- ✅ All Phase 1-8.1 features implemented

**What Needs Testing:**
1. Unit/integration tests (138 tests via pytest)
2. Voice transcription (Phase 8 - Whisper.cpp)
3. NLP parsing (Phase 8.1 - LLM auto-extraction)
4. MapBox location features (Phase 6)
5. Recurring reminders (Phase 7)
6. Cloud sync (Phase 5 - Cloudflare Workers)
7. Error handling and edge cases

---

## 🎯 YOUR MISSION

Use **house-bash** and **specialized agents** to execute all tests efficiently while minimizing token usage. Report results clearly and identify any issues that need fixing.

---

## 📁 PROJECT CONTEXT

### Architecture
- **Backend:** FastAPI + SQLite (local-first)
- **Frontend:** Vanilla JS + HTML/CSS (no framework)
- **Cloud:** Cloudflare Workers + D1 (sync & backup)
- **Voice:** Whisper.cpp (local STT)
- **NLP:** Llama 3.2 1B via LM Studio (local LLM)
- **Maps:** MapBox GL JS

### Key Files
- `server/main.py` - FastAPI app
- `server/database.py` - SQLite functions
- `server/tests/` - All test files
- `public/index.html` - Main UI
- `public/js/api.js` - API client
- `TODOS.md` - Current status
- `docs/phase8.1_completion.md` - Latest completion report

### Prerequisites
- Python 3.11+ with UV package manager
- LM Studio running on port 1234 (for NLP tests)
- MapBox API token in `secrets.json`
- API token in `secrets.json`

---

## 🧪 TESTING PLAN (Use Subagents!)

### Phase 1: Automated Test Suite ⚡ PRIORITY 1

**Use house-bash agent** to run pytest and analyze results:

```bash
# Run all tests with coverage
uv run pytest --cov=server --cov-report=html --cov-report=term -v

# Expected: 138 tests, >55% coverage overall, 80-90% for Phase 8.1 modules
```

**Tasks for agent:**
1. Execute pytest with full verbosity
2. Analyze test results (pass/fail counts)
3. Review coverage report
4. Identify any failing tests
5. Report summary in structured format

**Success Criteria:**
- All 138 tests pass (or document failures)
- Coverage meets targets (>85% for Phase 8.1 modules)
- No syntax or import errors

---

### Phase 2: Backend API Testing

**Use house-bash agent** to test all API endpoints:

```bash
# Health check
curl http://localhost:8000/api/health

# Get Swagger docs
curl http://localhost:8000/docs

# Test auth (replace TOKEN)
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/reminders/today

# Create reminder
curl -X POST http://localhost:8000/api/reminders \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Test reminder","priority":"chill"}'
```

**Tasks:**
1. Test all CRUD endpoints (GET/POST/PATCH/DELETE)
2. Test authentication (valid/invalid tokens)
3. Test query parameters (pagination, filters)
4. Test error handling (400/401/404/500 responses)
5. Verify Swagger UI loads correctly

---

### Phase 3: Voice Transcription Testing (Phase 8)

**Prerequisites:** Whisper.cpp installed at `whisper.cpp/build/bin/whisper-cli`

**Test Flow:**
1. Check Whisper binary exists
2. Create test audio file (or use existing)
3. Call `/api/voice/transcribe` endpoint
4. Verify transcription accuracy (>85%)

**Use haiku-coder agent** if fixes needed for file paths or dependencies.

**Success Criteria:**
- Whisper.cpp responds within 2-8 seconds
- Transcription accuracy >85% on clear audio
- Handles various audio formats (WebM, WAV, MP4)

---

### Phase 4: NLP Parsing Testing (Phase 8.1) ⭐ CRITICAL

**Prerequisites:**
- LM Studio running on port 1234
- Model: llama-3.2-1b-instruct loaded

**Test Cases:**
```bash
# Simple date/time
curl -X POST http://localhost:8000/api/voice/parse \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Call mom tomorrow at 3pm","mode":"local"}'

# Expected: due_date=tomorrow, due_time=15:00:00, confidence>0.8

# With priority
curl -X POST http://localhost:8000/api/voice/parse \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Buy milk today this is urgent","mode":"local"}'

# Expected: due_date=today, priority=urgent, confidence>0.7

# Complex parsing
curl -X POST http://localhost:8000/api/voice/parse \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Meeting next Tuesday at 2:30pm important","mode":"local"}'

# Expected: due_date=next-tuesday, due_time=14:30:00, priority=important
```

**Use house-bash agent** to run multiple test cases and analyze confidence scores.

**Success Criteria:**
- Date parsing: >90% accuracy
- Time parsing: >85% accuracy
- Priority detection: >75% accuracy
- Response time: <3 seconds (local mode)
- Fallback works if LM Studio offline

---

### Phase 5: Frontend UI Testing (Manual)

**Check these features work:**
1. Load http://localhost:3077 (UI renders)
2. Navigate: Today / Upcoming / Future views
3. Create reminder manually (form submission)
4. Edit reminder (update fields)
5. Complete reminder (animation plays)
6. Delete reminder (confirmation works)
7. Voice recorder button (if browser allows mic access)
8. Settings page (if exists)

**Use Explore agent** to find UI components if needed.

---

### Phase 6: MapBox Location Testing

**Prerequisites:** `mapbox_access_token` in `secrets.json`

**Test Flow:**
1. Create reminder with location
2. Verify map loads
3. Test geocoding (search address)
4. Test reverse geocoding (click map)
5. Query `/api/reminders/near-location?lat=X&lng=Y&radius=500`

**Use house-bash agent** to test location API endpoints.

---

### Phase 7: Recurring Reminders Testing (Phase 7)

**Test Cases:**
1. Daily reminder (every day at 9am)
2. Weekly reminder (every Monday, Wednesday)
3. Monthly reminder (1st of month)
4. End after N occurrences
5. End on specific date

**Verify:**
- Pattern saves correctly
- Instances generate (90-day horizon)
- Preview shows next 3 occurrences

---

### Phase 8: Cloud Sync Testing (Phase 5)

**Prerequisites:** Cloudflare Workers deployed (optional)

**Test Flow:**
1. Create reminder locally
2. Call `/api/sync` endpoint
3. Verify changes upload
4. Check conflict resolution (last-write-wins)
5. Test offline mode

**Note:** Cloud testing is optional if Workers not deployed yet.

---

### Phase 9: Error Handling & Edge Cases

**Test These Scenarios:**
1. No internet connection (offline mode)
2. LM Studio offline (NLP fallback)
3. Invalid dates (parsing errors)
4. Long text (500+ characters)
5. Special characters (Unicode, emojis)
6. Missing MapBox token (graceful degradation)
7. Invalid API token (401 response)
8. Database locked (concurrent access)

**Use house-bash agent** to systematically test error scenarios.

---

## 📊 REPORTING FORMAT

After completing tests, provide this structured report:

### Test Execution Summary
```
Total Tests Run: X/138
Passed: X
Failed: X
Skipped: X
Coverage: X%
Time: X seconds
```

### Feature Status
- [ ] Backend API (Health, CRUD, Auth)
- [ ] Voice Transcription (Phase 8)
- [ ] NLP Parsing (Phase 8.1)
- [ ] MapBox Locations (Phase 6)
- [ ] Recurring Reminders (Phase 7)
- [ ] Cloud Sync (Phase 5)
- [ ] Error Handling

### Issues Found
List any bugs, failures, or unexpected behavior with:
- File/line number
- Expected vs actual result
- Severity (critical/high/medium/low)
- Suggested fix

### Performance Metrics
- API response times
- NLP parsing latency
- Transcription speed
- Database query performance

### Recommendations
- Features ready for production
- Features needing fixes
- Features needing additional testing
- Next steps

---

## 🚀 EXECUTION STRATEGY

### Token Optimization Tips
1. **Use house-bash** for command execution (don't paste full output)
2. **Use specialized agents** (Explore, haiku-coder) for focused tasks
3. **Batch similar tests** (run all API tests together)
4. **Summarize results** (don't dump entire logs)
5. **Reference files by path** (don't read unless needed)

### Suggested Agent Usage
- **house-bash**: All pytest runs, API testing, performance tests
- **haiku-coder**: Quick fixes for test failures (<250 lines)
- **Explore**: Find specific test files or code sections
- **house-research**: If searching across 20+ files needed

### Parallel Execution
Run independent tests concurrently:
1. Unit tests (pytest)
2. API endpoint tests (curl)
3. Database integrity checks
4. Frontend smoke tests

---

## ✅ SUCCESS CRITERIA

**Minimum for Production:**
- [ ] All pytest tests pass (138/138)
- [ ] Backend API responds correctly
- [ ] Voice transcription works (>85% accuracy)
- [ ] NLP parsing works (>80% confidence on simple cases)
- [ ] Frontend UI loads and operates
- [ ] No critical security issues
- [ ] Error handling works gracefully

**Stretch Goals:**
- [ ] MapBox integration tested with real locations
- [ ] Recurring reminders validated
- [ ] Cloud sync tested end-to-end
- [ ] Performance benchmarks documented
- [ ] Edge cases handled correctly

---

## 📝 NOTES

### Known Issues (Pre-Testing)
- Database was 0 bytes (fixed: ran `init_db()`)
- Port 8000 was in use (fixed: killed old processes)
- config.json removed from git (intentional, use config_template.json)
- **MapBox "use my location" button:** Minor styling issue (button works, just UI glitch)

### Confirmed Working (Pre-Testing)
- ✅ Reminder creation works end-to-end
- ✅ MapBox map loads and displays correctly
- ✅ Geolocation shows accurate user position
- ✅ Frontend UI navigation works

### Current Deployment
- **Local API:** http://localhost:8000
- **Frontend UI:** http://localhost:3077
- **Cloud API:** https://reminders-api.m7jv4v7npb.workers.dev (deployed Phase 4)
- **LM Studio:** http://127.0.0.1:1234 (if running)

### Device Context
User is on a **new device** - no existing reminders data. This is a clean slate for testing, which is perfect for validation!

Cloud sync (Cloudflare D1) is the backup/multi-device solution, so syncing will be important to test if possible.

---

## 🎬 START HERE

**Step 1: Start Backend and Frontend in Background**

Start both servers in background so they run while you work:

```bash
# Start backend server (FastAPI on port 8000)
uv run uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
# (Use run_in_background: true in Bash tool)

# Start frontend server (UI on port 3077)
python serve_ui.py
# (Use run_in_background: true in Bash tool)
```

**Step 2: Verify Environment**
```bash
# Check servers are running
curl -s http://localhost:8000/api/health
curl -s http://localhost:3077 | head -5

# Verify pytest works
uv run pytest --version
```

**Step 3: Run Testing Phases**

Then proceed through the testing phases sequentially or use multiple agents in parallel for faster results.

**Important:** Both servers must remain running in background throughout the entire testing session!

**Good luck! 🚀**
