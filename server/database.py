"""
database.py - Database interface module

All database operations and SQL statements are isolated in this module.
Application code should never write SQL directly.
"""

import sqlite3
import os
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timezone
from pathlib import Path


# Database configuration
DB_PATH = Path(__file__).parent.parent / "reminders.db"


def get_connection(db_path: str = str(DB_PATH)) -> sqlite3.Connection:
    """
    Get database connection with proper configuration.

    Args:
        db_path: Path to SQLite database file

    Returns:
        Configured SQLite connection
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def init_db(db_path: str = str(DB_PATH), force: bool = False) -> None:
    """
    Initialize database with schema.

    Args:
        db_path: Path to SQLite database file
        force: If True, drop existing tables and recreate
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        if force:
            # Drop existing tables
            cursor.execute("DROP TABLE IF EXISTS reminders")
            cursor.execute("DROP TABLE IF EXISTS recurrence_patterns")

        # Create reminders table
        cursor.execute("""
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
            )
        """)

        # Create recurrence_patterns table (Phase 7)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recurrence_patterns (
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
            )
        """)

        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_reminders_due_date ON reminders(due_date)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_reminders_category ON reminders(category)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_reminders_priority ON reminders(priority)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_reminders_location ON reminders(location_lat, location_lng)
        """)

        conn.commit()
        print(f"SUCCESS: Database initialized successfully at {db_path}")

    except sqlite3.Error as e:
        conn.rollback()
        raise Exception(f"Database initialization failed: {e}")
    finally:
        conn.close()


def db_query(query: str, params: Tuple = (), db_path: str = str(DB_PATH)) -> List[Dict[str, Any]]:
    """
    Execute SELECT query and return results as list of dictionaries.

    Args:
        query: SQL SELECT statement
        params: Query parameters (use ? placeholders)
        db_path: Database path

    Returns:
        List of rows as dictionaries
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        raise Exception(f"Query failed: {e}")
    finally:
        conn.close()


def db_execute(query: str, params: Tuple = (), db_path: str = str(DB_PATH)) -> int:
    """
    Execute INSERT/UPDATE/DELETE and return affected row count.

    Args:
        query: SQL statement
        params: Query parameters (use ? placeholders)
        db_path: Database path

    Returns:
        Number of affected rows
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount
    except sqlite3.Error as e:
        conn.rollback()
        raise Exception(f"Execute failed: {e}")
    finally:
        conn.close()


def db_insert(query: str, params: Tuple = (), db_path: str = str(DB_PATH)) -> int:
    """
    Execute INSERT and return the last inserted row ID.

    Args:
        query: SQL INSERT statement
        params: Query parameters
        db_path: Database path

    Returns:
        Last inserted row ID (for INTEGER PRIMARY KEY)
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        conn.rollback()
        raise Exception(f"Insert failed: {e}")
    finally:
        conn.close()


# =============================================================================
# Domain-Specific Functions (Application Interface)
# =============================================================================

def get_reminder_by_id(reminder_id: str) -> Optional[Dict[str, Any]]:
    """Get reminder by ID."""
    results = db_query(
        "SELECT * FROM reminders WHERE id = ?",
        (reminder_id,)
    )
    return results[0] if results else None


def get_all_reminders(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Get all reminders with optional filters and pagination.

    Args:
        status: Filter by status ('pending', 'completed', 'snoozed')
        category: Filter by category
        priority: Filter by priority ('chill', 'important', 'urgent')
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of reminder dictionaries
    """
    query = "SELECT * FROM reminders WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)

    if category:
        query += " AND category = ?"
        params.append(category)

    if priority:
        query += " AND priority = ?"
        params.append(priority)

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    return db_query(query, tuple(params))


def create_reminder(reminder_data: Dict[str, Any]) -> str:
    """
    Create new reminder.

    Args:
        reminder_data: Dictionary with reminder fields

    Returns:
        Reminder ID (UUID)
    """
    # Build dynamic INSERT based on provided fields
    fields = list(reminder_data.keys())
    placeholders = ", ".join(["?"] * len(fields))
    field_names = ", ".join(fields)
    values = tuple(reminder_data[field] for field in fields)

    query = f"INSERT INTO reminders ({field_names}) VALUES ({placeholders})"
    db_execute(query, values)

    # Return the ID from reminder_data (it's a TEXT PRIMARY KEY)
    return reminder_data['id']


def update_reminder(reminder_id: str, update_data: Dict[str, Any]) -> bool:
    """
    Update reminder fields.

    Args:
        reminder_id: Reminder ID to update
        update_data: Dictionary of fields to update

    Returns:
        True if reminder was updated
    """
    if not update_data:
        return False

    # Build dynamic UPDATE
    set_clause = ", ".join([f"{field} = ?" for field in update_data.keys()])
    values = list(update_data.values())
    values.append(reminder_id)

    query = f"UPDATE reminders SET {set_clause} WHERE id = ?"
    affected = db_execute(query, tuple(values))

    return affected > 0


