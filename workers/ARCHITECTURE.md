# Cloudflare Workers Architecture - Technical Research

**Phase**: 4.0 - Cloud API Deployment
**Date**: 2025-11-02
**Purpose**: Document Cloudflare Workers + D1 architecture patterns for implementing the cloud sync API

---

## Executive Summary

This document outlines the technical architecture for deploying the ADHD-Friendly Reminders API on Cloudflare Workers with D1 database. The cloud API will replicate the local FastAPI endpoints, enabling multi-device sync and providing a fallback when the local server is unavailable.

**Key Technologies:**
- **Cloudflare Workers**: Serverless edge runtime (V8 isolates)
- **D1 Database**: Cloudflare's serverless SQLite
- **TypeScript**: Primary language for Workers
- **Hono**: Lightweight web framework for routing (~14KB)

---

## 1. Workers Runtime Environment

### 1.1 Runtime Architecture

**Key Differences from Node.js:**

| Aspect | Node.js | Cloudflare Workers |
|--------|---------|-------------------|
| Execution Model | Process-based (containers/VMs) | V8 isolates |
| Startup Time | ~100ms+ | <1ms (100x faster) |
| Memory Isolation | Process boundaries | V8 isolate boundaries |
| File System | Full access | **NO file system access** |
| Environment Variables | `process.env.VAR` | Direct globals (or `env.VAR` via bindings) |
| Module System | CommonJS + ES Modules | ES Modules only |

**Critical Limitations:**
- ❌ **No file system** - Cannot use `fs`, `path`, or read/write files
- ❌ **No `process` object** - Use `nodejs_compat` flag to enable `process.env`
- ❌ **No native Node.js modules** - Limited subset available under `node:` prefix
- ✅ **Web APIs only** - Fetch, Request, Response, crypto, URL, etc.

### 1.2 Available APIs

**Native Workers APIs:**
```typescript
// ✅ Available
crypto.randomUUID()                    // UUID generation
crypto.subtle                          // Cryptography
new Date().toISOString()              // ISO timestamps
fetch()                               // HTTP requests
Request / Response                    // Web standard APIs
URL / URLSearchParams                 // URL handling

// ❌ NOT Available (without polyfills)
fs.readFile()                         // No filesystem
process.env                           // Use env bindings instead
require()                             // ES modules only
```

### 1.3 TypeScript Support

**First-Class TypeScript:**
- All Workers APIs are fully typed
- Types generated from `workerd` (open-source runtime)
- Use `wrangler types` to generate types based on compatibility date

**Project Setup:**
```bash
npm init -y
npm install -D wrangler typescript @cloudflare/workers-types
npx wrangler types
```

---

## 2. D1 Database (Cloudflare's SQLite)

### 2.1 Overview

**D1 = Serverless SQLite at the Edge**
- Built on SQLite's query engine
- Managed backups and disaster recovery
- Accessible via Workers Binding API and REST API
- Supports most SQLite SQL conventions

### 2.2 Query API Patterns

**Workers Binding API (Primary Interface):**

```typescript
// 1. Bind database in wrangler.toml
// [[d1_databases]]
// binding = "DB"
// database_name = "reminders-db"
// database_id = "abc123..."

// 2. Access via env binding
export default {
  async fetch(request: Request, env: Env) {
    // Prepare statement (parameterized queries)
    const stmt = env.DB.prepare(
      "SELECT * FROM reminders WHERE id = ?"
    ).bind(reminderId);

    // Execute query
    const result = await stmt.first();  // Single row
    const results = await stmt.all();   // All rows
    await stmt.run();                   // Execute (INSERT/UPDATE/DELETE)

    return new Response(JSON.stringify(result));
  }
};
```

**Query Methods:**

| Method | Use Case | Returns |
|--------|----------|---------|
| `.first()` | Get single row | `{ id: "...", text: "..." }` or `null` |
| `.all()` | Get all rows | `{ results: [...], success: true, meta: {...} }` |
| `.run()` | INSERT/UPDATE/DELETE | `{ success: true, meta: { changes: 1 } }` |
| `.batch([])` | Multiple statements (transaction) | Array of results |

**Example: Create Reminder**
```typescript
const result = await env.DB.prepare(`
  INSERT INTO reminders (id, text, created_at, updated_at)
  VALUES (?, ?, ?, ?)
