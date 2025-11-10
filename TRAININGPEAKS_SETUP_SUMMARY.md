# TrainingPeaks OAuth Setup - Complete Summary

## ✅ What We've Built

You now have a **complete OAuth setup** for TrainingPeaks integration with AutoCoach, reusing your existing `eve-market.space` domain infrastructure!

## 🎯 Two Setup Options

### Option 1: Cloudflare Tunnel (Recommended) ⭐

**URL**: `https://autocoach.eve-market.space`

**Advantages**:
- ✅ Stable, permanent URL
- ✅ Professional domain
- ✅ HTTPS by default
- ✅ Reuses EVE project infrastructure
- ✅ No callback URL changes needed
- ✅ Works from anywhere

**Setup**: Run `./scripts/setup_cloudflare_tunnel.sh`

### Option 2: Localhost (Simple Testing)

**URL**: `http://localhost:8000`

**Advantages**:
- ✅ Quick setup
- ✅ No external dependencies
- ✅ Fast iteration

**Setup**: Just start the server with `uvicorn`

---

## 📁 Files Created

### Configuration
- `env.template` - Updated with Cloudflare tunnel URL
- `config/cloudflare-tunnel.yaml` - Tunnel configuration

### Scripts
- `scripts/setup_cloudflare_tunnel.sh` - One-time tunnel setup
- `scripts/start_with_tunnel.sh` - Combined tunnel + server startup
- `scripts/get_tokens.py` - Token extraction after OAuth
- `scripts/setup_trainingpeaks.sh` - General OAuth setup assistant

### Documentation
- `docs/CLOUDFLARE_TUNNEL_SETUP.md` - Complete tunnel guide (NEW!)
- `docs/OAUTH_QUICK_START.md` - Quick start guide (NEW!)
- `docs/TRAININGPEAKS_OAUTH_SETUP.md` - Detailed OAuth walkthrough
- `docs/OAUTH_FLOW_DIAGRAM.md` - Visual OAuth diagrams
- `scripts/TEST_HARNESS_USAGE.md` - Test harness documentation

---

## 🚀 Quick Start (3 Steps!)

### 1. Setup Cloudflare Tunnel

```bash
cd /Users/jeffbutler/Dev/AutoCoach
./scripts/setup_cloudflare_tunnel.sh
```

This:
- Reuses your existing `eve-market-auth` tunnel from EVE project
- Adds DNS route for `autocoach.eve-market.space`
- Configures everything automatically

### 2. Update TrainingPeaks Application

1. Go to: https://api.trainingpeaks.com/request-access
2. Edit your application
3. Set **Redirect URI**: `https://autocoach.eve-market.space/auth/callback`
4. Save

### 3. Start Everything

```bash
./scripts/start_with_tunnel.sh
```

This runs both:
- Cloudflare tunnel (for public access)
- FastAPI server (for API logic)

**Done!** Your AutoCoach API is now at: https://autocoach.eve-market.space

---

## 🧪 Test the Setup

### Test 1: Health Check

```bash
curl https://autocoach.eve-market.space/
```

Expected: `{"status": "ok"}`

### Test 2: OAuth Flow

**Browser**: https://autocoach.eve-market.space/auth/trainingpeaks?sandbox=true

1. Copy `authorization_url`
2. Visit in browser
3. Login to TrainingPeaks
4. Authorize AutoCoach
5. Get redirected back with success message

### Test 3: Extract Tokens

**While server running**, in new terminal:

```bash
cd /Users/jeffbutler/Dev/AutoCoach
source ac_env/bin/activate
PYTHONPATH=. python scripts/get_tokens.py
```

Copy output to `.env` file.

### Test 4: Verify Connection

```bash
PYTHONPATH=. python scripts/test_harness.py --tp-test
```

Expected:
```
✓ TrainingPeaks client initialized
✓ Access token found
✓ Authenticated as: Your Name
✓ FTP: 265W
```

### Test 5: Compare Workout

```bash
PYTHONPATH=. python scripts/test_harness.py \
  --file data/sample_workouts/Purple\ Patch-\ Nancy\ \&\ Frank\ Duet.fit.gz \
  --tp-compare
```

This will:
- Parse local FIT file (Feb 29, 2024 workout)
- Fetch FTP active on that date from TrainingPeaks
- Fetch daily metrics (HRV, RHR, sleep)
- Fetch workout from TrainingPeaks
- Show side-by-side comparison!

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   eve-market.space Domain                    │
└─────────────────────────────────────────────────────────────┘
                           │
      ┌────────────────────┼────────────────────┐
      │                    │                    │
      ▼                    ▼                    ▼
auth.eve-market.space  autocoach.eve-market  market.eve-market
  (EVE Auth)           (AutoCoach)           (Market Watch)
      │                    │                    │
      ▼                    ▼                    ▼
 localhost:5002       localhost:8000      localhost:3000

                 ▲
                 │
         Cloudflare Tunnel
         (eve-market-auth)
                 │
                 │ Single tunnel serves all subdomains!
                 ▼
        Cloudflare Network