def delete_reminder(reminder_id: str) -> bool:
    """Delete reminder by ID."""
    affected = db_execute(
        "DELETE FROM reminders WHERE id = ?",
        (reminder_id,)
    )
    return affected > 0


def count_reminders(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None
) -> int:
    """
    Count reminders with optional filters.

    Args:
        status: Filter by status
        category: Filter by category
        priority: Filter by priority

    Returns:
        Count of matching reminders
    """
    query = "SELECT COUNT(*) as count FROM reminders WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)

    if category:
        query += " AND category = ?"
        params.append(category)

    if priority:
        query += " AND priority = ?"
        params.append(priority)

    results = db_query(query, tuple(params))
    return results[0]['count'] if results else 0


# =============================================================================
# Seed Data
# =============================================================================

def seed_default_categories() -> None:
    """
    Create sample reminders with default categories.
    This is for demonstration purposes only.
    """
    default_categories = [
        "Personal",
        "Work",
        "Errands",
        "Home",
        "Health",
        "Calls",
        "Shopping",
        "Projects"
    ]

    print("Default categories available:")
    for cat in default_categories:
        print(f"  - {cat}")


# =============================================================================
# Utility Functions
# =============================================================================

def db_exists(db_path: str = str(DB_PATH)) -> bool:
    """Check if database file exists."""
    return os.path.exists(db_path)


def get_table_names(db_path: str = str(DB_PATH)) -> List[str]:
    """Get list of all table names."""
    results = db_query(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
        db_path=db_path
    )
    return [row['name'] for row in results]


def get_table_schema(table_name: str, db_path: str = str(DB_PATH)) -> str:
    """Get CREATE statement for table."""
    results = db_query(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
        db_path=db_path
    )
    return results[0]['sql'] if results else ""


def count_rows(table_name: str) -> int:
    """Count rows in table."""
    results = db_query(f"SELECT COUNT(*) as count FROM {table_name}")
    return results[0]['count']


# =============================================================================
# Sync Functions (Phase 5)
# =============================================================================

def get_changes_since(last_sync: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all reminders changed since last_sync timestamp.

    Args:
        last_sync: ISO 8601 timestamp of last sync (None = all reminders)

    Returns:
        List of reminder dictionaries changed since last_sync
    """
    if last_sync:
        return db_query(
            "SELECT * FROM reminders WHERE updated_at > ? ORDER BY updated_at ASC",
            (last_sync,)
        )
    else:
        # First sync - return all reminders
        return db_query("SELECT * FROM reminders ORDER BY updated_at ASC")


def apply_sync_change(change_id: str, action: str, data: Optional[Dict[str, Any]]) -> bool:
    """
    Apply a single sync change to local database.

    Args:
        change_id: Reminder UUID
        action: 'create', 'update', or 'delete'
        data: Reminder data (None for delete)

    Returns:
        True if change was applied successfully
    """
    if action == "delete":
        return delete_reminder(change_id)

    elif action == "create":
        if not data:
            return False
        create_reminder(data)
        return True

    elif action == "update":
        if not data:
            return False
        return update_reminder(change_id, data)

    return False


def update_synced_at(reminder_id: str, synced_at: str) -> bool:
    """
    Update synced_at timestamp for a reminder.

    Args:
        reminder_id: Reminder UUID
        synced_at: ISO 8601 timestamp

    Returns:
        True if updated successfully
    """
    affected = db_execute(
        "UPDATE reminders SET synced_at = ? WHERE id = ?",
        (synced_at, reminder_id)
    )
    return affected > 0


def batch_update_synced_at(reminder_ids: List[str], synced_at: str) -> int:
    """
    Update synced_at timestamp for multiple reminders.

    Args:
        reminder_ids: List of reminder UUIDs
        synced_at: ISO 8601 timestamp

    Returns:
        Number of reminders updated
    """
    if not reminder_ids:
        return 0

    conn = get_connection()
    cursor = conn.cursor()

    try:
        placeholders = ", ".join(["?"] * len(reminder_ids))
        query = f"UPDATE reminders SET synced_at = ? WHERE id IN ({placeholders})"
        params = [synced_at] + reminder_ids

        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount
    except sqlite3.Error as e:
        conn.rollback()
        raise Exception(f"Batch update failed: {e}")
    finally:
        conn.close()


# =============================================================================
# Initialization Script
# =============================================================================

if __name__ == "__main__":
    """
    Run this script directly to initialize the database.

    Usage:
        python server/database.py           # Initialize database
        python server/database.py --force   # Force recreate tables
    """
    import sys

    force = "--force" in sys.argv

    if force:
        print("WARNING: Force mode: Dropping and recreating all tables...")

    init_db(force=force)
    seed_default_categories()

    # Show database info
    print(f"\n=== Database Info:")
    print(f"   Path: {DB_PATH}")
    print(f"   Tables: {', '.join(get_table_names())}")
    print(f"   Reminder count: {count_rows('reminders')}")

    print("\nSUCCESS: Database ready for use!")
