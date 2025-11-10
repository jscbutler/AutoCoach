#!/usr/bin/env python3
"""Extract OAuth tokens from running FastAPI server.

Usage:
    python scripts/get_tokens.py

This script connects to the FastAPI server and extracts the current OAuth tokens
so you can save them to your .env file.

Note: Must be run while the FastAPI server is running and after completing OAuth flow.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import tp_client


def main() -> None:
    """Extract and display OAuth tokens."""
    print("\n" + "="*80)
    print("  TrainingPeaks OAuth Token Extractor")
    print("="*80 + "\n")
    
    if not tp_client:
        print("✗ No TrainingPeaks client initialized.")
        print("  Make sure you've run the OAuth flow first:")
        print("  1. Start server: uvicorn app.main:app --reload")
        print("  2. Visit: http://localhost:8000/auth/trainingpeaks?sandbox=true")
        print("  3. Complete authorization")
        print("  4. Run this script again")
        sys.exit(1)
    
    if not tp_client.oauth_session.token:
        print("✗ No tokens found in client.")
        print("  Complete OAuth flow first:")
        print("  1. Visit: http://localhost:8000/auth/trainingpeaks?sandbox=true")
        print("  2. Click the authorization_url")
        print("  3. Authorize the app")
        print("  4. Wait for callback")
        print("  5. Run this script again")
        sys.exit(1)
    
    token = tp_client.oauth_session.token
    
    print("✓ Tokens found!\n")
    print("Add these lines to your .env file:")
    print("-" * 80)
    
    access_token = token.get('access_token', '')
    refresh_token = token.get('refresh_token', '')
    expires_in = token.get('expires_in', 'Unknown')
    
    print(f"TRAININGPEAKS_ACCESS_TOKEN={access_token}")
    print(f"TRAININGPEAKS_REFRESH_TOKEN={refresh_token}")
    
    print("-" * 80)
    print(f"\nToken expires in: {expires_in} seconds")
    
    if isinstance(expires_in, int):
        hours = expires_in // 3600
        minutes = (expires_in % 3600) // 60
        print(f"                  ({hours}h {minutes}m)")
    
    print("\n⚠️  Security Notes:")
    print("  - These tokens provide full access to your TrainingPeaks account")
    print("  - Never commit .env file to git")
    print("  - Keep tokens secure and private")
    print("  - Rotate tokens periodically")
    
    print("\n💡 Next Steps:")
    print("  1. Copy the tokens above")
    print("  2. Edit .env file: nano .env")
    print("  3. Paste the tokens")
    print("  4. Save and close")
    print("  5. Test: python scripts/test_harness.py --tp-test")
    print("")


if __name__ == "__main__":
    main()

