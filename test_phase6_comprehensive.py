#!/usr/bin/env python3
"""
Comprehensive Phase 6 Location Features Test Suite
Tests backend endpoints, database schema, and API responses
"""
import requests
import json
import sqlite3
import time
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_TOKEN = "c27d0f34a3fbbb12faf361328615bfd42033b4adfc80732b30bdbaa7d3d0bc60"
DB_PATH = "/Users/mini/Documents/Projects/ProjectReminder/reminders.db"
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

# Test counters
tests_passed = 0
tests_failed = 0
test_results = []
created_reminder_ids = []

def log_test(name, passed, details=""):
    """Log test result"""
    global tests_passed, tests_failed
    status = "PASS" if passed else "FAIL"
    if passed:
        tests_passed += 1
    else:
        tests_failed += 1
    result = f"[{status}] {name}"
    if details:
        result += f"\n      {details}"
    test_results.append(result)
    print(result)

def test_health():
    """Test 1: Health endpoint"""
    print("\n=== BACKEND HEALTH TESTS ===")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        passed = response.status_code == 200 and response.json().get("status") == "ok"
        log_test("Health endpoint", passed, f"Status: {response.json().get('status')}, DB: {response.json().get('database')}")
    except Exception as e:
        log_test("Health endpoint", False, f"Error: {e}")

