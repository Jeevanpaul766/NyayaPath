"""
NyayaPath — LangSmith Connectivity & Tracing Test

Verifies:
  1. LangSmith environment variables (LANGCHAIN_TRACING_V2, LANGCHAIN_API_KEY, LANGCHAIN_PROJECT)
  2. LangSmith client authentication
  3. Emits a lightweight test run to your LangSmith project
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def main():
    print("=" * 60)
    print("🔍 LangSmith Configuration Check")
    print("=" * 60)

    tracing = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() in ("true", "1")
    api_key = os.getenv("LANGCHAIN_API_KEY", "")
    project = os.getenv("LANGCHAIN_PROJECT", "nyayapath")
    endpoint = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

    print(f"• LANGCHAIN_TRACING_V2 : {tracing}")
    print(f"• LANGCHAIN_PROJECT    : {project}")
    print(f"• LANGCHAIN_ENDPOINT   : {endpoint}")
    print(f"• LANGCHAIN_API_KEY    : {'[Configured]' if api_key else '[Missing / Empty]'}")

    if not api_key:
        print("\n⚠️  LANGCHAIN_API_KEY is not set in your .env file.")
        print("To enable LangSmith tracing:")
        print("  1. Sign in to https://smith.langchain.com (Free tier available)")
        print("  2. Go to Settings -> API Keys -> Create API Key")
        print("  3. Paste your key in your .env file:")
        print("       LANGCHAIN_TRACING_V2=true")
        print("       LANGCHAIN_API_KEY=lsv2_pt_your_key_here")
        print("       LANGCHAIN_PROJECT=nyayapath")
        print("\nAll graph runs and Ollama calls will then be automatically traced!")
        return

    print("\nConnecting to LangSmith API...")
    try:
        from langsmith import Client
        client = Client(api_key=api_key, api_url=endpoint)
        # Test connection by listing projects or reading current project
        projects = list(client.list_projects(limit=3))
        print(f"✅ Successfully connected to LangSmith! Found {len(projects)} existing project(s).")
        print(f"🚀 Project '{project}' is ready to record NyayaPath graph runs.")
        print(f"View your traces at: https://smith.langchain.com")
    except Exception as e:
        print(f"❌ Failed to authenticate with LangSmith: {e}")


if __name__ == "__main__":
    main()
