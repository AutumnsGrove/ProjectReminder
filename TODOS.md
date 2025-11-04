# TODOs - ADHD-Friendly Voice Reminders System

**Status:** 🚀 Phase 1-8 Complete (87.5% to MVP) | Phase 8.1 Next
**Last Updated:** November 4, 2025
**Cloud API:** https://reminders-api.m7jv4v7npb.workers.dev

---

## 🎯 NEXT: Phase 8.1 - LLM Natural Language Parsing

**Goal:** Auto-extract reminder metadata from voice transcriptions using local LLM OR cloud (Cloudflare Workers AI).

**What It Does:**
```
Voice → "Call mom about Thanksgiving tomorrow at 3pm, this is urgent"
Currently → Text: "Call mom about Thanksgiving tomorrow at 3pm, this is urgent" (manual fields)
After 8.1 → Text: "Call mom about Thanksgiving"
           Due Date: 2025-11-05 (parsed "tomorrow")
           Due Time: 15:00:00 (parsed "3pm")
           Priority: urgent (parsed "this is urgent")
           Category: Calls (inferred from "call")
```

**Architecture:** Dual-mode (local Llama 3.2 1B OR Cloudflare Workers AI)

---

### 📊 Phase 8.1 Progress Summary

**Current Status:** Phase 1 Research ✅ Complete → Phase 2 Development Ready
**Progress:** 25% (4/18 subagents complete)
**Time Invested:** ~2 hours (research)
**Time Remaining:** ~6-8 hours (development + testing)

**Completed:**
- ✅ Research Phase (4 subagents, 4 commits, 5,018 lines of docs)
- ✅ Requirements analysis, architecture design, edge cases identified
- ✅ Technology choices made (dateparser, LM Studio, Cloudflare AI)

**Next:** Phase 2 Development (8 subagents) → Phase 3 Testing (6 subagents)

**Key Documents for Next Agent:**
- `docs/phase8.1_requirements.md` - What to build
- `docs/phase8.1_architecture.md` - How to build it
- `docs/phase8.1_cloudflare_ai_research.md` - Cloudflare integration
- `docs/phase8.1_edge_cases.md` - What to test

**Autonomous Execution Notes:**
- All tasks are self-contained and documented
- Each subagent commits before handoff
- Follow `ClaudeUsage/subagent_usage.md` strictly
- LM Studio is running at `http://127.0.0.1:1234`
- Can proceed without user intervention

---

### Phase 1: Research ✅ COMPLETE

- [x] **1.1** Requirements Analysis - Extract requirements, define success criteria, dual-mode architecture
  - **Commit:** `bd69465` - `docs/phase8.1_requirements.md` (1,145 lines)
  - Defined 8 functional requirements, API contracts, success criteria (>85% accuracy)

- [x] **1.2** Cloudflare Workers AI Research - API patterns, Llama 3.2 1B availability, JSON mode
  - **Commit:** `ccecf30` - `docs/phase8.1_cloudflare_ai_research.md` (1,474 lines)
  - Confirmed Llama 3.2 1B available, JSON mode support, free tier 10k requests/day
  - Performance: 2-5s cloud vs 8-15s local, cost $0.31/month for 1,000 reminders

- [x] **1.3** Architecture Planning - Dual-mode design, endpoints, confidence scoring, fallback strategy
  - **Commit:** `bdbe594` - `docs/phase8.1_architecture.md` (1,115 lines)
  - Designed dual-mode architecture (auto/local/cloud), confidence scoring, fallback logic

- [x] **1.4** Edge Case Analysis - Date parsing, timezone handling, ambiguity resolution
  - **Commit:** `932d984` - `docs/phase8.1_edge_cases.md` (1,284 lines)
  - Identified 27+ edge cases, recommended `dateparser` library, 4-level degradation
  - Test plan: 81+ test cases across 7 categories

### Phase 2: Development (Ready to Start)

**Prerequisites:** Phase 1 Research complete ✅ (4 docs, 5,018 lines)
**LM Studio:** Already running at `http://127.0.0.1:1234` with `llama-3.2-1b-instruct`
**Estimated Time:** 4-5 hours (8 subagents)
**Commit Format:** `feat:` for new features, follow `ClaudeUsage/git_guide.md`

#### Development Subagents (Sequential Order)

- [ ] **2.1** Install Dependencies & Setup
  - Add `dateparser` to pyproject.toml dependencies
  - Add `python-dateutil` for ISO 8601 fallback
  - Run `uv sync` to install
  - Test imports and basic functionality
  - **Output:** Updated `pyproject.toml`, `uv.lock`
  - **Commit:** `chore: Add dateparser and date utilities for NLP parsing`

