# Cloudflare Workers API - Deployment & Testing

This directory contains the Cloudflare Workers API for the ADHD-Friendly Voice Reminders System.

## Quick Start

### Prerequisites
- Node.js 16+ installed
- Cloudflare account with Workers enabled
- Logged in with `npx wrangler login`

### One-Command Deployment
```bash
./deploy.sh
```

This interactive script will:
1. Check prerequisites and authentication
2. Guide you through subdomain registration (if needed)
3. Verify D1 database connection
4. Deploy the Worker
5. Configure production secrets
6. Test the deployment
7. Provide frontend configuration instructions

## Manual Deployment

If you prefer manual steps:

### 1. Register workers.dev Subdomain (One-Time)

**Required before first deployment.**

Visit: https://dash.cloudflare.com/YOUR_ACCOUNT_ID/workers/onboarding

Choose a subdomain (e.g., `autumnsgarden`, `reminder-app`)

### 2. Apply Database Migration

```bash
# Apply migration to production D1
npx wrangler d1 execute reminders-db --remote --file=./migrations/002_update_schema.sql

# Verify
npx wrangler d1 execute reminders-db --remote --command="SELECT COUNT(*) FROM reminders"
```

### 3. Deploy Worker

```bash
npx wrangler deploy
```

Expected output:
```
Published reminders-api (X.XX sec)
  https://reminders-api.your-subdomain.workers.dev
```

### 4. Set Production Secrets

```bash
# Set API_TOKEN (paste value when prompted)
npx wrangler secret put API_TOKEN

# The token from secrets.json:
# c27d0f34a3fbbb12faf361328615bfd42033b4adfc80732b30bdbaa7d3d0bc60

# Verify
npx wrangler secret list
```

### 5. Test Deployment

```bash
# Quick health check
curl https://reminders-api.your-subdomain.workers.dev/api/health

# Full test suite
./test-production.sh https://reminders-api.your-subdomain.workers.dev
```

## API Endpoints

### Health Check
```bash
GET /api/health
# No authentication required
# Returns: {"status": "ok", "timestamp": "...", "database": "connected"}
```

### List Reminders
```bash
GET /api/reminders
Authorization: Bearer YOUR_TOKEN

# Optional filters:
GET /api/reminders?status=pending&priority=urgent&category=work
```

### Get Single Reminder
```bash
GET /api/reminders/:id
Authorization: Bearer YOUR_TOKEN
```

### Create Reminder
```bash
POST /api/reminders
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "text": "Buy groceries",
  "priority": "chill",
  "category": "personal",
  "due_date": "2025-11-05",
  "due_time": "15:00:00"
}
```

### Update Reminder
```bash
PATCH /api/reminders/:id
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "text": "Updated text",
  "status": "completed"
}
```

### Delete Reminder
```bash
DELETE /api/reminders/:id
Authorization: Bearer YOUR_TOKEN
```

## Frontend Integration

### Update config.json

Edit `/public/config.json`:

```json
{
  "api": {
    "local_endpoint": "http://localhost:8000/api",
    "cloud_endpoint": "https://reminders-api.your-subdomain.workers.dev/api",
    "use_cloud": false,
    "token": "c27d0f34a3fbbb12faf361328615bfd42033b4adfc80732b30bdbaa7d3d0bc60"
  }
}
```

### Switch to Cloud Mode

In browser console:
```javascript
// Switch to cloud API
config.api.use_cloud = true;
await Storage.saveConfig(config);
location.reload();

// Or temporarily for testing:
localStorage.setItem('cloudApiUrl', 'https://reminders-api.your-subdomain.workers.dev/api');
```

### Test in Browser

1. Start UI server: `python ../serve_ui.py`
2. Open http://localhost:3000
3. Open browser console
4. Set cloud mode: `config.api.use_cloud = true`
5. Try creating/listing reminders
6. Check Network tab for requests to Worker URL

## CORS Configuration

CORS is configured in `src/index.ts` to allow:
- **Origins**: `http://localhost:3000`, `http://localhost:8080`, `http://127.0.0.1:3000`
- **Methods**: GET, POST, PATCH, DELETE, OPTIONS
- **Headers**: Content-Type, Authorization
- **Credentials**: true

To test CORS:
```bash
curl -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type, Authorization" \
  -X OPTIONS \
  https://reminders-api.your-subdomain.workers.dev/api/reminders \
  -v
```

Expected headers:
```
access-control-allow-origin: http://localhost:3000
access-control-allow-methods: GET, POST, PATCH, DELETE, OPTIONS
access-control-allow-headers: Content-Type, Authorization
access-control-allow-credentials: true
```

