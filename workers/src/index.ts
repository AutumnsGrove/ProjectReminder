/**
 * Cloudflare Workers API for ADHD-Friendly Reminders System
 *
 * Hono-based TypeScript API with:
 * - Health check endpoint with D1 connectivity verification
 * - Bearer token authentication middleware
 * - CORS configuration for local development
 *
 * Phase 4 - Development Phase
 * Subagent 9: Workers API - Health & Auth
 */

import { Hono } from 'hono'
import { cors } from 'hono/cors'

/**
 * Environment bindings from wrangler.toml
 */
type Bindings = {
  DB: D1Database           // D1 database binding
  API_TOKEN: string        // Bearer token for authentication
  ENVIRONMENT?: string     // Optional environment indicator
}

/**
 * Initialize Hono app with TypeScript bindings
 */
const app = new Hono<{ Bindings: Bindings }>()

/**
 * CORS Middleware
 *
 * Allows requests from localhost:3000 (frontend dev server)
 * Enables credentials for authentication
 */
app.use('/*', cors({
  origin: ['http://localhost:3000', 'http://127.0.0.1:3000'],
  allowMethods: ['GET', 'POST', 'PATCH', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization'],
  credentials: true,
}))

/**
 * Authentication Middleware
 *
 * Validates Bearer token from Authorization header
 * Returns 401 if missing or invalid
 *
 * Usage: app.get('/protected', authMiddleware, async (c) => {...})
 */
const authMiddleware = async (c: any, next: any) => {
  const authHeader = c.req.header('Authorization')

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return c.json({
      error: 'Unauthorized',
      message: 'Missing or invalid Authorization header. Expected format: Bearer <token>'
    }, 401)
  }

  const token = authHeader.substring(7) // Remove 'Bearer ' prefix

  if (token !== c.env.API_TOKEN) {
    return c.json({
      error: 'Unauthorized',
      message: 'Invalid API token'
    }, 401)
  }

  // Token is valid, continue to route handler
  await next()
}

/**
 * Health Check Endpoint
 *
 * GET /api/health
 *
 * Returns API health status with database connectivity check
 * Does NOT require authentication
 *
 * Response format (matches FastAPI backend exactly):
 * {
 *   "status": "healthy",
 *   "version": "1.0.0",
 *   "database": "connected" | "disconnected",
 *   "timestamp": "2025-11-03T12:34:56.789Z"
 * }
 */
app.get('/api/health', async (c) => {
  let databaseStatus = 'disconnected'

  try {
    // Test database connectivity with simple COUNT query
    const result = await c.env.DB.prepare(
      'SELECT COUNT(*) as count FROM reminders'
    ).first()

    // If query succeeded and returned a result, database is connected
    if (result !== null && result !== undefined) {
      databaseStatus = 'connected'
    }
  } catch (error) {
    // Database query failed - log error but still return health check
    console.error('Database connectivity check failed:', error)
    databaseStatus = 'disconnected'
  }

  return c.json({
    status: 'healthy',
    version: '1.0.0',
    database: databaseStatus,
    timestamp: new Date().toISOString()
  })
})

/**
 * Root endpoint - API info
 * Does NOT require authentication
 */
app.get('/', async (c) => {
  return c.json({
    name: 'Reminders API',
    version: '1.0.0',
    description: 'ADHD-Friendly Voice Reminders System - Cloudflare Workers API',
    endpoints: {
      health: '/api/health',
      listReminders: 'GET /api/reminders (with filtering and pagination)',
      getReminder: 'GET /api/reminders/:id',
      testAuth: '/api/test-auth (protected endpoint for testing)'
    },
    documentation: 'See workers/ARCHITECTURE.md for full API specification'
  })
})

/**
 * Test Authentication Endpoint
 * REQUIRES authentication - for testing auth middleware
 */
app.get('/api/test-auth', authMiddleware, async (c) => {
  return c.json({
    message: 'Authentication successful!',
    authenticated: true,
    timestamp: new Date().toISOString()
  })
})

