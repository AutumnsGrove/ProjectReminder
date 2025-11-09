# TODOs - ADHD-Friendly Voice Reminders System

**Status:** 🚧 Phase 9.0 Production Hardening (Post-Testing Fixes)
**Last Updated:** November 8, 2025
**Cloud API:** https://reminders-api.m7jv4v7npb.workers.dev

---

## 🎯 NEXT: Phase 9.0 - Production Hardening (CRITICAL)

**Goal:** Fix critical bugs and UX issues discovered during comprehensive testing before MVP launch

**Testing Summary:**
- ✅ 138/138 automated tests passing
- ✅ Voice pipeline working (96% transcription accuracy)
- ✅ NLP parsing functional (96% priority, 92% category)
- ⚠️ 2 critical blockers found
- ⚠️ 3 UX improvements needed
- 📊 Overall: 90% production ready

**Priority:** CRITICAL - Must complete before public launch

---

## 📋 Phase 9.0 Tasks

### Critical Blockers (Must Fix)

- [ ] **Fix Date Validation Bug** (45 min) - CRITICAL
  - **Issue:** API accepts invalid dates like "invalid-date", "2025-13-32"
  - **Impact:** Corrupts database with bad data
  - **Location:** `server/models.py` - Add Pydantic validators
  - **Testing:** Add tests in `tests/test_validation.py`
  - **Acceptance:** All invalid dates rejected with HTTP 422

- [ ] **Sync Cloud API Token** (10 min) - HIGH
  - **Issue:** Cloudflare Workers returns 401 (token mismatch)
  - **Impact:** Cloud sync non-functional
  - **Fix:** Run `cd workers && npx wrangler secret put API_TOKEN`
  - **Testing:** Test sync to cloud endpoint
  - **Acceptance:** Sync completes without 401 errors

### UX Improvements (Should Fix)

- [ ] **MapBox Default View** (30 min) - MEDIUM
  - **Issue:** Map starts blank instead of showing default view
  - **Fix:** Add default center/zoom to MapBox initialization
  - **Location:** `public/js/location.js` or wherever MapBox is initialized
  - **Testing:** Open edit form, verify map shows world view by default
  - **Acceptance:** Map shows zoomed-out earth on load

- [ ] **MapBox Save Button Clarity** (20 min) - MEDIUM
  - **Issue:** No clear "Save/Apply" button for selected location
  - **Fix:** Add explicit "Use This Location" button to map UI
  - **Location:** `public/edit.html` or location picker component
  - **Testing:** Select location, click save button, verify persists
  - **Acceptance:** Clear button makes location selection obvious

- [ ] **Future View Layout Fix** (30 min) - MEDIUM
  - **Issue:** Future view layout differs from Today/Upcoming (items top-left)
  - **Fix:** Align CSS with Today/Upcoming views
  - **Location:** `public/css/main.css` or `public/future.html`
  - **Testing:** Compare all 3 views side-by-side
  - **Acceptance:** Consistent layout across all views

### Performance Optimizations

- [ ] **Implement Opus Audio Compression** (60 min) - HIGH
  - **Goal:** 81% file size reduction (116KB → 22KB avg)
  - **Current:** Sending M4A files (2.9MB for 25 recordings)
  - **Target:** Convert to Opus 24kbps before upload
  - **Location:** `public/js/voice-recorder.js` - add conversion step
  - **Testing:** Record audio, verify Opus upload, check transcription quality
  - **Acceptance:** Audio files 5x smaller, no quality loss

---

## 🔮 Phase 9.1 - NLP Enhancement (After 9.0)

**Goal:** Improve temporal parsing accuracy from 40% dates / 28% times to 80%+ target

**Current Performance:**
- Priority: 96% ✅
- Category: 92% ✅
- Date: 40% ⚠️ (needs improvement)
- Time: 28% ⚠️ (needs improvement)
- Location: 28% ⚠️

### Tasks

- [ ] **Enhance Date Extraction** (2 hours)
  - Add `dateparser` library integration
  - Handle relative dates ("tomorrow", "next Monday", "in 3 days")
  - Handle fuzzy dates ("sometime next week", "end of month")
  - **Testing:** Re-run 25 test cases, target 80% accuracy

