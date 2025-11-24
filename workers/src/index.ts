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
  API_TOKEN: string        // Bearer token for authentication (legacy, will be removed)
  RESEND_API_KEY: string   // Resend API key for sending magic codes
  ALLOWED_EMAIL: string    // Single allowed email address
  RESEND_FROM_EMAIL: string // From email for Resend
  ENVIRONMENT?: string     // Optional environment indicator
}

/**
 * Session data stored in context
 */
type SessionData = {
  id: string
  email: string
  created_at: string
  expires_at: string
  last_used_at: string | null
  user_agent: string | null
}

/**
 * Initialize Hono app with TypeScript bindings
 */
const app = new Hono<{ Bindings: Bindings }>()

/**
 * CORS Middleware
 *
 * Allows requests from localhost:3077 (frontend dev server)
 * Enables credentials for authentication
 */
app.use('/*', cors({
  origin: [
    'http://localhost:3077',
    'http://127.0.0.1:3077',
    'https://reminders.autumnsgrove.com'
  ],
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
 * =============================================================================
 * Authentication Helper Functions (Magic Code Auth)
 * =============================================================================
 */

/**
 * Generate a 6-digit numeric code
 */
function generateMagicCode(): string {
  const array = new Uint32Array(1)
  crypto.getRandomValues(array)
  return String(array[0] % 1000000).padStart(6, '0')
}

/**
 * Generate a secure session token (64 hex characters = 256 bits)
 */
function generateSessionToken(): string {
  const array = new Uint8Array(32)
  crypto.getRandomValues(array)
  return Array.from(array).map(b => b.toString(16).padStart(2, '0')).join('')
}

/**
 * Check if email is the allowed email (case-insensitive)
 */
function isAllowedEmail(email: string, allowedEmail: string): boolean {
  return email.toLowerCase().trim() === allowedEmail.toLowerCase().trim()
}

/**
 * Send magic code via Resend
 */
async function sendMagicCodeEmail(
  resendApiKey: string,
  fromEmail: string,
  toEmail: string,
  code: string
): Promise<boolean> {
  try {
    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${resendApiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        from: fromEmail,
        to: [toEmail],
        subject: 'Your login code for Reminders',
        html: `
          <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 400px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #1f2937; margin-bottom: 16px;">Your login code</h2>
            <p style="color: #6b7280; margin-bottom: 24px;">Enter this code to sign in to Reminders:</p>
            <div style="background: #f3f4f6; border-radius: 8px; padding: 24px; text-align: center; margin-bottom: 24px;">
              <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1f2937;">${code}</span>
            </div>
            <p style="color: #9ca3af; font-size: 14px;">This code expires in 10 minutes.</p>
            <p style="color: #9ca3af; font-size: 14px;">If you didn't request this code, you can safely ignore this email.</p>
          </div>
        `
      })
    })

    if (!response.ok) {
      const error = await response.text()
      console.error('Resend API error:', error)
      return false
    }

    return true
  } catch (error) {
    console.error('Failed to send magic code email:', error)
    return false
  }
}

/**
 * Check and update rate limit
 * Returns: { allowed: boolean, retryAfter?: number }
 */
async function checkRateLimit(
  db: D1Database,
  identifier: string,
  type: 'email' | 'ip',
  maxRequests: number = 5,
  windowMinutes: number = 15
): Promise<{ allowed: boolean; retryAfter?: number }> {
  const now = new Date()
  const windowStart = new Date(now.getTime() - windowMinutes * 60 * 1000).toISOString()

  // Check existing rate limit record
  const existing = await db.prepare(
    'SELECT * FROM rate_limits WHERE id = ? AND type = ?'
  ).bind(identifier, type).first()

  if (existing) {
    // Check if blocked
    if (existing.blocked_until && (existing.blocked_until as string) > now.toISOString()) {
      const retryAfter = Math.ceil(
        (new Date(existing.blocked_until as string).getTime() - now.getTime()) / 1000
      )
      return { allowed: false, retryAfter }
    }

    // Check if within current window
    if ((existing.window_start as string) > windowStart) {
      const requests = (existing.requests as number) + 1

      if (requests > maxRequests) {
        // Block for 15 minutes
        const blockedUntil = new Date(now.getTime() + 15 * 60 * 1000).toISOString()
        await db.prepare(
          'UPDATE rate_limits SET requests = ?, blocked_until = ? WHERE id = ? AND type = ?'
        ).bind(requests, blockedUntil, identifier, type).run()
        return { allowed: false, retryAfter: 15 * 60 }
      }

      // Update request count
      await db.prepare(
        'UPDATE rate_limits SET requests = ? WHERE id = ? AND type = ?'
      ).bind(requests, identifier, type).run()
      return { allowed: true }
    }
  }

  // New window or expired - reset/insert
  await db.prepare(`
    INSERT INTO rate_limits (id, type, requests, window_start, blocked_until)
    VALUES (?, ?, 1, ?, NULL)
    ON CONFLICT(id) DO UPDATE SET requests = 1, window_start = excluded.window_start, blocked_until = NULL
  `).bind(identifier, type, now.toISOString()).run()

  return { allowed: true }
}

