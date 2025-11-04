"""
Comprehensive sync logic tests
Tests sync conflict resolution, change queue management, and sync state transitions
"""

import pytest
from datetime import datetime, timezone, timedelta
import time


# =============================================================================
# Helper Functions
# =============================================================================

def get_iso_timestamp(offset_seconds: int = 0) -> str:
    """Generate ISO 8601 timestamp with optional offset"""
    dt = datetime.now(timezone.utc)
    if offset_seconds:
        dt = dt + timedelta(seconds=offset_seconds)
    return dt.isoformat()


def create_reminder_with_timestamp(client, auth_headers, text: str, updated_at: str = None):
    """
    Create a reminder and optionally override its updated_at timestamp.
    Returns the created reminder data.
    """
    reminder_data = {
        "text": text,
        "priority": "chill",
        "category": "Test"
    }

    response = client.post(
        "/api/reminders",
        headers=auth_headers,
        json=reminder_data
    )
    assert response.status_code == 201
    reminder = response.json()

    # If custom timestamp provided, manually update in database
    if updated_at:
        from server import database as db
        db.db_execute(
            "UPDATE reminders SET updated_at = ? WHERE id = ?",
            (updated_at, reminder["id"])
        )
        # Fetch updated reminder
        updated_reminder = db.get_reminder_by_id(reminder["id"])
        return dict(updated_reminder)

    return reminder


# =============================================================================
# Conflict Resolution Tests
# =============================================================================

@pytest.mark.sync
def test_last_write_wins_client_newer(client, auth_headers):
    """Test conflict resolution when client has newer timestamp (client wins)"""
    # Create reminder on server
    server_time = get_iso_timestamp(-10)  # 10 seconds ago
    reminder = create_reminder_with_timestamp(client, auth_headers, "Test reminder", server_time)

    # Client has newer version
    client_time = get_iso_timestamp()  # Now
    sync_request = {
        "client_id": "test-device-123",
        "last_sync": server_time,
        "changes": [
            {
                "id": reminder["id"],
                "action": "update",
                "data": {
                    "text": "Updated by client",
                    "priority": "important"
                },
                "updated_at": client_time
            }
        ]
    }

    response = client.post("/api/sync", headers=auth_headers, json=sync_request)
    assert response.status_code == 200

    data = response.json()
    assert data["applied_count"] == 1
    assert len(data["conflicts"]) == 1

    # Verify conflict was resolved in favor of client
    conflict = data["conflicts"][0]
    assert conflict["id"] == reminder["id"]
    assert conflict["resolution"] == "client_wins"
    assert conflict["client_updated_at"] == client_time

    # Verify reminder was actually updated
    get_response = client.get(f"/api/reminders/{reminder['id']}", headers=auth_headers)
    updated = get_response.json()
    assert updated["text"] == "Updated by client"
    assert updated["priority"] == "important"


@pytest.mark.sync
def test_last_write_wins_server_newer(client, auth_headers):
    """Test conflict resolution when server has newer timestamp (server wins)"""
    # Create reminder on server with recent timestamp
    server_time = get_iso_timestamp()  # Now
    reminder = create_reminder_with_timestamp(client, auth_headers, "Server version", server_time)

    # Wait a tiny bit then update on server again
    time.sleep(0.01)
    update_response = client.patch(
        f"/api/reminders/{reminder['id']}",
        headers=auth_headers,
        json={"text": "Server updated version", "priority": "urgent"}
    )
    assert update_response.status_code == 200
    server_updated = update_response.json()

    # Client tries to sync with older timestamp
    client_time = get_iso_timestamp(-5)  # 5 seconds ago
    sync_request = {
        "client_id": "test-device-123",
        "last_sync": client_time,
        "changes": [
            {
                "id": reminder["id"],
                "action": "update",
                "data": {
                    "text": "Old client update",
                    "priority": "chill"
                },
                "updated_at": client_time
            }
        ]
    }

    response = client.post("/api/sync", headers=auth_headers, json=sync_request)
    assert response.status_code == 200

    data = response.json()
    # Server version wins, so change not applied
    assert data["applied_count"] == 0
    assert len(data["conflicts"]) == 1

    conflict = data["conflicts"][0]
    assert conflict["resolution"] == "server_wins"

    # Verify server version was preserved
    get_response = client.get(f"/api/reminders/{reminder['id']}", headers=auth_headers)
    current = get_response.json()
    assert current["text"] == "Server updated version"
    assert current["priority"] == "urgent"


