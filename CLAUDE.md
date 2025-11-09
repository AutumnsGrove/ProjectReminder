# Project Instructions - Claude Code

> **Note**: This is the main orchestrator file. For detailed guides, see `ClaudeUsage/README.md`

---

## Project Purpose
An ADHD-friendly, offline-first reminders system with voice input as the primary interaction method. Tasks persist visibly until explicitly completed, preventing "out of sight, out of mind" task loss common with traditional reminder apps.

## Tech Stack
- **Language**: Python 3.11+ (backend), TypeScript (cloud), Vanilla JavaScript (frontend)
- **Backend Framework**: FastAPI (local API server)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript (no frameworks)
- **Local Database**: SQLite 3
- **Cloud**: Cloudflare Workers + D1 (serverless edge API + cloud SQLite)
- **Maps**: MapBox GL JS (location-based reminders)
- **Package Manager**: UV (Python), npm (TypeScript/JavaScript)
- **NLP Parsing**: Local: Llama 3.2 1B (via LM Studio), Remote: GPT-OSS 20B (Cloudflare Workers AI)
- **Future**: Whisper.cpp (local STT)

## Architecture Notes
**Three-tier offline-first architecture:**
1. **Cloud Layer** - Cloudflare Workers + D1 for multi-device sync and backup
2. **Local Layer** - FastAPI + SQLite for offline-first primary operation (localhost:8000)
3. **Client Layer** - Plain HTML/CSS/JS web UI (auto-switches local → cloud fallback)

**Key Patterns:**
- Offline-first: Local SQLite is always authoritative for device, cloud is reconciliation point
- Bidirectional sync: Background sync every 5 minutes when online
- Conflict resolution: Last-write-wins (MVP), manual resolution (future)
- UUID generation: Client-side for offline creation
- Priority system: "chill/important/urgent" not numeric scales
- Functional-OOP hybrid: Composition over inheritance, small focused functions

**ADHD-Optimized Design:**
- Persistent visibility: Tasks don't disappear until completed
- Low friction: Voice input removes typing barrier
- Context-aware: Location-based reminders ("when I'm at Home Depot")
- Flexible timing: "Today" vs "Tuesday at 3pm exactly"
- No notification fatigue: Persistent display instead of aggressive pings

---

## Essential Instructions (Always Follow)

### Core Behavior
- Do what has been asked; nothing more, nothing less
- NEVER create files unless absolutely necessary for achieving your goal
- ALWAYS prefer editing existing files to creating new ones
- NEVER proactively create documentation files (*.md) or README files unless explicitly requested

### Naming Conventions
- **Directories**: Use CamelCase (e.g., `VideoProcessor`, `AudioTools`, `DataAnalysis`)
- **Date-based paths**: Use skewer-case with YYYY-MM-DD (e.g., `logs-2025-01-15`, `backup-2025-12-31`)
- **No spaces or underscores** in directory names (except date-based paths)

### TODO Management
- **Always check `TODOS.md` first** when starting a task or session
- **Update immediately** when tasks are completed, added, or changed
- Keep the list current and manageable

### Git Workflow Essentials

**After completing major changes, you MUST commit your work.**

**Conventional Commits Format:**
```bash
<type>: <brief description>

<optional body>

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Common Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`

**Examples:**
```bash
feat: Add user authentication
fix: Correct timezone bug
docs: Update README
```

**For complete details:** See `ClaudeUsage/git_guide.md`

---

## When to Read Specific Guides

**Read the full guide in `ClaudeUsage/` when you encounter these situations:**

### Secrets & API Keys
- **When managing API keys or secrets** → Read `ClaudeUsage/secrets_management.md`
- **Before implementing secrets loading** → Read `ClaudeUsage/secrets_management.md`

### Package Management
- **When using UV package manager** → Read `ClaudeUsage/uv_usage.md`
- **Before creating pyproject.toml** → Read `ClaudeUsage/uv_usage.md`
- **When managing Python dependencies** → Read `ClaudeUsage/uv_usage.md`

### Version Control
- **Before making a git commit** → Read `ClaudeUsage/git_guide.md`
- **When initializing a new repo** → Read `ClaudeUsage/git_guide.md`
- **For git workflow and branching** → Read `ClaudeUsage/git_guide.md`
- **For conventional commits reference** → Read `ClaudeUsage/git_guide.md`

### Database Management
- **When working with databases** → Read `ClaudeUsage/db_usage.md`
- **Before implementing data persistence** → Read `ClaudeUsage/db_usage.md`
- **For database.py template** → Read `ClaudeUsage/db_usage.md`

### Search & Research
- **When searching across 20+ files** → Read `ClaudeUsage/house_agents.md`
- **When finding patterns in codebase** → Read `ClaudeUsage/house_agents.md`
- **When locating TODOs/FIXMEs** → Read `ClaudeUsage/house_agents.md`

### Testing
- **Before writing tests** → Read `ClaudeUsage/testing_strategies.md`
- **When implementing test coverage** → Read `ClaudeUsage/testing_strategies.md`
- **For test organization** → Read `ClaudeUsage/testing_strategies.md`


### Code Quality
- **When refactoring code** → Read `ClaudeUsage/code_style_guide.md`
- **Before major code changes** → Read `ClaudeUsage/code_style_guide.md`
- **For style guidelines** → Read `ClaudeUsage/code_style_guide.md`

### Project Setup
- **When starting a new project** → Read `ClaudeUsage/project_setup.md`
- **For directory structure** → Read `ClaudeUsage/project_setup.md`
- **Setting up CI/CD** → Read `ClaudeUsage/project_setup.md`

---

## Quick Reference

### Security Basics
- Store API keys in `secrets.json` (NEVER commit)
- Add `secrets.json` to `.gitignore` immediately
- Provide `secrets_template.json` for setup
- Use environment variables as fallbacks

### API Keys Required
This project requires the following API keys:
- **MapBox Access Token** - For location picker and geocoding (get at: https://account.mapbox.com/)
- **API_TOKEN** - Self-generated bearer token for API authentication (use strong random string)
- **Cloudflare Account** - For Workers and D1 deployment (Phase 4+)

Store these in `secrets.json`:
```json
{
  "mapbox_access_token": "pk.eyJ1...",
  "api_token": "your-strong-random-token-here",
  "comment": "Never commit this file. Cloudflare tokens managed via wrangler CLI."
}
```

### House Agents Quick Trigger
**When searching 20+ files**, use house-research for:
- Finding patterns across codebase
- Searching TODO/FIXME comments
- Locating API endpoints or functions
- Documentation searches

---

## Code Style Guidelines

### Function & Variable Naming
- Use meaningful, descriptive names
- Keep functions small and focused on single responsibilities
- Add docstrings to functions and classes

### Error Handling
- Use try/except blocks gracefully
- Provide helpful error messages
- Never let errors fail silently

### File Organization
- Group related functionality into modules
- Use consistent import ordering:
  1. Standard library
  2. Third-party packages
  3. Local imports
- Keep configuration separate from logic

---

## Communication Style
- Be concise but thorough
- Explain reasoning for significant decisions
- Ask for clarification when requirements are ambiguous
- Proactively suggest improvements when appropriate

---

## Complete Guide Index
For all detailed guides, workflows, and examples, see:
**`ClaudeUsage/README.md`** - Master index of all documentation

---

*Last updated: 2025-11-02*
*Model: Claude Sonnet 4.5*
*Project: ADHD-Friendly Voice Reminders System*