`).bind(id, text, timestamp, timestamp).run();

// Check success
if (!result.success) {
  throw new Error("Failed to create reminder");
}
```

### 2.3 Batch Operations (Transactions)

**All-or-nothing transactions:**
```typescript
const results = await env.DB.batch([
  env.DB.prepare("INSERT INTO reminders VALUES (?, ?)").bind(id1, text1),
  env.DB.prepare("INSERT INTO reminders VALUES (?, ?)").bind(id2, text2),
  env.DB.prepare("UPDATE reminders SET status = ? WHERE id = ?").bind("pending", id3)
]);

// If ANY statement fails, entire batch rolls back
```

### 2.4 Migrations & Schema Setup

**Migration System:**
```bash
# Create migration folder (default: migrations/)
mkdir migrations

# Create migration file
echo "CREATE TABLE IF NOT EXISTS reminders (...)" > migrations/0001_create_reminders.sql

# Apply migration (local)
npx wrangler d1 execute reminders-db --local --file=./migrations/0001_create_reminders.sql

# Apply migration (production)
npx wrangler d1 execute reminders-db --remote --file=./migrations/0001_create_reminders.sql
```

**Migration Tracking:**
- Applied migrations tracked in `d1_migrations` table (auto-created)
- Customizable via `wrangler.toml`:
  ```toml
  [[d1_databases]]
  binding = "DB"
  database_name = "reminders-db"
  migrations_dir = "migrations"
  migrations_table = "d1_migrations"
  ```

**Schema Translation (SQLite → D1):**
```sql
-- ✅ Same schema as local SQLite (database.py)
CREATE TABLE IF NOT EXISTS reminders (
    -- Identification
    id TEXT PRIMARY KEY,

    -- Core Content
    text TEXT NOT NULL,

    -- Timing
    due_date TEXT,
    due_time TEXT,
    time_required INTEGER DEFAULT 0,

    -- Location
    location_text TEXT,
    location_lat REAL,
    location_lng REAL,
    location_radius INTEGER DEFAULT 100,

    -- Organization
    priority TEXT CHECK(priority IN ('someday', 'chill', 'important', 'urgent', 'waiting')) DEFAULT 'chill',
    category TEXT,

    -- Status Tracking
    status TEXT CHECK(status IN ('pending', 'completed', 'snoozed')) DEFAULT 'pending',
    completed_at TEXT,
    snoozed_until TEXT,

    -- Recurrence
    recurrence_id TEXT,

    -- Metadata
    source TEXT DEFAULT 'manual',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    synced_at TEXT
);

-- Create indexes (same as local)
CREATE INDEX IF NOT EXISTS idx_reminders_due_date ON reminders(due_date);
CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status);
CREATE INDEX IF NOT EXISTS idx_reminders_priority ON reminders(priority);
```

### 2.5 D1 Performance Considerations

**Best Practices:**
- ✅ Use parameterized queries (`.bind()`) - prevents SQL injection
- ✅ Use `.first()` when expecting single row (faster than `.all()`)
- ✅ Use batch operations for multiple writes (atomic transactions)
- ✅ Create indexes on frequently queried columns
- ❌ Avoid `SELECT *` - specify columns explicitly
- ❌ Avoid N+1 queries - batch when possible

---

## 3. TypeScript Worker Structure

### 3.1 Recommended Project Structure

```
workers/
├── src/
│   ├── index.ts              # Main entry point (fetch handler)
│   ├── routes/
│   │   ├── health.ts         # Health check endpoint
│   │   ├── reminders.ts      # CRUD endpoints
│   │   └── index.ts          # Route aggregation
│   ├── middleware/
│   │   └── auth.ts           # Bearer token authentication
│   ├── database/
│   │   └── queries.ts        # D1 query functions
│   ├── types/
│   │   ├── env.ts            # Environment bindings
│   │   └── models.ts         # Request/Response types
│   └── utils/
│       ├── uuid.ts           # UUID generation
│       └── timestamp.ts      # ISO timestamp generation
├── migrations/
│   └── 0001_create_reminders.sql
├── wrangler.toml             # Cloudflare configuration
├── package.json
└── tsconfig.json
```

### 3.2 Route Configuration

**Using Hono Framework (Recommended):**

