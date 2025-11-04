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


def _get_default_db_path(override: Optional[str] = None) -> str:
    """
    Get the database path, with optional override.

    This allows runtime evaluation of DB_PATH instead of binding at import time.
    Pass override=None to use the current DB_PATH value.

    Args:
        override: Optional database path override

    Returns:
        Database path to use
    """
    return override if override is not None else str(DB_PATH)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Get database connection with proper configuration.

    Args:
        db_path: Path to SQLite database file

    Returns:
        Configured SQLite connection
    """
    db_path = _get_default_db_path(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def init_db(db_path: Optional[str] = None, force: bool = False) -> None:
    """
    Initialize database with schema.

    Args:
        db_path: Path to SQLite database file
        force: If True, drop existing tables and recreate
    """
    db_path = _get_default_db_path(db_path)
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


def db_query(query: str, params: Tuple = (), db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Execute SELECT query and return results as list of dictionaries.

    Args:
        query: SQL SELECT statement
        params: Query parameters (use ? placeholders)
        db_path: Database path

    Returns:
        List of rows as dictionaries
    """
    db_path = _get_default_db_path(db_path)
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


def db_execute(query: str, params: Tuple = (), db_path: Optional[str] = None) -> int:
    """
    Execute INSERT/UPDATE/DELETE and return affected row count.

    Args:
        query: SQL statement
        params: Query parameters (use ? placeholders)
        db_path: Database path

    Returns:
        Number of affected rows
    """
    db_path = _get_default_db_path(db_path)
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


def db_insert(query: str, params: Tuple = (), db_path: Optional[str] = None) -> int:
    """
    Execute INSERT and return the last inserted row ID.

    Args:
        query: SQL INSERT statement
        params: Query parameters
        db_path: Database path

    Returns:
        Last inserted row ID (for INTEGER PRIMARY KEY)
    """
    db_path = _get_default_db_path(db_path)
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

def db_exists(db_path: Optional[str] = None) -> bool:
    """Check if database file exists."""
    db_path = _get_default_db_path(db_path)
    return os.path.exists(db_path)


def get_table_names(db_path: Optional[str] = None) -> List[str]:
    """Get list of all table names."""
    db_path = _get_default_db_path(db_path)
    results = db_query(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
        db_path=db_path
    )
    return [row['name'] for row in results]


def get_table_schema(table_name: str, db_path: Optional[str] = None) -> str:
    """Get CREATE statement for table."""
    db_path = _get_default_db_path(db_path)
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
# Recurrence Pattern Operations (Phase 7)
# =============================================================================

