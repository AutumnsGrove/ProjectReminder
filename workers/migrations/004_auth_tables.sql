-- Migration: 004_auth_tables.sql
-- Purpose: Add authentication tables for magic code login
-- Created: 2025-11-24

-- =============================================================================
-- Magic Codes Table (temporary codes for email verification)
-- =============================================================================
CREATE TABLE IF NOT EXISTS magic_codes (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    code TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    attempts INTEGER DEFAULT 0,
    used INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_magic_codes_email ON magic_codes(email);
CREATE INDEX IF NOT EXISTS idx_magic_codes_expires_at ON magic_codes(expires_at);

-- =============================================================================
-- Sessions Table (active user sessions)
-- =============================================================================
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    last_used_at TEXT,
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_email ON sessions(email);

-- =============================================================================
-- Rate Limiting Table (prevent brute force)
-- =============================================================================
CREATE TABLE IF NOT EXISTS rate_limits (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    requests INTEGER DEFAULT 1,
    window_start TEXT NOT NULL,
    blocked_until TEXT
);

CREATE INDEX IF NOT EXISTS idx_rate_limits_type ON rate_limits(type);
