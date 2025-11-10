# Strava Quick Start (5 Minutes)

## Prerequisites

- Python 3.9+ with `ac_env` virtual environment
- Strava account
- 5 minutes ⏱️

## 1. Create Strava App (2 minutes)

1. Go to: https://www.strava.com/settings/api
2. Click **"Create App"** (or "My API Application" if you have one)
3. Fill in:
   - **Application Name**: AutoCoach
   - **Website**: https://autocoach.eve-market.space (or localhost for dev)
   - **Authorization Callback Domain**: `localhost` (for dev) or `autocoach.eve-market.space` (for prod)
4. Click **"Create"**
5. Note your **Client ID** and **Client Secret**

## 2. Configure AutoCoach (1 minute)

```bash
cd /Users/jeffbutler/Dev/AutoCoach

# Copy template
cp env.template .env

# Edit .env and add your credentials
# STRAVA_CLIENT_ID=12345
# STRAVA_CLIENT_SECRET=abc123...
# OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback
```

## 3. Authorize (2 minutes)

### Option A: Automated Script (Recommended)

```bash
# Activate virtual environment
source ac_env/bin/activate

# Run OAuth helper
python scripts/get_strava_tokens.py
```

The script will:
1. Generate authorization URL
2. Prompt you to open it in a browser
3. Ask you to paste the authorization code
4. Exchange code for tokens
5. Save tokens to `.env` automatically

### Option B: Manual (if script doesn't work)

```bash
# 1. Start server
source ac_env/bin/activate
python -m uvicorn app.main:app --reload --port 8000

# 2. In another terminal, get auth URL
curl http://localhost:8000/auth/strava

# 3. Open the authorization_url in browser
# 4. Authorize and you'll be redirected to callback
# 5. Tokens are exchanged automatically
```

## 4. Test It!

```bash
# Get your athlete profile
curl http://localhost:8000/strava/athlete

# Get training zones
curl http://localhost:8000/strava/zones

# Get last 7 days of activities
curl "http://localhost:8000/strava/activities?start_date=2025-11-03&end_date=2025-11-10"

# Get a specific activity with streams
curl http://localhost:8000/strava/activity/12345678
curl http://localhost:8000/strava/activity/12345678/streams

# Compute metrics (TSS, CTL, ATL, TSB)
curl -X POST "http://localhost:8000/strava/metrics?start_date=2025-11-03&end_date=2025-11-10"
```

## 5. Production Setup (Optional)

For production via Cloudflare tunnel:

1. Update Strava app:
   - Authorization Callback Domain: `autocoach.eve-market.space`

2. Update `.env`:
   ```bash
   OAUTH_REDIRECT_URI=https://autocoach.eve-market.space/auth/callback
   ```

3. Start services:
   ```bash
   ./scripts/start_services.sh
   ```

4. Authorize via:
   ```
   https://autocoach.eve-market.space/auth/strava
   ```

## Common Issues

### "STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be set"
- Check that `.env` file exists
- Verify credentials are set (no quotes needed)
- Restart the server after updating `.env`

### "Authorization callback domain mismatch"
- For localhost: use `localhost` (not `127.0.0.1`)
- Must match exactly in Strava app settings
- Check for typos

### "Not authenticated with Strava"
- Run OAuth flow again
- Check that tokens were saved to `.env`
- Verify `STRAVA_ACCESS_TOKEN` and `STRAVA_REFRESH_TOKEN` are set

## What's Next?

With Strava connected, you can:

1. **Compare FIT files with Strava data**:
   ```bash
   python scripts/test_harness.py --source strava --date 2025-11-08
   ```

2. **Build Performance Management Chart**:
   - Fetch 42+ days of activities
   - Calculate CTL, ATL, TSB
   - Visualize form and fatigue

3. **Detect intervals**:
   - Fetch activity streams
   - Apply interval detection algorithm
   - Compare with planned workouts

4. **Score compliance**:
   - Match detected intervals to workout steps
   - Calculate step pass rates
   - Flag recovery issues

## Rate Limits

Strava limits:
- 100 requests per 15 minutes
- 1,000 requests per day

**Tips**:
- Cache activity data in local database
- Fetch only new/updated activities
- Use batch operations
- Consider webhooks for real-time updates (future)

## Resources

- **Strava API Docs**: https://developers.strava.com/docs/
- **AutoCoach Strava Client**: `app/clients/strava.py`
- **Strava Setup Guide**: `docs/STRAVA_OAUTH_SETUP.md`
- **API Endpoints**: http://localhost:8000/docs (FastAPI auto-docs)

