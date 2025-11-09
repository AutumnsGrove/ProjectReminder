# 🎤 ADHD-Friendly Voice Reminders System

An offline-first, persistent reminders system designed specifically for ADHD workflows. Voice input is the primary interaction method, with visual persistence across multiple devices (desktop, mobile, e-ink displays).

**Developer:** Autumn Brown
**Version:** 1.0 MVP
**Status:** 🚀 100% Production Ready - MVP Complete!
**Latest:** ✨ Phase 9.0 Complete - Security hardened, fully tested, ready to launch

---

## Key Features

### Core Philosophy: Persistent Visibility
- **Tasks don't disappear** - They stay visible until explicitly completed
- **Offline-first** - Works without internet, syncs when available
- **Voice-native** - Natural language input ("remind me to call mom tomorrow at 3pm")
- **Location-aware** - Context-based reminders ("when I'm at Home Depot")
- **Multi-device** - Desktop, mobile, e-ink dashboard synchronization

### ADHD-Optimized Design
- **Object permanence support** - Out of sight ≠ out of mind
- **Low friction** - Voice input removes typing barrier
- **Flexible timing** - "Today" vs "Tuesday at 3pm exactly"
- **Priority vibes** - "chill/important/urgent" not numeric scales
- **No notification fatigue** - Persistent display instead of aggressive pings

---

## Architecture

### Three-Tier System

```
┌─────────────────────────────────────────────────────┐
│                   Web UI (Client)                   │
│              HTML/CSS/Vanilla JavaScript            │
│         MapBox GL JS | LocalStorage Config          │
└──────────────┬─────────────────┬────────────────────┘
               │                 │
       ┌───────┴────────┐   ┌────┴──────────────┐
       │                │   │                    │
┌──────▼──────┐   ┌────▼──────────────┐   ┌────▼────────┐
│   Local     │   │   Cloudflare      │   │   E-ink     │
│   FastAPI   │   │   Workers API     │   │   Clients   │
│   Server    │   │   (TypeScript)    │   │  (Android)  │
└──────┬──────┘   └────┬──────────────┘   └─────────────┘
       │               │
┌──────▼──────┐   ┌────▼──────────────┐
│   SQLite    │   │  Cloudflare D1    │
│   Local DB  │◄──┤  (Cloud SQLite)   │
└─────────────┘   └───────────────────┘
       │                 │
       └────────┬────────┘
                │
         Background Sync
       (Bidirectional)
```

**1. Cloud Layer** - Cloudflare Workers + D1 for backup & multi-device sync
**2. Local Layer** - FastAPI + SQLite for offline-first primary operation
**3. Client Layer** - Web UI connects to local (first) or cloud (fallback)

---

## Tech Stack

### Backend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Local API | FastAPI (Python 3.11+) | REST API server |
| Local DB | SQLite 3 | Local data storage |
| Cloud API | Cloudflare Workers | Serverless edge API |
| Cloud DB | Cloudflare D1 | Cloud SQLite |
| Auth | Bearer Token | Simple auth (MVP) |

### Frontend
| Component | Technology | Purpose |
|-----------|------------|---------|
| UI | HTML5 + CSS3 + Vanilla JS | No framework overhead |
| Maps | MapBox GL JS | Location picker |
| Storage | LocalStorage | Settings/config |
| Requests | Fetch API | HTTP client |

### Future Additions
| Component | Technology | Purpose |
|-----------|------------|---------|
| Voice STT | Whisper.cpp / Vosk | Local speech-to-text |
| Mobile | React Native / Native Android | Phone app |
| E-ink | Android app | Car dashboard |

---

## 📁 Project Structure

Clear, organized, ADHD-friendly directory layout:

```
ProjectReminder/
├── 📄 README.md              # You are here!
├── 📄 CLAUDE.md              # AI assistant instructions
├── 🔧 pyproject.toml         # Python dependencies (UV)
├── 🔧 secrets.json           # API keys (create from template)
├── 🔧 secrets_template.json  # Template for secrets
│
├── 🖥️  server/               # FastAPI backend
│   ├── main.py              # API server
│   ├── database.py          # SQLite operations
│   ├── models.py            # Pydantic models
│   ├── tests/               # 248 tests, 100% passing
│   └── voice/               # Voice & NLP processing
│
├── 🌐 public/                # Frontend (HTML/CSS/JS)
│   ├── index.html           # Today view
│   ├── upcoming.html        # Upcoming reminders
│   ├── future.html          # Future reminders
│   ├── edit.html            # Create/edit form
│   ├── settings.html        # App settings
│   ├── js/                  # Vanilla JavaScript
│   └── css/                 # Stylesheets
│
├── ☁️  workers/              # Cloudflare Workers (cloud sync)
│   ├── src/index.ts         # Workers API
│   ├── wrangler.toml        # Cloudflare config
│   └── README.md            # Deployment guide
│
├── 📚 docs/                  # All documentation
│   ├── testing/             # Test reports
│   ├── architecture/        # Design docs
│   ├── guides/              # How-to guides
│   └── archives/            # Historical docs
│
├── 🧰 ClaudeUsage/          # Claude Code guidelines
│   └── *.md                 # Best practices for AI assistance
│
├── 🧪 test-artifacts/       # Test data (gitignored)
│   ├── recordings/          # 8 voice samples
│   ├── transcriptions/      # Test transcriptions
│   └── coverage/            # Coverage reports
│
└── 💾 data/                 # Runtime data (gitignored)
    ├── databases/           # SQLite files
    └── config/              # Local config
```

