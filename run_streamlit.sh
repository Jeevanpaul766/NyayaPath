#!/bin/bash
# ==============================================================================
# NyayaPath — Start Streamlit UI
# ==============================================================================

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "======================================================================"
echo "  ⚖️  NyayaPath — Streamlit UI Launcher"
echo "  Opening http://localhost:8501 ..."
echo "======================================================================"

streamlit run app.py