- [ ] **2.2** System Prompt Engineering
  - Create `server/voice/prompts.py` with system prompt
  - Design prompt based on `docs/phase8.1_requirements.md` examples
  - Include JSON schema, few-shot examples
  - Test with LM Studio API (manual verification)
  - Document prompt design decisions
  - **Output:** `server/voice/prompts.py`
  - **Commit:** `feat: Add LLM system prompt for reminder metadata extraction`

- [ ] **2.3** Date/Time Utilities Module
  - Create `server/voice/date_utils.py`
  - Implement `parse_natural_date(text, reference_date)` using dateparser
  - Implement `parse_natural_time(text)` for time extraction
  - Handle relative dates ("tomorrow", "next Friday")
  - Convert to ISO 8601 format
  - Add timezone awareness (use zoneinfo)
  - **Output:** `server/voice/date_utils.py` with 5+ functions
  - **Commit:** `feat: Add date/time parsing utilities with dateparser`

- [ ] **2.4** Local LLM Parser Module
  - Create `server/voice/parser.py`
  - Implement `LocalLLMParser` class
  - Connect to LM Studio at `http://127.0.0.1:1234`
  - Implement `parse_reminder_text(text: str) -> dict` method
  - Add JSON validation and error handling
  - Calculate confidence scores per field
  - Use date_utils for normalization
  - **Output:** `server/voice/parser.py` (200-300 lines)
  - **Commit:** `feat: Implement local LLM parser with confidence scoring`

- [ ] **2.5** Cloudflare AI Parser Module
  - Create `server/voice/cloudflare_parser.py`
  - Implement `CloudflareAIParser` class
  - Use `@cf/meta/llama-3.2-1b-instruct` model
  - Add API authentication from `secrets.json`
  - Implement same interface as LocalLLMParser
  - Add retry logic and timeout handling
  - **Output:** `server/voice/cloudflare_parser.py` (150-200 lines)
  - **Commit:** `feat: Implement Cloudflare Workers AI parser`

- [ ] **2.6** FastAPI Parse Endpoint
  - Add `ReminderParseRequest` and `ReminderParseResponse` models to `server/models.py`
  - Implement `POST /api/voice/parse` in `server/main.py`
  - Support mode parameter (auto/local/cloud)
  - Implement fallback logic (auto mode)
  - Add bearer token authentication
  - Return parsed data with confidence scores
  - **Output:** Updated `server/main.py`, `server/models.py`
  - **Commit:** `feat: Add POST /api/voice/parse endpoint with dual-mode support`

- [ ] **2.7** Frontend Integration
  - Add `parseReminderText(text, mode)` to `public/js/api.js`
  - Update `initVoiceRecorder()` in voice recorder integration
  - Auto-populate form fields from parse results
  - Add confidence indicators (green/yellow/red borders)
  - Show parsing status (loading spinner)
  - Allow manual override of parsed fields
  - **Output:** Updated `public/js/api.js`, voice integration code
  - **Commit:** `feat: Integrate NLP parsing with voice recorder UI`

- [ ] **2.8** Settings & Configuration UI
  - Create settings panel in UI (or update existing config)
  - Add mode selector: Auto / Local Only / Cloud Only
  - Store preference in localStorage (`nlp_mode`)
  - Add privacy notice for cloud mode
  - Update `public/config.json` with default mode
  - **Output:** Settings UI component, config updates
  - **Commit:** `feat: Add NLP mode configuration UI with privacy notice`

**After All Development:** Phase 3 Testing begins (test plan in `docs/phase8.1_edge_cases.md`)

### Phase 3: Testing (After Development Complete)

**Prerequisites:** Phase 2 Development complete ✅ (8 subagents, all features implemented)
**Test Plan:** See `docs/phase8.1_edge_cases.md` (81+ test cases defined)
**Estimated Time:** 2-3 hours (4-5 subagents)
**Commit Format:** `test:` for tests, `docs:` for reports

#### Testing Subagents (Sequential Order)

- [ ] **3.1** Unit Tests - Date/Time Utilities
  - Create `server/tests/test_date_utils.py`
  - Test `parse_natural_date()` with 20+ cases
  - Test `parse_natural_time()` with 15+ cases
  - Test timezone handling and DST transitions
  - Test edge cases (ambiguous dates, past dates)
  - **Output:** `server/tests/test_date_utils.py` (150+ lines)
  - **Commit:** `test: Add unit tests for date/time parsing utilities`

- [ ] **3.2** Unit Tests - Parser Modules
  - Create `server/tests/test_parser.py`
  - Test LocalLLMParser with mock LM Studio responses
  - Test CloudflareAIParser with mock API responses
  - Test confidence scoring algorithm
  - Test JSON validation and error handling
  - Test fallback logic (auto mode)
  - **Output:** `server/tests/test_parser.py` (200+ lines)
  - **Commit:** `test: Add unit tests for LLM parser modules`

