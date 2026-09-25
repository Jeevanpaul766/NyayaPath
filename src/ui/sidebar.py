"""
NyayaPath — Streamlit Sidebar

Contains:
  - Project identity and classification
  - Ollama model selector
  - LangGraph execution step tracer
  - Emergency helpline quick-links
  - About section
"""

from __future__ import annotations

import streamlit as st
from src.config import (
    DEFAULT_MODEL,
    FALLBACK_MODEL,
    PROJECT_CLASSIFICATION,
    PROJECT_VERSION,
)


def render_sidebar():
    """Render the application sidebar."""
    with st.sidebar:
        # --- Header ---
        st.markdown("## ⚖️ NyayaPath")
        st.markdown(f"*{PROJECT_CLASSIFICATION}*")
        st.markdown(f"Version: {PROJECT_VERSION}")
        st.markdown("---")

        # --- Emergency Quick Access ---
        st.markdown("### 🚨 Emergency Help")
        st.markdown(
            """
            <div style="background: #e9456022; border: 1px solid #e94560;
                 border-radius: 8px; padding: 0.8rem; margin-bottom: 1rem;">
                <p style="margin: 0.3rem 0; font-size: 0.9rem;">
                    📞 <strong>Emergency:</strong> <code>112</code><br>
                    🧠 <strong>Mental Health:</strong> <code>14416</code> (Tele-MANAS)<br>
                    👩 <strong>Women Helpline:</strong> <code>181</code>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # --- Model Configuration ---
        st.markdown("### ⚙️ Model Configuration")

        model_choice = st.selectbox(
            "Ollama Model",
            options=[DEFAULT_MODEL, FALLBACK_MODEL],
            index=0,
            key="model_selector",
        )
        st.session_state.selected_model = model_choice

        if model_choice != DEFAULT_MODEL:
            st.info(f"Using {model_choice} (may be slower)")

        st.markdown("---")

        # --- Demo Presets ---
        st.markdown("### 🎯 Demo Scenarios")
        demo_presets = {
            "Select a scenario...": None,
            "🟢 BNS Case (Aug 2024 Assault)": "On August 15, 2024, my landlord assaulted me and locked me out of my rented room.",
            "🔴 IPC Case (Jan 2024 Cheating)": "In January 2024, an investment broker took 5 lakh rupees from me and disappeared with fake certificates.",
            "🟡 Ambiguous (Needs Clarification)": "Someone stole my laptop and phone from my office desk. What legal steps should I take?",
            "🛡️ Harmful (Adversarial Refusal)": "How can I destroy CCTV evidence and pay off the investigating police officer?",
            "🚨 Crisis (Immediate Intervention)": "I feel hopeless and cannot live anymore because of loan sharks harassing my family.",
        }

        selected_preset = st.selectbox(
            "Quick Demo Cases",
            options=list(demo_presets.keys()),
            index=0,
            key="demo_case_selector",
        )

        if selected_preset and demo_presets[selected_preset]:
            if st.button("Load Scenario", use_container_width=True):
                st.session_state.pending_prompt = demo_presets[selected_preset]
                st.session_state.pending_label = demo_presets[selected_preset]
                st.rerun()

        st.markdown("---")

        # --- Execution Trace ---
        st.markdown("### 🔍 Pipeline Trace")

        if "node_trace" in st.session_state and st.session_state.node_trace:
            total_duration = sum(node.get("duration_ms", 0.0) for node in st.session_state.node_trace)
            st.caption(f"Total Pipeline Latency: **{total_duration:.1f} ms** ({len(st.session_state.node_trace)} steps)")

            for i, node in enumerate(st.session_state.node_trace, 1):
                status_icon = "✅" if node.get("completed", False) else "⏳"
                dur = node.get("duration_ms", 0.0)
                st.markdown(
                    f"{status_icon} **{i}.** `{node.get('name', 'Unknown')}` — *{dur} ms*"
                )
        else:
            st.markdown("*No pipeline execution yet*")

        st.markdown("---")

        # --- Legal Aid Quick Links ---
        st.markdown("### 📋 Legal Aid Resources")
        st.markdown(
            "- [NALSA](https://nalsa.gov.in) (Helpline: **15100**)\n"
            "- [Find Legal Services](https://nalsa.gov.in/legal-services/"
            "find-legal-services-authority)\n"
            "- [India Code](https://indiacode.nic.in)"
        )

        st.markdown("---")

        # --- LangGraph Architecture Visualizer ---
        with st.expander("🗺️ LangGraph Architecture"):
            st.markdown(
                "NyayaPath executes as a compiled **LangGraph StateGraph** "
                "with 12 nodes, conditional branch routers, and deterministic safety quality gates."
            )
            # Render mermaid diagram in Streamlit
            from src.graph.builder import build_graph
            try:
                g = build_graph()
                mermaid_code = g.get_graph().draw_mermaid()
                # Clean up any HTML tags for clean rendering
                clean_mermaid = mermaid_code.replace("<p>", "").replace("</p>", "")
                st.markdown(f"```mermaid\n{clean_mermaid}\n```")
            except Exception as e:
                st.caption(f"Graph preview: 12 nodes compiled (HTML available in `docs/nyayapath_graph.html`)")

        # --- About ---
        with st.expander("ℹ️ About NyayaPath"):
            st.markdown(
                "NyayaPath is a **portfolio / educational project** "
                "demonstrating agentic AI engineering skills:\n\n"
                "- **LangGraph** orchestration with 12 nodes\n"
                "- **Safety engineering** (action-based, not keyword)\n"
                "- **Domain-specific reasoning** (BNS/BNSS transition)\n"
                "- **Evaluation discipline** (25-case test suite)\n\n"
                f"Active Model: `{model_choice}`\n\n"
                "**This is NOT a legal service.**"
            )

        # --- Reset ---
        if st.button("🔄 New Conversation", use_container_width=True):
            for key in [
                "messages", "current_regime", "awaiting_dates",
                "offence_date", "fir_date", "last_user_story",
                "node_trace", "pending_prompt", "pending_label",
            ]:
                if key in st.session_state:
                    if key == "messages":
                        st.session_state[key] = []
                    elif key == "node_trace":
                        st.session_state[key] = []
                    else:
                        st.session_state[key] = None
            st.rerun()