```

---

## 🔧 Configuration Files

### `.env` (Your Configuration)

```bash
# TrainingPeaks OAuth - Use Cloudflare tunnel URL
TRAININGPEAKS_CLIENT_ID=your_client_id
TRAININGPEAKS_CLIENT_SECRET=your_client_secret
TRAININGPEAKS_REDIRECT_URI=https://autocoach.eve-market.space/auth/callback

# Tokens (filled after OAuth)
TRAININGPEAKS_ACCESS_TOKEN=eyJhbGciOi...
TRAININGPEAKS_REFRESH_TOKEN=def50200a7f...

# Settings
TRAININGPEAKS_SANDBOX=true
AUTOCOACH_PORT=8000
```

### `config/cloudflare-tunnel.yaml`

```yaml
tunnel: eve-market-auth  # Reuse EVE tunnel
credentials-file: /Users/jeffbutler/.cloudflared/eve-market-auth.json

ingress:
  - hostname: autocoach.eve-market.space
    service: http://localhost:8000
  - service: http_status:404
```

---

## 📋 Command Reference

```bash
# Setup (one-time)
./scripts/setup_cloudflare_tunnel.sh

# Start everything
./scripts/start_with_tunnel.sh

# Or start separately:
# Terminal 1 - Tunnel
cloudflared tunnel --config config/cloudflare-tunnel.yaml run eve-market-auth

# Terminal 2 - Server
source ac_env/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Get OAuth tokens
PYTHONPATH=. python scripts/get_tokens.py

# Test connection
PYTHONPATH=. python scripts/test_harness.py --tp-test

# Compare workout
PYTHONPATH=. python scripts/test_harness.py --file workout.fit.gz --tp-compare

# View tunnel logs
tail -f ~/.cloudflared/eve-market-auth.log

# Check tunnel status
cloudflared tunnel list
cloudflared tunnel info eve-market-auth
```

---

## 🎓 What You Can Do Now

### 1. Validate Metrics Calculations

Compare your FIT file parsing and metrics (NP, IF, TSS) against TrainingPeaks:

```bash
PYTHONPATH=. python scripts/test_harness.py \
  --file your_workout.fit.gz \
  --tp-compare
```

### 2. Fetch Historical Thresholds

Get the FTP that was active on a specific workout date (not just current FTP):

```python
from app.clients.trainingpeaks import TrainingPeaksClient
from datetime import date

client = TrainingPeaksClient.from_env(sandbox=True)
ftp = fetch_tp_threshold_for_date(client, date(2024, 2, 29))
```

### 3. Get Recovery Metrics

Fetch HRV, RHR, sleep data for workout analysis:

```python
metrics = client.get_daily_metrics(workout_date, workout_date)
print(f"HRV: {metrics['hrv']}, RHR: {metrics['rhr']}")
```

### 4. Build Features

Now you can build AutoCoach features with confidence that your metrics calculations match TrainingPeaks!

---

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **DNS not resolving** | Wait for propagation, check: `dig autocoach.eve-market.space` |
| **Tunnel not found** | Run from eve_py: `./scripts/setup_permanent_tunnel.sh` |
| **Redirect URI mismatch** | Must match exactly in `.env` and TrainingPeaks portal |
| **Tokens expired** | Re-run OAuth flow (tokens last ~1 hour) |
| **Connection refused** | Check server running on port 8000: `lsof -i :8000` |

### Debug Steps

1. **Check tunnel is running**:
   ```bash
   ps aux | grep cloudflared
   ```

2. **Test local server**:
   ```bash
   curl http://localhost:8000/
   ```

3. **Test via tunnel**:
   ```bash
   curl https://autocoach.eve-market.space/
   ```

4. **Check tunnel logs**:
   ```bash
   tail -f ~/.cloudflared/eve-market-auth.log
   ```

---

## 🎯 Next Steps

1. ✅ Complete OAuth setup
2. ✅ Test with sample workout
3. ✅ Verify metrics match TrainingPeaks
4. 🚀 Start building AutoCoach features:
   - Interval detection
   - Workout compliance scoring
   - Fatigue detection
   - Training load management

---

## 📚 Documentation Index

Start here based on your needs:

- **Quick Start**: `docs/OAUTH_QUICK_START.md`
- **Tunnel Setup**: `docs/CLOUDFLARE_TUNNEL_SETUP.md`  
- **OAuth Details**: `docs/TRAININGPEAKS_OAUTH_SETUP.md`
- **Visual Diagrams**: `docs/OAUTH_FLOW_DIAGRAM.md`
- **Test Harness**: `scripts/TEST_HARNESS_USAGE.md`

---

## 💡 Pro Tips

1. **Keep tunnel running**: Use `screen` or `tmux` to persist tunnel
2. **Use sandbox first**: Test everything before switching to production
3. **Save tokens**: They're in server memory until you extract them
4. **Check coverage**: Use `--tp-compare` to validate your calculations
5. **Reuse infrastructure**: Same tunnel serves all your projects!

---

## ✨ Summary

You now have:

✅ Professional OAuth setup with Cloudflare tunnel  
✅ Stable URL that never changes  
✅ Reuses existing EVE project infrastructure  
✅ Complete test harness for TrainingPeaks integration  
✅ Ability to compare local metrics with TrainingPeaks  
✅ Foundation for building AutoCoach features  

**Ready to build!** 🚀

```bash
./scripts/start_with_tunnel.sh
```