## Development & Testing

### Local Development

```bash
# Start local dev server with remote D1
npx wrangler dev

# Or with local D1 (requires .wrangler/state/)
npx wrangler dev --local

# Test locally
curl http://localhost:8787/api/health
```

### View Logs

```bash
# Stream logs from production
npx wrangler tail reminders-api

# Filter for errors only
npx wrangler tail reminders-api --status error
```

### View Deployments

```bash
# List recent deployments
npx wrangler deployments list

# Rollback to previous version
npx wrangler rollback <deployment-id>
```

## Database Management

### Execute SQL

```bash
# Production database
npx wrangler d1 execute reminders-db --remote --command="SELECT * FROM reminders LIMIT 5"

# Local database
npx wrangler d1 execute reminders-db --local --command="SELECT * FROM reminders LIMIT 5"
```

### Backup Database

```bash
# Export to SQL
npx wrangler d1 export reminders-db --remote --output=backup.sql

# Import from SQL
npx wrangler d1 execute reminders-db --remote --file=backup.sql
```

### Database Info

```bash
# Get database details
npx wrangler d1 info reminders-db

# List all databases
npx wrangler d1 list
```

## Troubleshooting

### "No subdomain registered" Error

**Problem:** Worker deployment fails with subdomain error

**Solution:**
1. Visit: https://dash.cloudflare.com/YOUR_ACCOUNT_ID/workers/onboarding
2. Register a subdomain
3. Try deployment again

### "Authentication required" Error

**Problem:** API returns 401 Unauthorized

**Solutions:**
- Check if API_TOKEN secret is set: `npx wrangler secret list`
- Verify token matches secrets.json
- Set token: `npx wrangler secret put API_TOKEN`

### CORS Errors

**Problem:** Browser shows CORS errors

**Solutions:**
- Check browser console for specific error
- Verify origin is in allowed list (src/index.ts)
- Test with curl: `curl -H "Origin: http://localhost:3000" URL -v`
- Check for preflight request (OPTIONS method)

### Database Connection Failed

**Problem:** Health check shows "disconnected"

**Solutions:**
- Verify D1 binding in wrangler.toml
- Check database ID matches
- Test: `npx wrangler d1 execute reminders-db --remote --command="SELECT 1"`
- Check Worker logs: `npx wrangler tail reminders-api`

### Worker Not Responding

**Problem:** Requests timeout or fail

**Solutions:**
- Check deployment status: `npx wrangler deployments list`
- View logs: `npx wrangler tail reminders-api`
- Verify Worker URL is correct
- Check Cloudflare dashboard for errors

## Project Structure

```
workers/
├── src/
│   └── index.ts          # Main Worker code (Hono app)
├── migrations/
│   ├── 001_init.sql      # Initial schema
│   └── 002_update_schema.sql  # Updated schema
├── deploy.sh             # Interactive deployment script
├── test-production.sh    # Production API testing
├── wrangler.toml         # Worker configuration
├── .dev.vars             # Local development secrets
└── README.md             # This file
```

## Configuration Files

### wrangler.toml
- Worker name and settings
- D1 database binding
- Environment variables

### .dev.vars (Local Only - Not Committed)
- API_TOKEN for local development
- Other local secrets

## Security Notes

- ✅ API_TOKEN stored in Cloudflare secrets (encrypted)
- ✅ Token required for all write operations
- ✅ CORS restricts origins to localhost
- ✅ Rate limiting via Cloudflare (automatic)
- ✅ Database isolated per account
- ⚠️ Token in config.json for demo purposes only
- ⚠️ Production apps should use OAuth or session tokens

## Performance

- **Edge locations**: Global deployment via Cloudflare's network
- **Cold start**: ~50ms
- **Warm response**: ~10-30ms
- **D1 queries**: ~5-20ms (edge-optimized SQLite)
- **Request size limit**: 100MB
- **Response size limit**: 10MB

## Costs (Free Tier)

- **Workers**: 100,000 requests/day
- **D1**: 5M reads/day, 100K writes/day
- **Storage**: 10GB database size
- **Egress**: 10GB/day

## Additional Resources

- [Cloudflare Workers Docs](https://developers.cloudflare.com/workers/)
- [D1 Database Docs](https://developers.cloudflare.com/d1/)
- [Hono Framework](https://hono.dev/)
- [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/)

---

**Last Updated:** 2025-11-03
**Phase:** 4 - Cloud Infrastructure
**Status:** Production Ready
**Model:** Claude Sonnet 4.5
