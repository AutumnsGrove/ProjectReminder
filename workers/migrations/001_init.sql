-- Migration: 001_init.sql
-- Purpose: Initialize reminders database with 5-level priority system for Cloudflare D1
-- Created: November 2, 2025
-- Phase: 4.2 (D1 Migration Planning - Research Phase)
-- Subagent: Subagent 6 - D1 Migration Planning
--
-- This migration matches the local SQLite schema in server/database.py exactly.
-- D1 uses SQLite syntax, so schema is 1:1 compatible with local database.
--
-- Schema Features:
--   - 5-level priority system (someday, chill, important, urgent, waiting)
--   - Location fields for Phase 6 (location-based reminders)
--   - Recurrence patterns table for Phase 7 (recurring reminders)
--   - Performance indexes for common queries
--   - Seed data with sample reminders for each priority level
--
-- Usage:
--   wrangler d1 migrations apply reminders-db --local  # Test locally
--   wrangler d1 migrations apply reminders-db          # Deploy to production

-- =============================================================================
-- Drop Existing Tables (Safe Re-run)
-- =============================================================================

DROP TABLE IF EXISTS recurrence_patterns;
DROP TABLE IF EXISTS reminders;

-- =============================================================================
-- Create Reminders Table
-- =============================================================================

CREATE TABLE reminders (
    -- Identification
    id TEXT PRIMARY KEY,

    -- Core Content
    text TEXT NOT NULL,

    -- Timing
    due_date TEXT,
    due_time TEXT,
    time_required INTEGER DEFAULT 0,

    -- Location (Phase 6: Location-based reminders)
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

    -- Recurrence (Phase 7: Recurring reminders)
    recurrence_id TEXT,

    -- Metadata
    source TEXT DEFAULT 'manual',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    synced_at TEXT
);

-- =============================================================================
-- Create Recurrence Patterns Table (Phase 7)
-- =============================================================================
-- Note: This table is defined now for future use but won't be actively used
-- until Phase 7 when recurring reminders are implemented.

CREATE TABLE recurrence_patterns (
    -- Identification
    id TEXT PRIMARY KEY,

    -- Pattern Definition
    frequency TEXT CHECK(frequency IN ('daily', 'weekly', 'monthly', 'yearly')),
    interval INTEGER DEFAULT 1,

    -- Constraints
    days_of_week TEXT,
    day_of_month INTEGER,
    month_of_year INTEGER,

    -- End Conditions
    end_date TEXT,
    end_count INTEGER,

    -- Metadata
    created_at TEXT NOT NULL
);

-- =============================================================================
-- Create Performance Indexes
-- =============================================================================

-- Index for date-based queries (Today, This Week, Future views)
CREATE INDEX idx_reminders_due_date ON reminders(due_date);

-- Index for status filtering (pending vs completed)
CREATE INDEX idx_reminders_status ON reminders(status);

-- Index for category filtering
CREATE INDEX idx_reminders_category ON reminders(category);

-- Index for priority filtering (someday, chill, important, urgent, waiting)
CREATE INDEX idx_reminders_priority ON reminders(priority);

-- Composite index for location-based queries (Phase 6)
CREATE INDEX idx_reminders_location ON reminders(location_lat, location_lng);

-- =============================================================================
-- Seed Data - Sample Reminders
-- =============================================================================
-- Insert sample reminders demonstrating each priority level and key features.
-- These can be deleted by users once they start creating their own reminders.

INSERT INTO reminders (id, text, category, priority, status, created_at, updated_at, notes) VALUES
    -- Welcome reminder (chill priority)
    ('seed-00000000-0000-0000-0000-000000000001',
     'Welcome to Voice Reminders! Delete this sample when ready.',
     'Personal',
     'chill',
     'pending',
     datetime('now'),
     datetime('now'),
     'This is a sample reminder. Tap the checkmark to complete it!'),

    -- Urgent priority example
    ('seed-00000000-0000-0000-0000-000000000002',
     'Review urgent client proposal',
     'Work',
     'urgent',
     'pending',
     datetime('now'),
     datetime('now'),
     'Demonstrates URGENT priority - highest importance, time-sensitive'),

    -- Important priority example
    ('seed-00000000-0000-0000-0000-000000000003',
     'Schedule dentist appointment',
     'Health',
     'important',
     'pending',
     datetime('now'),
     datetime('now'),
     'Demonstrates IMPORTANT priority - high priority, should be done soon'),

    -- Chill priority example
    ('seed-00000000-0000-0000-0000-000000000004',
     'Call mom to catch up',
     'Calls',
     'chill',
     'pending',
     datetime('now'),
     datetime('now'),
     'Demonstrates CHILL priority - default, get to it when you can'),

    -- Someday priority example
    ('seed-00000000-0000-0000-0000-000000000005',
     'Research vacation destinations',
     'Personal',
     'someday',
     'pending',
     datetime('now'),
     datetime('now'),
     'Demonstrates SOMEDAY priority - aspirational, no pressure'),

    -- Waiting priority example
    ('seed-00000000-0000-0000-0000-000000000006',
     'Follow up on insurance claim',
     'Personal',
     'waiting',
     'pending',
     datetime('now'),
     datetime('now'),
     'Demonstrates WAITING priority - blocked, waiting on someone else');

-- =============================================================================
-- Migration Complete
-- =============================================================================
-- Schema version: 001
-- Compatible with: ProjectReminder Phase 4+
-- Next migration: TBD (sync metadata, conflict resolution fields)
