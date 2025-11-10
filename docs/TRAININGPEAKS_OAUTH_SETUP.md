# TrainingPeaks OAuth Setup Guide

## Overview

This guide walks you through setting up OAuth authentication with TrainingPeaks so you can:
- Fetch athlete thresholds (FTP, LTHR, etc.)
- Download workout data
- Get daily metrics (HRV, RHR, sleep)
- Use the `--tp-compare` feature in the test harness

## Prerequisites

- TrainingPeaks account
- AutoCoach development environment set up
- FastAPI server running capability

## Step 1: Request TrainingPeaks API Access

### 1.1 Apply for API Access

1. Go to: **https://api.trainingpeaks.com/request-access**
2. Fill out the API access request form:
   - **Application Name**: AutoCoach (or your project name)
   - **Description**: Personal training analysis tool for endurance athletes
   - **Use Case**: Personal use / Research / Development (be specific)
   - **Redirect URI**: `http://localhost:8000/auth/callback`
   - **API Version**: v2 (or latest)

3. Submit the request

### 1.2 Wait for Approval

- **Timeline**: Can take 1-2 weeks for approval
- **Sandbox Access**: You'll get sandbox credentials first
- **Production Access**: Requires additional approval

### 1.3 Receive Credentials

You'll receive an email with:
- **Client ID**: Your application's unique identifier
- **Client Secret**: Your application's secret key (keep this secure!)
- **Sandbox API Base**: `https://api.sandbox.trainingpeaks.com`
- **Sandbox OAuth Base**: `https://oauth.sandbox.trainingpeaks.com`

**⚠️ Important**: Never commit Client Secret to git. Always use `.env` file.

## Step 2: Configure Environment Variables

### 2.1 Create `.env` File

```bash
cd /Users/jeffbutler/Dev/AutoCoach
cp env.template .env
```

### 2.2 Edit `.env` File

Open `.env` in your editor and fill in:

```bash
# TrainingPeaks API Configuration
TRAININGPEAKS_CLIENT_ID=your_actual_client_id_here
TRAININGPEAKS_CLIENT_SECRET=your_actual_client_secret_here

# Redirect URI (must match what you registered with TP)
TRAININGPEAKS_REDIRECT_URI=http://localhost:8000/auth/callback

# Use sandbox for testing (change to false for production later)
TRAININGPEAKS_SANDBOX=true

# Leave these empty for now - we'll get them in Step 4
TRAININGPEAKS_ACCESS_TOKEN=
TRAININGPEAKS_REFRESH_TOKEN=
```

### 2.3 Verify `.gitignore`

Make sure `.env` is in your `.gitignore` (it should already be):

```bash
grep -q "^\.env$" .gitignore && echo "✓ .env is ignored" || echo "⚠ Add .env to .gitignore!"
```

## Step 3: Start FastAPI Server

### 3.1 Activate Virtual Environment

```bash
cd /Users/jeffbutler/Dev/AutoCoach
source ac_env/bin/activate
```

### 3.2 Start the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 3.3 Verify Server is Running

Open browser and go to: **http://localhost:8000**

You should see:
```json
{"status": "ok"}
```

Also check the API docs: **http://localhost:8000/docs**

## Step 4: Complete OAuth Flow

### 4.1 Initiate OAuth Flow

Open your browser and navigate to:

**http://localhost:8000/auth/trainingpeaks?sandbox=true**

You should see a JSON response with an authorization URL:
```json
{
  "authorization_url": "https://oauth.sandbox.trainingpeaks.com/oauth/authorize?client_id=YOUR_CLIENT_ID&..."
}
```

### 4.2 Visit Authorization URL

Copy the entire `authorization_url` from the response and paste it into your browser.

You'll be redirected to TrainingPeaks login page:
1. **Log in** to your TrainingPeaks account (sandbox or production)
2. **Review permissions** requested by AutoCoach
3. **Click "Authorize"** to grant access

### 4.3 Authorization Callback

After authorization, TrainingPeaks will redirect you to:
```
http://localhost:8000/auth/callback?code=AUTHORIZATION_CODE_HERE
```

You should see a success response:
```json
{
  "message": "Authentication successful",
  "access_token": "eyJhbGciOiJSUzI1Ni...",
  "expires_in": 3600
}
```

