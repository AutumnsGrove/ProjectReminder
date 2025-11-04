# Contributing to ADHD-Friendly Voice Reminders System

Thank you for your interest in contributing! This is a personal project, but suggestions and improvements are welcome.

## Project Overview

This is an offline-first, voice-native reminders system designed specifically for ADHD workflows. The core philosophy is **persistent visibility** - tasks don't disappear until explicitly completed, preventing "out of sight, out of mind" task loss.

**Current Status:** Phase 8 Complete (87.5% to MVP) - Voice transcription with Whisper.cpp

## Getting Started

### Prerequisites

- **Python 3.11+** - Backend development
- **Node.js 18+** - Cloudflare Workers development
- **UV Package Manager** - Python dependency management (`pip install uv`)
- **MapBox Account** - Free tier for location features
- **Git** - Version control

### Setup Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AutumnsGrove/ProjectReminder.git
   cd ProjectReminder
   ```

2. **Set up Python environment:**
   ```bash
   uv sync
   ```

3. **Configure secrets:**
   ```bash
   cp secrets_template.json secrets.json
   # Edit secrets.json with your MapBox token and generate a strong API token
   ```

4. **Initialize database:**
   ```bash
   python server/database.py
   ```

5. **Start local API server:**
   ```bash
   uv run uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Open web UI:**
   ```bash
   # Option 1: Open directly
   open public/index.html

   # Option 2: Serve with Python
   python serve_ui.py
   ```

## Development Guidelines

### Code Style

This project follows specific coding patterns documented in `ClaudeUsage/`. Key guidelines:

1. **Database Operations** - All SQL isolated in `server/database.py`
2. **Pydantic Models** - API contracts in `server/models.py`
3. **Modular Frontend** - Separate JS modules (api.js, sync.js, storage.js, etc.)
4. **Mobile-First CSS** - Responsive design with CSS variables
5. **Conventional Commits** - See Git Workflow section below

**Reference:** See `ClaudeUsage/code_style_guide.md` for complete guidelines.

### Project Structure

```
ProjectReminder/
├── server/              # FastAPI backend (Python)
│   ├── main.py         # API endpoints
│   ├── database.py     # SQLite operations
│   ├── models.py       # Pydantic models
│   └── voice/          # Voice transcription (Whisper.cpp)
├── workers/            # Cloudflare Workers (TypeScript)
│   └── src/index.ts    # Edge API
├── public/             # Frontend (HTML/CSS/JS)
│   ├── *.html          # Views (index, upcoming, edit)
│   ├── css/            # Stylesheets
│   └── js/             # JavaScript modules
├── tests/              # Pytest test suite
└── ClaudeUsage/        # Development guides
```

### Making Changes

1. **Check current tasks:**
   ```bash
   cat TODOS.md
   ```

2. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes:**
   - Write clear, focused code
   - Follow existing patterns
   - Add docstrings to functions
   - Handle errors gracefully

4. **Test your changes:**
   ```bash
   # Run test suite
   pytest

   # Manual testing
   # - Test in browser
   # - Test offline functionality
   # - Test on mobile viewport
   ```

5. **Update documentation:**
   - Update `TODOS.md` if addressing tracked tasks
   - Add comments for complex logic
   - Update README if changing setup/usage

6. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: your descriptive commit message"
   ```

## Git Workflow

### Conventional Commits

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <brief description>

<optional body>

🤖 Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
```

**Common Types:**
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `refactor:` - Code restructuring
- `test:` - Testing additions/changes
- `chore:` - Maintenance tasks
- `perf:` - Performance improvements

**Examples:**
```bash
feat: Add location-based reminder filtering
fix: Correct timezone handling in due dates
docs: Update API documentation for voice endpoints
refactor: Extract sync logic to separate module
test: Add integration tests for recurring reminders
chore: Update dependencies to latest versions
```

**Reference:** See `ClaudeUsage/git_guide.md` for complete workflow.

### Branching Strategy

- `main` - Production-ready code
- `feature/*` - New features
- `fix/*` - Bug fixes
- `docs/*` - Documentation updates

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=server --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::test_create_reminder
```

### Writing Tests

- Place tests in `tests/` directory
- Use pytest fixtures (see `tests/conftest.py`)
- Test both success and error cases
- Aim for >80% code coverage

**Reference:** See `ClaudeUsage/testing_strategies.md` for patterns.

## API Key Management

**IMPORTANT:** Never commit API keys or secrets!

- All keys stored in `secrets.json` (gitignored)
- Template provided in `secrets_template.json`
- Use environment variables as fallbacks
- See `ClaudeUsage/secrets_management.md` for details

## Architecture Decisions

### Why Offline-First?

ADHD brains need **persistent visibility**. If reminders disappear when offline, they're forgotten. Local-first architecture ensures tasks are always visible, with cloud sync as enhancement.

### Why Voice Input?

Typing is a barrier. Voice removes friction, making it easier to capture thoughts before they're lost.

### Why SQLite?

Simple, fast, portable, and perfect for offline-first architecture. Cloud D1 provides same interface for sync.

### Why Vanilla JS?

No framework overhead, faster load times, easier debugging. Mobile performance is critical.

## Submitting Changes

### Pull Request Process

1. **Update your branch:**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Run tests:**
   ```bash
   pytest
   ```

3. **Push to GitHub:**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create Pull Request:**
   - Describe what changed and why
   - Reference any related issues
   - Include testing steps
   - Add screenshots for UI changes

5. **Wait for review:**
   - Address any feedback
   - Keep commits focused and atomic

## Questions or Issues?

- **Check Documentation:** `ClaudeUsage/README.md` has comprehensive guides
- **Review TODOS:** `TODOS.md` tracks current tasks and progress
- **Create GitHub Issue:** For bugs or feature requests
- **Read Project Spec:** `reminders-project-spec.md` has complete technical details

## Contact

**Developer:** Autumn Brown
**Location:** Smyrna, GA
**GitHub:** https://github.com/AutumnsGrove/ProjectReminder

---

## Code of Conduct

Be respectful, constructive, and kind. This is a learning project focused on solving real ADHD challenges.

---

**Thank you for contributing!** 🎉

*Last Updated: November 4, 2025*
