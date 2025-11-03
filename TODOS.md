# TODOs - ADHD-Friendly Voice Reminders System

**Project Status:** ✅ Phase 1, 2, 3 Complete - Ready for Phase 4
**Last Updated:** November 2, 2025 (Evening Session)

---

## Phase 1: Core Backend (Day 1) ✅ COMPLETE

### Setup & Configuration
- [x] Initialize Python environment with UV
- [x] Create `server/` directory structure
- [x] Set up FastAPI project structure
- [x] Create `secrets.json` from template
- [x] Add `secrets.json` to `.gitignore`
- [x] Configure MapBox and API tokens

### Database
- [x] Create `server/database.py` with SQLite interface
- [x] Implement reminders table schema (all fields from spec)
- [x] Add database indexes for performance
- [x] Create seed data function (default categories)
- [x] Write database initialization script
- [x] Test database connection and queries

### API Development
- [x] Create `server/main.py` FastAPI app entry point
- [x] Create `server/models.py` with Pydantic models
- [x] Create `server/config.py` for configuration
- [x] Implement bearer token authentication middleware
- [x] Add CORS configuration for web UI

### CRUD Endpoints
- [x] Implement `GET /api/health` - Health check endpoint
- [x] Implement `POST /api/reminders` - Create reminder
- [x] Implement `GET /api/reminders` - List reminders (with filters)
- [x] Implement `GET /api/reminders/:id` - Get single reminder
- [x] Implement `PATCH /api/reminders/:id` - Update reminder
- [x] Implement `DELETE /api/reminders/:id` - Delete reminder

### Testing & Documentation
- [x] Test all endpoints with curl/Postman
- [x] Verify Swagger docs at `/docs` work
- [x] Test authentication (valid/invalid tokens)
- [x] Verify database persistence
- [x] Document any deviations from spec

**Success Criteria:**
- ✅ API running on localhost:8000
- ✅ Can create/read/update/delete reminders
- ✅ Authentication works
- ✅ Database persists data
- ✅ All fields from spec implemented
- ✅ ISO 8601 formatting correct
- ✅ Priority and status enums working
- ✅ Error handling with proper status codes

---

## Phase 2: Web UI (Day 1-2) 📅

### Project Structure
- [ ] Create `public/` directory
- [ ] Create subdirectories: `css/`, `js/`, `assets/icons/`
- [ ] Set up basic HTML5 template structure

### HTML Pages
- [ ] Create `public/index.html` - Today view
- [ ] Create `public/upcoming.html` - Upcoming view
- [ ] Create `public/edit.html` - Create/edit form
- [ ] Create `public/settings.html` - Configuration

### CSS Styling
- [ ] Create `public/css/main.css` - Global styles
- [ ] Create `public/css/today.css` - Today view specific
- [ ] Create `public/css/upcoming.css` - Upcoming view specific
- [ ] Create `public/css/edit.css` - Form styles
- [ ] Implement mobile-first responsive design
- [ ] Add priority colors (chill: green, important: yellow, urgent: red)
- [ ] Style completion animations

### JavaScript Structure
- [ ] Create `public/js/app.js` - Main app logic with mock data
- [ ] Create `public/js/api.js` - API client wrapper (stub)
- [ ] Create `public/js/storage.js` - LocalStorage helpers
- [ ] Create `public/js/animations.js` - UI animations

### UI Implementation
- [ ] Build Today view with sample data
- [ ] Build Upcoming view with sample data
- [ ] Build reminder form with validation
- [ ] Add completion animation (checkbox → fade out → slide up)
- [ ] Implement swipe-to-delete gesture (mobile)
- [ ] Add priority badge visualization
- [ ] Test on mobile and desktop screen sizes

**Success Criteria:**
- ✅ UI looks good on mobile and desktop
- ✅ Animations work smoothly
- ✅ Forms validate input
- ✅ All pages render with mock data

---

## Phase 3: Integration (Day 2) ✅ COMPLETE

### API Client
- [x] Implement full API client in `public/js/api.js`
- [x] Add fetch() calls for all endpoints
- [x] Implement bearer token auth headers
- [x] Add error handling and user feedback

