#!/usr/bin/env bash

# Get the directory of the script
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "Checking Python environment..."
# Check if virtual environment exists, if not create it
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Use virtual environment python
PYTHON="$ROOT/.venv/bin/python"
PIP="$ROOT/.venv/bin/pip"

echo "Installing backend dependencies..."
"$PIP" install -r requirements.txt

echo "Checking Node.js environment..."
# Check if node_modules exists, if not run npm install
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi
cd ..

# Function to handle cleanup on exit
cleanup() {
    echo "Stopping FieldMind..."
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill -TERM $FRONTEND_PID 2>/dev/null # Use TERM for npm
    fi
    exit 0
}

# Set trap to call cleanup function on SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

echo "Starting FieldMind backend on http://localhost:8002 ..."
"$PYTHON" -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8002 &
BACKEND_PID=$!

echo "Starting FieldMind frontend (Vite) on port 5174 ..."
cd frontend
npm run dev -- --port 5174 &
FRONTEND_PID=$!
cd ..

echo ""
echo "FieldMind is starting."
echo "Backend:  http://localhost:8002"
echo "Frontend: http://localhost:5174"
echo ""
echo "Press Ctrl+C to stop both processes."

# Wait for all background processes
wait
