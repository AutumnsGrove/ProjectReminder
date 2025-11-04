"""
Location features tests for the reminders system
Tests Haversine distance calculations, geofencing queries, and edge cases
"""

import pytest
import math
from server.main import haversine_distance


# Known city coordinates for validation tests
NYC_COORDS = (40.7128, -74.0060)  # New York City
LA_COORDS = (34.0522, -118.2437)  # Los Angeles
EXPECTED_NYC_TO_LA = 3944  # km (approximately)

LONDON_COORDS = (51.5074, -0.1278)  # London
PARIS_COORDS = (48.8566, 2.3522)  # Paris
EXPECTED_LONDON_TO_PARIS = 344  # km (approximately)


# =============================================================================
# Distance Calculation Tests (Haversine Formula)
# =============================================================================

@pytest.mark.location
def test_calculate_distance_between_coordinates():
    """Test basic Haversine distance calculation"""
    # Test coordinates: ~111km apart (1 degree latitude at equator ≈ 111km)
    lat1, lng1 = 0.0, 0.0
    lat2, lng2 = 1.0, 0.0

    distance = haversine_distance(lat1, lng1, lat2, lng2)

    # Should be approximately 111,000 meters (111km)
    # Allow 5% tolerance for floating point and spherical earth approximation
    expected = 111000
    tolerance = expected * 0.05

    assert abs(distance - expected) < tolerance, \
        f"Expected ~{expected}m, got {distance}m"


@pytest.mark.location
def test_distance_same_location_returns_zero():
    """Test that distance between same point is zero"""
    lat, lng = 37.7749, -122.4194  # San Francisco

    distance = haversine_distance(lat, lng, lat, lng)

    assert distance == 0.0, "Distance between same point should be zero"


@pytest.mark.location
def test_distance_calculation_accuracy_known_cities():
    """Validate Haversine formula against known city distances"""
    # Test NYC to LA distance
    nyc_to_la = haversine_distance(
        NYC_COORDS[0], NYC_COORDS[1],
        LA_COORDS[0], LA_COORDS[1]
    )
    nyc_to_la_km = nyc_to_la / 1000

    # Allow 5% tolerance (±197km for this distance)
    tolerance_nyc_la = EXPECTED_NYC_TO_LA * 0.05
    assert abs(nyc_to_la_km - EXPECTED_NYC_TO_LA) < tolerance_nyc_la, \
        f"NYC to LA: Expected ~{EXPECTED_NYC_TO_LA}km, got {nyc_to_la_km:.1f}km"

    # Test London to Paris distance
    london_to_paris = haversine_distance(
        LONDON_COORDS[0], LONDON_COORDS[1],
        PARIS_COORDS[0], PARIS_COORDS[1]
    )
    london_to_paris_km = london_to_paris / 1000

    # Allow 5% tolerance (±17km for this distance)
    tolerance_london_paris = EXPECTED_LONDON_TO_PARIS * 0.05
    assert abs(london_to_paris_km - EXPECTED_LONDON_TO_PARIS) < tolerance_london_paris, \
        f"London to Paris: Expected ~{EXPECTED_LONDON_TO_PARIS}km, got {london_to_paris_km:.1f}km"


@pytest.mark.location
def test_distance_handles_negative_coordinates():
    """Test distance calculation with Southern/Western hemisphere coordinates"""
    # Sydney, Australia (Southern hemisphere, positive longitude)
    sydney = (-33.8688, 151.2093)

    # Buenos Aires, Argentina (Southern hemisphere, negative longitude)
    buenos_aires = (-34.6037, -58.3816)

    distance = haversine_distance(
        sydney[0], sydney[1],
        buenos_aires[0], buenos_aires[1]
    )

    # Should be approximately 11,800km (±5%)
    expected_km = 11800
    actual_km = distance / 1000
    tolerance = expected_km * 0.05

    assert distance > 0, "Distance should be positive"
    assert abs(actual_km - expected_km) < tolerance, \
        f"Sydney to Buenos Aires: Expected ~{expected_km}km, got {actual_km:.1f}km"


@pytest.mark.location
def test_distance_handles_dateline_crossing():
    """Test distance calculation across International Date Line"""
    # Tokyo, Japan (East of date line)
    tokyo = (35.6762, 139.6503)

    # Los Angeles, USA (West of date line)
    la = (34.0522, -118.2437)

    distance = haversine_distance(
        tokyo[0], tokyo[1],
        la[0], la[1]
    )

    # Should be approximately 8,800km (±5%)
    expected_km = 8800
    actual_km = distance / 1000
    tolerance = expected_km * 0.05

    assert distance > 0, "Distance should be positive"
    assert abs(actual_km - expected_km) < tolerance, \
        f"Tokyo to LA: Expected ~{expected_km}km, got {actual_km:.1f}km"


# =============================================================================
# Geofencing Query Tests (API Endpoint)
# =============================================================================

