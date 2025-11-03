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
      reminders: '/api/reminders (coming in Subagent 10-11)',
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
 * 404 Handler
 */
app.notFound((c) => {
  return c.json({
    error: 'Not Found',
    message: `Route ${c.req.method} ${c.req.path} not found`,
    availableEndpoints: ['GET /', 'GET /api/health']
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
