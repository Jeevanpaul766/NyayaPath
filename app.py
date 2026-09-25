"""
NyayaPath — Streamlit Application Entry Point

Ethical Legal Guidance Agent for Indian citizens.
Portfolio / Educational Project — NOT legal advice.
"""

import streamlit as st
from src.ui.components import (
    render_disclaimer_gate,
    render_chat_message,
    render_regime_badge,
    render_date_input_section,
)
from src.ui.sidebar import render_sidebar
from src.graph.builder import build_graph, get_initial_state
from src.config import PROJECT_CLASSIFICATION, PROJECT_VERSION

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="NyayaPath — Ethical Legal Guidance",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load custom CSS
with open("src/ui/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------

if "disclaimer_accepted" not in st.session_state:
    st.session_state.disclaimer_accepted = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "graph" not in st.session_state:
    st.session_state.graph = None
if "current_regime" not in st.session_state:
    st.session_state.current_regime = None
if "awaiting_dates" not in st.session_state:
    st.session_state.awaiting_dates = False
if "offence_date" not in st.session_state:
    st.session_state.offence_date = None
if "fir_date" not in st.session_state:
    st.session_state.fir_date = None
if "last_user_story" not in st.session_state:
    st.session_state.last_user_story = ""
if "processing" not in st.session_state:
    st.session_state.processing = False
if "node_trace" not in st.session_state:
    st.session_state.node_trace = []


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

render_sidebar()


# ---------------------------------------------------------------------------
# Main Content
# ---------------------------------------------------------------------------

st.markdown("# ⚖️ NyayaPath")
st.markdown(
    f"**Ethical Legal Guidance Agent** · {PROJECT_CLASSIFICATION} · v{PROJECT_VERSION}"
)
st.markdown("---")


# ---------------------------------------------------------------------------
# Disclaimer Gate (FR-1)
# ---------------------------------------------------------------------------

if not st.session_state.disclaimer_accepted:
    render_disclaimer_gate()
    st.stop()


# ---------------------------------------------------------------------------
# Chat Interface
# ---------------------------------------------------------------------------

# Display existing messages
for msg in st.session_state.messages:
    render_chat_message(msg["role"], msg["content"])

# Display regime badge if set
if st.session_state.current_regime:
    render_regime_badge(st.session_state.current_regime)

# Date input section when awaiting dates
if st.session_state.awaiting_dates:
    render_date_input_section()

# Chat input
user_input = st.chat_input(
    "Describe your legal situation...",
    disabled=st.session_state.processing,
)

# Determine prompt to process: direct chat input OR pending date clarification
prompt_to_process = None
display_prompt = None

if user_input:
    prompt_to_process = user_input
    display_prompt = user_input
elif "pending_prompt" in st.session_state and st.session_state.pending_prompt:
    prompt_to_process = st.session_state.pending_prompt
    display_prompt = st.session_state.get("pending_label", prompt_to_process)
    st.session_state.pending_prompt = None
    st.session_state.pending_label = None

if prompt_to_process:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": display_prompt})
    render_chat_message("user", display_prompt)

    # Build graph if not cached
    if st.session_state.graph is None:
        with st.spinner("Initializing NyayaPath..."):
            st.session_state.graph = build_graph()

    # Convert previous messages into LangChain messages
    from langchain_core.messages import HumanMessage, AIMessage
    lc_messages = []
    for m in st.session_state.messages:
        if m["role"] == "user":
            lc_messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            lc_messages.append(AIMessage(content=m["content"]))

    # If awaiting dates, preserve original root user story
    original_story = (
        st.session_state.last_user_story
        if (st.session_state.awaiting_dates and st.session_state.last_user_story)
        else prompt_to_process
    )

    # Prepare initial state
    initial_state = get_initial_state(
        user_story=prompt_to_process,
        disclaimer_accepted=True,
        original_user_story=original_story,
        messages=lc_messages,
        offence_date=st.session_state.offence_date,
        fir_date=st.session_state.fir_date,
        selected_model=st.session_state.get("selected_model", ""),
    )

    # Run the graph
    st.session_state.processing = True
    st.session_state.node_trace = []

    with st.spinner("Analyzing timeline and synthesizing legal guidance..."):
        try:
            result = st.session_state.graph.invoke(initial_state)

            # Store execution telemetry
            st.session_state.node_trace = result.get("node_trace", [])

            # Extract response
            final_guidance = result.get("final_guidance", "")
            code_regime = result.get("code_regime")

            if final_guidance:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_guidance,
                })
                st.session_state.current_regime = code_regime

                # Check if clarification was requested
                if result.get("needs_clarification", False):
                    st.session_state.awaiting_dates = True
                    if not st.session_state.last_user_story:
                        st.session_state.last_user_story = prompt_to_process
                else:
                    st.session_state.awaiting_dates = False
                    st.session_state.last_user_story = ""

        except Exception as e:
            error_msg = f"An error occurred: {str(e)}. Please try again."
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg,
            })

    st.session_state.processing = False
    st.rerun()