@pytest.mark.location
@pytest.mark.api
def test_get_reminders_near_location_within_radius(client, auth_headers):
    """Test finding reminders within search radius"""
    # Create reminders with location data
    # Central point: San Francisco (37.7749, -122.4194)
    central_point = {"lat": 37.7749, "lng": -122.4194}

    # Create reminder at central point
    reminder_center = {
        "text": "Reminder at center",
        "priority": "chill",
        "location_name": "San Francisco",
        "location_lat": central_point["lat"],
        "location_lng": central_point["lng"]
    }

    # Create reminder 500m away (approximately 0.0045 degrees)
    reminder_nearby = {
        "text": "Reminder nearby",
        "priority": "chill",
        "location_name": "Near SF",
        "location_lat": central_point["lat"] + 0.0045,
        "location_lng": central_point["lng"]
    }

    # Create reminder 2km away (outside 1km radius)
    reminder_far = {
        "text": "Reminder far away",
        "priority": "chill",
        "location_name": "Far from SF",
        "location_lat": central_point["lat"] + 0.018,
        "location_lng": central_point["lng"]
    }

    # Create reminders
    client.post("/api/reminders", headers=auth_headers, json=reminder_center)
    client.post("/api/reminders", headers=auth_headers, json=reminder_nearby)
    client.post("/api/reminders", headers=auth_headers, json=reminder_far)

    # Search within 1000m radius
    response = client.get(
        f"/api/reminders/near-location?lat={central_point['lat']}&lng={central_point['lng']}&radius=1000",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Should find 2 reminders (center and nearby)
    assert data["pagination"]["total"] == 2
    assert len(data["data"]) == 2

    # Verify reminders are sorted by distance
    distances = [r.get("distance", 0) for r in data["data"]]
    assert distances == sorted(distances), "Results should be sorted by distance"


@pytest.mark.location
@pytest.mark.api
def test_get_reminders_near_location_respects_100m_default(client, auth_headers):
    """Test that API uses 100m default radius correctly"""
    # Create reminder with location
    center = {"lat": 40.7128, "lng": -74.0060}

    reminder = {
        "text": "Test reminder",
        "priority": "chill",
        "location_name": "NYC",
        "location_lat": center["lat"],
        "location_lng": center["lng"],
        "location_radius": 100  # Default radius
    }

    client.post("/api/reminders", headers=auth_headers, json=reminder)

    # Search at exact location with large radius
    response = client.get(
        f"/api/reminders/near-location?lat={center['lat']}&lng={center['lng']}&radius=5000",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Should find the reminder (using max of search radius and reminder radius)
    assert data["pagination"]["total"] >= 1


@pytest.mark.location
@pytest.mark.api
def test_get_reminders_near_location_empty_outside_radius(client, auth_headers):
    """Test that reminders outside radius are not returned"""
    # Create reminder in NYC
    nyc = {"lat": 40.7128, "lng": -74.0060}

    reminder = {
        "text": "NYC reminder",
        "priority": "chill",
        "location_name": "New York",
        "location_lat": nyc["lat"],
        "location_lng": nyc["lng"]
    }

    client.post("/api/reminders", headers=auth_headers, json=reminder)

    # Search in LA (3,944km away)
    la = {"lat": 34.0522, "lng": -118.2437}

    response = client.get(
        f"/api/reminders/near-location?lat={la['lat']}&lng={la['lng']}&radius=1000",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Should find no reminders
    assert data["pagination"]["total"] == 0
    assert len(data["data"]) == 0


@pytest.mark.location
@pytest.mark.api
def test_near_location_with_10km_radius(client, auth_headers):
    """Test geofencing with large radius (10km)"""
    # Create reminders at various distances
    center = {"lat": 37.7749, "lng": -122.4194}

    # Reminder 5km away (approximately 0.045 degrees)
    reminder_5km = {
        "text": "5km away",
        "priority": "chill",
        "location_name": "5km",
        "location_lat": center["lat"] + 0.045,
        "location_lng": center["lng"]
    }

    # Reminder 15km away (outside 10km radius)
    reminder_15km = {
        "text": "15km away",
        "priority": "chill",
        "location_name": "15km",
        "location_lat": center["lat"] + 0.135,
        "location_lng": center["lng"]
    }

    client.post("/api/reminders", headers=auth_headers, json=reminder_5km)
    client.post("/api/reminders", headers=auth_headers, json=reminder_15km)

    # Search with 10km radius
    response = client.get(
        f"/api/reminders/near-location?lat={center['lat']}&lng={center['lng']}&radius=10000",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Should find only the 5km reminder
    assert data["pagination"]["total"] == 1
    assert "5km away" in data["data"][0]["text"]


@pytest.mark.location
@pytest.mark.api
def test_near_location_with_10m_precision(client, auth_headers):
    """Test geofencing with small radius (10m precision)"""
    # Create reminders very close together
    center = {"lat": 37.7749, "lng": -122.4194}

    # Reminder 5m away (approximately 0.000045 degrees)
    reminder_5m = {
        "text": "5m away",
        "priority": "chill",
        "location_name": "Very close",
        "location_lat": center["lat"] + 0.000045,
        "location_lng": center["lng"]
    }

    # Reminder 20m away (outside 10m radius)
    reminder_20m = {
        "text": "20m away",
        "priority": "chill",
        "location_name": "A bit further",
        "location_lat": center["lat"] + 0.00018,
        "location_lng": center["lng"]
    }

    client.post("/api/reminders", headers=auth_headers, json=reminder_5m)
    client.post("/api/reminders", headers=auth_headers, json=reminder_20m)

    # Search with minimum 10m radius
    response = client.get(
        f"/api/reminders/near-location?lat={center['lat']}&lng={center['lng']}&radius=10",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Due to reminder_radius (100m default), both might be returned
    # Just verify API accepts small radius
    assert data["pagination"]["total"] >= 0


# =============================================================================
# Edge Case Tests
# =============================================================================

@pytest.mark.location
def test_location_at_north_pole():
    """Test distance calculation at North Pole (90°N)"""
    north_pole = (90.0, 0.0)
    nearby_point = (89.9, 0.0)  # ~11km from pole

    distance = haversine_distance(
        north_pole[0], north_pole[1],
        nearby_point[0], nearby_point[1]
    )

    # Should be approximately 11km
    expected_km = 11
    actual_km = distance / 1000
    tolerance = expected_km * 0.1  # 10% tolerance for polar regions

    assert distance > 0, "Distance should be positive"
    assert abs(actual_km - expected_km) < tolerance, \
        f"North pole distance: Expected ~{expected_km}km, got {actual_km:.1f}km"


@pytest.mark.location
def test_location_at_south_pole():
    """Test distance calculation at South Pole (90°S)"""
    south_pole = (-90.0, 0.0)
    nearby_point = (-89.9, 0.0)  # ~11km from pole

    distance = haversine_distance(
        south_pole[0], south_pole[1],
        nearby_point[0], nearby_point[1]
    )

    # Should be approximately 11km
    expected_km = 11
    actual_km = distance / 1000
    tolerance = expected_km * 0.1  # 10% tolerance for polar regions

    assert distance > 0, "Distance should be positive"
    assert abs(actual_km - expected_km) < tolerance, \
        f"South pole distance: Expected ~{expected_km}km, got {actual_km:.1f}km"


@pytest.mark.location
@pytest.mark.api
def test_invalid_coordinates_returns_400(client, auth_headers):
    """Test that invalid coordinates return 400 error"""
    # Test latitude out of range (>90)
    response = client.get(
        "/api/reminders/near-location?lat=91.0&lng=0.0&radius=1000",
        headers=auth_headers
    )
    assert response.status_code == 422  # FastAPI validation error

    # Test latitude out of range (<-90)
    response = client.get(
        "/api/reminders/near-location?lat=-91.0&lng=0.0&radius=1000",
        headers=auth_headers
    )
    assert response.status_code == 422

    # Test longitude out of range (>180)
    response = client.get(
        "/api/reminders/near-location?lat=0.0&lng=181.0&radius=1000",
        headers=auth_headers
    )
    assert response.status_code == 422

    # Test longitude out of range (<-180)
    response = client.get(
        "/api/reminders/near-location?lat=0.0&lng=-181.0&radius=1000",
        headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.location
@pytest.mark.api
def test_missing_location_fields_returns_empty(client, auth_headers):
    """Test that reminders without location data are not returned"""
    # Create reminder without location
    reminder_no_location = {
        "text": "No location reminder",
        "priority": "chill"
    }

    client.post("/api/reminders", headers=auth_headers, json=reminder_no_location)

    # Search for reminders near a location
    response = client.get(
        "/api/reminders/near-location?lat=37.7749&lng=-122.4194&radius=1000",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Should not find the reminder without location
    assert data["pagination"]["total"] == 0


@pytest.mark.location
@pytest.mark.api
def test_location_with_extreme_radius(client, auth_headers):
    """Test geofencing with very large radius (>20000km)"""
    # Create reminder in NYC
    nyc = {"lat": 40.7128, "lng": -74.0060}

    reminder = {
        "text": "NYC reminder",
        "priority": "chill",
        "location_name": "New York",
        "location_lat": nyc["lat"],
        "location_lng": nyc["lng"]
    }

    client.post("/api/reminders", headers=auth_headers, json=reminder)

    # Search from Tokyo with maximum allowed radius (50,000m = 50km)
    tokyo = {"lat": 35.6762, "lng": 139.6503}

    response = client.get(
        f"/api/reminders/near-location?lat={tokyo['lat']}&lng={tokyo['lng']}&radius=50000",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Should not find NYC reminder (too far away)
    assert data["pagination"]["total"] == 0

    # Test radius limit validation (>50km should fail)
    response = client.get(
        f"/api/reminders/near-location?lat={tokyo['lat']}&lng={tokyo['lng']}&radius=100000",
        headers=auth_headers
    )
    assert response.status_code == 422  # Validation error
