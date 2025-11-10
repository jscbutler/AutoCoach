# Strava OAuth Setup Guide

## Why Strava?

**Instant API Access** ✅ No approval process required
**Rich Data**: Power, heart rate, GPS, cadence, temperature
**Large User Base**: Most popular cycling/running platform
**Rate Limits**: 100 req/15min, 1000/day (generous for MVP)

### Strava vs TrainingPeaks Comparison

| Feature | Strava | TrainingPeaks |
|---------|--------|---------------|
| API Access | Instant | 1-2 week approval |
| OAuth Setup | 5 minutes | Requires approval |
| Power Data | ✅ Yes | ✅ Yes |
| Planned Workouts | ❌ No | ✅ Yes |
| TSS Calculation | ❌ No (we calculate) | ✅ Yes |
| Interval Detection | Need our algo | Need our algo |
| Rate Limits | 100/15min, 1000/day | Unknown |
| Cost | Free tier available | Requires subscription |

## Step 1: Create Strava App

1. Go to https://www.strava.com/settings/api
2. Click **"Create App"** or **"My API Application"**
3. Fill in the application form:
   - **Application Name**: AutoCoach (or your preferred name)
   - **Category**: Data Importer, Visualizer, or Training
   - **Club**: Leave blank (or your club if applicable)
   - **Website**: Your website or `https://autocoach.eve-market.space`
   - **Application Description**: "Training analysis platform for endurance athletes"
   - **Authorization Callback Domain**: `autocoach.eve-market.space` (or `localhost` for dev)
   - **Upload Icon**: Optional

4. Click **"Create"**

## Step 2: Get Your Credentials

After creating the app, you'll see:

- **Client ID**: A number (e.g., 12345)
- **Client Secret**: A long string (keep this secret!)
- **Authorization Callback Domain**: Must match your redirect URI

## Step 3: Configure AutoCoach

1. Copy `env.template` to `.env`:
```bash
cd /Users/jeffbutler/Dev/AutoCoach
cp env.template .env
```

2. Edit `.env` and add your Strava credentials:
```bash
# Strava Configuration
STRAVA_CLIENT_ID=12345
STRAVA_CLIENT_SECRET=your_secret_here_abc123...

# For development (local testing)
OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback

# For production (via Cloudflare tunnel)
# OAUTH_REDIRECT_URI=https://autocoach.eve-market.space/auth/callback
```

3. Save the file

## Step 4: Start AutoCoach Server

```bash
# Activate virtual environment
source ac_env/bin/activate

# Start the server (on port 8000)
python -m uvicorn app.main:app --reload --port 8000
```

## Step 5: Authorize with Strava

### Option A: Via Browser (Recommended for First Time)

1. Navigate to: http://localhost:8000/auth/strava
2. You'll see: `{"authorization_url": "https://www.strava.com/oauth/authorize?..."}`
3. Copy the URL from `authorization_url` and paste it in your browser
4. Log in to Strava and click **"Authorize"**
5. You'll be redirected to the callback URL with a code
6. The server will exchange the code for tokens automatically

### Option B: Via curl

```bash
# 1. Get authorization URL
curl http://localhost:8000/auth/strava

# 2. Copy the authorization_url and open it in a browser
# 3. After authorizing, you'll be redirected to:
# http://localhost:8000/auth/strava/callback?code=XXXXX&scope=read,activity:read_all

# 4. The server will handle the callback automatically
```

## Step 6: Test the Integration

```bash
# Get athlete profile
curl http://localhost:8000/strava/athlete

# Get training zones (power & heart rate)
curl http://localhost:8000/strava/zones

# Get activities from the last 7 days
curl "http://localhost:8000/strava/activities?start_date=2025-11-03&end_date=2025-11-10"

# Get detailed activity
curl "http://localhost:8000/strava/activity/12345678"

# Get activity streams (time-series data)
curl "http://localhost:8000/strava/activity/12345678/streams"

# Compute metrics (TSS, CTL, ATL, TSB)
curl -X POST "http://localhost:8000/strava/metrics?start_date=2025-11-03&end_date=2025-11-10"
```

## Step 7: Production Setup (Cloudflare Tunnel)

For production use with the Cloudflare tunnel:

1. Update your Strava app settings:
   - Go to https://www.strava.com/settings/api
   - Change **Authorization Callback Domain** to: `autocoach.eve-market.space`
   - Save changes

2. Update `.env`:
```bash
# Production redirect URI
OAUTH_REDIRECT_URI=https://autocoach.eve-market.space/auth/callback
```

3. Start services:
```bash
cd /Users/jeffbutler/Dev/AutoCoach
./scripts/start_services.sh
```

4. Authorize via:
```
https://autocoach.eve-market.space/auth/strava
```

## Understanding Strava's Data

### Available Activity Data
- **Summary**: Distance, duration, speed, elevation, calories
- **Power**: Average, max, weighted average (NP equivalent)
- **Heart Rate**: Average, max
- **Cadence**: Average, max
- **Temperature**: If available from device

### Available Streams (Time-Series)
- `time`: Seconds from start
- `distance`: Meters from start
- `altitude`: Elevation in meters
- `velocity_smooth`: Speed in m/s
- `heartrate`: Beats per minute
- `cadence`: RPM (cycling) or SPM (running)
- `watts`: Power in watts (cycling)
- `temp`: Temperature in Celsius
- `latlng`: GPS coordinates [lat, lon]
- `grade_smooth`: Gradient percentage

### What Strava Doesn't Provide
- ❌ **TSS**: We calculate it using NP and FTP
- ❌ **Planned Workouts**: Not available via API
- ❌ **FTP History**: Only current FTP from zones
- ❌ **Training Peaks Calendar**: Strava has its own training calendar

## Rate Limits

Strava enforces rate limits:
- **Short term**: 100 requests per 15 minutes
- **Daily**: 1,000 requests per day

Rate limit headers in responses:
```
X-RateLimit-Limit: 600,30000
X-RateLimit-Usage: 5,127
```

**Best Practices**:
- Cache activity data locally
- Fetch in batches (use pagination)
- Only fetch new/updated activities
- Use webhooks for real-time updates (future feature)

## Troubleshooting

### "Not authenticated with Strava"
- Run the OAuth flow again: http://localhost:8000/auth/strava
- Check that `.env` has correct credentials
- Verify the server is running

### "Authorization callback domain mismatch"
- Verify the domain in Strava app settings matches your redirect URI
- For localhost: use `localhost` (not `127.0.0.1`)
- For production: use `autocoach.eve-market.space`

### "Rate limit exceeded"
- Wait for the 15-minute window to reset
- Check `X-RateLimit-Usage` header to monitor usage
- Consider caching frequently accessed data

### No power data in activities
- Verify the activity was recorded with a power meter
- Check that the user granted `activity:read_all` scope
- Some activities may not have power data (e.g., runs, swims)

## Next Steps

1. ✅ **Authenticate with Strava**
2. 📥 **Fetch historical activities** for comparison with FIT files
3. 🧮 **Calculate TSS** from Strava power data
4. 📊 **Build PMC** (Performance Management Chart) with CTL/ATL/TSB
5. 🎯 **Interval detection** on Strava activities
6. 🔄 **Webhook integration** for real-time activity updates

## API Documentation

Full Strava API docs: https://developers.strava.com/docs/reference/

Key endpoints we use:
- `/athlete` - Get athlete profile
- `/athlete/zones` - Get training zones
- `/athlete/activities` - List activities
- `/activities/{id}` - Get activity details
- `/activities/{id}/streams` - Get time-series data

