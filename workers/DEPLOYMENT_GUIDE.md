# Workers Deployment Guide

## Step 1: Register workers.dev Subdomain (ONE-TIME SETUP)

Your Cloudflare account needs a workers.dev subdomain registered before you can deploy.

### Option A: Use the Dashboard (Recommended)
1. Open this URL: https://dash.cloudflare.com/04e847fa7655624e84414a8280b3a4d0/workers/onboarding
2. Choose a subdomain (e.g., `autumnsgarden`, `reminder-app`, `adhd-reminders`)
3. Click "Register" or "Continue"

### Option B: Use CLI
```bash
# Check current subdomain status
npx wrangler whoami

# The subdomain will be visible once registered
```

## Step 2: Deploy the Worker

Once subdomain is registered:

```bash
cd /Users/mini/Documents/Projects/ProjectReminder/workers
npx wrangler deploy
```

Expected output:
```
Published reminders-api (X.XX sec)
  https://reminders-api.your-subdomain.workers.dev
```

## Step 3: Set Production Secrets

```bash
# Set API_TOKEN (paste value from secrets.json when prompted)
npx wrangler secret put API_TOKEN

# Verify
npx wrangler secret list
```

## Step 4: Test Production Endpoints

```bash
# Save these for testing
export WORKER_URL="https://reminders-api.your-subdomain.workers.dev"
export API_TOKEN="c27d0f34a3fbbb12faf361328615bfd42033b4adfc80732b30bdbaa7d3d0bc60"

# Test health check
curl $WORKER_URL/api/health

# Test with auth
curl $WORKER_URL/api/reminders -H "Authorization: Bearer $API_TOKEN"
```

## Troubleshooting

### "No subdomain" error
- Complete Step 1 above
- Wait a few minutes for propagation
- Try `npx wrangler deploy` again

### "Authentication required" error
- Make sure API_TOKEN secret is set (Step 3)
- Verify token matches secrets.json

### CORS errors from frontend
- Verify CORS headers in index.ts
- Check browser console for specific error
- Test with: `curl -H "Origin: http://localhost:3000" $WORKER_URL/api/health -v`
