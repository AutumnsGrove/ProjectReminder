# Project Next Steps

## Current Status: Phase 7 Complete ✅ | Phase 8 Next (Voice Input)

**Last Updated:** November 3, 2025 (Evening Session)
**MVP Progress:** 87.5% complete (7/8 phases)
**Remaining to MVP:** Phase 8 (Voice Input) - ~12-15 hours

---

## Recently Completed: Phase 7 (Recurring Reminders)

### What Was Built ✅
- Full recurring reminders system with 4 frequencies (daily/weekly/monthly/yearly)
- Server-side instance generation with 90-day horizon
- Advanced scheduling (specific days of week, day of month)
- 3 end conditions (never, until date, after N occurrences)
- Live UI preview showing next 3 occurrences
- Complete backend (FastAPI) + cloud (Workers) support

### Commit Details
- **Commit:** `9401cb6 feat: Phase 7 recurring reminders implementation`
- **Files Changed:** 9 files, +1,517 insertions, -40 deletions
- **Status:** Pushed to GitHub ✅

### Testing Status
⚠️ **Needs manual testing** when you have access to the app:
- Daily recurrence patterns
- Weekly with specific days (Mon, Wed, Fri)
- Monthly on specific day (15th)
- End conditions (never/date/count)
- Preview accuracy

---

## Immediate Next: Phase 8 (Voice Input & NLP)

**Estimated Time:** 12-15 hours (~2 days)
**Priority:** HIGH (completes MVP)

### ⚠️ IMPORTANT: Use Proper Subagent Workflow

**Phase 7 was done incorrectly** (monolithic, no subagents, no atomic commits).
**Phase 8 MUST follow** `ClaudeUsage/subagent_usage.md` guidelines.

### Required Workflow for Phase 8

#### 1. Research Phase (Day 1 Morning - 3-4 hours)

**Launch these subagents sequentially:**

1. **web-research-specialist** - Research Whisper.cpp integration
   - Query: "Whisper.cpp Python bindings 2025 installation best practices"
   - Query: "Whisper.cpp performance optimization local inference"
   - Output: `docs/whisper_research.md` → commit

2. **web-research-specialist** - Research small LLMs for NLP
   - Query: "Llama 3.2 1B Python integration local inference 2025"
   - Query: "Phi-3 Mini task parsing natural language 2025"
   - Output: `docs/llm_research.md` → commit

3. **house-planner** - Create Phase 8 architecture plan
   - Input: Research findings + Phase 7 codebase understanding
   - Output: `docs/phase8_architecture.md` with:
     - Component breakdown (6-8 subagents)
     - API endpoint design
     - Data flow diagrams
     - Edge case handling
   - Commit immediately

4. **security-auditor** - Review voice/audio security concerns
   - Input: Architecture plan
   - Output: `docs/phase8_security.md`
   - Commit immediately

#### 2. Development Phase (Day 1 Afternoon + Day 2 - 8-10 hours)

**Each subagent = 1 focused task = 1 atomic commit**

Launch these subagents one at a time:

1. **house-bash** - Install and test Whisper.cpp
   - Install dependencies
   - Test basic transcription
   - Document setup in `docs/whisper_setup.md`
   - Commit: `chore: install and configure Whisper.cpp`

2. **house-bash** - Install and test chosen LLM (Llama/Phi)
   - Install model and dependencies
   - Test basic inference
   - Document setup in `docs/llm_setup.md`
   - Commit: `chore: install and configure [LLM name]`

3. **quick-code-patch** - Add audio transcription endpoint
   - Create `POST /api/voice/transcribe`
   - Integrate Whisper.cpp wrapper
   - Add to `server/main.py`
   - Commit: `feat: add voice transcription endpoint`

4. **quick-code-patch** - Add NLP parsing endpoint
   - Create `POST /api/voice/parse`
   - Integrate LLM for task parsing
   - Add structured output (text, due_date, priority, etc.)
   - Commit: `feat: add NLP task parsing endpoint`

5. **quick-code-patch** - Add voice button UI
   - Add microphone button to edit form
   - Style with CSS
   - Add recording indicator
   - Commit: `feat: add voice input button UI`

6. **quick-code-patch** - Implement audio recording
   - Use browser MediaRecorder API
   - Handle permissions
   - Add visual feedback during recording
   - Commit: `feat: implement browser audio recording`

7. **quick-code-patch** - Connect frontend to backend
   - Upload audio to `/api/voice/transcribe`
   - Send transcription to `/api/voice/parse`
   - Populate form with parsed data
   - Commit: `feat: integrate voice input with backend`