/**
 * Clean up expired magic codes and sessions
 */
async function cleanupExpiredRecords(db: D1Database): Promise<void> {
  const now = new Date().toISOString()

  try {
    // Delete expired magic codes
    await db.prepare('DELETE FROM magic_codes WHERE expires_at < ?').bind(now).run()

    // Delete expired sessions
    await db.prepare('DELETE FROM sessions WHERE expires_at < ?').bind(now).run()

    // Clean up old rate limit windows (older than 1 hour)
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString()
    await db.prepare('DELETE FROM rate_limits WHERE window_start < ? AND blocked_until IS NULL').bind(oneHourAgo).run()
  } catch (error) {
    console.error('Cleanup error:', error)
  }
}

/**
 * Session-based Authentication Middleware
 * Validates session token from Authorization header
 */
const sessionAuthMiddleware = async (c: any, next: any) => {
  // Try Authorization header first
  let sessionToken: string | null = null
  const authHeader = c.req.header('Authorization')

  if (authHeader && authHeader.startsWith('Bearer ')) {
    sessionToken = authHeader.substring(7)
  }

  if (!sessionToken) {
    return c.json({
      error: 'Unauthorized',
      message: 'No session token provided',
      code: 'NO_SESSION'
    }, 401)
  }

  // Validate session
  const now = new Date().toISOString()
  const session = await c.env.DB.prepare(`
    SELECT * FROM sessions WHERE id = ? AND expires_at > ?
  `).bind(sessionToken, now).first()

  if (!session) {
    return c.json({
      error: 'Unauthorized',
      message: 'Invalid or expired session',
      code: 'INVALID_SESSION'
    }, 401)
  }

  // Update last_used_at
  await c.env.DB.prepare(
    'UPDATE sessions SET last_used_at = ? WHERE id = ?'
  ).bind(now, sessionToken).run()

  // Store session info in context for route handlers
  c.set('session', session as SessionData)

  await next()
}

/**
 * Combined Auth Middleware (supports both legacy token and session)
 * This allows gradual migration from static tokens to sessions
 */
const combinedAuthMiddleware = async (c: any, next: any) => {
  const authHeader = c.req.header('Authorization')

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return c.json({
      error: 'Unauthorized',
      message: 'Missing or invalid Authorization header'
    }, 401)
  }

  const token = authHeader.substring(7)

  // First, try legacy API token (for backward compatibility)
  if (c.env.API_TOKEN && token === c.env.API_TOKEN) {
    await next()
    return
  }

  // Then, try session token
  const now = new Date().toISOString()
  const session = await c.env.DB.prepare(`
    SELECT * FROM sessions WHERE id = ? AND expires_at > ?
  `).bind(token, now).first()

  if (session) {
    // Update last_used_at
    await c.env.DB.prepare(
      'UPDATE sessions SET last_used_at = ? WHERE id = ?'
    ).bind(now, token).run()

    c.set('session', session as SessionData)
    await next()
    return
  }

  // Neither worked
  return c.json({
    error: 'Unauthorized',
    message: 'Invalid token or session'
  }, 401)
}

/**
 * =============================================================================
 * Recurrence Pattern Helper Functions (Phase 7)
 * =============================================================================
 */

/**
 * Create a recurrence pattern in the database
 */
async function createRecurrencePattern(
  db: D1Database,
  patternId: string,
  pattern: any
): Promise<boolean> {
  try {
    const now = new Date().toISOString()
    const stmt = db.prepare(`
      INSERT INTO recurrence_patterns (
        id, frequency, interval,
        days_of_week, day_of_month, month_of_year,
        end_date, end_count, created_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `)

    const result = await stmt.bind(
      patternId,
      pattern.frequency,
      pattern.interval || 1,
      pattern.days_of_week || null,
      pattern.day_of_month || null,
      pattern.month_of_year || null,
      pattern.end_date || null,
      pattern.end_count || null,
      now
    ).run()

    return result.success
  } catch (error) {
    console.error('Failed to create recurrence pattern:', error)
    return false
  }
}

/**
 * Generate recurring reminder instances based on pattern
 */
