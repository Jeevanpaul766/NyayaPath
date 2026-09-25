"""
NyayaPath — LangGraph Architecture Visualizer

Generates:
  1. Interactive HTML diagram in docs/nyayapath_graph.html
  2. Mermaid syntax to console / docs/nyayapath_graph.mmd
  3. Formatted terminal workflow breakdown
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.graph.builder import build_graph

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
DOCS_DIR.mkdir(exist_ok=True)


def main():
    print("⚖️ Compiling NyayaPath LangGraph StateGraph...")
    graph = build_graph()
    mermaid_raw = graph.get_graph().draw_mermaid()
    clean_mermaid = mermaid_raw.replace("<p>", "").replace("</p>", "")

    # 1. Save .mmd file
    mmd_path = DOCS_DIR / "nyayapath_graph.mmd"
    with open(mmd_path, "w", encoding="utf-8") as f:
        f.write(clean_mermaid)
    print(f"✅ Saved Mermaid definition: {mmd_path}")

    # 2. Save Interactive HTML
    html_path = DOCS_DIR / "nyayapath_graph.html"
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>NyayaPath — LangGraph Architecture</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: #0b1120;
            color: #f1f5f9;
            margin: 0;
            padding: 32px;
        }}
        .header {{
            max-width: 1000px;
            margin: 0 auto 24px auto;
        }}
        h1 {{
            font-size: 26px;
            color: #38bdf8;
            margin: 0 0 8px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        p.subtitle {{
            color: #94a3b8;
            margin: 0 0 20px 0;
            font-size: 15px;
            line-height: 1.5;
        }}
        .badge {{
            display: inline-block;
            background: #1e293b;
            color: #e2e8f0;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
            border: 1px solid #334155;
            margin-right: 6px;
        }}
        .card {{
            max-width: 1000px;
            margin: 0 auto;
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 20px 35px rgba(0, 0, 0, 0.4);
            overflow-x: auto;
        }}
        .mermaid {{
            display: flex;
            justify-content: center;
        }}
        .legend {{
            max-width: 1000px;
            margin: 24px auto 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 12px;
        }}
        .legend-item {{
            background: #1e293b;
            border: 1px solid #334155;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 13px;
        }}
        .legend-title {{
            font-weight: 600;
            color: #38bdf8;
            margin-bottom: 4px;
        }}
        .legend-desc {{
            color: #94a3b8;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⚖️ NyayaPath — LangGraph StateGraph Architecture</h1>
        <p class="subtitle">
            12-node compiled stateful graph for Indian legal guidance with ethical guardrails,
            cross-regime reasoning (IPC/CrPC vs. BNS/BNSS), Tavily web search grading, and deterministic output sanitization.
        </p>
        <div>
            <span class="badge">Nodes: 12</span>
            <span class="badge">Conditional Branches: 5</span>
            <span class="badge">Safety Gates: 3</span>
            <span class="badge">Tracing: LangSmith Ready</span>
        </div>
    </div>

    <div class="card">
        <div class="mermaid">
{clean_mermaid}
        </div>
    </div>

    <div class="legend">
        <div class="legend-item">
            <div class="legend-title">🚨 Safety Tripwires</div>
            <div class="legend-desc">Crisis detection (112/14416) & Harm filter (crime commission refusal) short-circuit immediately.</div>
        </div>
        <div class="legend-item">
            <div class="legend-title">📅 Regime Reasoning</div>
            <div class="legend-desc">Classifies incident date against July 1, 2024 to assign IPC/CrPC or BNS/BNSS statutory regime.</div>
        </div>
        <div class="legend-item">
            <div class="legend-title">🔍 Tavily Retrieval & Grade</div>
            <div class="legend-desc">Queries trusted legal domains (IndiaCode, NALSA) with automatic 1-retry relevance grading.</div>
        </div>
        <div class="legend-item">
            <div class="legend-title">🛡️ Deterministic Quality Gate</div>
            <div class="legend-desc">Zero-LLM sanitizer verifies disclaimer, blocks predictions, and strips cross-regime hallucinated sections.</div>
        </div>
    </div>

    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            flowchart: {{
                curve: 'basis'
            }}
        }});
    </script>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ Saved interactive HTML viewer: {html_path}")
    print("\nOpen in your browser with:")
    print(f"  open '{html_path}'")


if __name__ == "__main__":
    main()