- [ ] **Enhance Time Extraction** (2 hours)
  - Add pattern matching for common phrases
  - Context-aware defaults:
    - "morning" → 9:00 AM
    - "afternoon" → 3:00 PM
    - "evening" → 6:00 PM
    - "night" → 9:00 PM
  - Handle "end of day" → 5:00 PM
  - **Testing:** Re-run 25 test cases, target 80% accuracy

- [ ] **Post-Processing Layer** (2 hours)
  - Add rule-based fallbacks for LLM misses
  - Implement regex patterns for common formats
  - Add confidence boosting for matched patterns
  - **Location:** New module `server/voice/post_processor.py`

- [ ] **Update System Prompt** (30 min)
  - Refine LLM prompt for better temporal extraction
  - Add examples of date/time formats
  - **Location:** `server/voice/prompts.py`

- [ ] **Add NLP Tests** (1 hour)
  - Create test suite for date/time parsing
  - Cover edge cases (timezones, DST, relative dates)
  - **Location:** `tests/test_nlp_parsing.py`

**Estimated Time:** 7.5 hours
**Success Criteria:** 80%+ date/time extraction accuracy

---

## 🔮 Phase 9.2 - Enhanced Recurring Reminders

**Goal:** Allow editing single instances vs entire series, improve UX

### Tasks

- [ ] **Edit Single Instance** (3 hours)
  - Add "Edit This Instance Only" vs "Edit Series" modal
  - Database: Add `is_exception` flag to reminders table
  - Store exception instances separately
  - **Testing:** Edit single recurring event, verify series unaffected

- [ ] **Delete Single Instance** (2 hours)
  - Add "Delete This Instance" vs "Delete Series" modal
  - Mark instance as deleted without removing series
  - **Testing:** Delete single occurrence, verify series continues

- [ ] **Recurrence Indicator** (1 hour)
  - Add ♻️ icon to recurring reminders in list views
  - Show recurrence pattern on hover/click
  - **Location:** `public/js/ui.js` rendering functions

- [ ] **View Original Pattern** (2 hours)
  - Add "View Series" button to recurring instances
  - Show recurrence pattern details modal
  - Link to parent pattern for editing
  - **Testing:** Click instance, view pattern, verify accuracy

**Estimated Time:** 8 hours
**Success Criteria:** Users can manage recurring series with granular control

---

## 🔮 Phase 10 - E-ink Display Clients

**Goal:** Android e-ink app for car dashboard (read-only with tap-to-complete)

### Research Phase (4 hours)

- [ ] E-ink Display Research
  - Test devices: BOOX, Remarkable, Kindle Fire mods
  - Refresh rate optimization strategies
  - Power consumption analysis

- [ ] Android E-ink SDK Evaluation
  - Compare frameworks (Jetpack Compose, React Native, Flutter)
  - E-ink-specific libraries (REGAL, A2 mode)
  - Decide on tech stack

### Development Phase (20-30 hours)

- [ ] **Read-Only Reminder Display** (8 hours)
  - Fetch reminders from API (local or cloud)
  - Display Today/Overdue lists
  - Optimize for e-ink (high contrast, minimal redraws)

- [ ] **Tap-to-Complete Gesture** (4 hours)
  - Single tap marks reminder complete
  - Haptic feedback confirmation
  - Optimized for e-ink refresh

- [ ] **Auto-Sync Background Service** (4 hours)
  - Poll API every 5 minutes
  - Minimal battery drain
  - Show sync status

- [ ] **Dashboard Mode** (4 hours)
  - Car dashboard optimized layout
  - Large touch targets for glances
  - Dark mode for night driving

- [ ] **Testing & Optimization** (4 hours)
  - Test on real e-ink devices
  - Optimize refresh rates (A2 mode for speed)
  - Battery life testing

**Estimated Time:** 24-34 hours
**Success Criteria:** Functional Android e-ink app with <1% battery drain/hour

---

## 🔮 Phase 11 - Smart Features

**Goal:** AI-powered automation and intelligence

### Tasks

- [ ] **Auto-Categorization** (4 hours)
  - Use LLM to suggest category based on text
  - Learn from user corrections
  - **Location:** Extend `server/voice/parser.py`

- [ ] **Duplicate Detection** (3 hours)
  - Fuzzy matching for similar reminders
  - Suggest merging duplicates
  - **Algorithm:** TF-IDF + cosine similarity

- [ ] **Reminder Templates** (4 hours)
  - Save common reminders as templates
  - Quick-create from template library
  - **UI:** Template picker in edit form

