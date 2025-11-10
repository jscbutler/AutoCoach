#!/bin/bash
# Start AutoCoach Server
# NOTE: Tunnel should already be running from EVE project

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "================================================================================"
echo "  Starting AutoCoach Server"
echo "================================================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "ac_env" ]; then
    echo "❌ Virtual environment not found!"
    echo ""
    echo "Create it with:"
    echo "  python3 -m venv ac_env"
    echo "  source ac_env/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo ""
    echo "Copy env.template to .env and configure:"
    echo "  cp env.template .env"
    echo "  nano .env"
    echo ""
fi

# Check if EVE tunnel is running
echo "Checking tunnel status..."
if ps aux | grep -q "[c]loudflared.*5a4becbf"; then
    echo "✓ EVE Cloudflare tunnel is running"
else
    echo "⚠️  EVE Cloudflare tunnel not detected"
    echo ""
    echo "Make sure the EVE tunnel is running (from eve_py project):"
    echo "  cd /Users/jeffbutler/Dev/Dev/eve_py"
    echo "  # Use your existing tunnel start script"
    echo ""
    echo "AutoCoach will still work on localhost even without the tunnel."
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "🚀 Starting AutoCoach server..."
echo ""

# Activate virtual environment and start server
source ac_env/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down AutoCoach server..."
    kill $SERVER_PID 2>/dev/null
    echo "✓ Server stopped"
    exit 0
}

trap cleanup INT TERM

sleep 2

if ps -p $SERVER_PID > /dev/null; then
    echo "✓ Server started (PID: $SERVER_PID)"
else
    echo "❌ Server failed to start"
    exit 1
fi

echo ""
echo "================================================================================"
echo "✅ AutoCoach is running!"
echo "================================================================================"
echo ""
echo "🏠 Local URL:    http://localhost:8000"
echo "🌐 Public URL:   https://autocoach.eve-market.space (if tunnel running)"
echo "📖 API Docs:     http://localhost:8000/docs"
echo "🏥 Health:       http://localhost:8000/"
echo ""
echo "🔐 TrainingPeaks OAuth:"
echo "   Local:  http://localhost:8000/auth/trainingpeaks?sandbox=true"
echo "   Public: https://autocoach.eve-market.space/auth/trainingpeaks?sandbox=true"
echo ""
echo "📋 Note:"
echo "   • AutoCoach server running on port 8000"
echo "   • EVE tunnel (if running) routes autocoach.eve-market.space to this server"
echo "   • To stop: Press Ctrl+C"
echo ""
echo "================================================================================"
echo ""

# Wait for server process (keeps script running)
wait $SERVER_PID

