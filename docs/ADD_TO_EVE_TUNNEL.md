# Adding AutoCoach to Existing EVE Tunnel

## Safe Integration Approach

To avoid interfering with your existing EVE Cloudflare tunnel, we'll **add AutoCoach as a new route** to your existing tunnel configuration.

## ✅ What's Safe

This approach:
- ✅ Uses your existing tunnel (no new tunnel created)
- ✅ Adds ONE line to your existing config
- ✅ Doesn't modify any EVE routes
- ✅ Only ONE tunnel runs (as before)
- ✅ AutoCoach and EVE share the tunnel seamlessly

## 📝 One-Time Setup

### Step 1: Add AutoCoach to EVE Tunnel Config

Edit the EVE tunnel configuration:

```bash
nano /Users/jeffbutler/Dev/Dev/eve_py/config/cloudflare-tunnel.yaml
```

Add this **single entry** after the existing hostnames (before the catch-all):

```yaml
tunnel: 5a4becbf-b84e-4e90-80d0-f4f8ec2ffc20
credentials-file: ~/.cloudflared/5a4becbf-b84e-4e90-80d0-f4f8ec2ffc20.json

ingress:
  # EVE SSO Authentication API
  - hostname: auth.eve-market.space
    service: http://localhost:5002
    
  # Main EVE Tools Landing Page  
  - hostname: eve-market.space
    service: http://localhost:3003
    
  # Market Watch UI
  - hostname: market.eve-market.space
    service: http://localhost:3000
    
  # Industry Finder
  - hostname: industry.eve-market.space
    service: http://localhost:3002
    
  # Mineral Trader
  - hostname: mineral.eve-market.space
    service: http://localhost:3001
    
  # Mineral Trader API
  - hostname: api.eve-market.space
    service: http://localhost:5001
  
  # 👇 ADD THIS ONE LINE FOR AUTOCOACH 👇
  - hostname: autocoach.eve-market.space
    service: http://localhost:8000
    
  # Catch all (required)
  - service: http_status:404
```

**That's it!** Just one hostname entry added.

### Step 2: Add DNS Route

```bash
cloudflared tunnel route dns 5a4becbf-b84e-4e90-80d0-f4f8ec2ffc20 autocoach.eve-market.space
```

This creates the DNS CNAME record pointing `autocoach.eve-market.space` to your tunnel.

### Step 3: Restart the Tunnel (if running)

If your EVE tunnel is currently running:

```bash
# Find and stop existing tunnel
ps aux | grep cloudflared
kill <PID>

# Restart with updated config
cd /Users/jeffbutler/Dev/Dev/eve_py
cloudflared tunnel --config config/cloudflare-tunnel.yaml run
```

Or use your existing start script from eve_py.

## 🚀 Using AutoCoach with the Tunnel

### Start AutoCoach Server

The tunnel handles routing, you just need to start AutoCoach:

```bash
cd /Users/jeffbutler/Dev/AutoCoach
source ac_env/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**That's all!** The tunnel (running from eve_py) will automatically route:
- `auth.eve-market.space` → localhost:5002 (EVE)
- `market.eve-market.space` → localhost:3000 (EVE)
- `autocoach.eve-market.space` → localhost:8000 (AutoCoach)

## 📊 How It Works

```
                    Cloudflare Tunnel
                  (ONE tunnel, ID: 5a4becbf...)
                           |
        ┌──────────────────┼──────────────────┐
        |                  |                  |
        v                  v                  v
auth.eve-market.space  autocoach.eve-market  market.eve-market
  localhost:5002        localhost:8000       localhost:3000
    (EVE Auth)          (AutoCoach)          (EVE Market)
