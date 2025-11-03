#!/bin/bash
# Test Production API Endpoints
# Usage: ./test-production.sh <WORKER_URL>
# Example: ./test-production.sh https://reminders-api.autumnsgarden.workers.dev

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
WORKER_URL="${1:-}"
API_TOKEN="c27d0f34a3fbbb12faf361328615bfd42033b4adfc80732b30bdbaa7d3d0bc60"

if [ -z "$WORKER_URL" ]; then
    echo -e "${RED}Error: Worker URL required${NC}"
    echo "Usage: $0 <WORKER_URL>"
    echo "Example: $0 https://reminders-api.autumnsgarden.workers.dev"
    exit 1
fi

# Remove trailing slash if present
WORKER_URL="${WORKER_URL%/}"

echo "========================================"
echo "Testing Production API"
echo "========================================"
echo "Worker URL: $WORKER_URL"
echo "Timestamp: $(date)"
echo ""

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to run tests
run_test() {
    local test_name="$1"
    local command="$2"
    local expected_status="$3"

    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "${YELLOW}Test $TESTS_RUN: $test_name${NC}"

    # Run command and capture output
    response=$(eval "$command" 2>&1)
    status=$?

    # Check status code
    http_status=$(echo "$response" | grep "HTTP/" | tail -1 | awk '{print $2}')

    if [ -z "$http_status" ]; then
        http_status="000"
    fi

    echo "Expected: $expected_status, Got: $http_status"

    if [ "$http_status" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo "$response" | tail -20
    else
        echo -e "${RED}✗ FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "$response"
    fi

    echo ""
    sleep 1
}

# Test 1: Health check (no auth)
echo "========================================"
echo "Test 1: Health Check (No Auth)"
echo "========================================"
curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
    "$WORKER_URL/api/health" | tee /tmp/test1.txt
echo ""

# Test 2: Auth failure (no token)
echo "========================================"
echo "Test 2: Auth Failure (No Token)"
echo "========================================"
curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
    "$WORKER_URL/api/reminders" | tee /tmp/test2.txt
echo ""

# Test 3: Create reminder
echo "========================================"
echo "Test 3: Create Reminder"
echo "========================================"
CREATE_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
    -X POST "$WORKER_URL/api/reminders" \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "text": "Production test reminder",
        "priority": "chill",
        "category": "test"
    }')
echo "$CREATE_RESPONSE" | tee /tmp/test3.txt

# Extract reminder ID from response
REMINDER_ID=$(echo "$CREATE_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
echo "Created Reminder ID: $REMINDER_ID"
echo ""

if [ -z "$REMINDER_ID" ]; then
    echo -e "${RED}ERROR: Failed to create reminder or extract ID${NC}"
    exit 1
fi

# Test 4: List reminders
echo "========================================"
echo "Test 4: List Reminders"
echo "========================================"
curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
    -H "Authorization: Bearer $API_TOKEN" \
    "$WORKER_URL/api/reminders" | tee /tmp/test4.txt
echo ""

# Test 5: Get specific reminder
echo "========================================"
echo "Test 5: Get Specific Reminder"
echo "========================================"
curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
    -H "Authorization: Bearer $API_TOKEN" \
    "$WORKER_URL/api/reminders/$REMINDER_ID" | tee /tmp/test5.txt
echo ""

# Test 6: Update reminder
echo "========================================"
echo "Test 6: Update Reminder"
echo "========================================"
curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
    -X PATCH "$WORKER_URL/api/reminders/$REMINDER_ID" \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "text": "Updated production test reminder"
    }' | tee /tmp/test6.txt
echo ""

# Test 7: Delete reminder
echo "========================================"
echo "Test 7: Delete Reminder"
echo "========================================"
curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
    -X DELETE "$WORKER_URL/api/reminders/$REMINDER_ID" \
    -H "Authorization: Bearer $API_TOKEN" | tee /tmp/test7.txt
echo ""

# Test 8: CORS preflight
echo "========================================"
echo "Test 8: CORS Preflight"
echo "========================================"
curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
    -X OPTIONS "$WORKER_URL/api/reminders" \
    -H "Origin: http://localhost:3000" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: Content-Type, Authorization" \
    -v 2>&1 | grep -E "(HTTP|access-control)" | tee /tmp/test8.txt
echo ""

# Summary
echo "========================================"
echo "Test Summary"
echo "========================================"
echo "Total Tests: 8"
echo "Expected Results:"
echo "  1. Health check: 200 OK with database status"
echo "  2. No auth: 401 Unauthorized"
echo "  3. Create: 201 Created with UUID"
echo "  4. List: 200 OK with array"
echo "  5. Get: 200 OK with reminder object"
echo "  6. Update: 200 OK with updated object"
echo "  7. Delete: 204 No Content"
echo "  8. CORS: 204 with proper headers"
echo ""
echo "Check /tmp/test*.txt files for detailed responses"
echo "========================================"
