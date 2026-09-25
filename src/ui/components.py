"""
NyayaPath — Streamlit UI Components

Modular UI components for the NyayaPath interface:
  - Disclaimer gate (non-dismissible)
  - Chat message renderer
  - Code regime badge
  - Date input section for clarification
"""

from __future__ import annotations

import streamlit as st


# ---------------------------------------------------------------------------
# Disclaimer Gate (FR-1)
# ---------------------------------------------------------------------------

def render_disclaimer_gate():
    """Render the non-dismissible disclaimer modal.

    The chat interface is completely locked until this is accepted.
    """
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
             padding: 2rem; border-radius: 16px; border: 1px solid #e94560;
             margin: 2rem auto; max-width: 700px;">
            <h2 style="color: #e94560; text-align: center; margin-bottom: 1rem;">
                ⚠️ Important Notice
            </h2>
            <p style="color: #eee; font-size: 1.05rem; line-height: 1.7;">
                <strong>NyayaPath</strong> is a <strong>portfolio / educational project</strong>
                demonstrating AI engineering capabilities. It is <strong>NOT</strong> a legal
                service and does <strong>NOT</strong> provide legal advice.
            </p>
            <ul style="color: #ccc; font-size: 0.95rem; line-height: 1.8;">
                <li>This system provides <strong>general educational information</strong> about
                    Indian legal procedures only.</li>
                <li>It is <strong>not a substitute</strong> for a qualified legal practitioner.</li>
                <li>Every case is unique — you <strong>must</strong> consult an advocate for
                    advice specific to your situation.</li>
                <li>This project is <strong>not publicly deployed</strong> as a service and
                    does not solicit clients.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    accepted = st.checkbox(
        "I understand that NyayaPath is an educational AI project and does "
        "not provide legal advice. I will consult a qualified advocate for "
        "any real legal matter.",
        key="disclaimer_checkbox",
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            "Continue to NyayaPath",
            disabled=not accepted,
            use_container_width=True,
            type="primary",
        ):
            st.session_state.disclaimer_accepted = True
            st.rerun()


# ---------------------------------------------------------------------------
# Chat Message Renderer
# ---------------------------------------------------------------------------

def render_chat_message(role: str, content: str):
    """Render a chat message with appropriate styling.

    Args:
        role: Either 'user' or 'assistant'.
        content: The message content (supports markdown).
    """
    with st.chat_message(role, avatar="👤" if role == "user" else "⚖️"):
        st.markdown(content)


# ---------------------------------------------------------------------------
# Code Regime Badge
# ---------------------------------------------------------------------------

_REGIME_DISPLAY = {
    "ipc_crpc": {
        "label": "Old Code (IPC / CrPC) — Offence Prior to July 1, 2024",
        "color": "#e94560",
        "emoji": "🔴",
    },
    "bns_bnss": {
        "label": "New Code (BNS / BNSS) — Offence On or After July 1, 2024",
        "color": "#0f9d58",
        "emoji": "🟢",
    },
    "ambiguous": {
        "label": "Ambiguous / Straddling Timeline — Dual Code Considerations",
        "color": "#f4b400",
        "emoji": "🟡",
    },
}


def render_regime_badge(regime: str):
    """Render a visual badge indicating the determined code regime.

    Args:
        regime: One of 'ipc_crpc', 'bns_bnss', or 'ambiguous'.
    """
    display = _REGIME_DISPLAY.get(regime)
    if not display:
        return

    st.markdown(
        f"""
        <div style="display: inline-flex; align-items: center; gap: 0.5rem;
             background: {display['color']}22; border: 1px solid {display['color']};
             border-radius: 8px; padding: 0.4rem 1rem; margin: 0.5rem 0;">
            <span style="font-size: 1.2rem;">{display['emoji']}</span>
            <span style="color: {display['color']}; font-weight: 600; font-size: 0.9rem;">
                {display['label']}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Date Input Section (Clarification)
# ---------------------------------------------------------------------------

def render_date_input_section():
    """Render date input fields when the agent requests clarification."""
    st.markdown("---")
    st.markdown("### 📅 Timeline Clarification")
    st.markdown(
        "The applicable law depends on when the events occurred. "
        "Please provide approximate dates if you can."
    )

    col1, col2 = st.columns(2)

    with col1:
        offence_date = st.text_input(
            "When did the events / alleged offence take place?",
            placeholder="e.g., March 2024, last year, 2023",
            key="offence_date_input",
        )

    with col2:
        fir_date = st.text_input(
            "When was the FIR / complaint registered?",
            placeholder="e.g., August 2024, last month",
            key="fir_date_input",
        )

    if st.button("Submit Dates", type="primary"):
        st.session_state.offence_date = offence_date if offence_date else None
        st.session_state.fir_date = fir_date if fir_date else None
        st.session_state.awaiting_dates = False

        # Prepare combined story and delegate to main chat execution loop
        if st.session_state.last_user_story:
            combined = st.session_state.last_user_story
            if offence_date:
                combined += f" The events took place around {offence_date}."
            if fir_date:
                combined += f" The FIR was registered around {fir_date}."

            st.session_state.pending_prompt = combined
            st.session_state.pending_label = (
                f"[Date clarification] Offence: {offence_date or 'not specified'}, "
                f"FIR: {fir_date or 'not specified'}"
            )
        st.rerun()

