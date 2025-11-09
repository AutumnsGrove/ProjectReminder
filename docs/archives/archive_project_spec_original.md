# Voice-First Reminders System - Project Specification

**Project Name:** ADHD-Friendly Voice Reminders System  
**Developer:** Autumn Brown  
**Location:** Smyrna, GA  
**Version:** 1.0 MVP  
**Last Updated:** November 2, 2025

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Core Philosophy](#core-philosophy)
3. [Architecture](#architecture)
4. [Database Schema](#database-schema)
5. [API Specification](#api-specification)
6. [Frontend Web UI](#frontend-web-ui)
7. [Implementation Phases](#implementation-phases)
8. [Tech Stack](#tech-stack)
9. [Configuration](#configuration)
10. [Future Features](#future-features)
11. [Development Notes](#development-notes)

---

## Project Overview

### Vision
A persistent, offline-first reminders system designed specifically for ADHD workflows. Voice input is the primary interaction method, with visual persistence across multiple devices (desktop, mobile, e-ink displays).

### Problem Statement
Current reminder apps (Apple Reminders, etc.) allow tasks to "lapse" and disappear from view. For ADHD users, out of sight means out of mind. This system provides:
- Persistent visibility (always-on displays)
- Flexible due dates (not just rigid time-based)
- Offline-first operation
- Location-aware reminders
- Natural language voice input

### Key Differentiators
- **Procedurally updating reminders** - tasks resurface frequently until completed
- **Offline-first** - works without internet, syncs when available
- **Multi-device** - desktop, mobile, e-ink dashboard
- **Voice-native** - Siri-like natural language parsing
- **ADHD-optimized** - simple, visible, non-overwhelming

### Target Devices
- Desktop/laptop (primary development environment)
- Android phone (full CRUD client)
- E-ink car dashboard (Boox Palma or similar - read/complete only)
- Future: Bedroom e-ink display, receipt printer integration

---

## Core Philosophy

### Design Principles
1. **Simple > Complex** - Must actually work, not be over-engineered
2. **Visible by Default** - Tasks stay in view until explicitly completed
3. **Offline-First** - Always functional, cloud is backup/sync layer
4. **Vibes > Numbers** - Priority is "chill/important/urgent" not 1-5
5. **Composition over Inheritance** - Functional-OOP hybrid style
6. **No Magic Numbers** - All values in config files

### ADHD-Specific Features
- **Object Permanence Support** - Tasks don't disappear, they persist
- **Context Awareness** - Location-based reminders ("when I'm at Home Depot")
- **Flexible Timing** - "Today" vs "Tuesday at 3pm exactly"
- **Low Friction** - Voice input removes typing barrier
- **Visual Feedback** - Satisfying completion animations
- **No Notification Fatigue** - Persistent display instead of aggressive pings

---

## Architecture

### System Overview

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

### Three-Tier Architecture

#### 1. Cloud Layer (Backup & Multi-Device Sync)
- **Cloudflare Workers** - Serverless API endpoints (TypeScript)
- **Cloudflare D1** - Cloud-hosted SQLite database
- **Purpose:** Multi-device sync, remote access, backup
- **Deployment:** Edge network (low latency globally)

#### 2. Local Layer (Offline-First Primary)
- **FastAPI** - Local Python REST API server
- **SQLite** - Local database file on device
- **Purpose:** Offline operation, LAN access, development
- **Runs on:** localhost:8000 (or custom port)

#### 3. Client Layer (User Interface)
- **Web UI** - Plain HTML/CSS/JS (no frameworks)
- **Connects to:** Either local FastAPI OR cloud Workers
- **Auto-switching:** Tries local first, falls back to cloud
- **Syncs:** Background sync every 5 minutes when online

### Data Flow Patterns

#### Normal Operation (Offline-First)
1. User opens web UI
2. Loads data from local FastAPI/SQLite
3. Displays reminders instantly (no network latency)
4. Background: Attempts cloud sync
5. User makes changes → saved to local DB immediately
6. Queued for cloud sync when online

#### Sync Process
1. Check last sync timestamp
2. Pull remote changes since last sync
3. Push local changes to remote
4. Detect conflicts (same reminder edited both places)
5. Resolve: Last-write-wins (MVP), manual resolution (future)
6. Update sync timestamp

#### Multi-Device Scenario
- Device A updates reminder → syncs to cloud
- Device B pulls sync → receives update
- Local SQLite always authoritative for that device
- Cloud D1 is reconciliation point

---

## Database Schema

### Tables

#### **reminders**
Primary table for all reminder data.

```sql
CREATE TABLE reminders (
    -- Identification
    id TEXT PRIMARY KEY,  -- UUID v4
    
    -- Core Content
    text TEXT NOT NULL,  -- Reminder description
    
    -- Timing
    due_date TEXT,  -- ISO 8601: "2025-11-03" or NULL
    due_time TEXT,  -- ISO 8601: "15:00:00" or NULL
    time_required BOOLEAN DEFAULT FALSE,  -- Must be done at specific time
    
    -- Location
    location_text TEXT,  -- Human-readable: "Home Depot, Smyrna GA"
    location_lat REAL,   -- Latitude (decimal degrees)
    location_lng REAL,   -- Longitude (decimal degrees)
    location_radius INTEGER DEFAULT 100,  -- Trigger radius in meters
    
    -- Organization
    priority TEXT CHECK(priority IN ('chill', 'important', 'urgent')) DEFAULT 'chill',
    category TEXT,  -- Freeform tag
    
    -- Status Tracking
    status TEXT CHECK(status IN ('pending', 'completed', 'snoozed')) DEFAULT 'pending',
    completed_at TEXT,  -- ISO 8601 timestamp
    snoozed_until TEXT,  -- ISO 8601 timestamp
    
    -- Recurrence
    recurrence_id TEXT,  -- Foreign key to recurrence_patterns
    
    -- Metadata
    source TEXT DEFAULT 'manual',  -- 'manual', 'voice', 'api'
    created_at TEXT NOT NULL,  -- ISO 8601 timestamp
    updated_at TEXT NOT NULL,  -- ISO 8601 timestamp
    synced_at TEXT  -- Last successful cloud sync
);

-- Indexes for performance
CREATE INDEX idx_reminders_due_date ON reminders(due_date);
CREATE INDEX idx_reminders_status ON reminders(status);
CREATE INDEX idx_reminders_category ON reminders(category);
CREATE INDEX idx_reminders_priority ON reminders(priority);
CREATE INDEX idx_reminders_location ON reminders(location_lat, location_lng);
```

#### **recurrence_patterns**
Defines recurring reminder patterns (Phase 7 - Iteration 2).

```sql
CREATE TABLE recurrence_patterns (
    -- Identification
    id TEXT PRIMARY KEY,  -- UUID v4
    
    -- Pattern Definition
    frequency TEXT CHECK(frequency IN ('daily', 'weekly', 'monthly', 'yearly')),
    interval INTEGER DEFAULT 1,  -- Every N days/weeks/months/years
    
    -- Constraints
    days_of_week TEXT,  -- JSON array: ["MO", "WE", "FR"] for weekly
    day_of_month INTEGER,  -- 1-31 for monthly
    month_of_year INTEGER,  -- 1-12 for yearly
    
    -- End Conditions
    end_date TEXT,  -- ISO 8601 date or NULL (infinite)
    end_count INTEGER,  -- Stop after N occurrences or NULL
    
    -- Metadata
    created_at TEXT NOT NULL
);
```

### Data Types & Formats

**Dates and Times:**
- All timestamps: ISO 8601 format
- Example date: `2025-11-03`
- Example time: `15:00:00`
- Example datetime: `2025-11-03T15:00:00Z`

**UUIDs:**
- Format: `550e8400-e29b-41d4-a716-446655440000`
- Generated client-side for offline creation

**Location:**
- Latitude/Longitude: Decimal degrees (WGS84)
- Example: `33.8839°N, 84.5144°W` → `(33.8839, -84.5144)`

**Priority Levels:**
- `chill` - Default, low stress (Green #4CAF50)
- `important` - Moderate priority (Yellow #FFC107)
- `urgent` - High priority (Red #F44336)

### Seed Data

**Default Categories:**
```json
[
  "Personal",
  "Work", 
  "Errands",
  "Home",
  "Health",
  "Calls",
  "Shopping",
  "Projects"
]
```

---

## API Specification

### Authentication

**Method:** Bearer Token  
**Header:** `Authorization: Bearer YOUR_SECRET_TOKEN`  
**MVP:** Single static token shared across all clients  
**Future:** Per-device tokens, OAuth2

### Base URLs

- **Local:** `http://localhost:8000/api`
- **Cloud:** `https://reminders-api.YOUR_SUBDOMAIN.workers.dev/api`

### Endpoints

#### **Health Check**

```http
GET /api/health
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2025-11-02T14:30:00Z"
}
```

---

#### **Create Reminder**

```http
POST /api/reminders
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "text": "Call mom about Thanksgiving plans",
  "due_date": "2025-11-03",
  "due_time": "15:00:00",
  "time_required": true,
  "priority": "important",
  "category": "Calls",
  "location_text": "Home"
}
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "text": "Call mom about Thanksgiving plans",
  "due_date": "2025-11-03",
  "due_time": "15:00:00",
  "time_required": true,
  "location_text": "Home",
  "location_lat": null,
  "location_lng": null,
  "location_radius": 100,
  "priority": "important",
  "category": "Calls",
  "status": "pending",
  "completed_at": null,
  "snoozed_until": null,
  "recurrence_id": null,
  "source": "manual",
  "created_at": "2025-11-02T14:30:00Z",
  "updated_at": "2025-11-02T14:30:00Z",
  "synced_at": null
}
```

---

#### **List Reminders**

```http
GET /api/reminders?status=pending&category=Work&limit=50&offset=0
Authorization: Bearer YOUR_TOKEN
```

**Query Parameters:**
- `status` - Filter by status (pending, completed, snoozed)
- `category` - Filter by category tag
- `priority` - Filter by priority level
- `view` - Predefined views (today, upcoming, all)
- `limit` - Number of results (default: 50)
- `offset` - Pagination offset (default: 0)

**Response:** `200 OK`
```json
{
  "reminders": [
    { /* reminder object */ },
    { /* reminder object */ }
  ],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

---

#### **Get Single Reminder**

```http
GET /api/reminders/:id
Authorization: Bearer YOUR_TOKEN
```

**Response:** `200 OK` (single reminder object)

---

#### **Update Reminder**

```http
PATCH /api/reminders/:id
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json
```

**Request Body (partial update):**
```json
{
  "status": "completed",
  "completed_at": "2025-11-02T14:45:00Z"
}
```

**Response:** `200 OK` (updated reminder object)

---

#### **Delete Reminder**

```http
DELETE /api/reminders/:id
Authorization: Bearer YOUR_TOKEN
```

**Response:** `204 No Content`

---

### Smart Views

#### **Today View**

```http
GET /api/reminders/today
Authorization: Bearer YOUR_TOKEN
```

**Logic:**
- Due today (any `due_date` matching today's date)
- Overdue (past `due_date` and still pending)
- No due date but status=pending (floating tasks)

**Sorting:**
1. Priority (urgent → important → chill)
2. Time (if time_required=true)
3. Created date (oldest first)

---

#### **Upcoming View**

```http
GET /api/reminders/upcoming
Authorization: Bearer YOUR_TOKEN
```

**Logic:**
- Due within next 7 days
- Excludes today (use /today for that)

**Sorting:**
1. Due date (ascending)
2. Priority
3. Time

---

#### **Near Location**

```http
GET /api/reminders/near-location?lat=33.8839&lng=-84.5144&radius=5000
Authorization: Bearer YOUR_TOKEN
```

**Query Parameters:**
- `lat` - Current latitude
- `lng` - Current longitude
- `radius` - Search radius in meters (default: 5000)

**Logic:**
- Calculate distance using Haversine formula
- Return reminders within radius
- Include reminders with no location set

---

### Sync Endpoint

```http
POST /api/sync
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "last_sync": "2025-11-02T12:00:00Z",
  "local_changes": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "action": "update",
      "data": {
        "status": "completed",
        "completed_at": "2025-11-02T14:45:00Z",
        "updated_at": "2025-11-02T14:45:00Z"
      }
    },
    {
      "id": "660f9511-f39c-52e5-b827-557766551111",
      "action": "create",
      "data": { /* full reminder object */ }
    },
    {
      "id": "770g0622-g49d-63f6-c938-668877662222",
      "action": "delete"
    }
  ]
}
```

**Response:** `200 OK`
```json
{
  "remote_changes": [
    {
      "id": "880h1733-h59e-74g7-d049-779988773333",
      "action": "update",
      "data": { /* reminder object */ }
    }
  ],
  "conflicts": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "local_updated_at": "2025-11-02T14:45:00Z",
      "remote_updated_at": "2025-11-02T14:50:00Z",
      "resolution": "remote_wins"
    }
  ],
  "sync_timestamp": "2025-11-02T15:00:00Z"
}
```

**Conflict Resolution (MVP):**
- Last-write-wins based on `updated_at` timestamp
- Future: User prompt for manual resolution

---

## Frontend Web UI

### Tech Stack
- **HTML5** - Semantic markup
- **CSS3** - Mobile-first responsive design
- **Vanilla JavaScript** - No frameworks (ES6+)
- **MapBox GL JS** - Location picker and maps
- **Fetch API** - HTTP requests to backend

### File Structure

```
/public/
├── index.html          # Today view
├── upcoming.html       # Upcoming view
├── edit.html          # Create/edit reminder
├── settings.html      # Configuration
├── css/
│   ├── main.css       # Global styles
│   ├── today.css      # Today view specific
│   ├── upcoming.css   # Upcoming view specific
│   └── edit.css       # Form styles
├── js/
│   ├── app.js         # Main app logic
│   ├── api.js         # API client wrapper
│   ├── sync.js        # Sync logic
│   ├── storage.js     # LocalStorage helpers
│   ├── location.js    # Geolocation/MapBox
│   └── animations.js  # UI animations
└── assets/
    ├── icons/         # SVG icons
    └── sounds/        # Completion sound effects (optional)
```

---

### Pages

#### **1. Today View** (`index.html`)

**Layout:**
```
┌─────────────────────────────────┐
│  Today - Saturday, Nov 2        │
│  [Online ✓]            [+ Add]  │
├─────────────────────────────────┤
│                                 │
│  ⬜ Call mom about Thanks...   │
│     📍 Home  🕒 3:00pm          │
│     [important]                 │
│                                 │
│  ⬜ Buy groceries               │
│     📍 Kroger                   │
│     [chill]                     │
│                                 │
│  ⬜ Submit expense report       │
│     [urgent]                    │
│                                 │
├─────────────────────────────────┤
│  Overdue (2)                    │
│                                 │
│  ⬜ Fix car headlight           │
│     Due: Oct 30                 │
│     [important]                 │
│                                 │
└─────────────────────────────────┘
```

**Features:**
- Header shows current date
- Online/offline status indicator
- Floating "+" button (bottom-right)
- Reminders grouped: "Today" and "Overdue"
- Each reminder shows:
  - Checkbox (tap to complete)
  - Text (truncated if long)
  - Location icon + text (if set)
  - Time (if time_required=true)
  - Priority badge (color-coded)
- Tap reminder text → edit page
- Swipe left → delete (with confirmation)

**Priority Colors:**
- Chill: `#4CAF50` (Green)
- Important: `#FFC107` (Yellow/Orange)
- Urgent: `#F44336` (Red)

**Completion Animation:**
1. Checkbox animates to checkmark
2. Item fades out (500ms)
3. Item slides up and removed from DOM
4. Optional: Confetti/celebration for urgent tasks

---

#### **2. Upcoming View** (`upcoming.html`)

**Layout:**
```
┌─────────────────────────────────┐
│  Upcoming                       │
│  [< Back]              [+ Add]  │
├─────────────────────────────────┤
│                                 │
│  Tomorrow (3)                   │
│  ⬜ Team meeting 9am            │
│  ⬜ Dentist appointment 2pm     │
│  ⬜ Water plants                │
│                                 │
│  Monday, Nov 4 (1)              │
│  ⬜ Submit timesheet            │
│                                 │
│  This Week (5)                  │
│  ⬜ ...                         │
│                                 │
│  Later (8)                      │
│  ⬜ ...                         │
│                                 │
└─────────────────────────────────┘
```

**Features:**
- Grouped by relative dates
- Same reminder display as Today view
- Collapsible sections (future)

---

#### **3. Create/Edit Reminder** (`edit.html`)

**Layout:**
```
┌─────────────────────────────────┐
│  New Reminder                   │
│  [< Cancel]            [Save]   │
├─────────────────────────────────┤
│                                 │
│  What needs to be done?         │
│  ┌─────────────────────────┐   │
│  │ Call mom about Thanks...│ 🎤│
│  └─────────────────────────┘   │
│                                 │
│  When?                          │
│  [Date: Nov 3, 2025 ▼]          │
│  [Time: 3:00 PM ▼]              │
│  ☑ Time required                │
│                                 │
│  Priority                       │
│  ( ) Chill  (•) Important  ( ) Urgent │
│                                 │
│  Category                       │
│  [Calls ▼] (or type new)        │
│                                 │
│  Location (optional)            │
│  ┌─────────────────────────┐   │
│  │ Home Depot, Smyrna GA   │   │
│  └─────────────────────────┘   │
│  [Map visualization]            │
│                                 │
│  [Delete Reminder]              │
│                                 │
└─────────────────────────────────┘
```

**Features:**
- Text field with voice button (🎤 - shows "Coming Soon!" toast)
- Date picker (optional)
- Time picker (optional, with "time required" checkbox)
- Priority selector (radio buttons with visual preview)
- Category dropdown (presets + freeform input)
- Location field + MapBox picker
  - Text input triggers geocoding
  - Map shows selected location
  - Drag pin to adjust
- Save validates required fields
- Delete button (edit mode only)

---

#### **4. Settings** (`settings.html`)

**Layout:**
```
┌─────────────────────────────────┐
│  Settings                       │
│  [< Back]                       │
├─────────────────────────────────┤
│                                 │
│  API Configuration              │
│  (•) Local Server               │
│  ( ) Cloud (Cloudflare)         │
│                                 │
│  API Endpoint                   │
│  ┌─────────────────────────┐   │
│  │ http://localhost:8000   │   │
│  └─────────────────────────┘   │
│                                 │
│  Auth Token                     │
│  ┌─────────────────────────┐   │
│  │ your-secret-token       │   │
│  └─────────────────────────┘   │
│                                 │
│  MapBox Token                   │
│  ┌─────────────────────────┐   │
│  │ pk.ey...                │   │
│  └─────────────────────────┘   │
│                                 │
│  Sync                           │
│  Last synced: 2 minutes ago     │
│  [Sync Now]                     │
│                                 │
│  Data                           │
│  [Clear Local Data]             │
│  [Export Data (JSON)]           │
│  [Import Data]                  │
│                                 │
│  About                          │
│  Version: 1.0.0                 │
│  Local DB: 47 reminders         │
│                                 │
└─────────────────────────────────┘
```

**Features:**
- API endpoint selector (local/cloud toggle)
- Token configuration
- Manual sync trigger
- Sync status indicator
- Data management (clear, export, import)
- System information

---

### JavaScript Architecture

#### **app.js** - Main Application Logic
```javascript
class ReminderApp {
  constructor() {
    this.api = new APIClient();
    this.syncManager = new SyncManager(this.api);
    this.init();
  }

  async init() {
    await this.loadConfig();
    await this.loadReminders();
    this.setupEventListeners();
    this.startSyncLoop();
  }

  async loadReminders() {
    const view = this.getCurrentView(); // 'today', 'upcoming'
    const reminders = await this.api.getReminders(view);
    this.renderReminders(reminders);
  }

  async completeReminder(id) {
    await this.api.completeReminder(id);
    this.animateCompletion(id);
    await this.loadReminders();
  }
}
```

#### **api.js** - API Client Wrapper
```javascript
class APIClient {
  constructor() {
    this.baseURL = this.getAPIEndpoint();
    this.token = this.getAuthToken();
  }

  async getReminders(view = 'today') {
    const response = await fetch(`${this.baseURL}/api/reminders/${view}`, {
      headers: {
        'Authorization': `Bearer ${this.token}`
      }
    });
    return response.json();
  }

  async createReminder(data) {
    const response = await fetch(`${this.baseURL}/api/reminders`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    return response.json();
  }

  async completeReminder(id) {
    return this.updateReminder(id, {
      status: 'completed',
      completed_at: new Date().toISOString()
    });
  }
}
```

#### **sync.js** - Background Sync Logic
```javascript
class SyncManager {
  constructor(apiClient) {
    this.api = apiClient;
    this.syncInterval = 5 * 60 * 1000; // 5 minutes
    this.lastSync = this.getLastSyncTimestamp();
  }

  startSyncLoop() {
    this.syncNow();
    setInterval(() => this.syncNow(), this.syncInterval);
  }

  async syncNow() {
    if (!navigator.onLine) {
      this.updateSyncStatus('offline');
      return;
    }

    try {
      this.updateSyncStatus('syncing');
      const localChanges = this.getLocalChanges();
      const result = await this.api.sync(this.lastSync, localChanges);
      this.applyRemoteChanges(result.remote_changes);
      this.resolveConflicts(result.conflicts);
      this.lastSync = result.sync_timestamp;
      this.updateSyncStatus('online');
    } catch (error) {
      this.updateSyncStatus('error');
      console.error('Sync failed:', error);
    }
  }
}
```

---

### Mobile Responsiveness

**Breakpoints:**
- Mobile: < 768px (default design)
- Tablet: 768px - 1024px
- Desktop: > 1024px

**Mobile-First Design:**
- Touch-friendly tap targets (min 44x44px)
- Large text for readability
- Swipe gestures for actions
- Bottom navigation for thumb reach
- Pull-to-refresh on Today/Upcoming views

---

## Implementation Phases

### **Phase 1: Core Backend (Day 1)** ✅
**Goal:** Working local API with database

**Tasks:**
1. Setup FastAPI project structure
2. Create SQLite database with schema
3. Implement CRUD endpoints
4. Add bearer token authentication
5. Seed default categories
6. Test with curl/Postman

**Deliverables:**
- `server/` directory with FastAPI code
- `reminders.db` SQLite database
- API running on `localhost:8000`
- Swagger docs at `/docs`

**Success Criteria:**
- Can create/read/update/delete reminders via API
- Authentication works
- Database persists data

---

### **Phase 2: Web UI (Day 1-2)** ✅
**Goal:** Functional frontend (no backend connection yet)

**Tasks:**
1. Create HTML pages (index, upcoming, edit, settings)
2. Write CSS (mobile-first, priority colors)
3. Build JavaScript app structure
4. Implement Today view with mock data
5. Implement Upcoming view
6. Create reminder form with validation
7. Add completion animations

**Deliverables:**
- `public/` directory with all files
- Working UI with hardcoded sample data
- Responsive design tested on mobile

**Success Criteria:**
- UI looks good on mobile and desktop
- Animations work smoothly
- Forms validate input

---

### **Phase 3: Integration (Day 2)** ✅
**Goal:** Connect UI to local API

**Tasks:**
1. Implement API client in `api.js`
2. Connect Today view to `/api/reminders/today`
3. Connect Upcoming view to `/api/reminders/upcoming`
4. Wire up create/edit form to POST/PATCH endpoints
5. Implement delete functionality
6. Add settings page for API config
7. Handle API errors gracefully

**Deliverables:**
- Fully functional local system
- UI loads real data from API
- CRUD operations work end-to-end

**Success Criteria:**
- Can create reminders in UI → saved to DB
- Can complete reminders → updates DB
- Can edit and delete reminders
- Settings page configures API endpoint

---

### **Phase 4: Cloudflare Workers (Day 2-3)** ✅
**Goal:** Cloud API deployment

**Tasks:**
1. Setup Cloudflare account and D1 database
2. Write Workers API in TypeScript
3. Implement same endpoints as FastAPI
4. Add CORS headers for web UI
5. Deploy to Cloudflare
6. Test cloud API independently

**Deliverables:**
- `workers/` directory with TypeScript code
- `wrangler.toml` configuration
- Deployed API at `*.workers.dev`
- D1 database configured

**Success Criteria:**
- Cloud API responds to requests
- Can switch UI to cloud endpoint
- Data persists in D1

---

### **Phase 5: Sync Logic (Day 3)** ✅
**Goal:** Offline-first with cloud backup

**Tasks:**
1. Implement `/api/sync` endpoint (both APIs)
2. Track local changes in UI
3. Build sync manager in `sync.js`
4. Implement conflict detection
5. Add last-write-wins resolution
6. Background sync every 5 minutes
7. Manual sync button in settings

**Deliverables:**
- Bidirectional sync working
- Sync status indicator in UI
- Conflict resolution (basic)

**Success Criteria:**
- Can work offline → changes saved locally
- When online → changes sync to cloud
- Other devices receive updates
- No data loss during sync

---

### **Phase 6: Location Features (Day 3-4)** ✅
**Goal:** Location-based reminders

**Tasks:**
1. Add MapBox GL JS to project
2. Create location picker component
3. Implement geocoding (address → lat/lng)
4. Add `/api/reminders/near-location` endpoint
5. Geolocation API integration
6. Display location reminders on map
7. "Errands while out" smart view

**Deliverables:**
- MapBox integration working
- Location picker in edit form
- Near-location endpoint
- Map view showing reminder locations (optional)

**Success Criteria:**
- Can set reminder location via text or map
- Can query reminders near current location
- Location-based filtering works

---

### **Phase 7: Recurring Reminders (Iteration 2)** 🔄
**Goal:** Handle repeating tasks

**Tasks:**
1. Implement `recurrence_patterns` table
2. Create recurrence UI in edit form
3. Build recurrence instance generator
4. Handle "this instance" vs "series" edits
5. Add recurrence display in reminder list
6. Test complex patterns (weekdays, monthly, etc.)

**Deliverables:**
- Recurrence patterns supported
- UI for creating/editing patterns
- Instances generated automatically

**Success Criteria:**
- Can create "every Tuesday" reminder
- Can edit/delete single instance or series
- Recurrence displayed correctly

---

### **Phase 8: Voice Input (Iteration 2)** 🔄
**Goal:** Local STT and NLP parsing

**Tasks:**
1. Research and select local STT model
2. Integrate STT (Whisper.cpp/Vosk)
3. Research and select small LLM
4. Implement NLP parsing pipeline
5. Add voice button functionality
6. Display transcription before saving
7. Handle parsing errors gracefully

**Deliverables:**
- Voice button activates recording
- Local STT transcribes audio
- LLM parses into structured data
- Fallback to manual edit if parse fails

**Success Criteria:**
- "Remind me to call mom tomorrow at 3pm" → correct reminder
- Runs locally (privacy preserved)
- Fast enough (<5 seconds end-to-end)

---

### **Future Phases**

**Phase 9: E-ink Clients**
- Android app for car dashboard
- Read-only view with tap-to-complete
- Refresh on wake/interval
- Low-power e-ink optimizations

**Phase 10: Smart Features**
- Auto-categorization (LLM)
- Priority suggestions
- Duplicate detection
- Reminder templates

**Phase 11: Receipt Printer**
- Print daily task list on thermal paper
- Integration with printer API
- Scheduled morning prints

---

## Tech Stack

### Backend

| Component | Technology | Purpose |
|-----------|------------|---------|
| Local API | FastAPI (Python 3.11+) | REST API server |
| Local DB | SQLite 3 | Local data storage |
| Cloud API | Cloudflare Workers | Serverless edge API |
| Cloud DB | Cloudflare D1 | Cloud SQLite |
| Validation | Pydantic (FastAPI) | Request validation |
| Auth | Bearer Token | Simple auth (MVP) |

### Frontend

| Component | Technology | Purpose |
|-----------|------------|---------|
| UI | HTML5 + CSS3 + Vanilla JS | No framework overhead |
| Maps | MapBox GL JS | Location picker |
| Icons | SVG | Scalable icons |
| Storage | LocalStorage | Settings/config |
| Requests | Fetch API | HTTP client |

### Future Additions

| Component | Technology | Purpose |
|-----------|------------|---------|
| Voice STT | Whisper.cpp / Vosk | Local speech-to-text |
| NLP | Llama 3.2 1B / Phi-3 Mini | Intent parsing |
| Mobile | React Native / Native Android | Phone app |
| E-ink | Android app | Car dashboard |

---

## Configuration

### **Frontend Config** (`config.json`)

```json
{
  "api": {
    "local_endpoint": "http://localhost:8000",
    "cloud_endpoint": "https://reminders-api.YOUR_SUBDOMAIN.workers.dev",
    "active": "local",
    "token": "your-secret-token-here"
  },
  "sync": {
    "interval_ms": 300000,
    "auto_sync": true,
    "conflict_resolution": "last_write_wins"
  },
  "mapbox": {
    "access_token": "pk.eyJ1IjoieW91cnVzZXIiLCJhIjoiY2x6..."
  },
  "ui": {
    "theme": "light",
    "animations": true,
    "sound_effects": false
  },
  "location": {
    "default_radius": 100,
    "auto_detect": true
  }
}
```

### **FastAPI Config** (`config.py`)

```python
import os
from pathlib import Path

# Database
DB_PATH = Path(__file__).parent / "reminders.db"

# Authentication
API_TOKEN = os.getenv("API_TOKEN", "your-secret-token-here")

# CORS
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "*"  # Remove in production
]

# Server
HOST = "0.0.0.0"
PORT = 8000
DEBUG = True

# Sync
SYNC_BATCH_SIZE = 100
```

### **Cloudflare Workers Config** (`wrangler.toml`)

```toml
name = "reminders-api"
main = "src/index.ts"
compatibility_date = "2025-01-01"

[env.production]
vars = { ENVIRONMENT = "production" }

[[d1_databases]]
binding = "DB"
database_name = "reminders"
database_id = "your-database-id-here"

[build]
command = "npm run build"

[observability]
enabled = true
```

---

## Future Features

### Iteration 2 (Post-MVP)

**Voice Input:**
- Local STT model (Whisper.cpp)
- Natural language parsing
- "Remind me to..." voice commands
- Confirmation before saving

**Smart Features:**
- Auto-categorization via LLM
- Priority suggestion based on keywords
- Duplicate detection
- Reminder templates

**Enhanced Recurrence:**
- Complex patterns (1st Monday, last Friday)
- Skip holidays
- Adjust for weekends

### Iteration 3 (Advanced)

**Multi-Device:**
- Native Android app
- E-ink dashboard client
- Wear OS integration

**Integrations:**
- Calendar sync (Google Calendar)
- Email parsing (create reminders from emails)
- Receipt printer output

**Analytics:**
- Completion rate tracking
- Productivity insights
- Time-of-day patterns

**Social:**
- Shared lists (family shopping list)
- Delegate reminders
- Collaboration features

---

## Development Notes

### Coding Style Preferences
- **Functional-OOP Hybrid:** Composition over inheritance
- **Small Functions:** Single responsibility principle
- **Data Transformation:** Prefer map/filter over loops
- **No Magic Numbers:** Use config files
- **Clear Naming:** Self-documenting code

### Git Strategy
- `main` - Production-ready code
- `dev` - Active development
- Feature branches: `feature/voice-input`
- Commit messages: Conventional Commits format

### Testing Strategy (Future)
- Unit tests for API endpoints
- Integration tests for sync logic
- E2E tests for critical flows
- Manual testing on real devices

### Performance Targets
- API response time: <100ms (local), <500ms (cloud)
- UI load time: <1s
- Sync time: <5s for 100 reminders
- STT latency: <3s (future)
- LLM parsing: <2s (future)

---

## Success Metrics

### MVP Success Criteria
✅ Can create reminders quickly (<10 seconds)  
✅ Works offline without degradation  
✅ Syncs reliably when online  
✅ Persistent visibility prevents task loss  
✅ Location reminders trigger appropriately  
✅ Priority system is intuitive  
✅ Mobile-friendly on phone  

### Long-Term Goals
- Daily active usage for 30+ days
- >80% completion rate on created reminders
- Voice input used for >50% of new reminders
- Multi-device sync working seamlessly
- Zero data loss incidents
- Measurable reduction in forgotten tasks

---

## Resources

### Documentation
- FastAPI: https://fastapi.tiangolo.com/
- Cloudflare Workers: https://developers.cloudflare.com/workers/
- Cloudflare D1: https://developers.cloudflare.com/d1/
- MapBox GL JS: https://docs.mapbox.com/mapbox-gl-js/

### Tools
- Claude Code: Terminal-based agentic coding
- Postman: API testing
- SQLite Browser: Database inspection
- Chrome DevTools: Frontend debugging

### Research Prompts
- See separate document for STT and LLM research prompts

---

## Contact & Support

**Developer:** Autumn Brown  
**Location:** Smyrna, GA  
**Development Environment:** Claude Code  

For questions or issues, refer to project documentation or create GitHub issue.

---

**Document Version:** 1.0  
**Last Updated:** November 2, 2025  
**Next Review:** After Phase 3 completion