@pytest.mark.sync
def test_sync_with_pending_local_changes(client, auth_headers):
    """Test sync correctly sends and applies pending local changes"""
    base_time = get_iso_timestamp(-30)

    # Create 3 reminders representing different local changes
    reminder1 = create_reminder_with_timestamp(client, auth_headers, "Reminder 1", base_time)
    reminder2 = create_reminder_with_timestamp(client, auth_headers, "Reminder 2", base_time)

    # Sync request with multiple pending changes
    sync_request = {
        "client_id": "test-device-123",
        "last_sync": base_time,
        "changes": [
            {
                "id": reminder1["id"],
                "action": "update",
                "data": {"text": "Updated reminder 1", "priority": "important"},
                "updated_at": get_iso_timestamp(-5)
            },
            {
                "id": reminder2["id"],
                "action": "delete",
                "data": None,
                "updated_at": get_iso_timestamp(-3)
            },
            {
                "id": "new-client-uuid-123",
                "action": "create",
                "data": {
                    "id": "new-client-uuid-123",
                    "text": "New client reminder",
                    "priority": "urgent",
                    "status": "pending",
                    "created_at": get_iso_timestamp(-1),
                    "updated_at": get_iso_timestamp(-1)
                },
                "updated_at": get_iso_timestamp(-1)
            }
        ]
    }

    response = client.post("/api/sync", headers=auth_headers, json=sync_request)
    assert response.status_code == 200

    data = response.json()
    assert data["applied_count"] == 3

    # Verify update was applied
    get1 = client.get(f"/api/reminders/{reminder1['id']}", headers=auth_headers)
    assert get1.status_code == 200
    assert get1.json()["text"] == "Updated reminder 1"

    # Verify delete was applied
    get2 = client.get(f"/api/reminders/{reminder2['id']}", headers=auth_headers)
    assert get2.status_code == 404

    # Verify create was applied
    get3 = client.get("/api/reminders/new-client-uuid-123", headers=auth_headers)
    assert get3.status_code == 200
    assert get3.json()["text"] == "New client reminder"


@pytest.mark.sync
def test_sync_detects_timestamp_collision(client, auth_headers):
    """Test handling of same timestamp on client and server"""
    collision_time = get_iso_timestamp()
    reminder = create_reminder_with_timestamp(client, auth_headers, "Original", collision_time)

    # Update server version with same timestamp (edge case)
    from server import database as db
    db.update_reminder(reminder["id"], {
        "text": "Server version",
        "updated_at": collision_time
    })

    # Client sends update with same timestamp
    sync_request = {
        "client_id": "test-device-123",
        "last_sync": get_iso_timestamp(-10),
        "changes": [
            {
                "id": reminder["id"],
                "action": "update",
                "data": {"text": "Client version", "priority": "important"},
                "updated_at": collision_time
            }
        ]
    }

    response = client.post("/api/sync", headers=auth_headers, json=sync_request)
    assert response.status_code == 200

    # With equal timestamps, client wins (not greater, but not less either)
    data = response.json()
    assert data["applied_count"] == 1


# =============================================================================
# Change Queue Management Tests
# =============================================================================

@pytest.mark.sync
def test_queue_multiple_changes_offline(client, auth_headers):
    """Test that multiple offline changes accumulate in queue"""
    base_time = get_iso_timestamp(-60)

    # Simulate multiple offline changes
    changes = []
    for i in range(5):
        change_time = get_iso_timestamp(-50 + i * 10)
        changes.append({
            "id": f"offline-reminder-{i}",
            "action": "create",
            "data": {
                "id": f"offline-reminder-{i}",
                "text": f"Offline reminder {i}",
                "priority": "chill",
                "status": "pending",
                "created_at": change_time,
                "updated_at": change_time
            },
            "updated_at": change_time
        })

    sync_request = {
        "client_id": "test-device-123",
        "last_sync": base_time,
        "changes": changes
    }

    response = client.post("/api/sync", headers=auth_headers, json=sync_request)
    assert response.status_code == 200

    data = response.json()
    assert data["applied_count"] == 5

    # Verify all 5 reminders were created
    for i in range(5):
        get_response = client.get(f"/api/reminders/offline-reminder-{i}", headers=auth_headers)
        assert get_response.status_code == 200