**⚠️ Important**: The full tokens are stored in the FastAPI server's memory but NOT persisted yet.

### 4.4 Get and Save Tokens

#### Option A: Manual Extraction (Quick & Dirty)

The tokens are in the server's memory. To extract them, you need to add a temporary endpoint or use the server logs.

**Better Option B: Proper Token Management**

Let's add a token retrieval endpoint. Create a temporary script:

```bash
cat > /Users/jeffbutler/Dev/AutoCoach/scripts/get_tokens.py << 'EOF'
#!/usr/bin/env python3
"""Extract OAuth tokens from FastAPI server."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import tp_client

if tp_client and tp_client.oauth_session.token:
    token = tp_client.oauth_session.token
    print("\n✓ Tokens found! Add these to your .env file:\n")
    print(f"TRAININGPEAKS_ACCESS_TOKEN={token.get('access_token', '')}")
    print(f"TRAININGPEAKS_REFRESH_TOKEN={token.get('refresh_token', '')}")
    print(f"\nExpires in: {token.get('expires_in', 'Unknown')} seconds")
else:
    print("✗ No tokens found. Complete OAuth flow first.")
    sys.exit(1)
EOF

chmod +x /Users/jeffbutler/Dev/AutoCoach/scripts/get_tokens.py
```

**Run it while the server is running** (in a new terminal):

```bash
cd /Users/jeffbutler/Dev/AutoCoach
source ac_env/bin/activate
PYTHONPATH=/Users/jeffbutler/Dev/AutoCoach python scripts/get_tokens.py
```

### 4.5 Update `.env` with Tokens

Copy the output from the previous step and paste into your `.env` file:

```bash
TRAININGPEAKS_ACCESS_TOKEN=eyJhbGciOiJSUzI1NiIsIn...  (very long string)
TRAININGPEAKS_REFRESH_TOKEN=def50200a7f3b2c...  (also long)
```

Save the file.

## Step 5: Test the Connection

### 5.1 Test with Test Harness

```bash
cd /Users/jeffbutler/Dev/AutoCoach
source ac_env/bin/activate
PYTHONPATH=/Users/jeffbutler/Dev/AutoCoach python scripts/test_harness.py --tp-test
```

Expected output:
```
================================================================================
  TrainingPeaks API Test
================================================================================

✓ TrainingPeaks client initialized
  API Base: https://api.sandbox.trainingpeaks.com
  OAuth Base: https://oauth.sandbox.trainingpeaks.com
✓ Access token found

Fetching athlete profile...
✓ Authenticated as: Your Name
  Athlete ID: 123456
  Email: your.email@example.com

Fetching athlete thresholds...
✓ Thresholds retrieved
  FTP: 265W
  LTHR: 168 bpm
```

### 5.2 Test Profile Endpoint

With server still running, visit:
**http://localhost:8000/trainingpeaks/profile**

You should see your athlete profile JSON.

### 5.3 Test Activities Endpoint

**http://localhost:8000/trainingpeaks/activities?start_date=2024-02-29&end_date=2024-02-29**

You should see activities from that date (if any exist).

## Step 6: Run Full Comparison

Now you can use the test harness comparison feature!

```bash
cd /Users/jeffbutler/Dev/AutoCoach
source ac_env/bin/activate
PYTHONPATH=/Users/jeffbutler/Dev/AutoCoach python scripts/test_harness.py \
  --file data/sample_workouts/Purple\ Patch-\ Nancy\ \&\ Frank\ Duet.fit.gz \
  --tp-compare
```

Expected sections in output:
- ✓ FIT File Analysis
- ✓ TrainingPeaks Data Fetch (threshold, metrics, workout)
- ✓ Comparison (side-by-side with match indicators)

## Troubleshooting

### Error: "TRAININGPEAKS_CLIENT_ID must be set"

**Problem**: `.env` file not loaded or missing credentials

**Solution**:
```bash
# Check if .env exists
ls -la .env

# Check if dotenv is loading
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('TRAININGPEAKS_CLIENT_ID'))"
```

### Error: "Not authenticated with TrainingPeaks"

**Problem**: Tokens expired or not set

