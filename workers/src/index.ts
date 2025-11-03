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
      createReminder: 'POST /api/reminders',
      updateReminder: 'PATCH /api/reminders/:id',
      deleteReminder: 'DELETE /api/reminders/:id',
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
 * Create Reminder Endpoint
 *
 * POST /api/reminders
 * REQUIRES authentication
 *
 * Request Body (JSON):
 * {
 *   "text": "Call mom",              // REQUIRED
 *   "priority": "important",         // Optional (default: 'chill')
 *   "category": "Calls",             // Optional
 *   "due_date": "2025-11-04",        // Optional
 *   "due_time": "15:00:00",          // Optional
 *   "time_required": 30,             // Optional (minutes)
 *   "location_name": "Home",         // Optional
 *   "location_address": "123 Main",  // Optional
 *   "location_lat": 40.7128,         // Optional
 *   "location_lng": -74.0060,        // Optional
 *   "location_radius": 100,          // Optional (default: 100)
 *   "notes": "Don't forget..."       // Optional
 * }
 *
 * Response format (201 Created):
 * Returns complete reminder object with generated id, created_at, updated_at
 *
 * Response format (400 Bad Request):
 * {
 *   "error": "Validation error",
 *   "message": "Missing required field: text"
 * }
 */
app.post('/api/reminders', authMiddleware, async (c) => {
  try {
    const body = await c.req.json()

    // Validate required field
    if (!body.text || body.text.trim() === '') {
      return c.json({
        error: 'Validation error',
        message: 'Missing required field: text'
      }, 400)
    }

    // Validate priority if provided
    const validPriorities = ['someday', 'chill', 'important', 'urgent', 'waiting']
    if (body.priority && !validPriorities.includes(body.priority)) {
      return c.json({
        error: 'Validation error',
        message: `Invalid priority. Must be one of: ${validPriorities.join(', ')}`
      }, 400)
    }

    // Validate status if provided
    const validStatuses = ['pending', 'completed', 'snoozed']
    if (body.status && !validStatuses.includes(body.status)) {
      return c.json({
        error: 'Validation error',
        message: `Invalid status. Must be one of: ${validStatuses.join(', ')}`
      }, 400)
    }

    // Generate server fields
    const id = crypto.randomUUID()
    const now = new Date().toISOString()

    // Build INSERT with all fields
    const stmt = c.env.DB.prepare(`
      INSERT INTO reminders (
        id, text, priority, category, status,
        due_date, due_time, time_required,
        location_name, location_address, location_lat, location_lng, location_radius,
        notes, completed_at, created_at, updated_at,
        snoozed_until, snooze_count, recurrence_id,
        is_recurring_instance, original_due_date
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `)

    const result = await stmt.bind(
      id,
      body.text,
      body.priority || 'chill',
      body.category || null,
      body.status || 'pending',
      body.due_date || null,
      body.due_time || null,
      body.time_required || null,
      body.location_name || null,
      body.location_address || null,
      body.location_lat || null,
      body.location_lng || null,
      body.location_radius || 100,
      body.notes || null,
      body.completed_at || null,
      now,
      now,
      body.snoozed_until || null,
      body.snooze_count || 0,
      body.recurrence_id || null,
      body.is_recurring_instance || 0,
      body.original_due_date || null
    ).run()

    if (!result.success) {
      console.error('Database insert failed:', result)
      return c.json({
        error: 'Database error',
        message: 'Failed to create reminder'
      }, 500)
    }

    // Fetch and return the created reminder
    const created = await c.env.DB.prepare('SELECT * FROM reminders WHERE id = ?').bind(id).first()

    if (!created) {
      return c.json({
        error: 'Database error',
        message: 'Reminder created but could not be retrieved'
      }, 500)
    }

    return c.json(created, 201)
  } catch (error) {
    console.error('Error creating reminder:', error)
    return c.json({
      error: 'Internal Server Error',
      message: 'Failed to create reminder',
      timestamp: new Date().toISOString()
    }, 500)
  }
})

/**
 * Update Reminder Endpoint
 *
 * PATCH /api/reminders/:id
 * REQUIRES authentication
 *
 * Path Parameter:
 * - id: UUID of the reminder
 *
 * Request Body (JSON):
 * All fields are optional (partial update)
 * {
 *   "text": "Updated text",
 *   "priority": "urgent",
 *   "status": "completed",
 *   "completed_at": "2025-11-03T18:30:00.000Z"
 * }
 *
 * Special Logic:
 * - If status changes to 'completed' and no completed_at provided, set it automatically
 * - If status changes from 'completed' to anything else, clear completed_at
 * - updated_at is always set to current timestamp
 *
 * Response format (200 OK):
 * Returns complete updated reminder object
 *
 * Response format (404 Not Found):
 * {
 *   "error": "Reminder not found"
 * }
 */
