#!/usr/bin/env python3
"""
NyayaPath — Start FastAPI Backend Server
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn

if __name__ == "__main__":
    print("=" * 65)
    print("  ⚖️  NyayaPath Legal Guidance Agent — FastAPI Backend")
    print("  Listening on http://127.0.0.1:8000")
    print("  API Docs:     http://127.0.0.1:8000/docs")
    print("=" * 65)
    uvicorn.run("backend.server:app", host="127.0.0.1", port=8000, reload=True)