8. **quick-code-patch** - Add error handling
   - Handle microphone permission denied
   - Handle parsing failures
   - Add fallback to manual edit
   - Commit: `fix: add voice input error handling`

#### 3. Testing Phase (Day 2 Afternoon - 2-3 hours)

1. **test-strategist** - Plan test cases
   - Output: `tests/test_voice_input_plan.md`
   - Commit

2. **house-bash** - Run manual testing
   - Test various voice commands
   - Document results in `docs/phase8_testing.md`
   - Commit

3. Manual testing by human (when available)

---

## Phase 8 Success Criteria

**Voice Input Must:**
- ✅ Record audio from browser microphone
- ✅ Transcribe audio using Whisper.cpp (locally)
- ✅ Parse transcription using small LLM (locally)
- ✅ Extract: text, due_date, due_time, priority, location
- ✅ Handle errors gracefully (permissions, parsing failures)
- ✅ Runs entirely offline (privacy preserved)
- ✅ Complete end-to-end in <5 seconds
- ✅ >90% accuracy on common phrases

**Example Interactions:**
```
"Remind me to call mom tomorrow at 3pm"
→ {text: "Call mom", due_date: "2025-11-04", due_time: "15:00"}

"Buy groceries when I'm at Kroger"
→ {text: "Buy groceries", location_text: "Kroger"}

"Important: Submit report by Friday 5pm"
→ {text: "Submit report", due_date: "2025-11-08", due_time: "17:00", priority: "important"}
```

---

## Key Files to Reference

### For Voice Input Implementation:
- `server/main.py` - Add voice endpoints here
- `server/models.py` - Create VoiceTranscriptionRequest/Response models
- `public/edit.html` - Add microphone button near form
- `public/js/app.js` - Reference form submission pattern
- `public/js/recurrence.js` - Reference modular JS pattern

### Architecture Patterns Already Established:
- Database functions isolated in `server/database.py`
- Pydantic models in `server/models.py`
- Bearer token auth via `verify_token()` dependency
- Frontend modular JS (storage.js, api.js, sync.js, etc.)
- Mobile-first CSS with CSS variables

---

## Quick Start for Next Agent

```bash
# 1. Check current status
git status
git log --oneline -5

# 2. Read Phase 8 requirements
cat TODOS.md | grep -A 50 "Phase 8"

# 3. Start research phase
# Launch web-research-specialist for Whisper.cpp
# Launch web-research-specialist for LLMs
# Launch house-planner for architecture

# 4. Create working branch (optional)
git checkout -b phase8-voice-input

# 5. Follow subagent workflow from above
# One subagent → one commit → next subagent
```

---

## Deferred to Future Phases

### Phase 7.1 Enhancements (Post-MVP)
- "Edit this instance only" vs "Edit series" for recurring reminders
- "Delete this instance only" vs "Delete series"
- Visual indicator in reminder list (♻️ icon)
- View/edit original recurrence pattern after creation

### Phase 9: Advanced Features (Post-MVP)
- E-ink display clients (Android car dashboard)
- Receipt printer integration
- Analytics and completion tracking
- Smart categorization
- Duplicate detection

### Phase 10: AI Enhancements (Post-MVP)
- Context-aware suggestions
- Priority recommendations
- Time-of-day pattern detection

---

## Current Project State

**Repository:** https://github.com/AutumnsGrove/ProjectReminder
**Local Server:** `cd server && uv run python -m uvicorn main:app --reload`
**Frontend:** `public/*.html` (open directly in browser)
**Cloud Deployment:** https://reminders-api.m7jv4v7npb.workers.dev

**Database Schema:** SQLite with these tables:
- `reminders` - Main reminder instances
- `recurrence_patterns` - Recurrence definitions (Phase 7)
- Both in local SQLite and cloud D1

**Secrets Required:** (stored in `secrets.json`)
- `mapbox_access_token` - For location features
- `api_token` - Bearer token for API auth

---

## Notes for Next Agent

1. **Follow subagent_usage.md religiously** - Phase 7 violated this, don't repeat
2. **Commit atomically** - Every logical change = one commit
3. **Test locally first** - Human can't test remotely right now
4. **Document as you go** - Each subagent produces documentation
5. **Ask questions** - If architecture unclear, use `house-planner`
6. **Check ClaudeUsage/** - Comprehensive guides for everything

**Good luck with Phase 8!** 🎤🎯

---

*Last Updated: November 3, 2025 (Evening Session)*
*Model: Claude Sonnet 4.5*
*Phase 7 Complete | Phase 8 Next | MVP 87.5% Complete*
