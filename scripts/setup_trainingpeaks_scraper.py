#!/usr/bin/env python3
"""
Helper script to set up TrainingPeaks scraper by discovering API endpoints.

This guides you through:
1. Finding the actual API endpoints TP uses
2. Extracting cookies from your browser
3. Testing the scraper
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_header(text: str) -> None:
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def main():
    print_header("TrainingPeaks Scraper Setup")
    
    print("""
This tool helps you set up the TrainingPeaks scraper by finding the
API endpoints and cookies from your browser.

WHY THIS WORKS:
TrainingPeaks is a SPA (Single Page App). When you view a workout,
the page makes authenticated API calls to fetch workout data as JSON.
We can reuse those same calls!

WHAT WE NEED:
1. The API endpoint URLs (where TP fetches workout data)
2. Your browser cookies (to authenticate)
3. Any required headers

Let's discover these together...
""")
    
    print_header("Step 1: Find API Endpoints")
    
    print("""
1. Open TrainingPeaks in Chrome: https://home.trainingpeaks.com
2. Log in to your account
3. Open DevTools (F12 or right-click → Inspect)
4. Go to the "Network" tab
5. Click on a workout in your calendar to view it
6. Look for API requests in the Network tab

WHAT TO LOOK FOR:
- Requests to api.trainingpeaks.com or home.trainingpeaks.com/api
- Look for requests that return JSON (not HTML)
- Common patterns:
  * /api/v1/workouts/{id}
  * /api/v1/athlete/workouts?startDate=...
  * /workout/{id}/details

EXAMPLE:
Request URL: https://api.trainingpeaks.com/v1/workouts/123456789
Method: GET
Status: 200

WHAT TO COPY:
- The full URL
- The Request Headers (especially Cookie, Authorization, User-Agent)
- The Response (to see what data we get)
""")
    
    input("Press Enter when you've found a workout API request...")
    
    print("\n📋 Paste the Request URL here:")
    api_url = input("> ").strip()
    
    print("\n" + "-" * 70)
    print("GREAT! Now let's get the cookies...")
    print("-" * 70)
    
    print_header("Step 2: Extract Cookies")
    
    print("""
OPTION A: Manual Copy (Simple)
-------------------------------
1. In DevTools Network tab, click on the workout request
2. Scroll to "Request Headers" section
3. Find the "Cookie:" header
4. Copy the entire cookie string

OPTION B: Export All Cookies (Recommended)
------------------------------------------
1. Install a browser extension: "EditThisCookie" or "Cookie Editor"
2. Visit TrainingPeaks
3. Click the extension icon
4. Export cookies as JSON
5. Save to a file

OPTION C: DevTools Application Tab
-----------------------------------
1. DevTools → Application tab
2. Storage → Cookies → https://trainingpeaks.com
3. Right-click → Copy all cookies
4. Paste into a text file

Which option did you choose? (A/B/C): """)
    
    cookie_option = input("> ").strip().upper()
    
    if cookie_option == "A":
        print("\n📋 Paste your cookie string:")
        print("(It should look like: TPAuth=abc123; session=xyz789; ...)")
        cookie_string = input("> ").strip()
        
        print(f"\n✓ Cookie captured ({len(cookie_string)} characters)")
        
    elif cookie_option in ["B", "C"]:
        print("\n📋 Paste the JSON array of cookies:")
        print("Format: [{\"name\": \"TPAuth\", \"value\": \"...\", \"domain\": \"...\"}, ...]")
        print("(Press Ctrl+D when done)")
        
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        
        cookie_json = "\n".join(lines)
        print(f"\n✓ Cookies captured ({len(cookie_json)} characters)")
    
    print_header("Step 3: Test Configuration")
    
    print(f"""
Configuration Summary:
- API URL: {api_url}
- Cookies: Captured ✓

Now let's test if this works...

You can test manually with:

```python
from app.clients.trainingpeaks_scraper import TrainingPeaksScraper
import json

# Set up scraper
scraper = TrainingPeaksScraper()
# Load your cookies...

# Try fetching a workout
workout = scraper.get_workout_for_date(date(2024, 2, 29))
print(workout.description)
```

Or use the endpoint in FastAPI (coming next)!
""")
    
    print_header("Step 4: What's Next?")
    
    print("""
NOW YOU CAN:

1. Save cookies to ~/.tp_cookies.json
2. Use TrainingPeaksScraper to fetch workout descriptions
3. Feed descriptions to LLM for parsing into WorkoutSpec
4. Compare planned vs executed workouts!

SAMPLE CODE:
```python
from datetime import date
from app.clients.trainingpeaks_scraper import TrainingPeaksScraper

scraper = TrainingPeaksScraper.from_env()

# Get workout for a specific date
workout = scraper.get_workout_for_date(date(2024, 2, 29))

if workout and workout.description:
    print(f"Coach's Instructions: {workout.description}")
    
    # TODO: Send to LLM to parse into structured WorkoutSpec
    # Example: "3x8min @ FTP, 3min easy" → JSON intervals
```

IMPORTANT NOTES:
- Cookies expire (usually after 30 days or on logout)
- You'll need to refresh them periodically
- This is for single-user MVP only
- Migrate to official API if you get approval

Need help? Check docs/TRAININGPEAKS_SCRAPER_GUIDE.md
""")
    
    print_header("Setup Complete!")
    print("You're ready to scrape TrainingPeaks workout descriptions! 🎉\n")


if __name__ == "__main__":
    main()