### Key Directories

- **`server/`** - Python backend (FastAPI + SQLite)
- **`public/`** - Frontend web app (vanilla JS, no frameworks)
- **`workers/`** - Cloud sync service (Cloudflare Workers + D1)
- **`docs/`** - All documentation in one place
- **`test-artifacts/`** - Test data (not committed)
- **`data/`** - Runtime data (not committed)

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ (for Cloudflare Workers)
- MapBox account (free tier)
- UV package manager (`pip install uv`)

### Quick Start (Local Development)

```bash
# 1. Clone the repository
git clone <repo-url>
cd ProjectReminder

# 2. Set up Python environment
uv init
uv add fastapi uvicorn sqlalchemy pydantic

# 3. Create secrets file
cp secrets_template.json secrets.json
# Edit secrets.json with your MapBox token and generate API token

# 4. Database is created automatically on first run
# No manual initialization needed!

# 5. Start local API server
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000 OR
uv run uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

# 6. Open web UI
open public/index.html
# Or serve with: python -m http.server 8080 --directory public
```

### Configuration

**secrets.json** (create from template, never commit):
```json
{
  "mapbox_access_token": "pk.eyJ1...",
  "api_token": "your-strong-random-token-here"
}
```

**Web UI settings** (configured in settings.html):
- API endpoint: `http://localhost:8000` (local) or cloud URL
- Sync interval: 5 minutes (default)
- Location settings: Auto-detect, default radius 100m

---

## Implementation Roadmap

### Phase 1: Core Backend ✅
- FastAPI REST API
- SQLite database with schema
- CRUD endpoints
- Bearer token auth

### Phase 2: Web UI ✅
- Today/Upcoming views
- Create/edit reminder form
- Mobile-responsive design
- Completion animations

### Phase 3: Integration ✅
- Connect UI to local API
- Full CRUD functionality
- Error handling

### Phase 4: Cloudflare Workers ✅
- TypeScript Workers API
- D1 database setup
- Deploy to edge network

### Phase 5: Sync Logic ✅
- Bidirectional sync
- Conflict resolution
- Background sync

### Phase 6: Location Features ✅
- MapBox integration
- Geocoding
- Near-location queries

### Phase 7: Recurring Reminders ✅
- Recurrence patterns
- Instance generation

### Phase 8: Voice Input ✅
- Whisper.cpp integration (local STT)
- Voice transcription endpoint
- Browser audio recording
- 85-90% transcription accuracy

### Phase 8.1: LLM Parsing ✅
- Auto-extract dates, times, priorities
- Natural language understanding
- Dual-mode: Local (Llama 3.2 1B via LM Studio) + Remote (GPT-OSS 20B via Cloudflare Workers AI)

---

## 📖 Documentation