### View Integration
- [x] Connect Today view to load reminders
- [x] Connect Upcoming view to load upcoming reminders
- [x] Wire up create form to `POST /api/reminders`
- [x] Wire up edit form to `PATCH /api/reminders/:id`
- [x] Implement delete functionality

### Error Handling
- [x] Handle offline state gracefully
- [x] Show user-friendly error messages (toast notifications)
- [x] Add loading states for async operations
- [x] Implement retry logic for failed requests (3 attempts)

### Critical Fixes
- [x] Fix race condition causing 401 errors
- [x] Rotate API tokens (security hardening)
- [x] Fix script loading order dependencies
- [x] Update getTodayReminders() structure in UI

**Success Criteria:**
- ✅ Can create reminders in UI → saved to DB
- ✅ Can complete reminders → updates DB
- ✅ Can edit and delete reminders
- ✅ Error messages are helpful
- ✅ Full stack integration working

**Previous Issues (RESOLVED):**
- [x] ~~🐛 Create reminder form doesn't save to database~~ - **FIXED** in commit 7d686fe (race condition causing 401 errors before config loaded)

**Known Issues for Next Session:**
- [ ] Time picker not appearing (HTML5 input type="time" not working in some browsers) - Use text input as workaround

**Enhancements Identified:**
- [ ] 💡 **UX Issue**: Reminders beyond 7 days are invisible - Add "Future" view for tasks >7 days out
  - Current: Today (overdue/today/floating) + Upcoming (next 7 days)
  - Needed: Future view for reminders 8+ days out
  - Alternative: Extend Upcoming window to 30 days
- [ ] ✅ **Testing**: Add automated tests - **DONE** in commit c85bbd7 (24 tests, 80% coverage)

---

## Phase 4: Cloudflare Workers (Day 2-3) 📅

### Setup
- [ ] Create Cloudflare account (free tier)
- [ ] Install Wrangler CLI (`npm install -g wrangler`)
- [ ] Login to Cloudflare: `wrangler login`
- [ ] Create `workers/` directory

### Workers Development
- [ ] Create `workers/src/index.ts` - Workers API
- [ ] Create `workers/wrangler.toml` - Configuration
- [ ] Implement TypeScript versions of all FastAPI endpoints
- [ ] Add CORS headers for web UI access
- [ ] Implement bearer token authentication

### D1 Database
- [ ] Create D1 database: `wrangler d1 create reminders`
- [ ] Create schema migration SQL file
- [ ] Run migrations to set up tables
- [ ] Seed default categories

### Deployment
- [ ] Deploy to Cloudflare: `wrangler deploy`
- [ ] Test cloud API with curl
- [ ] Verify D1 data persistence
- [ ] Update settings page with cloud URL

**Success Criteria:**
- ✅ Cloud API responds to requests
- ✅ Can switch UI to cloud endpoint
- ✅ Data persists in D1
- ✅ CORS allows web UI access

---

## Phase 5: Sync Logic (Day 3) 📅

### Sync Endpoint
- [ ] Implement `POST /api/sync` in FastAPI
- [ ] Implement `POST /api/sync` in Workers
- [ ] Add `synced_at` timestamp tracking
- [ ] Implement conflict detection logic

### Client Sync Manager
- [ ] Create `public/js/sync.js` - Sync manager
- [ ] Track local changes in queue
- [ ] Implement background sync (every 5 minutes)
- [ ] Add manual sync button in settings
- [ ] Show sync status indicator (online/offline/syncing)

### Conflict Resolution
- [ ] Implement last-write-wins based on `updated_at`
- [ ] Log conflicts for debugging
- [ ] Add sync error handling

### Testing
- [ ] Test offline → online sync
- [ ] Test multi-device sync scenario
- [ ] Verify no data loss during sync
- [ ] Test conflict resolution

**Success Criteria:**
- ✅ Can work offline → changes saved locally
- ✅ When online → changes sync to cloud
- ✅ Other devices receive updates
- ✅ No data loss during sync
- ✅ Conflicts resolved automatically

---

## Phase 6: Location Features (Day 3-4) 📅

### MapBox Setup
- [ ] Get MapBox access token (free tier)
- [ ] Add MapBox GL JS to project
- [ ] Configure MapBox in secrets.json