async function generateRecurrenceInstances(
  db: D1Database,
  baseReminder: any,
  pattern: any,
  horizonDays: number = 90
): Promise<string[]> {
  const generatedIds: string[] = []

  try {
    const frequency = pattern.frequency
    const interval = pattern.interval || 1
    const endDateStr = pattern.end_date
    const endCount = pattern.end_count

    // Parse start date from base reminder or use today
    let startDate: Date
    if (baseReminder.due_date) {
      startDate = new Date(baseReminder.due_date)
    } else {
      startDate = new Date()
    }
    startDate.setHours(0, 0, 0, 0)

    // Calculate horizon end date
    const horizonEnd = new Date()
    horizonEnd.setDate(horizonEnd.getDate() + horizonDays)

    // Parse pattern end date if provided
    let patternEnd: Date | null = null
    if (endDateStr) {
      patternEnd = new Date(endDateStr)
    }

    // Determine actual end date (whichever comes first)
    const endDate = patternEnd && patternEnd < horizonEnd ? patternEnd : horizonEnd

    // Generate instances
    let currentDate = new Date(startDate)
    let instanceCount = 0
    const now = new Date().toISOString()

    while (currentDate <= endDate) {
      // Check end_count limit
      if (endCount && instanceCount >= endCount) {
        break
      }

      // For weekly recurrence, check if current day matches pattern
      if (frequency === 'weekly' && pattern.days_of_week) {
        const allowedDays = pattern.days_of_week.split(',').map((d: string) => parseInt(d))
        const currentDay = (currentDate.getDay() + 6) % 7 // Convert Sun=0 to Mon=0
        if (!allowedDays.includes(currentDay)) {
          currentDate.setDate(currentDate.getDate() + 1)
          continue
        }
      }

      // For monthly recurrence, check day of month
      if (frequency === 'monthly' && pattern.day_of_month) {
        if (currentDate.getDate() !== pattern.day_of_month) {
          currentDate.setDate(currentDate.getDate() + 1)
          continue
        }
      }

      // Create instance
      const instanceId = crypto.randomUUID()
      const dueDateISO = currentDate.toISOString().split('T')[0]

      const stmt = db.prepare(`
        INSERT INTO reminders (
          id, text, due_date, due_time, time_required,
          location_name, location_address, location_lat, location_lng, location_radius,
          priority, category, status, completed_at, snoozed_until,
          recurrence_id, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `)

      await stmt.bind(
        instanceId,
        baseReminder.text,
        dueDateISO,
        baseReminder.due_time || null,
        baseReminder.time_required || null,
        baseReminder.location_name || null,
        baseReminder.location_address || null,
        baseReminder.location_lat || null,
        baseReminder.location_lng || null,
        baseReminder.location_radius || 100,
        baseReminder.priority || 'chill',
        baseReminder.category || null,
        'pending',
        null,
        null,
        baseReminder.recurrence_id,
        now,
        now
      ).run()

      generatedIds.push(instanceId)
      instanceCount++

      // Advance to next occurrence
      if (frequency === 'daily') {
        currentDate.setDate(currentDate.getDate() + interval)
      } else if (frequency === 'weekly') {
        currentDate.setDate(currentDate.getDate() + 1)
        // After checking 7 days, skip ahead by (interval-1) weeks
        if ((currentDate.getDay() + 6) % 7 === (startDate.getDay() + 6) % 7) {
          if (interval > 1) {
            currentDate.setDate(currentDate.getDate() + (interval - 1) * 7)
          }
        }
      } else if (frequency === 'monthly') {
        const month = currentDate.getMonth() + interval
        const year = currentDate.getFullYear() + Math.floor(month / 12)
        const newMonth = month % 12
        currentDate = new Date(year, newMonth, currentDate.getDate())
      } else if (frequency === 'yearly') {
        currentDate.setFullYear(currentDate.getFullYear() + interval)
      }
    }

    return generatedIds
  } catch (error) {
    console.error('Failed to generate recurrence instances:', error)
    return generatedIds
  }
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
      auth: {
        requestCode: 'POST /api/auth/request-code (send magic code)',
        verifyCode: 'POST /api/auth/verify-code (verify and create session)',
        session: 'GET /api/auth/session (check current session)',
        logout: 'POST /api/auth/logout (invalidate session)'
      },
      listReminders: 'GET /api/reminders (with filtering and pagination)',
      getReminder: 'GET /api/reminders/:id',
      createReminder: 'POST /api/reminders',
      updateReminder: 'PATCH /api/reminders/:id',
      deleteReminder: 'DELETE /api/reminders/:id',
      testAuth: '/api/test-auth (protected endpoint for testing)',
      voiceTranscribe: 'POST /api/voice/transcribe (local-only, 501 Not Implemented)'
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
 * =============================================================================
 * Authentication Endpoints (Magic Code Flow)
 * =============================================================================
 */

/**
 * POST /api/auth/request-code
 * Request a magic code to be sent to email
 * NO authentication required
 */
app.post('/api/auth/request-code', async (c) => {
  try {
    const body = await c.req.json()
    const email = body.email?.trim().toLowerCase()

    // Validate email format
    if (!email || !email.includes('@')) {
      return c.json({
        error: 'Validation error',
        message: 'Valid email address required'
      }, 400)
    }

    // Check if email is allowed (but don't reveal this to prevent enumeration)
    const isAllowed = isAllowedEmail(email, c.env.ALLOWED_EMAIL)

    // Rate limit check (apply regardless of email validity)
    const rateLimit = await checkRateLimit(c.env.DB, email, 'email', 5, 15)
    if (!rateLimit.allowed) {
      return c.json({
        error: 'Too many requests',
        message: 'Please wait before requesting another code',
        retryAfter: rateLimit.retryAfter
      }, 429)
    }

    // Only proceed if email is allowed
    if (isAllowed) {
      // Generate code
      const code = generateMagicCode()
      const now = new Date()
      const expiresAt = new Date(now.getTime() + 10 * 60 * 1000) // 10 minutes

      // Invalidate any existing codes for this email
      await c.env.DB.prepare(
        'UPDATE magic_codes SET used = 1 WHERE email = ? AND used = 0'
      ).bind(email).run()

      // Store new code
      await c.env.DB.prepare(`
        INSERT INTO magic_codes (id, email, code, created_at, expires_at, attempts, used)
        VALUES (?, ?, ?, ?, ?, 0, 0)
      `).bind(
        crypto.randomUUID(),
        email,
        code,
        now.toISOString(),
        expiresAt.toISOString()
      ).run()

      // Send email
      const sent = await sendMagicCodeEmail(
        c.env.RESEND_API_KEY,
        c.env.RESEND_FROM_EMAIL,
        email,
        code
      )

      if (!sent) {
        console.error('Failed to send magic code email to:', email)
        // Still return success to prevent enumeration
      }
    }

    // Always return success (prevents email enumeration)
    return c.json({
      success: true,
      message: 'If this email is registered, a code has been sent'
    })

  } catch (error) {
    console.error('Request code error:', error)
    return c.json({
      error: 'Internal Server Error',
      message: 'Failed to process request'
    }, 500)
  }
})

/**
 * POST /api/auth/verify-code
 * Verify magic code and create session
 * NO authentication required
 */
app.post('/api/auth/verify-code', async (c) => {
  try {
    const body = await c.req.json()
    const email = body.email?.trim().toLowerCase()
    const code = body.code?.trim()

    // Validate inputs
    if (!email || !code) {
      return c.json({
        error: 'Validation error',
        message: 'Email and code are required'
      }, 400)
    }

    // Validate code format (6 digits)
    if (!/^\d{6}$/.test(code)) {
      return c.json({
        error: 'Validation error',
        message: 'Invalid code format'
      }, 400)
    }

    const now = new Date().toISOString()

    // Find valid magic code
    const magicCode = await c.env.DB.prepare(`
      SELECT * FROM magic_codes
      WHERE email = ? AND used = 0 AND expires_at > ?
      ORDER BY created_at DESC LIMIT 1
    `).bind(email, now).first()

    if (!magicCode) {
      return c.json({
        error: 'Invalid code',
        message: 'Code expired or not found. Please request a new code.'
      }, 400)
    }

    // Check attempts (brute force protection)
    if ((magicCode.attempts as number) >= 5) {
      // Mark code as used to prevent further attempts
      await c.env.DB.prepare(
        'UPDATE magic_codes SET used = 1 WHERE id = ?'
      ).bind(magicCode.id).run()

      return c.json({
        error: 'Too many attempts',
        message: 'Too many failed attempts. Please request a new code.'
      }, 400)
    }

    // Verify code
    if (magicCode.code !== code) {
      // Increment attempts
      await c.env.DB.prepare(
        'UPDATE magic_codes SET attempts = attempts + 1 WHERE id = ?'
      ).bind(magicCode.id).run()

      const remainingAttempts = 5 - (magicCode.attempts as number) - 1

      return c.json({
        error: 'Invalid code',
        message: `Incorrect code. ${remainingAttempts} attempts remaining.`
      }, 400)
    }

    // Code is valid - mark as used
    await c.env.DB.prepare(
      'UPDATE magic_codes SET used = 1 WHERE id = ?'
    ).bind(magicCode.id).run()

    // Create session
    const sessionToken = generateSessionToken()
    const sessionExpires = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 7 days

    await c.env.DB.prepare(`
      INSERT INTO sessions (id, email, created_at, expires_at, last_used_at, user_agent)
      VALUES (?, ?, ?, ?, ?, ?)
    `).bind(
      sessionToken,
      email,
      now,
      sessionExpires.toISOString(),
      now,
      c.req.header('User-Agent') || null
    ).run()

    // Cleanup old records periodically (1 in 10 requests)
    if (Math.random() < 0.1) {
      cleanupExpiredRecords(c.env.DB)
    }

    return c.json({
      success: true,
      session_token: sessionToken,
      expires_at: sessionExpires.toISOString()
    })

  } catch (error) {
    console.error('Verify code error:', error)
    return c.json({
      error: 'Internal Server Error',
      message: 'Failed to verify code'
    }, 500)
  }
})

/**
 * GET /api/auth/session
 * Check current session status
 * REQUIRES session authentication
 */
app.get('/api/auth/session', sessionAuthMiddleware, async (c) => {
  const session = c.get('session') as SessionData

  return c.json({
    authenticated: true,
    email: session.email,
    expires_at: session.expires_at,
    created_at: session.created_at
  })
})

/**
 * POST /api/auth/logout
 * Invalidate current session
 * REQUIRES session authentication
 */
app.post('/api/auth/logout', sessionAuthMiddleware, async (c) => {
  const session = c.get('session') as SessionData

  // Delete session
  await c.env.DB.prepare(
    'DELETE FROM sessions WHERE id = ?'
  ).bind(session.id).run()

  return c.json({
    success: true,
    message: 'Logged out successfully'
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
app.get('/api/reminders', combinedAuthMiddleware, async (c) => {
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
/**
 * Location Endpoints (Phase 6)
 *
 * GET /api/reminders/near-location
 *
 * Find reminders near a specific location
 * Requires: Authentication
 * Query params: lat (required), lng (required), radius (optional, default 1000m)
 *
 * Response:
 * {
 *   "data": [...reminders within radius, sorted by distance...],
 *   "pagination": { "total": N, "limit": N, "offset": 0, "returned": N } 
 * }
 */
app.get('/api/reminders/near-location', combinedAuthMiddleware, async (c) => {
  try {
    // Parse query parameters
    const lat = parseFloat(c.req.query('lat') || '')
    const lng = parseFloat(c.req.query('lng') || '')
    const radius = parseInt(c.req.query('radius') || '1000')

    // Validate parameters
    if (isNaN(lat) || isNaN(lng)) {
      return c.json({
        error: 'Bad Request',
        message: 'Missing or invalid lat/lng parameters'
      }, 400)
    }

    if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
      return c.json({
        error: 'Bad Request',
        message: 'Latitude must be -90 to 90, longitude must be -180 to 180'
      }, 400)
    }

    if (isNaN(radius) || radius < 10 || radius > 50000) {
      return c.json({
        error: 'Bad Request',
        message: 'Radius must be between 10 and 50000 meters'
      }, 400)
    }

    // Get all reminders with location data
    const allReminders = await c.env.DB.prepare(`
      SELECT * FROM reminders
      WHERE location_lat IS NOT NULL
      AND location_lng IS NOT NULL
    `).all()

    // Calculate distances and filter by radius
    const nearbyReminders: any[] = []

    for (const reminder of allReminders.results || []) {
      const distance = haversineDistance(
        lat, lng,
        reminder.location_lat as number,
        reminder.location_lng as number
      )

      // Check if within reminder's configured radius (or search radius, whichever is larger)
      const reminderRadius = (reminder.location_radius as number) || 100
      const effectiveRadius = Math.max(radius, reminderRadius)

      if (distance <= effectiveRadius) {
        // Add distance metadata for sorting
        nearbyReminders.push({
          ...reminder,
          distance: Math.round(distance * 100) / 100 // Round to 2 decimal places
        })
      }
    }

    // Sort by distance (nearest first)
    nearbyReminders.sort((a, b) => a.distance - b.distance)

    // Return response with pagination metadata
    return c.json({
      data: nearbyReminders,
      pagination: {
        total: nearbyReminders.length,
        limit: nearbyReminders.length,
        offset: 0,
        returned: nearbyReminders.length
      }
    })
  } catch (error) {
    console.error('Near location error:', error)
    return c.json({
      error: 'Internal Server Error',
      message: 'Failed to find nearby reminders',
      timestamp: new Date().toISOString()
    }, 500)
  }
})
app.get('/api/reminders/:id', combinedAuthMiddleware, async (c) => {
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
app.post('/api/reminders', combinedAuthMiddleware, async (c) => {
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

    // Handle recurrence pattern if provided (Phase 7)
    let patternId = body.recurrence_id || null
    if (body.recurrence_pattern) {
      // Validate recurrence pattern
      const validFrequencies = ['daily', 'weekly', 'monthly', 'yearly']
      if (!validFrequencies.includes(body.recurrence_pattern.frequency)) {
        return c.json({
          error: 'Validation error',
          message: `Invalid recurrence frequency. Must be one of: ${validFrequencies.join(', ')}`
        }, 400)
      }

      // Create recurrence pattern
      patternId = crypto.randomUUID()
      const patternCreated = await createRecurrencePattern(
        c.env.DB,
        patternId,
        body.recurrence_pattern
      )

      if (!patternCreated) {
        return c.json({
          error: 'Database error',
          message: 'Failed to create recurrence pattern'
        }, 500)
      }

      // Generate recurring instances
      const baseReminder = {
        text: body.text,
        due_date: body.due_date,
        due_time: body.due_time,
        time_required: body.time_required,
        location_name: body.location_name,
        location_address: body.location_address,
        location_lat: body.location_lat,
        location_lng: body.location_lng,
        location_radius: body.location_radius || 100,
        priority: body.priority || 'chill',
        category: body.category,
        recurrence_id: patternId
      }

      const generatedIds = await generateRecurrenceInstances(
        c.env.DB,
        baseReminder,
        body.recurrence_pattern,
        90 // 90 days horizon
      )

      if (generatedIds.length === 0) {
        return c.json({
          error: 'Database error',
          message: 'Failed to generate recurrence instances'
        }, 500)
      }

      // Fetch and return the first generated instance
      const firstInstance = await c.env.DB.prepare(
        'SELECT * FROM reminders WHERE id = ?'
      ).bind(generatedIds[0]).first()

      if (!firstInstance) {
        return c.json({
          error: 'Database error',
          message: 'Instance created but could not be retrieved'
        }, 500)
      }

      return c.json(firstInstance, 201)
    }

    // No recurrence - create single reminder
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
      patternId,
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
app.patch('/api/reminders/:id', combinedAuthMiddleware, async (c) => {
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
app.delete('/api/reminders/:id', combinedAuthMiddleware, async (c) => {
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
 * Sync Endpoint (Phase 5)
 *
 * POST /api/sync
 * REQUIRES authentication
 *
 * Bidirectional sync endpoint for offline-first synchronization.
 *
 * Request body:
 * {
 *   "client_id": "device-uuid",
 *   "last_sync": "2025-11-03T10:00:00Z" | null,
 *   "changes": [
 *     {
 *       "id": "reminder-uuid",
 *       "action": "create" | "update" | "delete",
 *       "data": { reminder fields } | null,
 *       "updated_at": "2025-11-03T10:15:00Z"
 *     }
 *   ]
 * }
 *
 * Response format:
 * {
 *   "server_changes": [SyncChange[]],
 *   "conflicts": [ConflictInfo[]],
 *   "last_sync": "2025-11-03T10:30:00Z",
 *   "applied_count": 3
 * }
 */
app.post('/api/sync', combinedAuthMiddleware, async (c) => {
  try {
    const body = await c.req.json()
    const currentTime = new Date().toISOString()

    // Validate request body
    if (!body.client_id) {
      return c.json({
        error: 'Validation error',
        message: 'client_id is required'
      }, 400)
    }

    const conflicts: any[] = []
    let appliedCount = 0

    // Step 1: Apply client changes to server
    if (body.changes && Array.isArray(body.changes)) {
      for (const change of body.changes) {
        try {
          // Check if reminder exists on server
          const existing = await c.env.DB.prepare('SELECT * FROM reminders WHERE id = ?')
            .bind(change.id)
            .first()

          // Detect conflicts (both client and server modified same reminder)
          if (change.action === 'update' && existing) {
            const clientUpdatedAt = change.updated_at
            const serverUpdatedAt = existing.updated_at as string

            // Conflict: both updated since last sync
            if (serverUpdatedAt && clientUpdatedAt) {
              // Last-write-wins: Compare timestamps
              if (serverUpdatedAt > clientUpdatedAt) {
                // Server wins - skip client change
                conflicts.push({
                  id: change.id,
                  client_updated_at: clientUpdatedAt,
                  server_updated_at: serverUpdatedAt,
                  resolution: 'server_wins'
                })
                continue
              } else {
                // Client wins - apply change and log conflict
                conflicts.push({
                  id: change.id,
                  client_updated_at: clientUpdatedAt,
                  server_updated_at: serverUpdatedAt,
                  resolution: 'client_wins'
                })
              }
            }
          }

          // Apply the change
          if (change.action === 'delete') {
            const result = await c.env.DB.prepare('DELETE FROM reminders WHERE id = ?')
              .bind(change.id)
              .run()
            if (result.success) appliedCount++
          } else if (change.action === 'create') {
            if (!change.data) continue

            const data = change.data
            const result = await c.env.DB.prepare(`
              INSERT INTO reminders (
                id, text, notes, due_date, due_time, time_required,
                location_name, location_address, location_lat, location_lng, location_radius,
                priority, category, status, completed_at, snoozed_until, snooze_count,
                recurrence_id, is_recurring_instance, original_due_date,
                created_at, updated_at, synced_at
              ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            `).bind(
              data.id, data.text, data.notes || null, data.due_date || null, data.due_time || null,
              data.time_required || 0, data.location_name || null, data.location_address || null,
              data.location_lat || null, data.location_lng || null, data.location_radius || 100,
              data.priority || 'chill', data.category || null, data.status || 'pending',
              data.completed_at || null, data.snoozed_until || null, data.snooze_count || 0,
              data.recurrence_id || null, data.is_recurring_instance || 0, data.original_due_date || null,
              data.created_at, data.updated_at, currentTime
            ).run()

            if (result.success) appliedCount++
          } else if (change.action === 'update') {
            if (!change.data) continue

            const data = change.data
            const updates: string[] = []
            const params: any[] = []

            // Build dynamic UPDATE query
            Object.keys(data).forEach(key => {
              if (key !== 'id' && key !== 'created_at') {
                updates.push(`${key} = ?`)
                params.push(data[key])
              }
            })

            updates.push('synced_at = ?')
            params.push(currentTime)
            params.push(change.id)

            const result = await c.env.DB.prepare(
              `UPDATE reminders SET ${updates.join(', ')} WHERE id = ?`
            ).bind(...params).run()

            if (result.success) appliedCount++
          }
        } catch (error) {
          console.error(`Failed to apply change ${change.id}:`, error)
          continue
        }
      }
    }

    // Step 2: Get server changes since client's last sync
    let serverReminders: any[] = []
    if (body.last_sync) {
      const result = await c.env.DB.prepare(
        'SELECT * FROM reminders WHERE updated_at > ? ORDER BY updated_at ASC'
      ).bind(body.last_sync).all()
      serverReminders = result.results || []
    } else {
      // First sync - return all reminders
      const result = await c.env.DB.prepare(
        'SELECT * FROM reminders ORDER BY updated_at ASC'
      ).all()
      serverReminders = result.results || []
    }

    // Convert server reminders to SyncChange objects
    const serverChanges = serverReminders
      .filter(reminder => {
        // Skip reminders that were just updated by this sync request
        return !body.changes?.some((c: any) => c.id === reminder.id)
      })
      .map(reminder => ({
        id: reminder.id,
        action: 'update',
        data: reminder,
        updated_at: reminder.updated_at
      }))

    // Step 3: Update synced_at for all reminders sent to client
    if (serverChanges.length > 0) {
      const reminderIds = serverChanges.map(c => c.id)
      const placeholders = reminderIds.map(() => '?').join(',')
      await c.env.DB.prepare(
        `UPDATE reminders SET synced_at = ? WHERE id IN (${placeholders})`
      ).bind(currentTime, ...reminderIds).run()
    }

    // Step 4: Return sync response
    return c.json({
      server_changes: serverChanges,
      conflicts: conflicts,
      last_sync: currentTime,
      applied_count: appliedCount
    })
  } catch (error) {
    console.error('Sync error:', error)
    return c.json({
      error: 'Internal Server Error',
      message: 'Sync failed',
      timestamp: new Date().toISOString()
    }, 500)
  }
})

/**
 * Haversine Distance Calculation
 *
 * Calculate distance between two coordinates using Haversine formula
 *
 * @param lat1 - Latitude of first point (degrees)
 * @param lng1 - Longitude of first point (degrees)
 * @param lat2 - Latitude of second point (degrees)
 * @param lng2 - Longitude of second point (degrees)
 * @returns Distance in meters
 */
function haversineDistance(lat1: number, lng1: number, lat2: number, lng2: number): number {
  // Earth's radius in meters
  const R = 6371000

  // Convert degrees to radians
  const lat1Rad = lat1 * Math.PI / 180
  const lat2Rad = lat2 * Math.PI / 180
  const deltaLat = (lat2 - lat1) * Math.PI / 180
  const deltaLng = (lng2 - lng1) * Math.PI / 180

  // Haversine formula
  const a = Math.sin(deltaLat / 2) * Math.sin(deltaLat / 2) +
            Math.cos(lat1Rad) * Math.cos(lat2Rad) *
            Math.sin(deltaLng / 2) * Math.sin(deltaLng / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))

  return R * c
}

/**

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
      'POST /api/auth/request-code',
      'POST /api/auth/verify-code',
      'GET /api/auth/session',
      'POST /api/auth/logout',
      'GET /api/reminders',
      'GET /api/reminders/:id',
      'POST /api/reminders',
      'PATCH /api/reminders/:id',
      'DELETE /api/reminders/:id',
      'POST /api/sync',
      'GET /api/reminders/near-location',
      'GET /api/test-auth',
      'POST /api/voice/transcribe'
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
/**
 * Location Endpoints (Phase 6)
 *
 * GET /api/reminders/near-location
 *
 * Find reminders near a specific location
 * Requires: Authentication
 * Query params: lat (required), lng (required), radius (optional, default 1000m)
 *
 * Response:
 * {
 *   "data": [...reminders within radius, sorted by distance...],
 *   "pagination": { "total": N, "limit": N, "offset": 0, "returned": N } 
 * }
 */
app.get('/api/reminders/near-location', combinedAuthMiddleware, async (c) => {
  try {
    // Parse query parameters
    const lat = parseFloat(c.req.query('lat') || '')
    const lng = parseFloat(c.req.query('lng') || '')
    const radius = parseInt(c.req.query('radius') || '1000')

    // Validate parameters
    if (isNaN(lat) || isNaN(lng)) {
      return c.json({
        error: 'Bad Request',
        message: 'Missing or invalid lat/lng parameters'
      }, 400)
    }

    if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
      return c.json({
        error: 'Bad Request',
        message: 'Latitude must be -90 to 90, longitude must be -180 to 180'
      }, 400)
    }

    if (isNaN(radius) || radius < 10 || radius > 50000) {
      return c.json({
        error: 'Bad Request',
        message: 'Radius must be between 10 and 50000 meters'
      }, 400)
    }

    // Get all reminders with location data
    const allReminders = await c.env.DB.prepare(`
      SELECT * FROM reminders
      WHERE location_lat IS NOT NULL
      AND location_lng IS NOT NULL
    `).all()

    // Calculate distances and filter by radius
    const nearbyReminders: any[] = []

    for (const reminder of allReminders.results || []) {
      const distance = haversineDistance(
        lat, lng,
        reminder.location_lat as number,
        reminder.location_lng as number
      )

      // Check if within reminder's configured radius (or search radius, whichever is larger)
      const reminderRadius = (reminder.location_radius as number) || 100
      const effectiveRadius = Math.max(radius, reminderRadius)

      if (distance <= effectiveRadius) {
        // Add distance metadata for sorting
        nearbyReminders.push({
          ...reminder,
          distance: Math.round(distance * 100) / 100 // Round to 2 decimal places
        })
      }
    }

    // Sort by distance (nearest first)
    nearbyReminders.sort((a, b) => a.distance - b.distance)

    // Return response with pagination metadata
    return c.json({
      data: nearbyReminders,
      pagination: {
        total: nearbyReminders.length,
        limit: nearbyReminders.length,
        offset: 0,
        returned: nearbyReminders.length
      }
    })
  } catch (error) {
    console.error('Near location error:', error)
    return c.json({
      error: 'Internal Server Error',
      message: 'Failed to find nearby reminders',
      timestamp: new Date().toISOString()
    }, 500)
  }
})
/**
 * Voice Transcription Endpoint (501 Not Implemented)
 *
 * POST /api/voice/transcribe
 *
 * Stub endpoint to maintain API parity
 *
 * Response format (501 Not Implemented):
 * {
 *   "detail": "Voice transcription requires local server",
 *   "error": "not_implemented",
 *   "suggestion": "Ensure local FastAPI server is running with Whisper.cpp",
 *   "feature": "voice_transcription",
 *   "available_on": "local_only"
 * }
 */
app.post('/api/voice/transcribe', combinedAuthMiddleware, async (c) => {
  return c.json(
    {
      detail: "Voice transcription requires local server. Please connect to local API at http://localhost:8000",
      error: "not_implemented",
      suggestion: "Ensure your local FastAPI server is running with Whisper.cpp installed",
      feature: "voice_transcription",
      available_on: "local_only"
    },
    {
      status: 501,
      headers: {
        'X-Feature-Availability': 'local-only',
        'X-Reason': 'Whisper.cpp requires native binaries (incompatible with Workers runtime)'
      }
    }
  )
})

export default app