### Getting Started
- [Quick Start Guide](#getting-started) - Setup instructions above
- [Secrets Template](secrets_template.json) - API key configuration

### Testing & Quality
- [Comprehensive Test Report](docs/testing/COMPREHENSIVE_TEST_REPORT.md) - 248 tests, 100% passing, 36% coverage
- [Test Artifacts](test-artifacts/README.md) - Voice samples and test data

### Development Guides
- [Project Roadmap](docs/guides/PROJECT_ROADMAP.md) - Current status and future plans
- [Contributing Guide](docs/guides/CONTRIBUTING.md) - How to contribute
- [Claude Usage Guides](ClaudeUsage/README.md) - AI-assisted development best practices

### Architecture & Design
- [Architecture Docs](docs/architecture/) - System design and technical decisions
- [Workers Deployment](workers/README.md) - Cloudflare Workers setup

### Data & Configuration
- [Data Directory](data/README.md) - Database and config files
- [Test Artifacts](test-artifacts/README.md) - Test recordings and results

---

## API Documentation

### Base URLs
- **Local:** `http://localhost:8000/api`
- **Cloud:** `https://reminders-api.YOUR_SUBDOMAIN.workers.dev/api`

### Key Endpoints
- `POST /api/reminders` - Create reminder
- `GET /api/reminders/today` - Today view
- `GET /api/reminders/upcoming` - Upcoming view
- `PATCH /api/reminders/:id` - Update reminder
- `DELETE /api/reminders/:id` - Delete reminder
- `POST /api/sync` - Bidirectional sync

### Authentication
All requests require bearer token:
```http
Authorization: Bearer YOUR_API_TOKEN
```

For complete API specification, see `reminders-project-spec.md` (API Specification section).

---

## Database Schema

### reminders table
```sql
CREATE TABLE reminders (
    id TEXT PRIMARY KEY,           -- UUID v4
    text TEXT NOT NULL,            -- Reminder description
    due_date TEXT,                 -- ISO 8601 date
    due_time TEXT,                 -- ISO 8601 time
    time_required BOOLEAN,         -- Must be done at specific time
    location_text TEXT,            -- Human-readable location
    location_lat REAL,             -- Latitude
    location_lng REAL,             -- Longitude
    location_radius INTEGER,       -- Trigger radius (meters)
    priority TEXT,                 -- 'chill', 'important', 'urgent'
    category TEXT,                 -- Freeform tag
    status TEXT,                   -- 'pending', 'completed', 'snoozed'
    completed_at TEXT,             -- ISO 8601 timestamp
    snoozed_until TEXT,            -- ISO 8601 timestamp
    recurrence_id TEXT,            -- Foreign key to recurrence_patterns
    source TEXT,                   -- 'manual', 'voice', 'api'
    created_at TEXT NOT NULL,      -- ISO 8601 timestamp
    updated_at TEXT NOT NULL,      -- ISO 8601 timestamp
    synced_at TEXT                 -- Last cloud sync
);
```

---

## Development Workflow

### Before You Start
1. Check `TODOS.md` for current tasks
2. Read relevant guides in `ClaudeUsage/`
3. Ensure secrets are configured

### Making Changes
1. Create feature branch: `git checkout -b feature/name`
2. Implement changes
3. Test locally
4. Update `TODOS.md`
5. Commit with conventional commits format
6. Merge to `main` when complete

### Conventional Commits
```bash
feat: Add location picker component
fix: Correct timezone handling in due dates
docs: Update API documentation
refactor: Extract validation logic to separate module
```

For complete git workflow, see `ClaudeUsage/git_guide.md`.

---

## Testing

### Manual Testing (MVP)
- Test CRUD operations via Swagger docs (`http://localhost:8000/docs`)
- Test UI on multiple screen sizes
- Test offline functionality (disable network)
- Test sync with multiple devices

### Future: Automated Testing
- Unit tests for API endpoints
- Integration tests for sync logic
- E2E tests for critical flows

---

## Deployment

### Local Deployment
```bash
# Run FastAPI server
uvicorn server.main:app --host 0.0.0.0 --port 8000

# Serve web UI
python -m http.server 8080 --directory public
```

### Cloudflare Workers Deployment (Phase 4)
```bash
cd workers
npm install
npx wrangler login
npx wrangler d1 create reminders
npx wrangler deploy
```

---

## Troubleshooting

### API Not Responding
- Check server is running: `curl http://localhost:8000/api/health`
- Verify port 8000 is not in use: `lsof -i :8000`
- Check logs for errors

### Database Issues
- Ensure `reminders.db` exists in project root
- Verify permissions: `chmod 644 reminders.db`
- Reinitialize if corrupted: `python server/database.py`

### UI Not Loading Data
- Check API endpoint in settings
- Verify bearer token is correct
- Check browser console for errors
- Ensure CORS is configured (FastAPI)

---

## Contributing

This is a personal project, but suggestions welcome! If you find issues:
1. Check `TODOS.md` to see if it's already tracked
2. Create GitHub issue with details
3. Follow project coding style (see `ClaudeUsage/code_style_guide.md`)

---

## Resources

### Documentation
- [Full Project Specification](reminders-project-spec.md)
- [Development Guides](ClaudeUsage/README.md)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Cloudflare Workers](https://developers.cloudflare.com/workers/)
- [MapBox GL JS](https://docs.mapbox.com/mapbox-gl-js/)

### Tools
- Claude Code - Terminal-based agentic coding
- Postman - API testing
- SQLite Browser - Database inspection
- Chrome DevTools - Frontend debugging

---

## License

This project is provided as-is for personal use.

---

## Contact

**Developer:** Autumn Brown
**Location:** Smyrna, GA
**Development Environment:** Claude Code

For questions or issues, refer to project documentation or create GitHub issue.

---

**Last Updated:** November 4, 2025
**Version:** 1.0 MVP (In Development - 87.5% Complete)
**Next Milestone:** Phase 8.1 - LLM Natural Language Parsing