def create_recurrence_pattern(
    pattern_id: str,
    frequency: str,
    interval: int = 1,
    days_of_week: Optional[str] = None,
    day_of_month: Optional[int] = None,
    month_of_year: Optional[int] = None,
    end_date: Optional[str] = None,
    end_count: Optional[int] = None,
    db_path: Optional[str] = None
) -> str:
    """
    Create a new recurrence pattern.

    Args:
        pattern_id: UUID for the pattern
        frequency: 'daily', 'weekly', 'monthly', or 'yearly'
        interval: Repeat every N days/weeks/months (default: 1)
        days_of_week: Comma-separated day numbers for weekly (0=Mon, 6=Sun)
        day_of_month: Day of month for monthly recurrence (1-31)
        month_of_year: Month for yearly recurrence (1-12)
        end_date: ISO 8601 date when pattern ends
        end_count: Number of occurrences before stopping
        db_path: Path to database

    Returns:
        Pattern ID
    """
    db_path = _get_default_db_path(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        now = datetime.now(timezone.utc).isoformat()

        cursor.execute("""
            INSERT INTO recurrence_patterns (
                id, frequency, interval,
                days_of_week, day_of_month, month_of_year,
                end_date, end_count,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pattern_id, frequency, interval,
            days_of_week, day_of_month, month_of_year,
            end_date, end_count,
            now
        ))

        conn.commit()
        return pattern_id
    except sqlite3.Error as e:
        conn.rollback()
        raise Exception(f"Failed to create recurrence pattern: {e}")
    finally:
        conn.close()


def get_recurrence_pattern(pattern_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get recurrence pattern by ID.

    Args:
        pattern_id: Pattern UUID
        db_path: Path to database

    Returns:
        Pattern dictionary or None if not found
    """
    db_path = _get_default_db_path(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT * FROM recurrence_patterns
            WHERE id = ?
        """, (pattern_id,))

        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_recurrence_pattern(
    pattern_id: str,
    frequency: Optional[str] = None,
    interval: Optional[int] = None,
    days_of_week: Optional[str] = None,
    day_of_month: Optional[int] = None,
    month_of_year: Optional[int] = None,
    end_date: Optional[str] = None,
    end_count: Optional[int] = None,
    db_path: Optional[str] = None
) -> bool:
    """
    Update recurrence pattern.

    Args:
        pattern_id: Pattern UUID
        frequency: New frequency
        interval: New interval
        days_of_week: New days of week
        day_of_month: New day of month
        month_of_year: New month of year
        end_date: New end date
        end_count: New end count
        db_path: Path to database

    Returns:
        True if updated, False if not found
    """
    db_path = _get_default_db_path(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        # Build dynamic update query based on provided fields
        updates = []
        params = []

        if frequency is not None:
            updates.append("frequency = ?")
            params.append(frequency)
        if interval is not None:
            updates.append("interval = ?")
            params.append(interval)
        if days_of_week is not None:
            updates.append("days_of_week = ?")
            params.append(days_of_week)
        if day_of_month is not None:
            updates.append("day_of_month = ?")
            params.append(day_of_month)
        if month_of_year is not None:
            updates.append("month_of_year = ?")
            params.append(month_of_year)
        if end_date is not None:
            updates.append("end_date = ?")
            params.append(end_date)
        if end_count is not None:
            updates.append("end_count = ?")
            params.append(end_count)

        if not updates:
            return False  # Nothing to update

        params.append(pattern_id)
        query = f"""
            UPDATE recurrence_patterns
            SET {', '.join(updates)}
            WHERE id = ?
        """

        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        conn.rollback()
        raise Exception(f"Failed to update recurrence pattern: {e}")
    finally:
        conn.close()


def delete_recurrence_pattern(pattern_id: str, db_path: Optional[str] = None) -> bool:
    """
    Delete recurrence pattern and unlink from reminders.

    Args:
        pattern_id: Pattern UUID
        db_path: Path to database

    Returns:
        True if deleted, False if not found
    """
    db_path = _get_default_db_path(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        # First unlink any reminders using this pattern
        cursor.execute("""
            UPDATE reminders
            SET recurrence_id = NULL
            WHERE recurrence_id = ?
        """, (pattern_id,))

        # Delete the pattern
        cursor.execute("""
            DELETE FROM recurrence_patterns
            WHERE id = ?
        """, (pattern_id,))

        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        conn.rollback()
        raise Exception(f"Failed to delete recurrence pattern: {e}")
    finally:
        conn.close()


def generate_recurrence_instances(
    base_reminder: Dict[str, Any],
    pattern: Dict[str, Any],
    horizon_days: int = 90,
    db_path: Optional[str] = None
) -> List[str]:
    """
    Generate recurring reminder instances based on pattern.

    Args:
        base_reminder: The template reminder with all fields
        pattern: Recurrence pattern dictionary
        horizon_days: How many days ahead to generate instances
        db_path: Path to database

    Returns:
        List of generated reminder IDs
    """
    from datetime import date, timedelta
    import uuid

    db_path = _get_default_db_path(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    generated_ids = []

    try:
        frequency = pattern['frequency']
        interval = pattern.get('interval', 1)
        end_date_str = pattern.get('end_date')
        end_count = pattern.get('end_count')

        # Parse start date from base reminder's due_date or use today
        start_date_str = base_reminder.get('due_date')
        if start_date_str:
            start_date = date.fromisoformat(start_date_str)
        else:
            start_date = date.today()

        # Calculate horizon end date
        horizon_end = date.today() + timedelta(days=horizon_days)

        # Parse pattern end date if provided
        pattern_end = None
        if end_date_str:
            pattern_end = date.fromisoformat(end_date_str)

        # Determine actual end date (whichever comes first)
        end_date = min(horizon_end, pattern_end) if pattern_end else horizon_end

        # Generate instances
        current_date = start_date
        instance_count = 0
        now = datetime.now(timezone.utc).isoformat()

        while current_date <= end_date:
            # Check end_count limit
            if end_count and instance_count >= end_count:
                break

            # For weekly recurrence, check if current day matches pattern
            if frequency == 'weekly':
                days_of_week = pattern.get('days_of_week')
                if days_of_week:
                    # days_of_week is comma-separated: "0,2,4" for Mon, Wed, Fri
                    allowed_days = [int(d) for d in days_of_week.split(',')]
                    if current_date.weekday() not in allowed_days:
                        current_date += timedelta(days=1)
                        continue

            # For monthly recurrence, check day of month
            if frequency == 'monthly':
                day_of_month = pattern.get('day_of_month')
                if day_of_month and current_date.day != day_of_month:
                    current_date += timedelta(days=1)
                    continue

            # Create instance
            instance_id = str(uuid.uuid4())
            instance_data = base_reminder.copy()
            instance_data['id'] = instance_id
            instance_data['due_date'] = current_date.isoformat()
            instance_data['created_at'] = now
            instance_data['updated_at'] = now

            # Insert instance
            cursor.execute("""
                INSERT INTO reminders (
                    id, text, due_date, due_time, time_required,
                    location_name, location_address, location_lat, location_lng, location_radius,
                    priority, category, status, completed_at, snoozed_until,
                    recurrence_id, source, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                instance_data['id'],
                instance_data['text'],
                instance_data['due_date'],
                instance_data.get('due_time'),
                instance_data.get('time_required', False),
                instance_data.get('location_name'),
                instance_data.get('location_address'),
                instance_data.get('location_lat'),
                instance_data.get('location_lng'),
                instance_data.get('location_radius', 100),
                instance_data.get('priority', 'chill'),
                instance_data.get('category'),
                instance_data.get('status', 'pending'),
                instance_data.get('completed_at'),
                instance_data.get('snoozed_until'),
                instance_data.get('recurrence_id'),
                instance_data.get('source', 'manual'),
                instance_data['created_at'],
                instance_data['updated_at']
            ))

            generated_ids.append(instance_id)
            instance_count += 1

            # Advance to next occurrence
            if frequency == 'daily':
                current_date += timedelta(days=interval)
            elif frequency == 'weekly':
                # For weekly, advance day by day to check each day
                current_date += timedelta(days=1)
                # After checking 7 days, skip ahead by (interval-1) weeks
                if current_date.weekday() == start_date.weekday():
                    if interval > 1:
                        current_date += timedelta(weeks=interval - 1)
            elif frequency == 'monthly':
                # Monthly: advance month by interval
                month = current_date.month + interval
                year = current_date.year
                while month > 12:
                    month -= 12
                    year += 1
                # Handle day overflow (e.g., Jan 31 -> Feb 28)
                try:
                    current_date = date(year, month, current_date.day)
                except ValueError:
                    # Day doesn't exist in target month, use last day
                    import calendar
                    last_day = calendar.monthrange(year, month)[1]
                    current_date = date(year, month, last_day)
            elif frequency == 'yearly':
                current_date = date(current_date.year + interval, current_date.month, current_date.day)

        conn.commit()
        return generated_ids
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to generate recurrence instances: {e}")
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