```typescript
// src/index.ts
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import healthRoutes from './routes/health';
import reminderRoutes from './routes/reminders';
import { authMiddleware } from './middleware/auth';

type Env = {
  DB: D1Database;
  API_TOKEN: string;
};

const app = new Hono<{ Bindings: Env }>();

// CORS middleware
app.use('/*', cors({
  origin: ['http://localhost:8080', 'http://127.0.0.1:8080'],
  allowMethods: ['GET', 'POST', 'PATCH', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization'],
  credentials: true,
}));

// Public routes (no auth)
app.route('/api/health', healthRoutes);

// Protected routes (auth required)
app.use('/api/reminders/*', authMiddleware);
app.route('/api/reminders', reminderRoutes);

// Root endpoint
app.get('/', (c) => c.json({
  name: "ADHD-Friendly Reminders API (Cloud)",
  version: "1.0.0",
  status: "running",
  docs: "/docs",
  health: "/api/health"
}));

export default app;
```

**Why Hono?**
- 🚀 **Fast**: 402,820 ops/sec (2x faster than itty-router)
- 📦 **Small**: ~14KB (vs Express.js ~500KB+)
- 🔷 **TypeScript-first**: Full type safety with path parameters
- 🎯 **Familiar API**: Similar to Express.js routing
- 🌐 **Web Standard**: Uses Request/Response APIs
- 🔧 **Middleware support**: Built-in and custom middleware

### 3.3 Error Handling

**Consistent Error Responses:**
```typescript
// Match FastAPI error format
app.onError((err, c) => {
  const status = err instanceof HTTPException ? err.status : 500;
  return c.json({
    detail: err.message || "Internal server error"
  }, status);
});

// Throw errors
throw new HTTPException(404, { message: "Reminder not found" });
throw new HTTPException(401, { message: "Invalid API token" });
```

### 3.4 Environment Variables & Secrets

**wrangler.toml (DO NOT commit secrets):**
```toml
name = "reminders-api"
main = "src/index.ts"
compatibility_date = "2025-11-01"
node_compat = true

[[d1_databases]]
binding = "DB"
database_name = "reminders-db"
database_id = "<generated-uuid>"

# For local development only (secrets via wrangler CLI in prod)
[vars]
# API_TOKEN is set via: wrangler secret put API_TOKEN
```

**Set secrets securely:**
```bash
# Production
npx wrangler secret put API_TOKEN
# Enter secret: <paste-token>

# Local (use .dev.vars file - gitignored)
echo "API_TOKEN=your-token-here" > .dev.vars
```

---

## 4. Authentication in Workers

### 4.1 Bearer Token Authentication

**Implementation Pattern:**
```typescript
// middleware/auth.ts
import { Context, Next } from 'hono';
import { HTTPException } from 'hono/http-exception';

export async function authMiddleware(c: Context, next: Next) {
  const authHeader = c.req.header('Authorization');

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw new HTTPException(401, {
      message: 'Missing or invalid authorization header. Use: Bearer YOUR_TOKEN'
    });
  }

  const token = authHeader.replace('Bearer ', '');

  if (!c.env.API_TOKEN) {
    throw new HTTPException(500, {
      message: 'Server configuration error: API_TOKEN not set'
    });
  }

  if (token !== c.env.API_TOKEN) {
    throw new HTTPException(401, {
      message: 'Invalid API token'
    });
  }

  await next();
}
```

### 4.2 CORS Configuration

**Handling Preflight Requests:**
```typescript
import { cors } from 'hono/cors';

app.use('/*', cors({
  origin: ['http://localhost:8080', 'http://127.0.0.1:8080'],
  allowMethods: ['GET', 'POST', 'PATCH', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization'],
  credentials: true,
  exposeHeaders: ['Content-Length'],
  maxAge: 600,  // Preflight cache (10 minutes)
}));
```

**Manual CORS (if needed):**
```typescript
// For OPTIONS preflight
app.options('/*', (c) => c.text('', 204));

// Add headers to responses
function addCorsHeaders(response: Response): Response {
  response.headers.set('Access-Control-Allow-Origin', '*');
  response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS');
  response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  return response;
}
```

---

## 5. API Endpoint Mapping

### 5.1 FastAPI → Workers Mapping