- [ ] **Priority Suggestions** (3 hours)
  - Learn priority patterns from user behavior
  - Suggest priority based on keywords/timing
  - **ML:** Simple classification model

- [ ] **Smart Defaults** (2 hours)
  - "Buy milk" → auto-set location to grocery store
  - "Call" → auto-set category to Personal
  - Learn from user patterns

**Estimated Time:** 16 hours
**Success Criteria:** 80% auto-category accuracy, 50% fewer manual edits

---

## 🔮 Phase 12 - Analytics & Insights

**Goal:** Help users understand their productivity patterns

### Tasks

- [ ] **Completion Rate Tracking** (3 hours)
  - Calculate daily/weekly/monthly completion %
  - Show trends over time
  - **Database:** Add analytics table

- [ ] **Time-of-Day Patterns** (3 hours)
  - When are reminders most often created?
  - When are they most often completed?
  - Heatmap visualization

- [ ] **Productivity Dashboard** (6 hours)
  - Weekly summary view
  - Category breakdown
  - Priority distribution
  - Completion streaks
  - **UI:** New dashboard.html page

- [ ] **Insights Engine** (4 hours)
  - "You complete 80% more tasks when you add a time"
  - "Your busiest day is Tuesday"
  - "Most overdue tasks are in category: Work"

- [ ] **Export Reports** (2 hours)
  - CSV export for completed reminders
  - Weekly summary email (optional)
  - PDF reports

**Estimated Time:** 18 hours
**Success Criteria:** Actionable insights visible on dashboard

---

## ✅ Completed Phases

<details>
<summary><strong>Phase 1-8.1: Core MVP (ALL COMPLETE ✅)</strong></summary>

### Phase 1-3: Foundation
- ✅ FastAPI REST API
- ✅ SQLite database
- ✅ Web UI (Today/Upcoming/Future views)
- ✅ CRUD operations
- ✅ 5-level priority system
- ✅ 138 automated tests (100% passing)

### Phase 4: Cloudflare Workers
- ✅ Hono TypeScript API
- ✅ D1 cloud database
- ✅ Edge deployment (81-112ms)
- ✅ Production URL: https://reminders-api.m7jv4v7npb.workers.dev

### Phase 5: Sync Logic
- ✅ Offline-first architecture
- ✅ Bidirectional sync (every 5 min)
- ✅ Last-write-wins conflict resolution
- ✅ Sync UI with 5 states

### Phase 6: Location Features
- ✅ MapBox GL JS integration
- ✅ Geocoding & reverse geocoding
- ✅ Radius-based queries (Haversine)
- ✅ Location picker UI

### Phase 7: Recurring Reminders
- ✅ Daily/weekly/monthly/yearly patterns
- ✅ Advanced scheduling (days of week, day of month)
- ✅ 3 end conditions (never, until date, after N)
- ✅ 90-day instance generation
- ✅ Live preview (next 3 occurrences)

### Phase 8: Voice Input
- ✅ Whisper.cpp integration (base.en model)
- ✅ Browser audio recording
- ✅ 96% transcription accuracy
- ✅ 0.32s avg processing time
- ✅ 14 tests (100% passing)

### Phase 8.1: NLP Parsing
- ✅ LM Studio integration (llama-3.2-1b-instruct)
- ✅ Dual-mode (local + Cloudflare Workers AI)
- ✅ Priority extraction (96% accuracy)
- ✅ Category classification (92% accuracy)
- ✅ Confidence scoring
- ✅ 65 tests (100% passing)

</details>

---

## 📊 Testing Results Summary

### Comprehensive Testing Session (Nov 8, 2025)

**Automated Tests:**
- 138/138 passing (100%)
- 52% code coverage (80-90% for Phase 8.1)
- 1.40s execution time

**Voice Pipeline:**
- 25/25 audio files transcribed (100%)
- 96% transcription accuracy (24/25 perfect)
- 8 seconds total (0.32s avg per file)

**NLP Parsing:**
- 25/25 parsed successfully (100%)
- Priority: 96% accuracy ✅
- Category: 92% accuracy ✅
- Date: 40% accuracy ⚠️
- Time: 28% accuracy ⚠️
- Avg confidence: 0.858