app.patch('/api/reminders/:id', authMiddleware, async (c) => {
  try {
    const id = c.req.param('id')
    const body = await c.req.json()

    // First check if reminder exists
    const existing = await c.env.DB.prepare('SELECT * FROM reminders WHERE id = ?').bind(id).first()
    if (!existing) {
      return c.json({
        error: 'Reminder not found'
      }, 404)
    }

    // Build dynamic UPDATE query
    const updates: string[] = []
    const params: any[] = []

    // Add each field that's present in the body
    if (body.text !== undefined) {
      updates.push('text = ?')
      params.push(body.text)
    }
    if (body.priority !== undefined) {
      // Validate priority
      const validPriorities = ['someday', 'chill', 'important', 'urgent', 'waiting']
      if (!validPriorities.includes(body.priority)) {
        return c.json({
          error: 'Validation error',
          message: `Invalid priority. Must be one of: ${validPriorities.join(', ')}`
        }, 400)
      }
      updates.push('priority = ?')
      params.push(body.priority)
    }
    if (body.category !== undefined) {
      updates.push('category = ?')
      params.push(body.category)
    }
    if (body.due_date !== undefined) {
      updates.push('due_date = ?')
      params.push(body.due_date)
    }
    if (body.due_time !== undefined) {
      updates.push('due_time = ?')
      params.push(body.due_time)
    }
    if (body.time_required !== undefined) {
      updates.push('time_required = ?')
      params.push(body.time_required)
    }
    if (body.location_name !== undefined) {
      updates.push('location_name = ?')
      params.push(body.location_name)
    }
    if (body.location_address !== undefined) {
      updates.push('location_address = ?')
      params.push(body.location_address)
    }
    if (body.location_lat !== undefined) {
      updates.push('location_lat = ?')
      params.push(body.location_lat)
    }
    if (body.location_lng !== undefined) {
      updates.push('location_lng = ?')
      params.push(body.location_lng)
    }
    if (body.location_radius !== undefined) {
      updates.push('location_radius = ?')
      params.push(body.location_radius)
    }
    if (body.notes !== undefined) {
      updates.push('notes = ?')
      params.push(body.notes)
    }
    if (body.snoozed_until !== undefined) {
      updates.push('snoozed_until = ?')
      params.push(body.snoozed_until)
    }
    if (body.snooze_count !== undefined) {
      updates.push('snooze_count = ?')
      params.push(body.snooze_count)
    }
    if (body.recurrence_id !== undefined) {
      updates.push('recurrence_id = ?')
      params.push(body.recurrence_id)
    }
    if (body.is_recurring_instance !== undefined) {
      updates.push('is_recurring_instance = ?')
      params.push(body.is_recurring_instance)
    }
    if (body.original_due_date !== undefined) {
      updates.push('original_due_date = ?')
      params.push(body.original_due_date)
    }

    // Special logic: handle status change to/from completed
    if (body.status !== undefined) {
      // Validate status
      const validStatuses = ['pending', 'completed', 'snoozed']
      if (!validStatuses.includes(body.status)) {
        return c.json({
          error: 'Validation error',
          message: `Invalid status. Must be one of: ${validStatuses.join(', ')}`
        }, 400)
      }

      updates.push('status = ?')
      params.push(body.status)

      // Auto-set completed_at when marking as completed
      if (body.status === 'completed' && body.completed_at === undefined) {
        updates.push('completed_at = ?')
        params.push(new Date().toISOString())
      } else if (body.status !== 'completed') {
        // Clear completed_at when changing away from completed
        updates.push('completed_at = ?')
        params.push(null)
      }
    }

    // Handle explicit completed_at if provided
    if (body.completed_at !== undefined) {
      updates.push('completed_at = ?')
      params.push(body.completed_at)
    }

    // Always update updated_at
    updates.push('updated_at = ?')
    params.push(new Date().toISOString())

    // If no fields to update (empty body), just return current state
    if (updates.length === 1) { // Only updated_at
      return c.json(existing)
    }

    // Add id for WHERE clause
    params.push(id)

    const query = `UPDATE reminders SET ${updates.join(', ')} WHERE id = ?`
    const result = await c.env.DB.prepare(query).bind(...params).run()

    if (!result.success) {
      console.error('Database update failed:', result)
      return c.json({
        error: 'Database error',
        message: 'Failed to update reminder'
      }, 500)
    }

    // Fetch and return updated reminder
    const updated = await c.env.DB.prepare('SELECT * FROM reminders WHERE id = ?').bind(id).first()

    if (!updated) {
      return c.json({
        error: 'Database error',
        message: 'Reminder updated but could not be retrieved'
      }, 500)
    }

    return c.json(updated)
  } catch (error) {
    console.error('Error updating reminder:', error)
    return c.json({
      error: 'Internal Server Error',
      message: 'Failed to update reminder',
      timestamp: new Date().toISOString()
    }, 500)
  }
})

/**
 * Delete Reminder Endpoint
 *
 * DELETE /api/reminders/:id
 * REQUIRES authentication
 *
 * Path Parameter:
 * - id: UUID of the reminder
 *
 * Implementation: Hard delete (actually removes from database)
 *
 * Response format (204 No Content):
 * Empty body, HTTP status 204
 *
 * Response format (404 Not Found):
 * {
 *   "error": "Reminder not found"
 * }
 */
app.delete('/api/reminders/:id', authMiddleware, async (c) => {
  try {
    const id = c.req.param('id')

    // Check if exists first (for proper 404)
    const existing = await c.env.DB.prepare('SELECT * FROM reminders WHERE id = ?').bind(id).first()
    if (!existing) {
      return c.json({
        error: 'Reminder not found'
      }, 404)
    }

    // Hard delete
    const result = await c.env.DB.prepare('DELETE FROM reminders WHERE id = ?').bind(id).run()

    if (!result.success) {
      console.error('Database delete failed:', result)
      return c.json({
        error: 'Database error',
        message: 'Failed to delete reminder'
      }, 500)
    }

    // Return 204 No Content
    return c.body(null, 204)
  } catch (error) {
    console.error('Error deleting reminder:', error)
    return c.json({
      error: 'Internal Server Error',
      message: 'Failed to delete reminder',
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
      'POST /api/reminders',
      'PATCH /api/reminders/:id',
      'DELETE /api/reminders/:id',
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
