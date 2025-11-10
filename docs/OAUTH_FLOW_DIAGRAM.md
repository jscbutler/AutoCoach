# TrainingPeaks OAuth Flow - Visual Guide

## Quick Start Path

```
┌─────────────────────────────────────────────────────────────────────┐
│  START HERE: ./scripts/setup_trainingpeaks.sh                      │
│  (Automated helper script that guides you through setup)           │
└─────────────────────────────────────────────────────────────────────┘
```

## Complete OAuth Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        STEP 1: GET API CREDENTIALS                       │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  1. Visit: api.trainingpeaks.com/request-access│
        │  2. Fill out application form                 │
        │  3. Wait for approval (1-2 weeks)             │
        │  4. Receive Client ID and Client Secret       │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        STEP 2: CONFIGURE .ENV                            │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  cp env.template .env                         │
        │  # Edit .env and add:                         │
        │  TRAININGPEAKS_CLIENT_ID=your_id              │
        │  TRAININGPEAKS_CLIENT_SECRET=your_secret      │
        │  TRAININGPEAKS_SANDBOX=true                   │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     STEP 3: START FASTAPI SERVER                         │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  source ac_env/bin/activate                   │
        │  uvicorn app.main:app --reload --port 8000    │
        │  # Server running at http://localhost:8000    │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                   STEP 4: INITIATE OAUTH FLOW                            │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌─────────────────────────────────────────────────────┐
        │  Browser: http://localhost:8000/auth/trainingpeaks │
        │           ?sandbox=true                            │
        │                                                     │
        │  Response:                                          │
        │  {                                                  │
        │    "authorization_url": "https://oauth..."         │
        │  }                                                  │
        └─────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    STEP 5: USER AUTHORIZATION                            │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌─────────────────────────────────────────────────────┐
        │  1. Copy authorization_url from response           │
        │  2. Paste in browser                                │
        │  3. TrainingPeaks login page appears                │
        │  4. Enter TP credentials                            │
        │  5. Review permissions                              │
        │  6. Click "Authorize"                               │
        └─────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    STEP 6: OAUTH CALLBACK                                │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌─────────────────────────────────────────────────────┐
        │  TrainingPeaks redirects to:                       │
        │  http://localhost:8000/auth/callback?code=ABC123   │
        │                                                     │
        │  AutoCoach server:                                  │
        │  - Receives authorization code                      │
        │  - Exchanges code for tokens                        │
        │  - Stores tokens in memory                          │
        │                                                     │
        │  Response:                                          │
        │  {                                                  │
        │    "message": "Authentication successful",         │
        │    "access_token": "eyJ...",                       │
        │    "expires_in": 3600                              │
        │  }                                                  │
        └─────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    STEP 7: EXTRACT TOKENS                                │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌─────────────────────────────────────────────────────┐
        │  # In new terminal (server still running):         │
        │  PYTHONPATH=. python scripts/get_tokens.py         │
        │                                                     │
        │  Output:                                            │
        │  TRAININGPEAKS_ACCESS_TOKEN=eyJ...                 │
        │  TRAININGPEAKS_REFRESH_TOKEN=def...                │
        └─────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    STEP 8: SAVE TOKENS TO .ENV                           │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌─────────────────────────────────────────────────────┐
        │  1. Copy token lines from get_tokens.py output     │
        │  2. Edit .env file: nano .env                       │
        │  3. Paste tokens at the bottom                      │
        │  4. Save and close                                  │
        └─────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    STEP 9: TEST CONNECTION                               │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌─────────────────────────────────────────────────────┐
        │  PYTHONPATH=. python scripts/test_harness.py \     │
        │    --tp-test                                        │
        │                                                     │
        │  Expected output:                                   │
        │  ✓ TrainingPeaks client initialized                │
        │  ✓ Access token found                              │
        │  ✓ Authenticated as: Your Name                     │
        │  ✓ Thresholds retrieved                            │
        │    FTP: 265W                                        │
        └─────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    ✅ SETUP COMPLETE!                                    │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌─────────────────────────────────────────────────────┐
        │  Now you can:                                       │
        │                                                     │
        │  # Compare local FIT with TrainingPeaks            │
        │  PYTHONPATH=. python scripts/test_harness.py \     │
        │    --file data/sample_workouts/Purple*.fit.gz \    │
        │    --tp-compare                                     │
        │                                                     │
        │  # Use API endpoints                                │
        │  http://localhost:8000/trainingpeaks/profile       │
        │  http://localhost:8000/trainingpeaks/activities    │
        └─────────────────────────────────────────────────────┘
