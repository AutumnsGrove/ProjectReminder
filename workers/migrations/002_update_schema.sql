-- Migration: 002_update_schema.sql
-- Purpose: Update reminders table to match Phase 4 production schema
-- Created: November 3, 2025
-- Phase: 4.3 (Development Phase)
-- Subagent: Subagent 11 - Workers API Write Endpoints
--
-- Changes:
--   - Rename location_text to location_name and location_address
--   - Add notes, snooze_count, is_recurring_instance, original_due_date
--   - Remove source and synced_at (not needed for MVP)
--
-- Usage:
--   wrangler d1 migrations apply reminders-db --local  # Apply locally

-- =============================================================================
-- Update Reminders Table Schema
-- =============================================================================

-- Step 1: Create new table with updated schema
CREATE TABLE reminders_new (
    -- Identification
    id TEXT PRIMARY KEY,

    -- Core Content
    text TEXT NOT NULL,
    notes TEXT,

    -- Timing
    due_date TEXT,
    due_time TEXT,
    time_required INTEGER,

    -- Location (Phase 6: Location-based reminders)
    location_name TEXT,
    location_address TEXT,
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
    snooze_count INTEGER DEFAULT 0,

    -- Recurrence (Phase 7: Recurring reminders)
    recurrence_id TEXT,
    is_recurring_instance INTEGER DEFAULT 0,
    original_due_date TEXT,

    -- Metadata
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Step 2: Copy data from old table to new table
INSERT INTO reminders_new (
    id, text, due_date, due_time, time_required,
    location_name, location_lat, location_lng, location_radius,
    priority, category, status, completed_at, snoozed_until,
    recurrence_id, created_at, updated_at
)
SELECT
    id, text, due_date, due_time, time_required,
    location_text, location_lat, location_lng, location_radius,
    priority, category, status, completed_at, snoozed_until,
    recurrence_id, created_at, updated_at
FROM reminders;

-- Step 3: Drop old table
DROP TABLE reminders;

-- Step 4: Rename new table to reminders
ALTER TABLE reminders_new RENAME TO reminders;

-- =============================================================================
-- Recreate Performance Indexes
-- =============================================================================

-- Index for date-based queries
CREATE INDEX idx_reminders_due_date ON reminders(due_date);

-- Index for status filtering
CREATE INDEX idx_reminders_status ON reminders(status);

-- Index for category filtering
CREATE INDEX idx_reminders_category ON reminders(category);

-- Index for priority filtering
CREATE INDEX idx_reminders_priority ON reminders(priority);

-- Composite index for location-based queries (Phase 6)
CREATE INDEX idx_reminders_location ON reminders(location_lat, location_lng);

-- =============================================================================
-- Migration Complete
-- =============================================================================
-- Schema version: 002
-- Compatible with: ProjectReminder Phase 4+
-- Changes: Updated schema to match production D1 database
