#!/usr/bin/env python3
"""
Helper script to get Strava OAuth tokens.

This script walks you through the OAuth flow and saves tokens to .env file.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.clients.strava import StravaClient
from dotenv import load_dotenv, set_key


def main():
    """Run Strava OAuth flow and save tokens."""
    # Load environment
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
    
    print("=" * 70)
    print("Strava OAuth Token Generator")
    print("=" * 70)
    print()
    
    # Check for credentials
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")
    redirect_uri = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/auth/callback")
    
    if not client_id or not client_secret:
        print("❌ ERROR: STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be set in .env")
        print()
        print("Please follow these steps:")
        print("1. Go to https://www.strava.com/settings/api")
        print("2. Create a new app")
        print("3. Copy your Client ID and Client Secret")
        print("4. Add them to .env file")
        print()
        return 1
    
    print(f"✅ Found Strava credentials")
    print(f"   Client ID: {client_id}")
    print(f"   Redirect URI: {redirect_uri}")
    print()
    
    # Create client
    try:
        client = StravaClient(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
        )
    except Exception as e:
        print(f"❌ ERROR: Failed to create Strava client: {e}")
        return 1
    
    # Get authorization URL
    try:
        auth_url = client.get_authorization_url()
    except Exception as e:
        print(f"❌ ERROR: Failed to get authorization URL: {e}")
        return 1
    
    print("Step 1: Authorize AutoCoach with Strava")
    print("-" * 70)
    print()
    print("Please open this URL in your browser:")
    print()
    print(f"  {auth_url}")
    print()
    print("After authorizing, you'll be redirected to:")
    print(f"  {redirect_uri}?code=XXXXX&scope=...")
    print()
    
    # Get authorization code from user
    print("Step 2: Copy the authorization code")
    print("-" * 70)
    print()
    code = input("Paste the 'code' parameter from the redirect URL: ").strip()
    
    if not code:
        print("❌ ERROR: No code provided")
        return 1
    
    # Exchange code for tokens
    print()
    print("Step 3: Exchange code for tokens...")
    print("-" * 70)
    
    try:
        token = client.exchange_code_for_token(code)
    except Exception as e:
        print(f"❌ ERROR: Failed to exchange code for token: {e}")
        return 1
    
    # Extract tokens
    access_token = token.get("access_token")
    refresh_token = token.get("refresh_token")
    athlete = token.get("athlete", {})
    
    if not access_token or not refresh_token:
        print("❌ ERROR: Missing tokens in response")
        return 1
    
    print()
    print("✅ SUCCESS! Got tokens:")
    print(f"   Access Token: {access_token[:20]}...")
    print(f"   Refresh Token: {refresh_token[:20]}...")
    if athlete:
        print(f"   Athlete: {athlete.get('firstname')} {athlete.get('lastname')}")
        print(f"   Athlete ID: {athlete.get('id')}")
    print()
    
    # Save to .env
    print("Step 4: Save tokens to .env")
    print("-" * 70)
    
    try:
        set_key(env_path, "STRAVA_ACCESS_TOKEN", access_token)
        set_key(env_path, "STRAVA_REFRESH_TOKEN", refresh_token)
        print("✅ Tokens saved to .env")
    except Exception as e:
        print(f"⚠️  WARNING: Failed to save tokens to .env: {e}")
        print()
        print("Please manually add these to your .env file:")
        print(f"STRAVA_ACCESS_TOKEN={access_token}")
        print(f"STRAVA_REFRESH_TOKEN={refresh_token}")
    
    print()
    print("=" * 70)
    print("✅ OAuth setup complete!")
    print("=" * 70)
    print()
    print("You can now:")
    print("  - Fetch activities: python -m app.main")
    print("  - Test with curl: curl http://localhost:8000/strava/athlete")
    print("  - Run test harness: python scripts/test_harness.py --source strava")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

