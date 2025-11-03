#!/bin/bash
# Complete Deployment Script for Cloudflare Workers
# This script guides you through the entire deployment process

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================"
echo "Cloudflare Workers Deployment"
echo "========================================${NC}"
echo ""

# Step 1: Check prerequisites
echo -e "${YELLOW}Step 1: Checking prerequisites...${NC}"
if ! command -v npx &> /dev/null; then
    echo -e "${RED}Error: npx not found. Please install Node.js${NC}"
    exit 1
fi

if ! command -v wrangler &> /dev/null && ! npx wrangler --version &> /dev/null; then
    echo -e "${RED}Error: wrangler not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites met${NC}"
echo ""

# Step 2: Check login status
echo -e "${YELLOW}Step 2: Checking Cloudflare authentication...${NC}"
if ! npx wrangler whoami &> /dev/null; then
    echo -e "${RED}Error: Not logged in to Cloudflare${NC}"
    echo "Run: npx wrangler login"
    exit 1
fi

ACCOUNT_INFO=$(npx wrangler whoami 2>&1)
echo "$ACCOUNT_INFO"
echo -e "${GREEN}✓ Logged in${NC}"
echo ""

# Step 3: Check subdomain registration
echo -e "${YELLOW}Step 3: Checking workers.dev subdomain...${NC}"
echo ""
echo "IMPORTANT: You need a workers.dev subdomain registered."
echo ""
echo "To check if you have one, try deploying:"
echo "  npx wrangler deploy --dry-run"
echo ""
echo "If you see an error about needing a subdomain, register one at:"
ACCOUNT_ID=$(echo "$ACCOUNT_INFO" | grep "Account ID" | awk '{print $NF}')
echo -e "${BLUE}https://dash.cloudflare.com/$ACCOUNT_ID/workers/onboarding${NC}"
echo ""
read -p "Have you registered a workers.dev subdomain? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Please register a subdomain first, then run this script again.${NC}"
    exit 0
fi

# Step 4: Verify D1 database
echo -e "${YELLOW}Step 4: Verifying D1 database connection...${NC}"
DB_CHECK=$(npx wrangler d1 execute reminders-db --remote --command="SELECT COUNT(*) as count FROM reminders" 2>&1)
if echo "$DB_CHECK" | grep -q "success"; then
    REMINDER_COUNT=$(echo "$DB_CHECK" | grep -o '"count":[0-9]*' | cut -d':' -f2)
    echo -e "${GREEN}✓ Database connected (${REMINDER_COUNT} reminders)${NC}"
else
    echo -e "${RED}✗ Database connection failed${NC}"
    echo "$DB_CHECK"
    exit 1
fi
echo ""

# Step 5: Deploy Worker
echo -e "${YELLOW}Step 5: Deploying Worker...${NC}"
echo ""
DEPLOY_OUTPUT=$(npx wrangler deploy 2>&1)
echo "$DEPLOY_OUTPUT"

if echo "$DEPLOY_OUTPUT" | grep -q "Published"; then
    echo -e "${GREEN}✓ Deployment successful!${NC}"

    # Extract Worker URL
    WORKER_URL=$(echo "$DEPLOY_OUTPUT" | grep -o 'https://[^ ]*workers.dev' | head -1)

    if [ -n "$WORKER_URL" ]; then
        echo ""
        echo -e "${GREEN}Your Worker URL: $WORKER_URL${NC}"
        echo ""

        # Save URL for later use
        echo "$WORKER_URL" > .worker-url

    else
        echo -e "${YELLOW}Warning: Could not extract Worker URL from output${NC}"
        echo "Please check the output above for your Worker URL"
        read -p "Enter your Worker URL: " WORKER_URL
        echo "$WORKER_URL" > .worker-url
    fi
else
    echo -e "${RED}✗ Deployment failed${NC}"
    exit 1
fi
echo ""

# Step 6: Set production secrets
echo -e "${YELLOW}Step 6: Setting production secrets...${NC}"
echo ""
echo "Checking if API_TOKEN secret is set..."
SECRET_LIST=$(npx wrangler secret list 2>&1)

if echo "$SECRET_LIST" | grep -q "API_TOKEN"; then
    echo -e "${GREEN}✓ API_TOKEN already set${NC}"
else
    echo "API_TOKEN not found. Setting now..."
    echo "The token value is: c27d0f34a3fbbb12faf361328615bfd42033b4adfc80732b30bdbaa7d3d0bc60"
    echo ""
    echo "When prompted, paste the token above."
    echo ""
    npx wrangler secret put API_TOKEN
    echo -e "${GREEN}✓ API_TOKEN set${NC}"
fi
echo ""

# Step 7: Test health endpoint
echo -e "${YELLOW}Step 7: Testing deployment...${NC}"
echo ""
echo "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s "$WORKER_URL/api/health")
echo "$HEALTH_RESPONSE"

if echo "$HEALTH_RESPONSE" | grep -q "connected"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${YELLOW}⚠ Health check returned unexpected response${NC}"
fi
echo ""

# Step 8: Run comprehensive tests
echo -e "${YELLOW}Step 8: Running comprehensive API tests...${NC}"
echo ""
read -p "Would you like to run the full test suite? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    chmod +x ./test-production.sh
    ./test-production.sh "$WORKER_URL"
else
    echo "Skipping tests. You can run them manually with:"
    echo "  ./test-production.sh $WORKER_URL"
fi
echo ""

# Step 9: Update frontend configuration
echo -e "${YELLOW}Step 9: Frontend configuration${NC}"
echo ""
echo "To connect your frontend to the cloud API:"
echo ""
echo "1. Edit public/config.json:"
echo "   \"cloud_endpoint\": \"$WORKER_URL/api\""
echo ""
echo "2. To test cloud mode, in your browser console:"
echo "   localStorage.setItem('cloudApiUrl', '$WORKER_URL/api')"
echo ""

# Summary
echo -e "${BLUE}========================================"
echo "Deployment Complete!"
echo "========================================${NC}"
echo ""
echo -e "${GREEN}✓ Worker deployed${NC}"
echo -e "${GREEN}✓ Secrets configured${NC}"
echo -e "${GREEN}✓ Database connected${NC}"
echo ""
echo "Worker URL: $WORKER_URL"
echo "API Endpoint: $WORKER_URL/api"
echo ""
echo "Next steps:"
echo "1. Update frontend config.json with the Worker URL"
echo "2. Test the API with: ./test-production.sh $WORKER_URL"
echo "3. Update documentation with the new Worker URL"
echo ""
echo -e "${BLUE}=======================================${NC}"
