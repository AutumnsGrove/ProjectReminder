"""
End-to-End Integration Tests for Complete User Workflows
Tests multi-feature interactions from creation through completion
"""

import pytest
from datetime import datetime, timezone, timedelta, date
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


# =============================================================================
# Complete CRUD Workflows (3 tests)
# =============================================================================

@pytest.mark.e2e
def test_create_read_update_complete_delete_reminder_flow(client, auth_headers):
    """Test complete reminder lifecycle from creation to deletion."""
    # Step 1: Create reminder
    create_response = client.post(
        "/api/reminders",
        json={"text": "E2E Test Reminder", "priority": "important"},
        headers=auth_headers
    )
    assert create_response.status_code == 201
    reminder_id = create_response.json()["id"]
    assert reminder_id is not None

    # Step 2: Read reminder
    get_response = client.get(f"/api/reminders/{reminder_id}", headers=auth_headers)
    assert get_response.status_code == 200
    reminder = get_response.json()
    assert reminder["text"] == "E2E Test Reminder"
    assert reminder["priority"] == "important"
    assert reminder["status"] == "pending"

    # Step 3: Update reminder text and priority
    update_response = client.patch(
        f"/api/reminders/{reminder_id}",
        json={"text": "Updated E2E Test", "priority": "urgent"},
        headers=auth_headers
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["text"] == "Updated E2E Test"
    assert updated["priority"] == "urgent"

    # Step 4: Mark as completed
    complete_response = client.patch(
        f"/api/reminders/{reminder_id}",
        json={"status": "completed"},
        headers=auth_headers
    )
    assert complete_response.status_code == 200
    completed = complete_response.json()
    assert completed["status"] == "completed"
    assert completed["completed_at"] is not None

    # Step 5: Delete reminder
    delete_response = client.delete(f"/api/reminders/{reminder_id}", headers=auth_headers)
    assert delete_response.status_code == 204

    # Step 6: Verify deleted (404)
    verify_response = client.get(f"/api/reminders/{reminder_id}", headers=auth_headers)
    assert verify_response.status_code == 404


@pytest.mark.e2e
def test_create_multiple_list_filter_update_workflow(client, auth_headers):
    """Test creating multiple reminders, listing, filtering, and updating."""
    # Step 1: Create multiple reminders with different priorities
    reminders = []
    priorities = ["chill", "important", "urgent", "chill", "important"]
    for i, priority in enumerate(priorities):
        response = client.post(
            "/api/reminders",
            json={"text": f"Reminder {i+1}", "priority": priority},
            headers=auth_headers
        )
        assert response.status_code == 201
        reminders.append(response.json())

    # Step 2: List all reminders
    list_response = client.get("/api/reminders", headers=auth_headers)
    assert list_response.status_code == 200
    all_reminders = list_response.json()
    assert len(all_reminders["data"]) >= 5

    # Step 3: Filter by priority (chill)
    filter_response = client.get("/api/reminders?priority=chill", headers=auth_headers)
    assert filter_response.status_code == 200
    chill_reminders = filter_response.json()
    assert len(chill_reminders["data"]) >= 2
    for reminder in chill_reminders["data"]:
        assert reminder["priority"] == "chill"

    # Step 4: Update one reminder from chill to urgent
    chill_id = chill_reminders["data"][0]["id"]
    update_response = client.patch(
        f"/api/reminders/{chill_id}",
        json={"priority": "urgent"},
        headers=auth_headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["priority"] == "urgent"

    # Step 5: Verify filter updated
    new_filter = client.get("/api/reminders?priority=chill", headers=auth_headers)
    assert new_filter.status_code == 200
    # Should have one less chill reminder now
    assert len(new_filter.json()["data"]) == len(chill_reminders["data"]) - 1


@pytest.mark.e2e
def test_reminder_status_transitions(client, auth_headers):
    """Test reminder status transitions: pending → snoozed → completed."""
    # Create reminder
    response = client.post(
        "/api/reminders",
        json={"text": "Status transition test", "priority": "important"},
        headers=auth_headers
    )
    assert response.status_code == 201
    reminder_id = response.json()["id"]

    # Verify initial status is pending
    get_response = client.get(f"/api/reminders/{reminder_id}", headers=auth_headers)
    assert get_response.json()["status"] == "pending"

    # Transition to snoozed
    update1 = client.patch(
        f"/api/reminders/{reminder_id}",
        json={"status": "snoozed"},
        headers=auth_headers
    )
    assert update1.status_code == 200
    assert update1.json()["status"] == "snoozed"
    assert update1.json()["completed_at"] is None

    # Transition back to pending
    update2 = client.patch(
        f"/api/reminders/{reminder_id}",
        json={"status": "pending"},
        headers=auth_headers
    )
    assert update2.status_code == 200
    assert update2.json()["status"] == "pending"

    # Transition to completed
    update3 = client.patch(
        f"/api/reminders/{reminder_id}",
        json={"status": "completed"},
        headers=auth_headers
    )
    assert update3.status_code == 200
    assert update3.json()["status"] == "completed"
    assert update3.json()["completed_at"] is not None


# =============================================================================
# Multi-Feature Workflows (4 tests)
# =============================================================================

@pytest.mark.e2e
def test_create_with_location_search_near_location(client, auth_headers):
    """Test creating reminder with location, then searching near that location."""
    # Step 1: Create reminder with location in San Francisco
    sf_location = {"lat": 37.7749, "lng": -122.4194}
    create_response = client.post(
        "/api/reminders",
        json={
            "text": "Buy groceries at Whole Foods",
            "priority": "important",
            "location_name": "Whole Foods SF",
            "location_address": "123 Market St, San Francisco",
            "location_lat": sf_location["lat"],
            "location_lng": sf_location["lng"],
            "location_radius": 200
        },
        headers=auth_headers
    )
    assert create_response.status_code == 201
    reminder = create_response.json()
    assert reminder["location_name"] == "Whole Foods SF"

    # Step 2: Search near the location (within 500m)
    search_response = client.get(
        f"/api/reminders/near-location?lat={sf_location['lat']}&lng={sf_location['lng']}&radius=500",
        headers=auth_headers
    )
    assert search_response.status_code == 200
    nearby = search_response.json()

    # Step 3: Verify reminder was found
    found_ids = [r["id"] for r in nearby["data"]]
    assert reminder["id"] in found_ids

    # Step 4: Verify distance metadata is present
    found_reminder = next(r for r in nearby["data"] if r["id"] == reminder["id"])
    assert "distance" in found_reminder
    assert found_reminder["distance"] < 500  # Within search radius


@pytest.mark.e2e
def test_create_multiple_reminders_complete_workflow(client, auth_headers):
    """Test creating multiple reminders with different attributes and completing them."""
    # Create 3 reminders with different priorities and categories
    reminders = []
    configs = [
        {"text": "Buy groceries", "priority": "important", "category": "Personal"},
        {"text": "Team meeting", "priority": "urgent", "category": "Work"},
        {"text": "Call dentist", "priority": "chill", "category": "Health"}
    ]

    for config in configs:
        response = client.post("/api/reminders", json=config, headers=auth_headers)
        assert response.status_code == 201
        reminders.append(response.json())

    # Verify all created
    for reminder in reminders:
        get_response = client.get(f"/api/reminders/{reminder['id']}", headers=auth_headers)
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "pending"

    # Filter by category
    work_filter = client.get("/api/reminders?category=Work", headers=auth_headers)
    assert work_filter.status_code == 200
    work_reminders = work_filter.json()["data"]
    assert len(work_reminders) >= 1
    assert any(r["text"] == "Team meeting" for r in work_reminders)

    # Complete all reminders
    for reminder in reminders:
        complete = client.patch(
            f"/api/reminders/{reminder['id']}",
            json={"status": "completed"},
            headers=auth_headers
        )
        assert complete.status_code == 200
        assert complete.json()["status"] == "completed"

    # Verify all completed
    completed_filter = client.get("/api/reminders?status=completed", headers=auth_headers)
    assert completed_filter.status_code == 200
    completed_ids = [r["id"] for r in completed_filter.json()["data"]]
    for reminder in reminders:
        assert reminder["id"] in completed_ids


@pytest.mark.e2e
def test_location_based_reminder_triggers_at_location(client, auth_headers):
    """Test location-based reminder appears when querying near that location."""
    # Create reminder at Home Depot
    home_depot = {"lat": 37.7833, "lng": -122.4167}  # SF Civic Center area

    create_response = client.post(
        "/api/reminders",
        json={
            "text": "Buy wood planks and screws",
            "priority": "chill",
            "location_name": "Home Depot",
            "location_lat": home_depot["lat"],
            "location_lng": home_depot["lng"],
            "location_radius": 300
        },
        headers=auth_headers
    )
    assert create_response.status_code == 201
    reminder_id = create_response.json()["id"]

    # Query nearby location (simulate being near Home Depot)
    nearby_response = client.get(
        f"/api/reminders/near-location?lat={home_depot['lat']}&lng={home_depot['lng']}&radius=500",
        headers=auth_headers
    )
    assert nearby_response.status_code == 200
    nearby = nearby_response.json()

    # Verify reminder appears in results
    found_ids = [r["id"] for r in nearby["data"]]
    assert reminder_id in found_ids

    # Query far location (should not appear)
    far_location = {"lat": 40.7128, "lng": -74.0060}  # NYC
    far_response = client.get(
        f"/api/reminders/near-location?lat={far_location['lat']}&lng={far_location['lng']}&radius=1000",
        headers=auth_headers
    )
    assert far_response.status_code == 200
    far = far_response.json()

    # Verify reminder does NOT appear in far results
    far_ids = [r["id"] for r in far["data"]]
    assert reminder_id not in far_ids


@pytest.mark.e2e
def test_create_reminder_with_all_features_complete_workflow(client, auth_headers):
    """Test creating reminder with all features (location, recurrence, category, due date)."""
    # Create reminder with all features
    today = date.today()
    tomorrow = today + timedelta(days=1)

    create_response = client.post(
        "/api/reminders",
        json={
            "text": "Team meeting at office",
            "priority": "important",
            "category": "Work",
            "due_date": tomorrow.isoformat(),
            "due_time": "10:00:00",
            "time_required": True,
            "location_name": "Office",
            "location_address": "456 Tech Blvd",
            "location_lat": 37.7749,
            "location_lng": -122.4194,
            "location_radius": 100
        },
        headers=auth_headers
    )
    assert create_response.status_code == 201
    reminder = create_response.json()

    # Verify all fields
    assert reminder["text"] == "Team meeting at office"
    assert reminder["priority"] == "important"
    assert reminder["category"] == "Work"
    assert reminder["due_date"] == tomorrow.isoformat()
    assert reminder["due_time"] == "10:00:00"
    assert reminder["time_required"] is True
    assert reminder["location_name"] == "Office"
    assert reminder["location_lat"] == 37.7749

    # Update reminder
    update_response = client.patch(
        f"/api/reminders/{reminder['id']}",
        json={"priority": "urgent", "due_time": "09:30:00"},
        headers=auth_headers
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["priority"] == "urgent"
    assert updated["due_time"] == "09:30:00"
    assert updated["category"] == "Work"  # Unchanged


# =============================================================================
# Multi-Device Sync Scenarios (3 tests)
# =============================================================================

@pytest.mark.e2e
def test_create_local_sync_verify_cloud(client, auth_headers):
    """Test creating reminder locally and syncing to cloud."""
    from server import database as db

    # Step 1: Create reminder (simulates local creation)
    create_response = client.post(
        "/api/reminders",
        json={"text": "Local reminder to sync", "priority": "chill"},
        headers=auth_headers
    )
    assert create_response.status_code == 201
    reminder = create_response.json()

    # Verify initial synced_at is None
    initial = db.get_reminder_by_id(reminder["id"])
    assert initial["synced_at"] is None or initial["synced_at"] == ""

    # Step 2: Perform sync
    base_time = get_iso_timestamp(-60)
    sync_request = {
        "client_id": "device-123",
        "last_sync": base_time,
        "changes": []  # Just pulling server changes
    }

    sync_response = client.post("/api/sync", json=sync_request, headers=auth_headers)
    assert sync_response.status_code == 200
    sync_data = sync_response.json()

    # Step 3: Verify synced_at timestamp was updated
    after_sync = db.get_reminder_by_id(reminder["id"])
    assert after_sync["synced_at"] is not None
    assert after_sync["synced_at"] != ""

    # Step 4: Verify reminder appears in server changes
    server_changes = sync_data.get("server_changes", [])
    synced_ids = [c["id"] for c in server_changes]
    assert reminder["id"] in synced_ids


@pytest.mark.e2e
def test_offline_create_multiple_sync_when_online(client, auth_headers):
    """Test creating multiple reminders offline, then syncing all at once."""
    base_time = get_iso_timestamp(-120)

    # Simulate 3 offline creations
    offline_changes = []
    for i in range(3):
        change_time = get_iso_timestamp(-90 + i * 30)
        reminder_id = f"offline-reminder-{i}-{int(time.time())}"
        offline_changes.append({
            "id": reminder_id,
            "action": "create",
            "data": {
                "id": reminder_id,
                "text": f"Offline reminder {i+1}",
                "priority": "chill",
                "status": "pending",
                "created_at": change_time,
                "updated_at": change_time
            },
            "updated_at": change_time
        })

    # Sync all changes at once
    sync_request = {
        "client_id": "device-offline-test",
        "last_sync": base_time,
        "changes": offline_changes
    }

    sync_response = client.post("/api/sync", json=sync_request, headers=auth_headers)
    assert sync_response.status_code == 200
    sync_data = sync_response.json()

    # Verify all 3 were applied
    assert sync_data["applied_count"] == 3

    # Verify all reminders exist on server
    for change in offline_changes:
        get_response = client.get(f"/api/reminders/{change['id']}", headers=auth_headers)
        assert get_response.status_code == 200
        reminder = get_response.json()
        assert reminder["text"] == change["data"]["text"]


@pytest.mark.e2e
def test_conflict_resolution_last_write_wins_e2e(client, auth_headers):
    """Test conflict resolution with last-write-wins strategy."""
    from server import database as db

    # Step 1: Create reminder on "server"
    create_response = client.post(
        "/api/reminders",
        json={"text": "Original text", "priority": "chill"},
        headers=auth_headers
    )
    assert create_response.status_code == 201
    reminder_id = create_response.json()["id"]

    # Step 2: Update on server with recent timestamp
    time.sleep(0.01)
    server_update = client.patch(
        f"/api/reminders/{reminder_id}",
        json={"text": "Server updated text", "priority": "urgent"},
        headers=auth_headers
    )
    assert server_update.status_code == 200
    server_version = server_update.json()
    server_timestamp = server_version["updated_at"]

    # Step 3: Client tries to sync with older timestamp (conflict)
    old_client_time = get_iso_timestamp(-10)
    sync_request = {
        "client_id": "device-conflict-test",
        "last_sync": old_client_time,
        "changes": [
            {
                "id": reminder_id,
                "action": "update",
                "data": {"text": "Old client text", "priority": "chill"},
                "updated_at": old_client_time
            }
        ]
    }

    sync_response = client.post("/api/sync", json=sync_request, headers=auth_headers)
    assert sync_response.status_code == 200
    sync_data = sync_response.json()

    # Step 4: Verify conflict was detected
    assert len(sync_data["conflicts"]) == 1
    conflict = sync_data["conflicts"][0]
    assert conflict["id"] == reminder_id
    assert conflict["resolution"] == "server_wins"

    # Step 5: Verify server version was preserved
    final = client.get(f"/api/reminders/{reminder_id}", headers=auth_headers)
    assert final.status_code == 200
    assert final.json()["text"] == "Server updated text"
    assert final.json()["priority"] == "urgent"


# =============================================================================
# Priority Workflows (2 tests)
# =============================================================================

@pytest.mark.e2e
def test_create_urgent_update_to_chill_workflow(client, auth_headers):
    """Test creating urgent reminder and updating to chill priority."""
    # Create urgent reminder
    create_response = client.post(
        "/api/reminders",
        json={"text": "Urgent task", "priority": "urgent"},
        headers=auth_headers
    )
    assert create_response.status_code == 201
    reminder_id = create_response.json()["id"]

    # Verify it's urgent
    get_response = client.get(f"/api/reminders/{reminder_id}", headers=auth_headers)
    assert get_response.json()["priority"] == "urgent"

    # Filter by urgent
    urgent_filter = client.get("/api/reminders?priority=urgent", headers=auth_headers)
    assert urgent_filter.status_code == 200
    urgent_ids = [r["id"] for r in urgent_filter.json()["data"]]
    assert reminder_id in urgent_ids

    # Update to chill
    update_response = client.patch(
        f"/api/reminders/{reminder_id}",
        json={"priority": "chill"},
        headers=auth_headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["priority"] == "chill"

    # Filter by chill (should appear)
    chill_filter = client.get("/api/reminders?priority=chill", headers=auth_headers)
    assert chill_filter.status_code == 200
    chill_ids = [r["id"] for r in chill_filter.json()["data"]]
    assert reminder_id in chill_ids

    # Filter by urgent (should NOT appear)
    new_urgent_filter = client.get("/api/reminders?priority=urgent", headers=auth_headers)
    new_urgent_ids = [r["id"] for r in new_urgent_filter.json()["data"]]
    assert reminder_id not in new_urgent_ids


@pytest.mark.e2e
def test_filter_by_priority_update_verify_filter(client, auth_headers):
    """Test creating reminders with different priorities, filtering, and updating."""
    # Create reminders with all priorities
    priorities = ["chill", "important", "urgent", "someday", "waiting"]
    created_ids = {}

    for priority in priorities:
        response = client.post(
            "/api/reminders",
            json={"text": f"{priority.capitalize()} reminder", "priority": priority},
            headers=auth_headers
        )
        assert response.status_code == 201
        created_ids[priority] = response.json()["id"]

    # Filter by each priority
    for priority in priorities:
        filter_response = client.get(f"/api/reminders?priority={priority}", headers=auth_headers)
        assert filter_response.status_code == 200
        filtered = filter_response.json()["data"]

        # Verify our reminder appears
        filtered_ids = [r["id"] for r in filtered]
        assert created_ids[priority] in filtered_ids

        # Verify all filtered reminders have correct priority
        for reminder in filtered:
            assert reminder["priority"] == priority

    # Update someday to urgent
    update_response = client.patch(
        f"/api/reminders/{created_ids['someday']}",
        json={"priority": "urgent"},
        headers=auth_headers
    )
    assert update_response.status_code == 200

    # Verify it moved from someday to urgent
    someday_check = client.get("/api/reminders?priority=someday", headers=auth_headers)
    someday_ids = [r["id"] for r in someday_check.json()["data"]]
    assert created_ids["someday"] not in someday_ids

    urgent_check = client.get("/api/reminders?priority=urgent", headers=auth_headers)
    urgent_ids = [r["id"] for r in urgent_check.json()["data"]]
    assert created_ids["someday"] in urgent_ids


# =============================================================================
# Error Recovery Workflows (2 tests)
# =============================================================================

@pytest.mark.e2e
def test_sync_continues_after_partial_error(client, auth_headers):
    """Test sync continues processing after encountering invalid changes."""
    base_time = get_iso_timestamp(-60)

    sync_request = {
        "client_id": "device-error-test",
        "last_sync": base_time,
        "changes": [
            # Valid change 1
            {
                "id": f"valid-1-{int(time.time())}",
                "action": "create",
                "data": {
                    "id": f"valid-1-{int(time.time())}",
                    "text": "Valid reminder 1",
                    "priority": "chill",
                    "status": "pending",
                    "created_at": get_iso_timestamp(-30),
                    "updated_at": get_iso_timestamp(-30)
                },
                "updated_at": get_iso_timestamp(-30)
            },
            # Invalid change (missing data)
            {
                "id": "invalid-change",
                "action": "update",
                "data": None,  # Invalid
                "updated_at": get_iso_timestamp(-20)
            },
            # Valid change 2
            {
                "id": f"valid-2-{int(time.time())}",
                "action": "create",
                "data": {
                    "id": f"valid-2-{int(time.time())}",
                    "text": "Valid reminder 2",
                    "priority": "important",
                    "status": "pending",
                    "created_at": get_iso_timestamp(-10),
                    "updated_at": get_iso_timestamp(-10)
                },
                "updated_at": get_iso_timestamp(-10)
            }
        ]
    }

    response = client.post("/api/sync", json=sync_request, headers=auth_headers)
    assert response.status_code == 200
    sync_data = response.json()

    # Should apply 2 out of 3 (invalid one skipped)
    assert sync_data["applied_count"] == 2

    # Verify valid reminders were created
    changes = sync_request["changes"]
    get1 = client.get(f"/api/reminders/{changes[0]['id']}", headers=auth_headers)
    assert get1.status_code == 200

    get2 = client.get(f"/api/reminders/{changes[2]['id']}", headers=auth_headers)
    assert get2.status_code == 200


@pytest.mark.e2e
def test_bulk_operations_workflow(client, auth_headers):
    """Test bulk operations: create multiple, filter, batch update, batch delete."""
    # Step 1: Create 10 reminders
    reminder_ids = []
    for i in range(10):
        priority = ["chill", "important", "urgent"][i % 3]
        response = client.post(
            "/api/reminders",
            json={"text": f"Task {i+1}", "priority": priority},
            headers=auth_headers
        )
        assert response.status_code == 201
        reminder_ids.append(response.json()["id"])

    # Step 2: Verify all exist
    list_response = client.get("/api/reminders?limit=20", headers=auth_headers)
    assert list_response.status_code == 200
    all_reminders = list_response.json()["data"]
    assert len(all_reminders) >= 10

    # Step 3: Filter by urgent priority
    urgent_response = client.get("/api/reminders?priority=urgent", headers=auth_headers)
    urgent_reminders = urgent_response.json()["data"]
    urgent_ids = [r["id"] for r in urgent_reminders if r["id"] in reminder_ids]
    assert len(urgent_ids) >= 3  # Should have at least 3 urgent (10/3)

    # Step 4: Complete all urgent reminders
    for urgent_id in urgent_ids:
        complete = client.patch(
            f"/api/reminders/{urgent_id}",
            json={"status": "completed"},
            headers=auth_headers
        )
        assert complete.status_code == 200

    # Step 5: Verify urgent reminders are completed
    for urgent_id in urgent_ids:
        get_response = client.get(f"/api/reminders/{urgent_id}", headers=auth_headers)
        assert get_response.json()["status"] == "completed"

    # Step 6: Delete half of remaining reminders
    remaining_ids = [rid for rid in reminder_ids if rid not in urgent_ids]
    to_delete = remaining_ids[:len(remaining_ids)//2]

    for rid in to_delete:
        delete_response = client.delete(f"/api/reminders/{rid}", headers=auth_headers)
        assert delete_response.status_code == 204

    # Step 7: Verify deleted reminders are gone
    for rid in to_delete:
        get_response = client.get(f"/api/reminders/{rid}", headers=auth_headers)
        assert get_response.status_code == 404