```

**Single tunnel, multiple routes, zero interference!**

## ✅ Verification

### Test AutoCoach

```bash
curl https://autocoach.eve-market.space/
```

Expected: `{"status": "ok"}`

### Test EVE Still Works

```bash
curl https://auth.eve-market.space/health
```

Expected: EVE auth server response

### Both Work Simultaneously!

The tunnel routes traffic based on hostname, so both projects work together seamlessly.

## 🔧 Configuration Summary

### What Changed in EVE Project
- **File**: `/Users/jeffbutler/Dev/Dev/eve_py/config/cloudflare-tunnel.yaml`
- **Change**: Added 2 lines (1 hostname + 1 service)
- **Impact**: None on existing EVE routes
- **Rollback**: Just remove those 2 lines if needed

### What Stays in AutoCoach
- **No tunnel config** in AutoCoach project
- **Just runs server** on port 8000
- **Uses .env** for redirect URI: `https://autocoach.eve-market.space/auth/callback`

### What's Shared
- ✅ Cloudflare tunnel (existing)
- ✅ Domain (eve-market.space)
- ✅ Tunnel credentials file
- ✅ DNS management

### What's Separate
- ❌ Server processes (different ports)
- ❌ Code/projects (completely independent)
- ❌ Configuration files (except shared tunnel)
- ❌ Dependencies (separate virtual envs)

## 🛡️ Safety Guarantees

1. **EVE routes unchanged**: All existing hostname → port mappings stay the same
2. **Separate ports**: AutoCoach (8000) doesn't conflict with EVE ports (5001, 5002, 3000-3003)
3. **Independent servers**: AutoCoach server crash won't affect EVE
4. **Easy rollback**: Remove 2 lines from config to remove AutoCoach
5. **Testing safe**: Can test AutoCoach without affecting EVE

## 🚦 Port Allocation

To avoid conflicts:

| Service | Port | Project |
|---------|------|---------|
| EVE Auth API | 5002 | eve_py |
| EVE Mineral API | 5001 | eve_py |
| EVE Market Watch | 3000 | eve_py |
| EVE Mineral UI | 3001 | eve_py |
| EVE Industry Finder | 3002 | eve_py |
| EVE Landing Page | 3003 | eve_py |
| **AutoCoach API** | **8000** | **AutoCoach** |

AutoCoach uses port 8000, which doesn't conflict with any EVE ports.

## 📝 Alternative: Keep Completely Separate

If you prefer to keep projects 100% separate, you can:

1. **Use localhost for AutoCoach**: Don't add to tunnel, use `http://localhost:8000`
2. **Pros**: Zero interaction with EVE setup
3. **Cons**: Must change TrainingPeaks callback URL when switching

To use localhost:
```bash
# .env
TRAININGPEAKS_REDIRECT_URI=http://localhost:8000/auth/callback

# TrainingPeaks portal
Redirect URI: http://localhost:8000/auth/callback

# Just start server (no tunnel needed)
uvicorn app.main:app --reload --port 8000
```

## 💡 Recommendation

**Add to EVE tunnel** - it's clean, professional, and truly non-invasive:
- One line in config
- Shared infrastructure
- No conflicts
- Easy to remove if needed
- Both projects benefit from stable URLs

---

## 🔄 Quick Reference

### To Add AutoCoach to Tunnel

```bash
# 1. Edit EVE tunnel config
nano /Users/jeffbutler/Dev/Dev/eve_py/config/cloudflare-tunnel.yaml
# Add autocoach.eve-market.space → localhost:8000

# 2. Add DNS route
cloudflared tunnel route dns 5a4becbf-b84e-4e90-80d0-f4f8ec2ffc20 autocoach.eve-market.space

# 3. Restart tunnel (if running)
# From eve_py project, use your existing start script

# 4. Start AutoCoach
cd /Users/jeffbutler/Dev/AutoCoach
source ac_env/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### To Remove AutoCoach from Tunnel

```bash
# 1. Remove DNS route
cloudflared tunnel route dns delete autocoach.eve-market.space

# 2. Edit EVE tunnel config
nano /Users/jeffbutler/Dev/Dev/eve_py/config/cloudflare-tunnel.yaml
# Remove the 2 AutoCoach lines

# 3. Restart tunnel
# EVE project is unaffected
```

---

**Summary**: This approach is safe, clean, and follows the principle of reusing infrastructure without creating dependencies or conflicts. Your EVE project continues to work exactly as before, and AutoCoach gets the benefit of your professional domain setup! 🎯