**MapBox:**
- ✅ Loading correctly
- ✅ Geolocation working
- ✅ Distance queries accurate
- ⚠️ UX improvements needed (default view, save button)

**Recurring Reminders:**
- ✅ 725 reminders in database (includes instances)
- ✅ All patterns generating correctly
- ✅ 90-day horizon working
- 🐛 Fixed: `get_reminder()` → `get_reminder_by_id()` (commit 9377c11)

**Cloud Sync:**
- ✅ Local sync working (526 changes)
- ⚠️ Cloud sync failing (401 token mismatch)

**Error Handling:**
- 12/13 tests passing (92%)
- ❌ Date validation missing (CRITICAL)

**Audio Compression:**
- Tested Opus 24kbps: 81% size reduction
- No quality degradation
- ✅ Recommended for production

**UI Testing:**
- ✅ 725 reminders loading
- ✅ All navigation working
- ✅ Sync status functional
- ⚠️ Future view layout different

**Production Readiness:** 90% (2 blockers, 3 UX improvements)

---

## 🚀 Future Ideas (Phase 13+)

### Hardware Integration
- Receipt printer for daily task lists
- Smart home integration (Google Home, Alexa)
- Wearable notifications (smartwatch)

### Advanced Features
- Habit tracking
- Calendar app integration (Google Calendar, iCal)
- Siri/Google Assistant shortcuts
- Email-to-reminder (forward@reminders.app)
- Collaborative reminders (shared with family)

### AI Enhancements
- Voice commands ("Show me today's tasks")
- Proactive suggestions ("You usually buy groceries on Saturday")
- Task dependencies ("Complete X before Y")
- Smart scheduling (find optimal time based on calendar)

### Mobile Apps
- iOS native app
- Android native app
- Progressive Web App (PWA)
- Offline-first mobile sync

---

## 📚 Quick Reference

### Development Commands

```bash
# Start local API server
uv run uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

# Serve frontend
python3 serve_ui.py
# OR open public/index.html directly

# Run tests
uv run pytest
uv run pytest --cov=server --cov-report=html

# Deploy to Cloudflare
cd workers && npx wrangler deploy

# Update cloud secrets
cd workers && npx wrangler secret put API_TOKEN
```

### Project URLs

- **Local API:** http://localhost:8000
- **Local Frontend:** http://localhost:3077
- **Cloud API:** https://reminders-api.m7jv4v7npb.workers.dev
- **API Docs:** http://localhost:8000/docs (Swagger)

### Secrets Required

Stored in `secrets.json` (see `secrets_template.json`):
- `mapbox_access_token` - MapBox GL JS (get at https://account.mapbox.com/)
- `api_token` - Bearer token for API auth (strong random string)

### Database Schema

SQLite tables (local + cloud D1):
- `reminders` - Main reminder instances
- `recurrence_patterns` - Recurrence definitions

### Testing Files

- Test audio: `EXAMPLE_RECORDINGS/` (25 M4A files)
- Transcriptions: `transcriptions/` (25 TXT files)
- NLP results: `nlp_results/` (25 JSON files)
- Test report: `COMPREHENSIVE_TEST_REPORT.md`

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

## 📈 Progress Timeline

- **November 1, 2025** - Phase 1-3 complete (Backend + Frontend + Testing)
- **November 2, 2025** - Phase 4 complete (Cloudflare Workers)
- **November 2, 2025** - Phase 5 complete (Sync Logic)
- **November 3, 2025** - Phase 6 complete (MapBox Location)
- **November 3, 2025** - Phase 7 complete (Recurring Reminders)
- **November 3, 2025** - Phase 8 complete (Voice Transcription)
- **November 4, 2025** - Phase 8.1 complete (NLP Parsing)
- **November 8, 2025** - Comprehensive testing session complete
- **November 8, 2025** - **NOW:** Phase 9.0 Production Hardening

---

## 🎯 Current Sprint: Phase 9.0 Production Hardening

**Goal:** Fix 2 critical blockers + 3 UX improvements before MVP launch

**Tasks:** 6 items (see Phase 9.0 section above)

**Estimated Time:** ~3 hours total

**Completion Target:** November 9, 2025

**Next Sprint:** Phase 9.1 NLP Enhancement (7.5 hours)

---

*Last Updated: November 8, 2025*
*Model: Claude Sonnet 4.5*
*Status: Testing Complete ✅ | Production Hardening Next 🔧*