@pytest.mark.sync
def test_queue_processes_sequentially(client, auth_headers):
    """Test that changes are applied in sequence (order matters)"""
    base_time = get_iso_timestamp(-30)

    # Create, update, update again - must process in order
    reminder_id = "sequential-test-123"
    create_time = get_iso_timestamp(-20)
    sync_request = {
        "client_id": "test-device-123",
        "last_sync": base_time,
        "changes": [
            {
                "id": reminder_id,
                "action": "create",
                "data": {
                    "id": reminder_id,
                    "text": "Version 1",
                    "priority": "chill",
                    "status": "pending",
                    "created_at": create_time,
                    "updated_at": create_time
                },
                "updated_at": create_time
            },
            {
                "id": reminder_id,
                "action": "update",
                "data": {"text": "Version 2", "priority": "important"},
                "updated_at": get_iso_timestamp(-10)
            },
            {
                "id": reminder_id,
                "action": "update",
                "data": {"text": "Version 3", "priority": "urgent"},
                "updated_at": get_iso_timestamp()
            }
        ]
    }

    response = client.post("/api/sync", headers=auth_headers, json=sync_request)
    assert response.status_code == 200

    data = response.json()
    assert data["applied_count"] == 3

    # Final version should be Version 3
    get_response = client.get(f"/api/reminders/{reminder_id}", headers=auth_headers)
    assert get_response.status_code == 200
    final = get_response.json()
    assert final["text"] == "Version 3"
    assert final["priority"] == "urgent"


@pytest.mark.sync
def test_empty_queue_no_changes(client, auth_headers):
    """Test sync with empty change queue returns no applied changes"""
    base_time = get_iso_timestamp(-30)

    sync_request = {
        "client_id": "test-device-123",
        "last_sync": base_time,
        "changes": []  # Empty queue
    }

    response = client.post("/api/sync", headers=auth_headers, json=sync_request)
    assert response.status_code == 200

    data = response.json()
    assert data["applied_count"] == 0
    assert data.get("server_changes", []) == []
    assert "last_sync" in data


# =============================================================================
# Sync State Transitions Tests
# =============================================================================

@pytest.mark.sync
def test_sync_status_idle_to_syncing_to_success(client, auth_headers):
    """Test happy path sync flow returns success status"""
    base_time = get_iso_timestamp(-30)
    current_time = get_iso_timestamp()

    sync_request = {
        "client_id": "test-device-123",
        "last_sync": base_time,
        "changes": [
            {
                "id": "success-test-123",
                "action": "create",
                "data": {
                    "id": "success-test-123",
                    "text": "Success test",
                    "priority": "chill",
                    "status": "pending",
                    "created_at": current_time,
                    "updated_at": current_time
                },
                "updated_at": current_time
            }
        ]
    }

    response = client.post("/api/sync", headers=auth_headers, json=sync_request)
    assert response.status_code == 200

    data = response.json()
    assert "last_sync" in data
    assert "applied_count" in data
    assert data["applied_count"] >= 0


@pytest.mark.sync
def test_sync_returns_server_changes(client, auth_headers):
    """Test sync returns server changes since last_sync"""
    # Create some reminders on server
    base_time = get_iso_timestamp(-60)

    reminder1 = create_reminder_with_timestamp(client, auth_headers, "Server reminder 1", get_iso_timestamp(-50))
    reminder2 = create_reminder_with_timestamp(client, auth_headers, "Server reminder 2", get_iso_timestamp(-40))

    # Client syncs with old last_sync - should get both reminders
    sync_request = {
        "client_id": "test-device-123",
        "last_sync": base_time,  # Before both reminders
        "changes": []
    }

    response = client.post("/api/sync", headers=auth_headers, json=sync_request)
    assert response.status_code == 200

    data = response.json()
    server_changes = data.get("server_changes", [])
    assert len(server_changes) >= 2

    # Verify server changes contain our reminders
    change_ids = [change["id"] for change in server_changes]
    assert reminder1["id"] in change_ids
    assert reminder2["id"] in change_ids


@pytest.mark.sync
def test_first_sync_returns_all_reminders(client, auth_headers):
    """Test first sync (last_sync=null) returns all reminders"""
    # Create reminders
    reminder1 = create_reminder_with_timestamp(client, auth_headers, "Reminder 1")
    reminder2 = create_reminder_with_timestamp(client, auth_headers, "Reminder 2")

    # First sync with no last_sync
    sync_request = {
        "client_id": "new-device-456",
        "last_sync": None,  # First sync
        "changes": []
    }

    response = client.post("/api/sync", headers=auth_headers, json=sync_request)
    assert response.status_code == 200

    data = response.json()
    server_changes = data.get("server_changes", [])
    assert len(server_changes) >= 2


# =============================================================================
# Edge Cases Tests
# =============================================================================