| FastAPI Endpoint | Workers Endpoint | Method | Auth | Status |
|-----------------|------------------|--------|------|--------|
| `GET /api/health` | `GET /api/health` | GET | ❌ No | Ready |
| `POST /api/reminders` | `POST /api/reminders` | POST | ✅ Yes | Ready |
| `GET /api/reminders` | `GET /api/reminders` | GET | ✅ Yes | Ready |
| `GET /api/reminders/{id}` | `GET /api/reminders/:id` | GET | ✅ Yes | Ready |
| `PATCH /api/reminders/{id}` | `PATCH /api/reminders/:id` | PATCH | ✅ Yes | Ready |
| `DELETE /api/reminders/{id}` | `DELETE /api/reminders/:id` | DELETE | ✅ Yes | Ready |
| `GET /` | `GET /` | GET | ❌ No | Ready |

### 5.2 Request/Response Format Compatibility

**All endpoints return identical JSON structures to FastAPI:**

```typescript
// GET /api/health
{
  "status": "ok",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2025-11-02T20:00:00.000Z"
}

// POST /api/reminders (201 Created)
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "text": "Buy milk",
  "due_date": "2025-11-03",
  "priority": "chill",
  "status": "pending",
  "created_at": "2025-11-02T20:00:00.000Z",
  "updated_at": "2025-11-02T20:00:00.000Z",
  // ... all reminder fields
}

// GET /api/reminders (with pagination)
{
  "data": [/* array of reminders */],
  "pagination": {
    "total": 42,
    "limit": 100,
    "offset": 0,
    "returned": 42
  }
}

// Error responses (4xx/5xx)
{
  "detail": "Reminder not found"
}
```

### 5.3 Implementation Example

**Health Check Endpoint:**
```typescript
// routes/health.ts
import { Hono } from 'hono';

const health = new Hono<{ Bindings: Env }>();

health.get('/', async (c) => {
  try {
    // Test database connectivity
    const result = await c.env.DB.prepare(
      "SELECT COUNT(*) as count FROM reminders"
    ).first();

    return c.json({
      status: "ok",
      version: "1.0.0",
      database: "connected",
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    return c.json({
      status: "error",
      version: "1.0.0",
      database: "disconnected",
      timestamp: new Date().toISOString()
    });
  }
});

export default health;
```

**Create Reminder Endpoint:**
```typescript
// routes/reminders.ts
import { Hono } from 'hono';
import { HTTPException } from 'hono/http-exception';

const reminders = new Hono<{ Bindings: Env }>();

reminders.post('/', async (c) => {
  const body = await c.req.json();

  // Generate ID and timestamps
  const id = crypto.randomUUID();
  const timestamp = new Date().toISOString();

  // Insert into D1
  const result = await c.env.DB.prepare(`
    INSERT INTO reminders (
      id, text, due_date, due_time, priority, category,
      status, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    id,
    body.text,
    body.due_date || null,
    body.due_time || null,
    body.priority || 'chill',
    body.category || null,
    'pending',
    timestamp,
    timestamp
  ).run();

  if (!result.success) {
    throw new HTTPException(500, { message: 'Failed to create reminder' });
  }

  // Fetch created reminder
  const created = await c.env.DB.prepare(
    "SELECT * FROM reminders WHERE id = ?"
  ).bind(id).first();

  return c.json(created, 201);
});

