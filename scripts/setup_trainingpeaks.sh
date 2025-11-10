#!/bin/bash
# Quick setup script for TrainingPeaks OAuth

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "================================================================================"
echo "  TrainingPeaks OAuth Setup Assistant"
echo "================================================================================"
echo ""

# Check if .env exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "❌ .env file not found"
    echo ""
    echo "Creating .env from template..."
    cp "$PROJECT_DIR/env.template" "$PROJECT_DIR/.env"
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  ACTION REQUIRED:"
    echo "  1. Edit .env file: nano $PROJECT_DIR/.env"
    echo "  2. Add your TrainingPeaks Client ID and Secret"
    echo "  3. Save and run this script again"
    echo ""
    exit 0
fi

# Load .env
source "$PROJECT_DIR/.env" 2>/dev/null || true

# Check if credentials are set
if [ -z "$TRAININGPEAKS_CLIENT_ID" ] || [ "$TRAININGPEAKS_CLIENT_ID" = "your_client_id_here" ]; then
    echo "❌ TrainingPeaks credentials not configured"
    echo ""
    echo "⚠️  ACTION REQUIRED:"
    echo "  1. Request API access: https://api.trainingpeaks.com/request-access"
    echo "  2. Wait for approval email with credentials"
    echo "  3. Edit .env: nano $PROJECT_DIR/.env"
    echo "  4. Add your Client ID and Client Secret"
    echo "  5. Run this script again"
    echo ""
    exit 0
fi

echo "✓ .env file found"
echo "✓ TrainingPeaks credentials configured"
echo ""

# Check if tokens exist
if [ -n "$TRAININGPEAKS_ACCESS_TOKEN" ] && [ "$TRAININGPEAKS_ACCESS_TOKEN" != "your_access_token_here" ]; then
    echo "✓ OAuth tokens found in .env"
    echo ""
    echo "Testing connection..."
    cd "$PROJECT_DIR"
    source ac_env/bin/activate 2>/dev/null || {
        echo "❌ Virtual environment not found"
        echo "  Run: python3 -m venv ac_env && source ac_env/bin/activate && pip install -r requirements.txt"
        exit 1
    }
    
    PYTHONPATH="$PROJECT_DIR" python scripts/test_harness.py --tp-test
    
    echo ""
    echo "✅ Setup complete! You can now use TrainingPeaks integration."
    echo ""
    echo "Try it out:"
    echo "  PYTHONPATH=. python scripts/test_harness.py --file data/sample_workouts/Purple\\ Patch-\\ Nancy\\ \\&\\ Frank\\ Duet.fit.gz --tp-compare"
    exit 0
fi

echo "⚠️  OAuth tokens not found in .env"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Start the FastAPI server (in a separate terminal):"
echo "   cd $PROJECT_DIR"
echo "   source ac_env/bin/activate"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "2. In your browser, visit:"
echo "   http://localhost:8000/auth/trainingpeaks?sandbox=true"
echo ""
echo "3. Copy the 'authorization_url' from the response"
echo ""
echo "4. Paste the URL in your browser and authorize the app"
echo ""
echo "5. After authorization, extract the tokens (in another terminal):"
echo "   cd $PROJECT_DIR"
echo "   source ac_env/bin/activate"
echo "   PYTHONPATH=. python scripts/get_tokens.py"
echo ""
echo "6. Copy the token lines to your .env file"
echo ""
echo "7. Run this script again to test: ./scripts/setup_trainingpeaks.sh"
echo ""
echo "📖 For detailed instructions, see:"
echo "   docs/TRAININGPEAKS_OAUTH_SETUP.md"
echo ""