@pytest.mark.sync
def test_sync_with_deleted_reminders(client, auth_headers):
    """Test sync handles deleted reminders correctly"""
    base_time = get_iso_timestamp(-30)

    # Create reminder then delete it via sync
    reminder = create_reminder_with_timestamp(client, auth_headers, "To be deleted", base_time)

    sync_request = {
        "client_id": "test-device-123",
        "last_sync": base_time,
        "changes": [
            {
                "id": reminder["id"],
                "action": "delete",
                "data": None,
                "updated_at": get_iso_timestamp()
            }
        ]
    }

    response = client.post("/api/sync", headers=auth_headers, json=sync_request)
    assert response.status_code == 200

    data = response.json()
    assert data["applied_count"] == 1

    # Verify reminder was deleted
    get_response = client.get(f"/api/reminders/{reminder['id']}", headers=auth_headers)
    assert get_response.status_code == 404


@pytest.mark.sync
def test_partial_sync_continues_after_single_error(client, auth_headers):
    """Test sync continues processing after a single change fails"""
    base_time = get_iso_timestamp(-30)
    time1 = get_iso_timestamp(-10)
    time2 = get_iso_timestamp()

    sync_request = {
        "client_id": "test-device-123",
        "last_sync": base_time,
        "changes": [
            {
                "id": "valid-reminder-1",
                "action": "create",
                "data": {
                    "id": "valid-reminder-1",
                    "text": "Valid 1",
                    "priority": "chill",
                    "status": "pending",
                    "created_at": time1,
                    "updated_at": time1
                },
                "updated_at": time1
            },
            {
                "id": "invalid-reminder",
                "action": "update",
                "data": None,  # Invalid - no data for update
                "updated_at": get_iso_timestamp(-5)
            },
            {
                "id": "valid-reminder-2",
                "action": "create",
                "data": {
                    "id": "valid-reminder-2",
                    "text": "Valid 2",
                    "priority": "important",
                    "status": "pending",
                    "created_at": time2,
                    "updated_at": time2
                },
                "updated_at": time2
            }
        ]
    }

    response = client.post("/api/sync", headers=auth_headers, json=sync_request)
    assert response.status_code == 200

    data = response.json()
    # Should apply 2 out of 3 (the invalid one fails)
    assert data["applied_count"] == 2

    # Verify valid reminders were created
    get1 = client.get("/api/reminders/valid-reminder-1", headers=auth_headers)
    assert get1.status_code == 200

    get2 = client.get("/api/reminders/valid-reminder-2", headers=auth_headers)
    assert get2.status_code == 200


@pytest.mark.sync
def test_concurrent_sync_prevention_via_timestamps(client, auth_headers):
    """Test that synced_at timestamps prevent duplicate syncs"""
    base_time = get_iso_timestamp(-60)

    # First sync
    reminder = create_reminder_with_timestamp(client, auth_headers, "Test", base_time)

    sync1 = {
        "client_id": "device-1",
        "last_sync": base_time,
        "changes": []
    }

    response1 = client.post("/api/sync", headers=auth_headers, json=sync1)
    assert response1.status_code == 200
    data1 = response1.json()
    first_sync_time = data1["last_sync"]

    # Second sync immediately after with same last_sync
    sync2 = {
        "client_id": "device-1",
        "last_sync": first_sync_time,
        "changes": []
    }

    response2 = client.post("/api/sync", headers=auth_headers, json=sync2)
    assert response2.status_code == 200
    data2 = response2.json()

    # Should have no changes (already synced)
    assert len(data2.get("server_changes", [])) == 0


# =============================================================================
# Error Scenarios Tests
# =============================================================================

@pytest.mark.sync
def test_sync_invalid_changes_missing_required_fields(client, auth_headers):
    """Test sync with invalid change data returns appropriate response"""
    sync_request = {
        "client_id": "test-device-123",
        "last_sync": get_iso_timestamp(-30),
        "changes": [
            {
                "id": "invalid-change",
                "action": "create",
                "data": {},  # Missing required 'text' field
                "updated_at": get_iso_timestamp()
            }
        ]
    }

    # Note: The current implementation continues on errors, so this might return 200
    # but with applied_count=0
    response = client.post("/api/sync", headers=auth_headers, json=sync_request)

    # Either returns error or succeeds with no changes applied
    if response.status_code == 200:
        data = response.json()
        assert data["applied_count"] == 0
    else:
        assert response.status_code in [400, 422, 500]


@pytest.mark.sync
def test_sync_without_authentication(client):
    """Test sync endpoint requires authentication"""
    sync_request = {
        "client_id": "test-device-123",
        "last_sync": get_iso_timestamp(-30),
        "changes": []
    }

    response = client.post("/api/sync", json=sync_request)
    assert response.status_code == 401