```

## Detailed Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           OAUTH FLOW COMPONENTS                          │
└─────────────────────────────────────────────────────────────────────────┘

    Your Browser          FastAPI Server       TrainingPeaks OAuth
        │                      │                      │
        │  1. Initiate         │                      │
        ├─────────────────────>│                      │
        │  GET /auth/trainingpeaks                    │
        │                      │                      │
        │                      │  2. Create auth URL  │
        │                      ├─────────────────────>│
        │                      │  (includes client_id)│
        │                      │                      │
        │  3. Return URL       │                      │
        │<─────────────────────┤                      │
        │  {"authorization_url": "..."}               │
        │                      │                      │
        │  4. Visit URL        │                      │
        ├──────────────────────┼─────────────────────>│
        │  (User clicks link)  │                      │
        │                      │                      │
        │  5. Login page       │                      │
        │<─────────────────────┼──────────────────────┤
        │  (TP login form)     │                      │
        │                      │                      │
        │  6. Enter creds      │                      │
        ├──────────────────────┼─────────────────────>│
        │  username, password  │                      │
        │                      │                      │
        │  7. Auth code        │                      │
        │<─────────────────────┼──────────────────────┤
        │  Redirect to callback│                      │
        │                      │                      │
        │  8. Callback         │                      │
        ├─────────────────────>│                      │
        │  GET /auth/callback?code=ABC123             │
        │                      │                      │
        │                      │  9. Exchange code    │
        │                      ├─────────────────────>│
        │                      │  POST /oauth/token   │
        │                      │  (code + secret)     │
        │                      │                      │
        │                      │  10. Tokens          │
        │                      │<─────────────────────┤
        │                      │  {access, refresh}   │
        │                      │                      │
        │  11. Success         │                      │
        │<─────────────────────┤                      │
        │  {"message": "Auth successful"}             │
        │                      │                      │
```

## Token Storage Flow

```
┌────────────────────────────────────────────────────────────┐
│                   TOKEN PERSISTENCE                         │
└────────────────────────────────────────────────────────────┘

OAuth Callback
     │
     ▼
Store in Memory          ─────>  tp_client.oauth_session.token
(Current)                        (Lost when server restarts)
     │
     ▼
Extract Manually         ─────>  python scripts/get_tokens.py
     │
     ▼
Save to .env File        ─────>  TRAININGPEAKS_ACCESS_TOKEN=...
     │                           TRAININGPEAKS_REFRESH_TOKEN=...
     ▼
Load on Startup          ─────>  TrainingPeaksClient.from_env()
     │
     ▼
Use for API Calls        ─────>  test_harness.py --tp-compare


Future: Persistent Storage
     │
     ▼
Database Table           ─────>  user_tokens(user_id, access, refresh, expires_at)
     │
     ▼
Per-User Auth            ─────>  Multi-user support
     │
     ▼
Auto-Refresh             ─────>  Background task refreshes before expiry
```

## Troubleshooting Decision Tree

```
                    ┌───────────────────────┐
                    │  OAuth Not Working?   │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼────────────┐
                    │ Do you have .env file? │
                    └───┬────────────────┬───┘
                       NO              YES
                        │                │
                        ▼                ▼
                ┌──────────────┐  ┌──────────────────┐
                │cp env.template│  │Are credentials   │
                │    .env       │  │     set?         │
                └──────────────┘  └─┬──────────────┬─┘
                                   NO            YES
                                    │              │
                                    ▼              ▼
                            ┌────────────┐  ┌──────────────┐
                            │Get from TP │  │Is server     │
                            │  API portal│  │  running?    │
                            └────────────┘  └─┬──────────┬─┘
                                             NO        YES
                                              │          │
                                              ▼          ▼
                                    ┌──────────────┐  ┌──────────┐
                                    │Start server: │  │Have you  │
                                    │uvicorn app...│  │completed │
                                    └──────────────┘  │OAuth flow│
                                                      └─┬──────┬─┘
                                                       NO    YES
                                                        │      │
                                                        ▼      ▼
                                            ┌────────────────┐┌──────────┐
                                            │Visit:          ││Are tokens│
                                            │/auth/          ││in .env?  │
                                            │trainingpeaks   │└─┬──────┬─┘
                                            └────────────────┘ NO    YES
                                                                │      │
                                                                ▼      ▼
                                                    ┌────────────────┐┌────┐
                                                    │Run:            ││✅ │
                                                    │get_tokens.py   │└────┘
                                                    │& save to .env  │
                                                    └────────────────┘
```

## Security Considerations

```
┌─────────────────────────────────────────────────────────────────┐
│                      SECURITY CHECKLIST                          │
└─────────────────────────────────────────────────────────────────┘

✓ .env file in .gitignore           (Never commit tokens)
✓ Tokens stored securely            (Encrypted in production)
✓ HTTPS in production               (Not http://)
✓ Token rotation policy             (Refresh periodically)
✓ Minimal scope requests            (Only needed permissions)
✓ Token expiry handling             (Auto-refresh before expiry)
✓ Per-user token storage            (Database, not shared file)
✓ Rate limit awareness              (Respect API limits)
✓ Error logging (no tokens)         (Truncate in logs)
✓ OAuth state parameter             (CSRF protection)
```

## Common Issues & Solutions

### "No module named 'app'"
```
❌ Problem: Python can't find app module
✅ Solution: PYTHONPATH=/Users/jeffbutler/Dev/AutoCoach python scripts/...
```

### "Not authenticated"
```
❌ Problem: No tokens or tokens expired
✅ Solution:
   1. Check .env has tokens
   2. Check token expiry (usually 1 hour)
   3. Re-run OAuth flow if expired
```

### "Invalid redirect URI"
```
❌ Problem: Redirect URI mismatch
✅ Solution:
   1. Check TP portal: Registered URI
   2. Check .env: TRAININGPEAKS_REDIRECT_URI
   3. Must match exactly (including protocol, port)
```

### "Rate limit exceeded"
```
❌ Problem: Too many API requests
✅ Solution:
   1. Wait 15 minutes
   2. Implement caching
   3. Reduce request frequency
```

