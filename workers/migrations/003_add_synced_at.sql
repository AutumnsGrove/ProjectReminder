-- Migration: 003_add_synced_at.sql
-- Purpose: Add synced_at column for Phase 5 sync logic
-- Created: November 3, 2025
-- Phase: 5 (Sync Logic Implementation)
--
-- Changes:
--   - Add synced_at timestamp column for tracking last cloud sync
--
-- Usage:
--   wrangler d1 migrations apply reminders-db --remote  # Apply to production

-- =============================================================================
-- Add synced_at Column
-- =============================================================================

ALTER TABLE reminders ADD COLUMN synced_at TEXT;

-- Create index for sync queries (get changes since last sync)
CREATE INDEX idx_reminders_synced_at ON reminders(synced_at);

-- =============================================================================
-- Migration Complete
-- =============================================================================
-- Schema version: 003
-- Compatible with: ProjectReminder Phase 5+
-- Changes: Added synced_at for sync logic
