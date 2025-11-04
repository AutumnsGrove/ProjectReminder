# TODOs - ADHD-Friendly Voice Reminders System

**Status:** 🚀 Phase 1-8 Complete (87.5% to MVP) | Phase 8.1 Next
**Last Updated:** November 4, 2025
**Cloud API:** https://reminders-api.m7jv4v7npb.workers.dev

---

## 🎯 NEXT: Phase 8.1 - LLM Natural Language Parsing

**Goal:** Auto-extract reminder metadata from voice transcriptions using local LLM.

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

### Tasks

- [ ] Install and configure Llama 3.2 1B or Phi-3 Mini
- [ ] Design system prompt for reminder parsing (dates, times, priorities, locations)
- [ ] Create `POST /api/voice/parse` endpoint (FastAPI)
- [ ] Implement parsing pipeline: text → structured JSON
- [ ] Add fallback to manual edit if parse confidence is low
- [ ] Integrate with voice recorder UI (auto-fill form fields)
- [ ] Test with 20+ varied natural language inputs
- [ ] Add Workers endpoint (or return 501 for MVP)

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