def test_mapbox_config():
    """Test 2: MapBox config endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/config/mapbox", timeout=5)
        data = response.json()
        passed = response.status_code == 200 and "mapbox_access_token" in data and data["mapbox_access_token"].startswith("pk.")
        log_test("MapBox config endpoint", passed, f"Token length: {len(data.get('mapbox_access_token', ''))}")
    except Exception as e:
        log_test("MapBox config endpoint", False, f"Error: {e}")

def create_test_reminder(text, location_name, location_lat, location_lng, location_address=""):
    """Helper: Create a test reminder with location"""
    payload = {
        "text": text,
        "priority": "important",
        "status": "pending",
        "location_name": location_name,
        "location_address": location_address,
        "location_lat": location_lat,
        "location_lng": location_lng,
        "location_radius": 1000,
        "source": "manual"  # Must be 'manual', 'voice', or 'api'
    }
    response = requests.post(f"{BASE_URL}/api/reminders", json=payload, headers=HEADERS)
    return response

def test_create_reminders():
    """Test 3-5: Create reminders with locations"""
    print("\n=== REMINDER CREATION TESTS ===")
    
    test_cases = [
        ("Buy groceries", "Austin, TX", 30.2672, -97.7431, "Austin, Texas"),
        ("Visit Golden Gate", "San Francisco, CA", 37.7749, -122.4194, "San Francisco, California"),
        ("Times Square meeting", "New York, NY", 40.7128, -74.0060, "New York City, New York")
    ]
    
    for text, location, lat, lng, address in test_cases:
        try:
            response = create_test_reminder(text, location, lat, lng, address)
            if response.status_code != 201:
                print(f"      Error response: {response.text}")
            data = response.json()
            passed = (response.status_code == 201 and 
                     data.get("location_name") == location and
                     data.get("location_lat") == lat)
            if passed and "id" in data:
                created_reminder_ids.append(data["id"])
            log_test(f"Create reminder: {text}", passed, 
                    f"ID: {data.get('id', 'N/A')[:8]}... Location: {location}")
        except Exception as e:
            log_test(f"Create reminder: {text}", False, f"Error: {e}")

def test_near_location():
    """Test 6-9: Near location queries"""
    print("\n=== NEAR LOCATION QUERY TESTS ===")
    
    test_cases = [
        ("Austin, TX", 30.2672, -97.7431, 1000, 1),  # Should find Austin reminder (within 1km radius)
        ("San Francisco, CA", 37.7749, -122.4194, 1000, 1),  # Should find SF reminder
        ("New York, NY", 40.7128, -74.0060, 1000, 1),  # Should find NYC reminder
        ("London, UK", 51.5074, -0.1278, 1000, 0),  # Should find nothing
    ]
    
    for location, lat, lng, radius, expected_count in test_cases:
        try:
            response = requests.get(
                f"{BASE_URL}/api/reminders/near-location",
                params={"lat": lat, "lng": lng, "radius": radius},
                headers=HEADERS
            )
            data = response.json()
            actual_count = len(data.get("data", []))
            # For Austin test, accept either 1 or 2 (existing + new)
            if location == "Austin, TX":
                passed = response.status_code == 200 and actual_count >= expected_count
            else:
                passed = response.status_code == 200 and actual_count == expected_count
            log_test(f"Near location: {location}", passed, 
                    f"Expected {expected_count}, got {actual_count} reminders")
        except Exception as e:
            log_test(f"Near location: {location}", False, f"Error: {e}")

def test_radius_variations():
    """Test 10-12: Various radius values"""
    print("\n=== RADIUS VARIATION TESTS ===")
    
    # Test with Austin coords and different radii
    lat, lng = 30.2672, -97.7431
    radius_tests = [
        (100, "100m radius"),  # Small
        (1000, "1km radius"),  # Medium
        (10000, "10km radius"),  # Large
    ]
    
    for radius, description in radius_tests:
        try:
            response = requests.get(
                f"{BASE_URL}/api/reminders/near-location",
                params={"lat": lat, "lng": lng, "radius": radius},
                headers=HEADERS
            )
            data = response.json()
            passed = response.status_code == 200 and "data" in data
            count = len(data.get("data", []))
            log_test(f"Radius test: {description}", passed, 
                    f"Found {count} reminders within {radius}m")
        except Exception as e:
            log_test(f"Radius test: {description}", False, f"Error: {e}")

def test_distance_sorting():
    """Test 13: Distance sorting"""
    print("\n=== DISTANCE SORTING TEST ===")
    try:
        # Query from a central US location
        lat, lng = 35.0, -95.0  # Central US
        response = requests.get(
            f"{BASE_URL}/api/reminders/near-location",
            params={"lat": lat, "lng": lng, "radius": 50000},  # 50km
            headers=HEADERS
        )
        data = response.json()
        reminders = data.get("data", [])
        
        # Check if distances are in ascending order
        distances = [r.get("distance", float('inf')) for r in reminders if "distance" in r]
        sorted_distances = sorted(distances)
        passed = distances == sorted_distances and len(reminders) >= 3
        
        if len(reminders) > 0:
            log_test("Distance sorting (closest first)", passed, 
                    f"Found {len(reminders)} reminders, first 3 distances: {[f'{d:.0f}m' for d in distances[:3]]}")
        else:
            log_test("Distance sorting (closest first)", False, "No reminders found")
    except Exception as e:
        log_test("Distance sorting", False, f"Error: {e}")

def test_database_schema():
    """Test 14-15: Database schema verification"""
    print("\n=== DATABASE SCHEMA TESTS ===")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check columns exist
        cursor.execute("PRAGMA table_info(reminders)")
        columns = {row[1] for row in cursor.fetchall()}
        required_cols = {"location_name", "location_address", "location_lat", "location_lng"}
        missing = required_cols - columns
        passed = required_cols.issubset(columns)
        log_test("Location columns exist", passed, 
                f"Required: {len(required_cols)}, Found: {len(required_cols & columns)}" + (f", Missing: {missing}" if missing else ""))
        
        # Check data is stored
        cursor.execute("""
            SELECT COUNT(*) FROM reminders 
            WHERE location_name IS NOT NULL 
            AND location_lat IS NOT NULL 
            AND location_lng IS NOT NULL
        """)
        count = cursor.fetchone()[0]
        passed = count >= 3
        log_test("Location data stored correctly", passed, 
                f"Found {count} reminders with complete location data")
        
        conn.close()
    except Exception as e:
        log_test("Database schema tests", False, f"Error: {e}")

def test_api_response_format():
    """Test 16-17: API response format"""
    print("\n=== API RESPONSE FORMAT TESTS ===")
    
    try:
        # Get all reminders
        response = requests.get(f"{BASE_URL}/api/reminders", headers=HEADERS)
        data = response.json()
        
        # Check pagination metadata
        passed = all(k in data for k in ["data", "pagination"])
        pagination = data.get("pagination", {})
        log_test("Pagination metadata present", passed, 
                f"Total: {pagination.get('total')}, Limit: {pagination.get('limit')}, Returned: {pagination.get('returned')}")
        
        # Check location fields in reminders
        reminders = data.get("data", [])
        location_reminders = [r for r in reminders if r.get("location_name")]
        if location_reminders:
            sample = location_reminders[0]
            has_fields = all(k in sample for k in ["location_name", "location_lat", "location_lng", "location_address"])
            log_test("Location fields in response", has_fields, 
                    f"Sample: '{sample.get('location_name')}' at ({sample.get('location_lat')}, {sample.get('location_lng')})")
        else:
            log_test("Location fields in response", False, "No location reminders found")
            
    except Exception as e:
        log_test("API response format", False, f"Error: {e}")

def test_authentication():
    """Test 18: Authentication required"""
    print("\n=== AUTHENTICATION TEST ===")
    
    try:
        # Try without token
        response = requests.get(f"{BASE_URL}/api/reminders/near-location?lat=30&lng=-97&radius=10000")
        passed = response.status_code == 401
        log_test("Authentication required for near-location", passed, 
                f"Status without token: {response.status_code} (expected 401)")
    except Exception as e:
        log_test("Authentication required", False, f"Error: {e}")

def test_sample_queries():
    """Test 19-20: Sample real-world queries"""
    print("\n=== SAMPLE QUERY TESTS ===")
    
    try:
        # Test 1: Get reminder by ID
        if created_reminder_ids:
            test_id = created_reminder_ids[0]
            response = requests.get(f"{BASE_URL}/api/reminders/{test_id}", headers=HEADERS)
            data = response.json()
            passed = response.status_code == 200 and data.get("id") == test_id
            log_test("Get reminder by ID", passed, f"Retrieved: '{data.get('text', '')[:30]}...'")
        else:
            log_test("Get reminder by ID", False, "No test reminders created")
            
        # Test 2: Query with distance field
        response = requests.get(
            f"{BASE_URL}/api/reminders/near-location",
            params={"lat": 37.7749, "lng": -122.4194, "radius": 5000},
            headers=HEADERS
        )
        data = response.json()
        reminders = data.get("data", [])
        if reminders:
            has_distance = "distance" in reminders[0]
            log_test("Distance field included in results", has_distance, 
                    f"First result distance: {reminders[0].get('distance', 'N/A')}m")
        else:
            log_test("Distance field included in results", False, "No reminders found in query")
            
    except Exception as e:
        log_test("Sample queries", False, f"Error: {e}")

def cleanup_test_data():
    """Clean up test reminders"""
    print("\n=== CLEANUP ===")
    cleaned = 0
    for reminder_id in created_reminder_ids:
        try:
            response = requests.delete(f"{BASE_URL}/api/reminders/{reminder_id}", headers=HEADERS)
            if response.status_code == 204:
                cleaned += 1
        except:
            pass
    print(f"Cleaned up {cleaned}/{len(created_reminder_ids)} test reminders")

def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    total = tests_passed + tests_failed
    pass_rate = (tests_passed / total * 100) if total > 0 else 0
    print(f"Total Tests: {total}")
    print(f"Passed: {tests_passed} ({'✓' if tests_passed == total else '~'})")
    print(f"Failed: {tests_failed} ({'✗' if tests_failed > 0 else '✓'})")
    print(f"Pass Rate: {pass_rate:.1f}%")
    
    if tests_failed > 0:
        print("\nFailed Tests:")
        for result in test_results:
            if result.startswith("[FAIL]"):
                print(f"  - {result}")
    
    print("="*60)
    
    # Save results to file
    with open("/Users/mini/Documents/Projects/ProjectReminder/test-results-phase6.txt", "w") as f:
        f.write(f"Phase 6 Location Features - Comprehensive Test Results\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Test Environment: FastAPI @ {BASE_URL}\n")
        f.write("="*60 + "\n\n")
        f.write("\n".join(test_results))
        f.write("\n\n" + "="*60 + "\n")
        f.write("SUMMARY\n")
        f.write("="*60 + "\n")
        f.write(f"Total Tests: {total}\n")
        f.write(f"Passed: {tests_passed}\n")
        f.write(f"Failed: {tests_failed}\n")
        f.write(f"Pass Rate: {pass_rate:.1f}%\n")
        f.write("="*60 + "\n")
        
        if tests_failed > 0:
            f.write("\nFailed Tests:\n")
            for result in test_results:
                if result.startswith("[FAIL]"):
                    f.write(f"{result}\n")

if __name__ == "__main__":
    print("="*60)
    print("Phase 6 Location Features - Comprehensive Test Suite")
    print("="*60)
    print(f"Target: {BASE_URL}")
    print(f"Database: {DB_PATH}")
    print("="*60)
    
    # Run all tests
    test_health()
    test_mapbox_config()
    test_create_reminders()
    test_near_location()
    test_radius_variations()
    test_distance_sorting()
    test_database_schema()
    test_api_response_format()
    test_authentication()
    test_sample_queries()
    
    # Cleanup
    cleanup_test_data()
    
    # Print summary
    print_summary()
