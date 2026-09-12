#!/bin/bash

# ==============================================================================
# SAAR - macOS Localhost One-Click Startup Script
# Automatically configures venv, installs dependencies, and boots SAAR
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "========================================================"
echo " 🔬 Starting SAAR Scientific Reasoning Engine on macOS"
echo "========================================================"

# 1. Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed."
    echo "   Run: brew install python@3.11"
    exit 1
fi

# 2. Check Node & npm
if ! command -v npm &> /dev/null; then
    echo "❌ Error: Node.js / npm is not installed."
    echo "   Run: brew install node"
    exit 1
fi

# 3. Setup Backend
echo "📦 [1/4] Checking Python backend environment..."
if [ ! -d "backend/venv" ]; then
    echo "   Creating virtual environment in backend/venv..."
    python3 -m venv backend/venv
fi

source backend/venv/bin/activate

if [ ! -f "backend/.env" ]; then
    echo "   Creating backend/.env from .env.example..."
    cp backend/.env.example backend/.env
fi

echo "   Installing/verifying backend dependencies..."
pip install -q -r backend/requirements.txt

# 4. Setup Frontend
echo "📦 [2/4] Checking React frontend dependencies..."
if [ ! -d "frontend/node_modules" ]; then
    echo "   Installing npm dependencies (first run only)..."
    (cd frontend && npm install)
fi

# Function to clean up background processes on Ctrl+C or exit
cleanup() {
    echo ""
    echo "🛑 Shutting down SAAR backend and frontend..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 5. Start Backend
echo "⚡ [3/4] Launching FastAPI Backend on http://127.0.0.1:8001..."
(cd backend && python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload) &
BACKEND_PID=$!

# Wait 2 seconds for backend to bind to port
sleep 2

# 6. Start Frontend
echo "⚡ [4/4] Launching React Frontend on http://localhost:3000..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

# Wait 2 seconds for frontend server to be ready
sleep 2

# 7. Open browser automatically on macOS
echo "🌐 Opening http://localhost:3000 in your browser..."
open "http://localhost:3000" 2>/dev/null || true

echo "========================================================"
echo " ✅ SAAR is live on localhost!"
echo "   • Frontend:  http://localhost:3000"
echo "   • Backend:   http://127.0.0.1:8001"
echo "   • API Docs:  http://127.0.0.1:8001/docs"
echo "========================================================"
echo "Press [Ctrl+C] in this terminal to stop all servers."

# Keep script running and wait for background processes
wait