@pytest.mark.sync
def test_sync_with_invalid_token(client, invalid_auth_headers):
    """Test sync with invalid token returns 401"""
    sync_request = {
        "client_id": "test-device-123",
        "last_sync": get_iso_timestamp(-30),
        "changes": []
    }

    response = client.post("/api/sync", headers=invalid_auth_headers, json=sync_request)
    assert response.status_code == 401


@pytest.mark.sync
def test_sync_updates_synced_at_timestamp(client, auth_headers):
    """Test that sync updates synced_at field for synced reminders"""
    from server import database as db

    base_time = get_iso_timestamp(-60)

    # Create reminder AFTER the base_time so it will be included in server_changes
    reminder_time = get_iso_timestamp(-30)  # After last_sync
    reminder = create_reminder_with_timestamp(client, auth_headers, "Test", reminder_time)

    # Verify initial synced_at is None
    initial = db.get_reminder_by_id(reminder["id"])
    assert initial["synced_at"] is None or initial["synced_at"] == ""

    # Perform sync - reminder should be sent to client since it's newer than last_sync
    sync_request = {
        "client_id": "test-device-123",
        "last_sync": base_time,  # Before reminder was created
        "changes": []
    }

    response = client.post("/api/sync", headers=auth_headers, json=sync_request)
    assert response.status_code == 200

    data = response.json()
    # Verify reminder was sent to client
    assert len(data["server_changes"]) >= 1
    assert any(c["id"] == reminder["id"] for c in data["server_changes"])

    # Verify synced_at was updated
    after_sync = db.get_reminder_by_id(reminder["id"])
    assert after_sync["synced_at"] is not None
    assert after_sync["synced_at"] != ""


# =============================================================================
# Advanced Conflict Tests
# =============================================================================

@pytest.mark.sync
def test_multiple_conflicts_in_single_sync(client, auth_headers):
    """Test handling multiple conflicts in one sync request"""
    base_time = get_iso_timestamp(-60)

    # Create 3 reminders on server
    reminder1 = create_reminder_with_timestamp(client, auth_headers, "R1", get_iso_timestamp(-50))
    reminder2 = create_reminder_with_timestamp(client, auth_headers, "R2", get_iso_timestamp(-40))
    reminder3 = create_reminder_with_timestamp(client, auth_headers, "R3", get_iso_timestamp(-30))

    # Update all 3 on server with newer timestamps
    time.sleep(0.01)
    for r in [reminder1, reminder2, reminder3]:
        client.patch(
            f"/api/reminders/{r['id']}",
            headers=auth_headers,
            json={"text": f"Server updated {r['id']}", "priority": "urgent"}
        )

    # Client tries to update all 3 with older timestamps
    old_time = get_iso_timestamp(-20)
    sync_request = {
        "client_id": "test-device-123",
        "last_sync": base_time,
        "changes": [
            {
                "id": reminder1["id"],
                "action": "update",
                "data": {"text": "Client update 1", "priority": "chill"},
                "updated_at": old_time
            },
            {
                "id": reminder2["id"],
                "action": "update",
                "data": {"text": "Client update 2", "priority": "chill"},
                "updated_at": old_time
            },
            {
                "id": reminder3["id"],
                "action": "update",
                "data": {"text": "Client update 3", "priority": "chill"},
                "updated_at": old_time
            }
        ]
    }

    response = client.post("/api/sync", headers=auth_headers, json=sync_request)
    assert response.status_code == 200

    data = response.json()
    # All should be conflicts with server winning
    assert len(data["conflicts"]) == 3
    assert all(c["resolution"] == "server_wins" for c in data["conflicts"])


@pytest.mark.sync
def test_sync_skips_changes_already_in_server_response(client, auth_headers):
    """Test that server doesn't send back changes client just pushed"""
    base_time = get_iso_timestamp(-30)

    # Client creates new reminder
    new_id = "client-created-123"
    sync_request = {
        "client_id": "test-device-123",
        "last_sync": base_time,
        "changes": [
            {
                "id": new_id,
                "action": "create",
                "data": {"text": "Client created", "priority": "chill"},
                "updated_at": get_iso_timestamp()
            }
        ]
    }

    response = client.post("/api/sync", headers=auth_headers, json=sync_request)
    assert response.status_code == 200

    data = response.json()
    server_changes = data.get("server_changes", [])

    # Server should NOT echo back the reminder client just created
    change_ids = [c["id"] for c in server_changes]
    assert new_id not in change_ids