/**
 * List Reminders Endpoint
 *
 * GET /api/reminders
 * REQUIRES authentication
 *
 * Query Parameters:
 * - status (optional): Filter by status (pending/completed/snoozed)
 * - category (optional): Filter by category
 * - priority (optional): Filter by priority (someday/chill/important/urgent/waiting)
 * - limit (optional, default: 100): Max results to return
 * - offset (optional, default: 0): Pagination offset
 *
 * Response format (matches FastAPI backend exactly):
 * {
 *   "reminders": [...],
 *   "total": 10,
 *   "limit": 100,
 *   "offset": 0
 * }
 */
app.get('/api/reminders', authMiddleware, async (c) => {
  try {
    // Parse query parameters
    const status = c.req.query('status')
    const category = c.req.query('category')
    const priority = c.req.query('priority')
    const limit = parseInt(c.req.query('limit') || '100', 10)
    const offset = parseInt(c.req.query('offset') || '0', 10)

    // Build base query with dynamic filters
    let query = 'SELECT * FROM reminders WHERE 1=1'
    const params: any[] = []

    // Add filters conditionally
    if (status) {
      query += ' AND status = ?'
      params.push(status)
    }
    if (category) {
      query += ' AND category = ?'
      params.push(category)
    }
    if (priority) {
      query += ' AND priority = ?'
      params.push(priority)
    }

    // Add ordering (match FastAPI: created_at DESC)
    query += ' ORDER BY created_at DESC'

    // Add pagination
    query += ' LIMIT ? OFFSET ?'
    params.push(limit, offset)

    // Execute query with D1
    const stmt = c.env.DB.prepare(query)
    const result = await stmt.bind(...params).all()

    // Build count query for total
    let countQuery = 'SELECT COUNT(*) as total FROM reminders WHERE 1=1'
    const countParams: any[] = []

    // Apply same filters to count query
    if (status) {
      countQuery += ' AND status = ?'
      countParams.push(status)
    }
    if (category) {
      countQuery += ' AND category = ?'
      countParams.push(category)
    }
    if (priority) {
      countQuery += ' AND priority = ?'
      countParams.push(priority)
    }

    // Execute count query
    const countStmt = c.env.DB.prepare(countQuery)
    const countResult = await countStmt.bind(...countParams).first()
    const total = countResult ? (countResult.total as number) : 0

    // Return response matching FastAPI format
    return c.json({
      reminders: result.results || [],
      total: total,
      limit: limit,
      offset: offset
    })
  } catch (error) {
    console.error('Error fetching reminders:', error)
    return c.json({
      error: 'Internal Server Error',
      message: 'Failed to fetch reminders',
      timestamp: new Date().toISOString()
    }, 500)
  }
})

/**
 * Get Single Reminder Endpoint
 *
 * GET /api/reminders/:id
 * REQUIRES authentication
 *
 * Path Parameter:
 * - id: UUID of the reminder
 *
 * Response format (200 OK):
 * {
 *   "id": "uuid-string",
 *   "text": "Call mom",
 *   ... all fields
 * }
 *
 * Response format (404 Not Found):
 * {
 *   "error": "Reminder not found"
 * }
 */
app.get('/api/reminders/:id', authMiddleware, async (c) => {
  try {
    const id = c.req.param('id')

    // Query single reminder by ID
    const stmt = c.env.DB.prepare('SELECT * FROM reminders WHERE id = ?')
    const result = await stmt.bind(id).first()

    // Return 404 if not found
    if (!result) {
      return c.json({
        error: 'Reminder not found'
      }, 404)
    }

    // Return single reminder object (not array)
    return c.json(result)
  } catch (error) {
    console.error('Error fetching reminder:', error)
    return c.json({
      error: 'Internal Server Error',
      message: 'Failed to fetch reminder',
      timestamp: new Date().toISOString()
    }, 500)
  }
})

/**
 * 404 Handler
 */
app.notFound((c) => {
  return c.json({
    error: 'Not Found',
    message: `Route ${c.req.method} ${c.req.path} not found`,
    availableEndpoints: [
      'GET /',
      'GET /api/health',
      'GET /api/reminders',
      'GET /api/reminders/:id',
      'GET /api/test-auth'
    ]
  }, 404)
})

/**
 * Global Error Handler
 */
app.onError((err, c) => {
  console.error('Unhandled error:', err)
  return c.json({
    error: 'Internal Server Error',
    message: err.message || 'An unexpected error occurred',
    timestamp: new Date().toISOString()
  }, 500)
})

/**
 * Export Hono app for Cloudflare Workers
 */
export default app
