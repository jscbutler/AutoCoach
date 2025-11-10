# TrainingPeaks OAuth - Quick Start Guide

Choose your setup path based on your needs:

## 🚀 Recommended: Cloudflare Tunnel (Stable URL)

**Best for**: Long-term development, stable callback URL

```bash
# 1. Setup tunnel (one-time)
./scripts/setup_cloudflare_tunnel.sh

# 2. Update TrainingPeaks app callback URL
#    → https://autocoach.eve-market.space/auth/callback

# 3. Update .env
TRAININGPEAKS_REDIRECT_URI=https://autocoach.eve-market.space/auth/callback

# 4. Start everything
./scripts/start_with_tunnel.sh

# 5. Visit in browser
https://autocoach.eve-market.space/auth/trainingpeaks?sandbox=true
```

**Pros**:  
✅ Professional domain (`autocoach.eve-market.space`)  
✅ Never change callback URL  
✅ Works anywhere (no localhost needed)  
✅ HTTPS by default  
✅ Reuses EVE project infrastructure  

**See**: `CLOUDFLARE_TUNNEL_SETUP.md`

---

## 🏠 Alternative: Localhost (Simple Testing)

**Best for**: Quick testing, no tunnel setup

```bash
# 1. Update TrainingPeaks app callback URL
#    → http://localhost:8000/auth/callback

# 2. Update .env
TRAININGPEAKS_REDIRECT_URI=http://localhost:8000/auth/callback

# 3. Start server
source ac_env/bin/activate
uvicorn app.main:app --reload --port 8000

# 4. Visit in browser
http://localhost:8000/auth/trainingpeaks?sandbox=true
```

**Pros**:  
✅ Simple setup  
✅ Fast iteration  

**Cons**:  
⚠️ Must change TrainingPeaks callback if switching between methods  
⚠️ Only works on local machine  
⚠️ HTTP only (not HTTPS)  

**See**: `TRAININGPEAKS_OAUTH_SETUP.md`

---

## 📋 Prerequisites

Both methods require:

1. **TrainingPeaks API Access**
   - Apply at: https://api.trainingpeaks.com/request-access
   - Wait for approval (1-2 weeks)
   - Receive Client ID and Secret

2. **Environment Configuration**
   ```bash
   cp env.template .env
   nano .env  # Add Client ID and Secret
   ```

3. **Virtual Environment**
   ```bash
   source ac_env/bin/activate
   ```

---

## 🔄 OAuth Flow (Both Methods)

```
1. Visit authorization URL
   ↓
2. Login to TrainingPeaks
   ↓
3. Approve AutoCoach access
   ↓
4. Redirect to callback URL with code
   ↓
5. AutoCoach exchanges code for tokens
   ↓
6. Extract tokens with get_tokens.py
   ↓
7. Save tokens to .env
   ↓
8. Test with: test_harness.py --tp-test
```

---

## 🧪 Testing After Setup

```bash
# Test connection
PYTHONPATH=. python scripts/test_harness.py --tp-test

# Compare FIT file with TrainingPeaks
PYTHONPATH=. python scripts/test_harness.py \
  --file data/sample_workouts/Purple\ Patch-\ Nancy\ \&\ Frank\ Duet.fit.gz \
  --tp-compare
```

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| **"No module named 'app'"** | Use `PYTHONPATH=. python scripts/...` |
| **"Not authenticated"** | Complete OAuth flow, check tokens in `.env` |
| **"Redirect URI mismatch"** | Ensure `.env` matches TrainingPeaks portal exactly |
| **Tunnel not working** | Check tunnel running: `cloudflared tunnel list` |
| **Tokens expired** | Re-run OAuth flow (tokens expire after ~1 hour) |

---

## 📚 Full Documentation

- `CLOUDFLARE_TUNNEL_SETUP.md` - Complete Cloudflare tunnel setup
- `TRAININGPEAKS_OAUTH_SETUP.md` - Detailed OAuth guide (localhost focus)
- `OAUTH_FLOW_DIAGRAM.md` - Visual diagrams of OAuth flow
- `TEST_HARNESS_USAGE.md` - How to use test harness with TrainingPeaks

---

## 🎯 Recommended Path

1. Start with **Cloudflare Tunnel** approach
2. Set it up once, use forever
3. Never worry about callback URLs again
4. Professional setup from day one

```bash
./scripts/setup_cloudflare_tunnel.sh
./scripts/start_with_tunnel.sh
```

Done! Now you can focus on building AutoCoach features. 🚴‍♂️💨

