"""
Database function tests - Direct testing of database.py functions
"""

import pytest
from datetime import datetime, timezone
import uuid

from server import database as db


def test_create_reminder_returns_id(test_db):
    """Verify create_reminder returns the reminder ID using db primitives."""
    reminder_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    reminder_data = {
        'id': reminder_id,
        'text': 'Test reminder for ID check',
        'priority': 'chill',
        'status': 'pending',
        'created_at': now,
        'updated_at': now
    }

    # Build INSERT query
    fields = list(reminder_data.keys())
    placeholders = ", ".join(["?"] * len(fields))
    field_names = ", ".join(fields)
    values = tuple(reminder_data[field] for field in fields)
    query = f"INSERT INTO reminders ({field_names}) VALUES ({placeholders})"

    # Insert directly
    db.db_execute(query, values, db_path=test_db)

    # Verify reminder was created using db_query
    results = db.db_query("SELECT * FROM reminders WHERE id = ?", (reminder_id,), db_path=test_db)
    assert len(results) == 1
    assert results[0]['id'] == reminder_id
    assert results[0]['text'] == 'Test reminder for ID check'


def test_get_reminder_by_id(test_db):
    """Test fetching a reminder by ID using db_query."""
    reminder_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # Create reminder directly
    db.db_execute(
        """INSERT INTO reminders (id, text, priority, category, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (reminder_id, 'Fetch test reminder', 'important', 'Work', 'pending', now, now),
        db_path=test_db
    )

    # Fetch by ID
    results = db.db_query("SELECT * FROM reminders WHERE id = ?", (reminder_id,), db_path=test_db)

    assert len(results) == 1
    result = results[0]
    assert result['id'] == reminder_id
    assert result['text'] == 'Fetch test reminder'
    assert result['priority'] == 'important'
    assert result['category'] == 'Work'
    assert result['status'] == 'pending'


def test_get_reminder_not_found(test_db):
    """Test fetching with invalid ID returns empty results."""
    non_existent_id = str(uuid.uuid4())

    results = db.db_query("SELECT * FROM reminders WHERE id = ?", (non_existent_id,), db_path=test_db)

    assert len(results) == 0


def test_update_reminder(test_db):
    """Test updating reminder fields using db_execute."""
    reminder_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # Create initial reminder
    db.db_execute(
        """INSERT INTO reminders (id, text, priority, category, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (reminder_id, 'Original text', 'chill', 'Personal', 'pending', now, now),
        db_path=test_db
    )

    # Update multiple fields
    updated_at = datetime.now(timezone.utc).isoformat()
    affected = db.db_execute(
        """UPDATE reminders
           SET text = ?, priority = ?, status = ?, updated_at = ?
           WHERE id = ?""",
        ('Updated text', 'urgent', 'completed', updated_at, reminder_id),
        db_path=test_db
    )

    assert affected == 1

    # Verify updates
    results = db.db_query("SELECT * FROM reminders WHERE id = ?", (reminder_id,), db_path=test_db)
    updated = results[0]
    assert updated['text'] == 'Updated text'
    assert updated['priority'] == 'urgent'
    assert updated['status'] == 'completed'
    assert updated['category'] == 'Personal'  # Unchanged field


def test_delete_reminder(test_db):
    """Test deleting a reminder using db_execute."""
    reminder_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # Create reminder
    db.db_execute(
        """INSERT INTO reminders (id, text, priority, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (reminder_id, 'Reminder to be deleted', 'chill', 'pending', now, now),
        db_path=test_db
    )

    # Verify it exists
    results = db.db_query("SELECT * FROM reminders WHERE id = ?", (reminder_id,), db_path=test_db)
    assert len(results) == 1

    # Delete
    affected = db.db_execute("DELETE FROM reminders WHERE id = ?", (reminder_id,), db_path=test_db)
    assert affected == 1

    # Verify deletion
    results = db.db_query("SELECT * FROM reminders WHERE id = ?", (reminder_id,), db_path=test_db)
    assert len(results) == 0

    # Delete non-existent reminder should return 0 affected rows
    affected_again = db.db_execute("DELETE FROM reminders WHERE id = ?", (reminder_id,), db_path=test_db)
    assert affected_again == 0


def test_count_reminders_with_filters(test_db):
    """Test counting reminders with status/category/priority filters using db_query."""
    now = datetime.now(timezone.utc).isoformat()

    # Create multiple reminders with different attributes
    reminders = [
        (str(uuid.uuid4()), 'R1', 'chill', 'Personal', 'pending', now, now),
        (str(uuid.uuid4()), 'R2', 'important', 'Work', 'pending', now, now),
        (str(uuid.uuid4()), 'R3', 'urgent', 'Personal', 'completed', now, now),
        (str(uuid.uuid4()), 'R4', 'chill', 'Work', 'pending', now, now),
        (str(uuid.uuid4()), 'R5', 'important', 'Personal', 'completed', now, now),
    ]

    for reminder in reminders:
        db.db_execute(
            """INSERT INTO reminders (id, text, priority, category, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            reminder,
            db_path=test_db
        )

    # Test total count (no filters)
    total_results = db.db_query("SELECT COUNT(*) as count FROM reminders", db_path=test_db)
    assert total_results[0]['count'] == 5

    # Test status filter
    pending_results = db.db_query(
        "SELECT COUNT(*) as count FROM reminders WHERE status = ?",
        ('pending',),
        db_path=test_db
    )
    assert pending_results[0]['count'] == 3

    completed_results = db.db_query(
        "SELECT COUNT(*) as count FROM reminders WHERE status = ?",
        ('completed',),
        db_path=test_db
    )
    assert completed_results[0]['count'] == 2

    # Test category filter
    personal_results = db.db_query(
        "SELECT COUNT(*) as count FROM reminders WHERE category = ?",
        ('Personal',),
        db_path=test_db
    )
    assert personal_results[0]['count'] == 3

    work_results = db.db_query(
        "SELECT COUNT(*) as count FROM reminders WHERE category = ?",
        ('Work',),
        db_path=test_db
    )
    assert work_results[0]['count'] == 2

    # Test priority filter
    chill_results = db.db_query(
        "SELECT COUNT(*) as count FROM reminders WHERE priority = ?",
        ('chill',),
        db_path=test_db
    )
    assert chill_results[0]['count'] == 2

    important_results = db.db_query(
        "SELECT COUNT(*) as count FROM reminders WHERE priority = ?",
        ('important',),
        db_path=test_db
    )
    assert important_results[0]['count'] == 2

    urgent_results = db.db_query(
        "SELECT COUNT(*) as count FROM reminders WHERE priority = ?",
        ('urgent',),
        db_path=test_db
    )
    assert urgent_results[0]['count'] == 1

    # Test combined filters
    pending_personal_results = db.db_query(
        "SELECT COUNT(*) as count FROM reminders WHERE status = ? AND category = ?",
        ('pending', 'Personal'),
        db_path=test_db
    )
    assert pending_personal_results[0]['count'] == 1

    pending_work_results = db.db_query(
        "SELECT COUNT(*) as count FROM reminders WHERE status = ? AND category = ?",
        ('pending', 'Work'),
        db_path=test_db
    )
    assert pending_work_results[0]['count'] == 2

    completed_important_results = db.db_query(
        "SELECT COUNT(*) as count FROM reminders WHERE status = ? AND priority = ?",
        ('completed', 'important'),
        db_path=test_db
    )
    assert completed_important_results[0]['count'] == 1

    # Test filter with no matches
    no_match_results = db.db_query(
        "SELECT COUNT(*) as count FROM reminders WHERE status = ?",
        ('snoozed',),
        db_path=test_db
    )
    assert no_match_results[0]['count'] == 0