**Solution**:
1. Check token expiration (usually 1 hour)
2. Run OAuth flow again (Step 4)
3. Or implement token refresh:

```bash
# Test token refresh
curl -X POST http://localhost:8000/trainingpeaks/refresh
```

### Error: "Invalid client credentials"

**Problem**: Wrong Client ID or Secret

**Solutions**:
- Double-check credentials in TrainingPeaks API portal
- Ensure no extra spaces in `.env` file
- Try regenerating credentials in TP portal

### Error: "Redirect URI mismatch"

**Problem**: The redirect URI in your request doesn't match what's registered

**Solution**:
1. Check registered URI in TrainingPeaks API portal
2. Update `.env` to match exactly: `TRAININGPEAKS_REDIRECT_URI=http://localhost:8000/auth/callback`
3. Restart server after changing `.env`

### Sandbox vs Production

**Sandbox** (for testing):
- Separate from production data
- No impact on real training data
- Faster approval process
- Use `TRAININGPEAKS_SANDBOX=true`

**Production** (for real use):
- Requires additional approval
- Access to real athlete data
- Use `TRAININGPEAKS_SANDBOX=false`
- Change `.env` and restart server

## Token Management

### Token Expiration

Access tokens typically expire after **1 hour**. You'll need to:

1. **Option A**: Re-run OAuth flow
2. **Option B**: Use refresh token to get new access token
3. **Option C**: Implement automatic refresh (recommended for production)

### Automatic Token Refresh (TODO)

The TrainingPeaks client already has `refresh_access_token()` method. We should:
1. Catch 401 errors
2. Automatically refresh token
3. Retry the request
4. Update stored tokens

### Security Best Practices

1. **Never commit** `.env` to git
2. **Never log** full tokens (we truncate in responses)
3. **Store tokens securely** in production (encrypted database, not files)
4. **Rotate credentials** periodically
5. **Use HTTPS** in production (not http://localhost)

## Next Steps

### For Development
1. ✓ Complete OAuth setup
2. ✓ Test with sample workout
3. Run comparisons to validate metrics
4. Add more sample workouts for testing

### For Production
1. Apply for production API access
2. Implement proper token storage (database)
3. Add token refresh automation
4. Set up multi-user token management
5. Implement OAuth state parameter for CSRF protection
6. Add proper error handling for rate limits

## Rate Limits

TrainingPeaks API rate limits (check latest documentation):
- **Requests**: ~100 requests per 15 minutes
- **Daily limit**: ~1,000 requests per day
- **Avoid**: Polling/frequent requests
- **Use**: Webhooks (if available) or cache data

## Useful Resources

- **TrainingPeaks API Docs**: https://api.trainingpeaks.com/docs
- **OAuth 2.0 Spec**: https://oauth.net/2/
- **Authlib Docs**: https://docs.authlib.org/
- **TrainingPeaks Support**: support@trainingpeaks.com

## Quick Reference

### Environment Variables
```bash
TRAININGPEAKS_CLIENT_ID          # Required: Your app's client ID
TRAININGPEAKS_CLIENT_SECRET      # Required: Your app's secret
TRAININGPEAKS_REDIRECT_URI       # Optional: Default is localhost:8000/auth/callback
TRAININGPEAKS_ACCESS_TOKEN       # Optional: Pre-existing token
TRAININGPEAKS_REFRESH_TOKEN      # Optional: For refreshing access token
TRAININGPEAKS_SANDBOX            # Optional: true=sandbox, false=production
```

### Key URLs
```bash
# Initiate OAuth
http://localhost:8000/auth/trainingpeaks?sandbox=true

# OAuth callback (automatic)
http://localhost:8000/auth/callback?code=...

# Test endpoints
http://localhost:8000/trainingpeaks/profile
http://localhost:8000/trainingpeaks/activities?start_date=2024-02-29&end_date=2024-02-29

# API documentation
http://localhost:8000/docs
```

### Test Harness Commands
```bash
# Test connection
PYTHONPATH=. python scripts/test_harness.py --tp-test

# Sync current FTP
PYTHONPATH=. python scripts/test_harness.py --file sample.fit.gz --tp-sync

# Full comparison
PYTHONPATH=. python scripts/test_harness.py --file sample.fit.gz --tp-compare
```

