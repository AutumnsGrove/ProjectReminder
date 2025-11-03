"""
Pytest configuration and fixtures for testing
"""

import pytest
import tempfile
import os
from pathlib import Path
from fastapi.testclient import TestClient

# Import application modules
from server import database as db
from server.main import app
from server import config


@pytest.fixture(scope="function")
def test_db():
    """
    Create a temporary test database for each test.
    Automatically cleaned up after test completes.
    """
    # Create temporary database file
    temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
    temp_db_path = temp_db.name
    temp_db.close()

    # Initialize test database
    db.init_db(db_path=temp_db_path, force=True)

    yield temp_db_path

    # Cleanup: Remove temporary database
    try:
        os.unlink(temp_db_path)
    except OSError:
        pass


@pytest.fixture(scope="function")
def client():
    """
    FastAPI test client with authentication.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def test_token():
    """
    Valid API token for authentication.
    """
    return config.API_TOKEN


@pytest.fixture(scope="function")
def auth_headers():
    """
    Valid authentication headers for API requests.
    """
    return {
        "Authorization": f"Bearer {config.API_TOKEN}",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="function")
def invalid_auth_headers():
    """
    Invalid authentication headers for testing auth failures.
    """
    return {
        "Authorization": "Bearer invalid_token_12345",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="function")
def sample_reminder_data():
    """
    Sample reminder data for testing create operations.
    """
    return {
        "text": "Test reminder",
        "priority": "chill",
        "category": "Personal",
        "due_date": "2025-11-15",
        "due_time": "14:30:00",
        "time_required": False,
        "location_text": "Home"
    }


@pytest.fixture(scope="function")
def sample_reminder_minimal():
    """
    Minimal reminder data (only required fields).
    """
    return {
        "text": "Minimal test reminder",
        "priority": "chill"
    }


@pytest.fixture(scope="function")
def created_reminder(client, auth_headers, sample_reminder_data):
    """
    Create a reminder and return its data.
    Useful for testing update/delete operations.
    """
    response = client.post(
        "/api/reminders",
        headers=auth_headers,
        json=sample_reminder_data
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture(scope="function")
def multiple_reminders(client, auth_headers):
    """
    Create multiple reminders for testing list operations.
    """
    reminders_data = [
        {"text": "Reminder 1", "priority": "chill", "category": "Personal"},
        {"text": "Reminder 2", "priority": "important", "category": "Work"},
        {"text": "Reminder 3", "priority": "urgent", "category": "Health"},
        {"text": "Reminder 4", "priority": "chill", "status": "completed"},
        {"text": "Reminder 5", "priority": "important", "due_date": "2025-11-20"},
    ]

    created = []
    for data in reminders_data:
        response = client.post(
            "/api/reminders",
            headers=auth_headers,
            json=data
        )
        assert response.status_code == 201
        created.append(response.json())

    return created