export default reminders;
```

---

## 6. Key Decisions

### 6.1 Technology Choices

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Web Framework** | Hono | Fast, small, TypeScript-first, Express-like API |
| **Database** | D1 (SQLite) | Same schema as local, serverless, edge-native |
| **Language** | TypeScript | Type safety, better DX, official Workers support |
| **Auth Pattern** | Bearer Token | Simple, matches FastAPI, stateless |
| **CORS** | Hono middleware | Built-in, handles preflight automatically |
| **UUID Generation** | `crypto.randomUUID()` | Native Web API, no dependencies |
| **Timestamps** | `new Date().toISOString()` | ISO 8601, matches FastAPI |

### 6.2 Architecture Patterns

**Offline-First Reconciliation Strategy:**
- ✅ Local SQLite is **authoritative** for the device
- ✅ Cloud D1 is **reconciliation point** for multi-device sync
- ✅ Last-write-wins conflict resolution (MVP)
- ✅ Client-side UUID generation enables offline creation
- ✅ `synced_at` timestamp tracks sync status

**API Compatibility:**
- ✅ Cloud API is **drop-in replacement** for local API
- ✅ Identical endpoints, request/response formats
- ✅ Frontend switches automatically: local → cloud fallback
- ✅ Same bearer token authentication

### 6.3 Gotchas to Avoid

| Issue | Problem | Solution |
|-------|---------|----------|
| **No `process.env`** | `process.env.API_TOKEN` fails | Use `c.env.API_TOKEN` (binding) |
| **No file system** | Cannot load `.env` files | Use wrangler secrets |
| **Async-only D1** | All queries are async | Use `await` for all DB operations |
| **Integer booleans** | SQLite stores booleans as 0/1 | Convert when reading/writing |
| **Batch transactions** | Single failure rolls back all | Wrap critical operations in batch |
| **CORS preflight** | OPTIONS requests fail auth | Exempt OPTIONS from auth middleware |

---

## 7. Implementation Checklist

**Phase 4.1 - Project Setup:**
- [ ] Create `workers/` directory
- [ ] Initialize npm project (`npm init -y`)
- [ ] Install dependencies: `wrangler`, `hono`, `typescript`, `@cloudflare/workers-types`
- [ ] Create `tsconfig.json`
- [ ] Create `wrangler.toml` configuration
- [ ] Create `.dev.vars` for local secrets (gitignore)
- [ ] Generate types: `npx wrangler types`

**Phase 4.2 - Database Setup:**
- [ ] Create D1 database: `npx wrangler d1 create reminders-db`
- [ ] Copy schema from `server/database.py` → `migrations/0001_create_reminders.sql`
- [ ] Apply migration locally: `npx wrangler d1 execute --local --file=migrations/0001_create_reminders.sql`
- [ ] Test D1 connectivity with simple query

**Phase 4.3 - Core Implementation:**
- [ ] Create `src/index.ts` (main entry point)
- [ ] Create `src/types/env.ts` (environment bindings)
- [ ] Create `src/utils/uuid.ts` (UUID generation)
- [ ] Create `src/utils/timestamp.ts` (ISO timestamp)
- [ ] Create `src/middleware/auth.ts` (bearer token)
- [ ] Create `src/routes/health.ts` (health check)
- [ ] Set up Hono app with CORS middleware

**Phase 4.4 - CRUD Endpoints:**
- [ ] Implement `POST /api/reminders` (create)
- [ ] Implement `GET /api/reminders` (list with filters)
- [ ] Implement `GET /api/reminders/:id` (get single)
- [ ] Implement `PATCH /api/reminders/:id` (update)
- [ ] Implement `DELETE /api/reminders/:id` (delete)

**Phase 4.5 - Testing & Deployment:**
- [ ] Test locally: `npx wrangler dev`
- [ ] Test with integration tests (curl/Postman)
- [ ] Deploy to production: `npx wrangler deploy`
- [ ] Test production endpoint
- [ ] Update frontend to use cloud endpoint

**Phase 4.6 - Documentation:**
- [ ] Update `NEXT_STEPS.md` with deployment instructions
- [ ] Document cloud endpoint URL
- [ ] Document Wrangler CLI commands
- [ ] Update `SO_FAR.md` with Phase 4 completion

---

## 8. References

**Official Documentation:**
- Cloudflare Workers: https://developers.cloudflare.com/workers/
- D1 Database: https://developers.cloudflare.com/d1/
- Hono Framework: https://hono.dev/
- Wrangler CLI: https://developers.cloudflare.com/workers/wrangler/

**Key Resources:**
- D1 Migrations: https://developers.cloudflare.com/d1/reference/migrations/
- Workers TypeScript: https://developers.cloudflare.com/workers/languages/typescript/
- Hono with D1: https://hono.dev/docs/guides/cloudflare-workers
- CORS in Workers: https://developers.cloudflare.com/workers/examples/cors-header-proxy/

**Performance Benchmarks:**
- Hono: 402,820 ops/sec
- itty-router: 212,598 ops/sec
- Workers startup: <1ms (100x faster than Node.js containers)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-02
**Author**: Subagent 5 (Research Phase)
**Model**: Claude Haiku 4.5
**Next Phase**: 4.1 - Project Setup & Scaffolding
