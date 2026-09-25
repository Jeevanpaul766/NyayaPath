#!/bin/bash
# ==============================================================================
# NyayaPath — Start Modern Full-Stack (FastAPI Backend + React Frontend)
# ==============================================================================

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "======================================================================"
echo "  ⚖️  NyayaPath Legal AI Agent — Modern Full-Stack Launcher"
echo "======================================================================"

# 1. Activate Python virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment 'venv' not found! Please create it."
    exit 1
fi

# 2. Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "⚠️  Ollama is not running on http://localhost:11434!"
    echo "   Please start Ollama in another terminal with: ollama serve"
    echo "   Proceeding anyway..."
fi

# 3. Start FastAPI Backend in background
echo "🚀 Starting FastAPI Backend on http://127.0.0.1:8000 ..."
python backend/run_backend.py &
BACKEND_PID=$!

# Trap signals to kill backend on exit
trap "echo 'Stopping NyayaPath servers...'; kill $BACKEND_PID 2>/dev/null; exit 0" INT TERM EXIT

sleep 2

# 4. Start Vite React Frontend
echo "✨ Starting Vite React Frontend on http://localhost:5173 ..."
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173

# Wait for background processes
wait $BACKEND_PID