- [ ] **3.3** Integration Tests - API Endpoints
  - Create `server/tests/test_parse_endpoint.py`
  - Test `POST /api/voice/parse` with varied inputs
  - Test all 3 modes (auto/local/cloud)
  - Test authentication (valid/invalid tokens)
  - Test error scenarios (LLM unavailable, timeout)
  - Test response schema compliance
  - **Output:** `server/tests/test_parse_endpoint.py` (150+ lines)
  - **Commit:** `test: Add integration tests for parse endpoint`

- [ ] **3.4** Manual Testing & Validation
  - Test 20+ real-world voice inputs (from `docs/phase8.1_edge_cases.md`)
  - Verify accuracy: dates >90%, times >85%, priority >75%
  - Test frontend auto-population with confidence indicators
  - Test settings UI (mode switching)
  - Document failures and accuracy metrics
  - **Output:** `docs/phase8.1_manual_test_results.md`
  - **Commit:** `docs: Add Phase 8.1 manual testing results`

- [ ] **3.5** Test Suite Execution & Coverage
  - Run full test suite: `pytest --cov=server --cov-report=html`
  - Verify >85% code coverage for new modules
  - Fix any failing tests
  - Generate coverage report
  - **Output:** Coverage report, all tests passing
  - **Commit:** `test: Achieve >85% coverage for Phase 8.1 modules`

- [ ] **3.6** Phase 8.1 Completion Report
  - Create `docs/phase8.1_completion.md`
  - Document implementation details (architecture, tech stack)
  - Record performance metrics (latency, accuracy)
  - List known limitations and future enhancements
  - Include commit log (all Phase 8.1 commits)
  - **Output:** `docs/phase8.1_completion.md` (similar to `phase8_completion.md`)
  - **Commit:** `docs: Add Phase 8.1 completion report`

**After Testing:** Update `TODOS.md` to mark Phase 8.1 complete ✅

### Success Criteria

- ✅ Auto-extract dates: "tomorrow", "next Friday", "Dec 25"
- ✅ Auto-extract times: "at 3pm", "9:30am", "noon"
- ✅ Auto-extract priority: "urgent", "important", "this is critical"
- ✅ Auto-extract locations: "at Kroger", "when I'm at Home Depot"
- ✅ Auto-extract categories: "call" → Calls, "buy" → Shopping
- ✅ Handle ambiguity gracefully (fallback to manual)
- ✅ <3 second parsing time (local inference)

**Estimated Time:** 8-10 hours (1-2 days with subagents)

**Tech Stack:**
- Llama 3.2 1B or Phi-3 Mini (local, offline)
- llama.cpp or llama-cpp-python
- Custom system prompt + JSON output mode

**Documentation:** Create `docs/phase8.1_completion.md` when done

---

## ✅ Completed Phases

<details>
<summary><strong>Phase 1-3.6: Foundation (Backend + Frontend + Testing)</strong></summary>

**Phase 1: Core Backend**
- FastAPI REST API, SQLite database, CRUD endpoints, bearer auth, Swagger docs

**Phase 2: Web UI**
- Today/Upcoming/Future views, mobile-responsive, 5-level priorities, animations

**Phase 3: Integration**
- API client, error handling, offline state, full CRUD integration

**Phase 3.5: Testing**
- 24 pytest tests, 80% coverage, CI-ready

**Phase 3.6: 5-Level Priorities**
- someday/chill/important/urgent/waiting with color coding
</details>

<details>
<summary><strong>Phase 4: Cloudflare Workers ✅</strong> - Production cloud deployment</summary>

- Hono TypeScript API on Cloudflare Workers
- D1 database (cloud SQLite) with 3 migrations
- All 6 REST endpoints deployed
- 81-112ms edge performance
- Production: https://reminders-api.m7jv4v7npb.workers.dev
</details>

<details>
<summary><strong>Phase 5: Sync Logic ✅</strong> - Bidirectional synchronization</summary>

- Offline-first with auto-sync every 5 minutes
- Manual sync button with UI status (5 states)
- Conflict resolution (last-write-wins)
- Change queue in localStorage
- `POST /api/sync` endpoint (FastAPI + Workers)
- 459-line sync manager (`public/js/sync.js`)
</details>

<details>
<summary><strong>Phase 6: Location Features ✅</strong> - MapBox integration</summary>

- MapBox GL JS location picker in edit form
- Geocoding (address → lat/lng) and reverse geocoding
- Map visualization with draggable pin
- Radius configuration (10m-10km, default 100m)
- `GET /api/reminders/near-location` endpoint
- Haversine distance calculation
- Browser Geolocation API integration
</details>

