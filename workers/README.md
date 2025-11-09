# Cloudflare Workers API - Deployment & Testing

This directory contains the Cloudflare Workers API for the ADHD-Friendly Voice Reminders System, featuring:
- **D1 Database** for multi-device sync and backup
- **Workers AI** with GPT-OSS 20B for cloud-based NLP parsing
- **Global Edge Deployment** via Cloudflare's network
- **TypeScript** with Hono framework for type safety

## Quick Start

### Prerequisites
- Node.js 16+ installed
- Cloudflare account with Workers enabled
- **Workers AI access** (requires paid plan or trial)
- Logged in with `npx wrangler login`

## Workers AI Configuration

### Overview

Workers AI is integrated for natural language parsing of reminder text. The system uses **GPT-OSS 20B** model for:
- Extracting due dates and times from user input
- Parsing task priority and categories
- Understanding temporal expressions (e.g., "tomorrow at 3pm")
- Converting voice transcripts to structured reminder data

### AI Model Details

**Model:** `@cf/openai/gpt-oss-20b`
- **Purpose:** Natural language understanding and temporal extraction
- **Context window:** 2048 tokens
- **Performance:** Better temporal extraction than Llama 3.2 1B
- **Latency:** ~500-1000ms per request (varies by input length)

### Binding Configuration

The AI binding is configured in `wrangler.toml`:

```toml
[ai]
binding = "AI"
```

This creates an `AI` object accessible in Worker code via `env.AI`.

### Using Workers AI in Code

To use the AI model in `src/index.ts`:

```typescript
// Type definition for AI binding (add to Bindings type)
type Bindings = {
  DB: D1Database
  API_TOKEN: string
  AI: any  // Workers AI binding
  ENVIRONMENT?: string
}

// Usage example: Parse reminder text
async function parseReminderWithAI(env: any, text: string) {
  try {
    const response = await env.AI.run('@cf/openai/gpt-oss-20b', {
      messages: [
        {
          role: 'system',
          content: `You are a reminder parser. Extract structured data from user input.

Return JSON with: {
  "text": "cleaned task description",
  "due_date": "YYYY-MM-DD or null",
  "due_time": "HH:MM:SS or null",
  "priority": "chill|important|urgent",
  "category": "work|personal|health|home|shopping|finance|other",
  "location": "location string or null",
  "recurrence": "once|daily|weekly|monthly|yearly or null"
}`
        },
        {
          role: 'user',
          content: text
        }
      ],
      temperature: 0.3,
      max_tokens: 400
    })

    // Parse response
    const parsed = JSON.parse(response.response)
    return parsed
  } catch (error) {
    console.error('AI parsing failed:', error)
    // Fallback: return basic reminder with just text
    return { text, priority: 'chill', category: 'personal' }
  }
}
```

### API Endpoint Example: Parse Text

Future endpoint to leverage Workers AI:

```bash
POST /api/parse
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "text": "Buy milk tomorrow at 3pm"
}

Response:
{
  "text": "Buy milk",
  "due_date": "2025-11-10",
  "due_time": "15:00:00",
  "priority": "chill",
  "category": "shopping",
  "location": null,
  "recurrence": "once"
}
```

### Model Capabilities & Limitations

**Strengths:**
- ✅ Accurate temporal expression parsing ("next Tuesday", "3 weeks from now")
- ✅ Priority inference from keywords ("urgent", "ASAP", "eventually")
- ✅ Location extraction for place-based reminders
- ✅ Category classification for task organization
- ✅ Recurrence pattern recognition

**Limitations:**
- ⚠️ Doesn't generate absolute dates (needs current date context)
- ⚠️ Timezone-naive (returns times without timezone info)
- ⚠️ May struggle with ambiguous inputs
- ⚠️ Requires well-formed system prompts

### Cost Estimates

**Workers AI Pricing:**
- **Pay-as-you-go model:** Charged per 1000 neurons (model-specific)
- **GPT-OSS 20B:** ~$0.011 per inference (100 neurons per 1000)

**Estimated Costs (MVP):**
- 100 parses/day × 30 days = 3,000 parses/month
- ~3,000 parses × $0.00011 = **~$0.33/month**
- With local Llama as fallback: **<$1/month**

**Limits:**
- Free tier: 1,000 Workers AI calls/day
- Paid tier: No daily limit, pay per inference
- Recommended: Use local Llama for frequent parsing, Workers AI for fallback

### Switching Models

To use a different Workers AI model:

1. Check available models: https://developers.cloudflare.com/workers-ai/models/
2. Update model ID in code:
   ```typescript
   // Change from:
   await env.AI.run('@cf/openai/gpt-oss-20b', {...})

   // To:
   await env.AI.run('@cf/meta/llama-2-7b-chat-int8', {...})
   ```
3. Adjust system prompt for model capabilities
4. Test thoroughly (different models have different behaviors)

### Troubleshooting AI

**Error: "AI binding not found"**
- Check `wrangler.toml` has `[ai]` section with `binding = "AI"`
- Verify Cloudflare account has Workers AI access
- Redeploy: `npx wrangler deploy`

**Error: "Model not found" / 400 response**
- Verify exact model ID: `@cf/openai/gpt-oss-20b`
- Check Workers AI is enabled on your account
- Review pricing/plan requirements for the model

**Errors: API returns `null` or malformed JSON**
- Increase `max_tokens` if response is cut off
- Ensure JSON format in system prompt
- Add error handling to parse invalid responses

**High latency (>2 seconds)**
- Workers AI queries can take 500ms-2s depending on model
- Consider caching results for similar inputs
- Use local Llama for time-sensitive operations

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

### Workers AI Issues

**Problem:** AI endpoints fail or return 400/401 errors

**Solutions:**
- See "Troubleshooting AI" section above (detailed AI-specific guidance)
- Verify Workers AI binding in wrangler.toml
- Check Cloudflare account has Workers AI enabled
- Review API documentation: https://developers.cloudflare.com/workers-ai/

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
- [Workers AI Documentation](https://developers.cloudflare.com/workers-ai/)
- [Workers AI Models Catalog](https://developers.cloudflare.com/workers-ai/models/)
- [D1 Database Docs](https://developers.cloudflare.com/d1/)
- [Hono Framework](https://hono.dev/)
- [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/)

---

**Last Updated:** 2025-11-09
**Phase:** 4 - Cloud Infrastructure with AI Integration
**Status:** Production Ready
**Model:** Claude Sonnet 4.5
**Workers AI Model:** GPT-OSS 20B