### Location Picker
- [ ] Create location picker component in edit form
- [ ] Implement geocoding (address → lat/lng)
- [ ] Add map visualization
- [ ] Enable pin dragging to adjust location
- [ ] Add radius configuration (default: 100m)

### Location Endpoints
- [ ] Implement `GET /api/reminders/near-location` (FastAPI)
- [ ] Implement `GET /api/reminders/near-location` (Workers)
- [ ] Add Haversine distance calculation
- [ ] Test location-based filtering

### Geolocation
- [ ] Integrate browser Geolocation API
- [ ] Add "Use my location" button
- [ ] Handle permission denied gracefully
- [ ] Display location reminders on map (optional view)

**Success Criteria:**
- ✅ Can set reminder location via text or map
- ✅ Can query reminders near current location
- ✅ Location-based filtering works
- ✅ Geocoding is accurate

---

## Phase 7: Recurring Reminders (Iteration 2) 🔮

### Database
- [ ] Create `recurrence_patterns` table
- [ ] Add foreign key relationship to reminders
- [ ] Implement recurrence pattern validation

### Recurrence UI
- [ ] Add recurrence section to edit form
- [ ] Create UI for pattern selection (daily/weekly/monthly/yearly)
- [ ] Add interval configuration (every N days/weeks/etc.)
- [ ] Add end conditions (date/count/infinite)

### Instance Generation
- [ ] Write recurrence instance generator
- [ ] Handle "this instance" vs "series" edits
- [ ] Implement deletion logic (instance vs series)
- [ ] Display recurrence info in reminder list

### Testing
- [ ] Test daily recurrence
- [ ] Test weekly recurrence (specific days)
- [ ] Test monthly recurrence
- [ ] Test complex patterns

**Success Criteria:**
- ✅ Can create "every Tuesday" reminder
- ✅ Can edit/delete single instance or series
- ✅ Recurrence displayed correctly
- ✅ Instances generated automatically

---

## Phase 8: Voice Input (Iteration 2) 🔮

### Research
- [ ] Research local STT options (Whisper.cpp, Vosk)
- [ ] Research small LLMs (Llama 3.2 1B, Phi-3 Mini)
- [ ] Evaluate performance on target hardware
- [ ] Choose final stack

### STT Integration
- [ ] Install and configure chosen STT model
- [ ] Create Python wrapper for STT
- [ ] Add voice recording endpoint
- [ ] Test transcription accuracy

### NLP Parsing
- [ ] Install and configure chosen LLM
- [ ] Create prompt for reminder parsing
- [ ] Implement parsing pipeline (text → structured data)
- [ ] Add fallback to manual edit if parse fails

### UI Integration
- [ ] Add voice button (🎤) to edit form
- [ ] Implement audio recording in browser
- [ ] Send audio to backend for processing
- [ ] Display transcription before saving
- [ ] Handle parsing errors gracefully

### Testing
- [ ] Test: "Remind me to call mom tomorrow at 3pm"
- [ ] Test: "Buy groceries when I'm at Kroger"
- [ ] Test: "Important: Submit report by Friday"
- [ ] Measure end-to-end latency (<5 seconds target)

**Success Criteria:**
- ✅ Voice input creates correct reminders
- ✅ Runs locally (privacy preserved)
- ✅ Fast enough (<5 seconds)
- ✅ Handles ambiguity gracefully

---

## Future Features (Post-MVP) 🔮

### E-ink Clients
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
- [ ] Test print output

### Analytics
- [ ] Track completion rates
- [ ] Generate productivity insights
- [ ] Identify time-of-day patterns

---

## Documentation & Maintenance

### Current Session
- [x] Customize CLAUDE.md with project specifics
- [x] Update README.md with project details
- [x] Update TODOS.md with implementation phases

### Ongoing
- [ ] Update TODOS.md as phases complete
- [ ] Document architectural decisions
- [ ] Keep API documentation current
- [ ] Update project spec with learnings

---

## Notes

- Phase 1-3 are MVP "must-haves"
- Phase 4-5 enable multi-device functionality
- Phase 6-8 are "nice-to-haves" for v1.0
- Future features are iteration 2+

**Current Focus:** Phase 1 - Core Backend

---

*Generated by Claude Sonnet 4.5*
*Last Updated: November 2, 2025*