<details>
<summary><strong>Phase 7: Recurring Reminders ✅</strong> - Recurrence patterns</summary>

- Daily, weekly, monthly, yearly frequencies
- Advanced scheduling (specific days of week, day of month)
- 3 end conditions (never, until date, after N occurrences)
- Server-side instance generation (90-day horizon)
- Live UI preview showing next 3 occurrences
- `recurrence_patterns` table with CRUD functions
- 350-line recurrence module (`public/js/recurrence.js`)

**Testing:** ⚠️ Needs manual testing when available (daily/weekly/monthly patterns, end conditions)
</details>

<details>
<summary><strong>Phase 8: Voice Input ✅</strong> - Voice-to-text transcription (November 3, 2025)</summary>

- Whisper.cpp integration (base.en model, 23x realtime, local/offline)
- `POST /api/voice/transcribe` endpoint (FastAPI)
- Browser audio recording (`public/js/voice-recorder.js`)
- Voice button (🎤) with 3 states (idle/recording/processing)
- 85-90% transcription accuracy (2-8 seconds end-to-end)
- 14 pytest tests (100% pass, 97% coverage)
- Comprehensive error handling (permissions, timeouts, failures)

**User Flow:** Click 🎤 → Speak → Auto-transcribe → Manual field completion

**Docs:** See `docs/phase8_*.md` for architecture, requirements, completion report
</details>

**Summary:** 8 phases complete, ~5,000 lines of code, 24+ tests passing, production deployed

---

## 🔮 Post-MVP Features (Phase 9+)

### Phase 7.1: Enhanced Recurring Reminders
- Edit/delete single instance vs entire series
- Display recurrence indicator (♻️) in reminder lists
- View/edit original recurrence pattern

### Phase 9: E-ink Display Clients
- Android e-ink app for car dashboard
- Read-only view with tap-to-complete
- Optimized for e-ink refresh rates

### Phase 10: Smart Features
- Auto-categorization via LLM
- Duplicate detection
- Reminder templates
- Priority suggestions

### Phase 11: Analytics & Insights
- Completion rate tracking
- Time-of-day patterns
- Productivity insights dashboard

### Future Ideas
- Receipt printer integration (daily task list printouts)
- Habit tracking
- Integration with calendar apps
- Siri/Google Assistant shortcuts

---

## 📚 Quick Reference

### Development Commands

```bash
# Start local API server
uv run uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

# Serve frontend
python serve_ui.py
# OR open public/index.html directly

# Run tests
pytest
pytest --cov=server --cov-report=html

# Deploy to Cloudflare
cd workers && npx wrangler deploy
```

### Project URLs

- **Local API:** http://localhost:8000
- **Cloud API:** https://reminders-api.m7jv4v7npb.workers.dev
- **API Docs:** http://localhost:8000/docs (Swagger)
- **GitHub:** https://github.com/AutumnsGrove/ProjectReminder

### Secrets Required

Stored in `secrets.json` (see `secrets_template.json`):
- `mapbox_access_token` - MapBox GL JS (get at https://account.mapbox.com/)
- `api_token` - Bearer token for API auth (strong random string)

### Database Schema

SQLite tables (local + cloud D1):
- `reminders` - Main reminder instances (id, text, due_date, due_time, location, priority, status, etc.)
- `recurrence_patterns` - Recurrence definitions (frequency, interval, days_of_week, end_condition, etc.)

### Architecture Patterns

- **Database:** All SQL isolated in `server/database.py` (function-based interface)
- **Models:** Pydantic models in `server/models.py` (request/response contracts)
- **Auth:** Bearer token via `verify_token()` dependency injection
- **Frontend:** Modular JS (api.js, sync.js, storage.js, recurrence.js, voice-recorder.js)
- **CSS:** Mobile-first with CSS variables for theming

---

## 🛠️ Development Best Practices

**For All Future Work:**

1. **Use subagents** - Follow `ClaudeUsage/subagent_usage.md` for focused, atomic tasks
2. **Commit atomically** - One logical change = one commit (conventional format)
3. **Test locally first** - Run pytest, test in browser before deploying
4. **Document as you go** - Create completion reports for major phases
5. **Reference guides** - Check `ClaudeUsage/` for patterns (git, testing, database, etc.)
6. **Update TODOS** - Mark tasks complete, add new discoveries

**Git Commit Format:**
```
<type>: <description>

🤖 Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`

---

*Last Updated: November 4, 2025*
*Model: Claude Sonnet 4.5*
*Phase 8 Complete ✅ | Phase 8.1 Next 🚀 | 87.5% to MVP*
