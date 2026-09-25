#!/usr/bin/env python3
"""
NyayaPath — Environment Verification Script

Pre-flight check to ensure all dependencies are satisfied before running
the application. Verifies:
  1. Python version >= 3.11
  2. Ollama server reachability and model availability
  3. Tavily API key presence and basic validity
  4. Required packages installed

Usage:
    python scripts/verify_env.py
"""

import sys
import os
import importlib

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def check_python_version() -> bool:
    """Verify Python 3.11+."""
    ok = sys.version_info >= (3, 11)
    tag = "✅" if ok else "❌"
    print(f"  {tag} Python version: {sys.version.split()[0]} (need ≥3.11)")
    return ok


def check_packages() -> bool:
    """Verify core packages are importable."""
    required = [
        "langgraph",
        "langchain_core",
        "langchain_community",
        "langchain_ollama",
        "tavily",
        "streamlit",
        "pydantic",
        "dotenv",
        "rich",
        "pytest",
    ]
    all_ok = True
    for pkg in required:
        try:
            importlib.import_module(pkg)
            print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ❌ {pkg} — not installed")
            all_ok = False
    return all_ok


def check_ollama() -> bool:
    """Ping the Ollama server and check if the model is available."""
    try:
        import urllib.request
        import json

        from src.config import OLLAMA_BASE_URL, DEFAULT_MODEL

        # Check server
        req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())

        models = [m["name"] for m in data.get("models", [])]
        has_model = any(DEFAULT_MODEL in m for m in models)

        print(f"  ✅ Ollama server reachable at {OLLAMA_BASE_URL}")
        if has_model:
            print(f"  ✅ Model '{DEFAULT_MODEL}' available")
        else:
            print(f"  ⚠️  Model '{DEFAULT_MODEL}' not found. Available: {models}")
            print(f"      Run: ollama pull {DEFAULT_MODEL}")
        return True
    except Exception as exc:
        print(f"  ❌ Ollama server unreachable — {exc}")
        print(f"      Start Ollama and run: ollama pull qwen2.5:7b")
        return False


def check_tavily() -> bool:
    """Verify Tavily API key is set."""
    from src.config import TAVILY_API_KEY

    if TAVILY_API_KEY and TAVILY_API_KEY != "tvly-your-key-here":
        print(f"  ✅ TAVILY_API_KEY is set ({TAVILY_API_KEY[:8]}...)")
        return True
    else:
        print("  ❌ TAVILY_API_KEY not set or is placeholder")
        print("      Get a free key at https://tavily.com and add to .env")
        return False


def main():
    print("=" * 60)
    print("  NyayaPath — Environment Verification")
    print("=" * 60)

    sections = [
        ("Python Version", check_python_version),
        ("Required Packages", check_packages),
        ("Ollama Server & Model", check_ollama),
        ("Tavily API Key", check_tavily),
    ]

    all_pass = True
    for title, checker in sections:
        print(f"\n🔍 {title}")
        if not checker():
            all_pass = False

    print("\n" + "=" * 60)
    if all_pass:
        print("  ✅ All checks passed — ready to run NyayaPath!")
    else:
        print("  ⚠️  Some checks failed — review above before running.")
    print("=" * 60)

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
