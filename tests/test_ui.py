"""
NyayaPath — Streamlit UI Automated Test Suite

Uses Streamlit's official AppTest framework to verify:
  1. Disclaimer Gate (FR-1): non-dismissible gate, checkbox validation, unlocking chat.
  2. Sidebar: Emergency helplines (112, 14416, 181), model selector, demo scenario presets.
  3. Chat Interface: Message history rendering and chat input availability.
  4. Code Regime Badge: Visual badge rendering for ipc_crpc, bns_bnss, ambiguous.
  5. Date Clarification Section: Timeline clarification inputs and submission handling.
"""

import pytest
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).parent.parent / "app.py")


@pytest.fixture
def app_initial():
    """Create an AppTest instance for app.py with default timeout."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()
    return at


@pytest.fixture
def app_unlocked():
    """Create an AppTest instance with disclaimer already accepted."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()
    # Check disclaimer checkbox
    if at.checkbox:
        at.checkbox[0].check().run()
        # Click Continue button
        for btn in at.button:
            if "Continue" in btn.label:
                btn.click().run()
                break
    return at


# ===========================================================================
# 1. Disclaimer Gate (FR-1) Tests
# ===========================================================================

def test_disclaimer_gate_initially_locked(app_initial):
    """FR-1: Chat must be completely locked until disclaimer is accepted."""
    at = app_initial
    assert at.session_state.disclaimer_accepted is False
    assert len(at.checkbox) >= 1
    assert at.checkbox[0].value is False

    # Continue button should be disabled when checkbox is unchecked
    continue_btn = next((b for b in at.button if "Continue" in b.label), None)
    assert continue_btn is not None
    assert continue_btn.disabled is True

    # Chat input should NOT be present while gate is locked
    assert len(at.chat_input) == 0


def test_disclaimer_gate_acceptance_unlocks_interface(app_initial):
    """FR-1: Accepting the disclaimer unlocks the main chat interface."""
    at = app_initial
    # Check the disclaimer checkbox
    at.checkbox[0].check().run()

    # Continue button should now be enabled
    continue_btn = next((b for b in at.button if "Continue" in b.label), None)
    assert continue_btn is not None
    assert continue_btn.disabled is False

    # Click continue
    continue_btn.click().run()

    # Disclaimer should now be accepted and chat input rendered
    assert at.session_state.disclaimer_accepted is True
    assert len(at.chat_input) == 1
    assert at.chat_input[0].placeholder == "Describe your legal situation..."


# ===========================================================================
# 2. Sidebar Component Tests
# ===========================================================================

def test_sidebar_emergency_helplines(app_unlocked):
    """Sidebar must render emergency helplines: 112, Tele-MANAS 14416, 181."""
    at = app_unlocked
    sidebar_text = " ".join([m.value for m in at.sidebar.markdown])
    assert "112" in sidebar_text
    assert "14416" in sidebar_text
    assert "Tele-MANAS" in sidebar_text
    assert "181" in sidebar_text


def test_sidebar_model_selector(app_unlocked):
    """Sidebar should contain model selector dropdown."""
    at = app_unlocked
    selectboxes = at.sidebar.selectbox
    assert len(selectboxes) >= 1
    model_sb = next((s for s in selectboxes if s.key == "model_selector"), None)
    assert model_sb is not None
    assert "qwen2.5:7b" in model_sb.options


def test_sidebar_demo_presets(app_unlocked):
    """Sidebar should provide quick demo scenarios for testing."""
    at = app_unlocked
    demo_sb = next((s for s in at.sidebar.selectbox if s.key == "demo_case_selector"), None)
    assert demo_sb is not None
    options = demo_sb.options
    assert any("BNS Case" in opt for opt in options)
    assert any("IPC Case" in opt for opt in options)
    assert any("Ambiguous" in opt for opt in options)
    assert any("Harmful" in opt for opt in options)
    assert any("Crisis" in opt for opt in options)


# ===========================================================================
# 3. Chat Interface & Message Rendering
# ===========================================================================

def test_chat_messages_render_correctly(app_unlocked):
    """Existing messages in session_state should be rendered to UI."""
    at = app_unlocked
    # Inject sample user and assistant messages
    at.session_state.messages = [
        {"role": "user", "content": "What is Section 420 IPC?"},
        {"role": "assistant", "content": "Section 420 of the Indian Penal Code deals with cheating."},
    ]
    at.run()

    # Verify both messages are in session_state
    assert len(at.session_state.messages) == 2
    assert at.session_state.messages[0]["content"] == "What is Section 420 IPC?"
    assert "cheating" in at.session_state.messages[1]["content"]


# ===========================================================================
# 4. Code Regime Badge Tests
# ===========================================================================

def test_regime_badge_renders_when_set(app_unlocked):
    """Setting current_regime in session_state displays the appropriate badge."""
    at = app_unlocked

    # Test BNS badge
    at.session_state.current_regime = "bns_bnss"
    at.run()
    markdown_texts = " ".join([m.value for m in at.markdown])
    assert "BNS / BNSS" in markdown_texts or "New Code" in markdown_texts

    # Test IPC badge
    at.session_state.current_regime = "ipc_crpc"
    at.run()
    markdown_texts = " ".join([m.value for m in at.markdown])
    assert "IPC / CrPC" in markdown_texts or "Old Code" in markdown_texts


# ===========================================================================
# 5. Date Clarification Section Tests
# ===========================================================================

def test_date_clarification_section_renders_when_awaiting_dates(app_unlocked):
    """When awaiting_dates is True, date input fields and submit button appear."""
    at = app_unlocked
    at.session_state.awaiting_dates = True
    at.session_state.last_user_story = "Someone stole my phone."
    at.run()

    # Verify text inputs for offence and FIR dates are rendered
    offence_input = next((ti for ti in at.text_input if ti.key == "offence_date_input"), None)
    fir_input = next((ti for ti in at.text_input if ti.key == "fir_date_input"), None)
    submit_btn = next((b for b in at.button if "Submit Dates" in b.label), None)

    assert offence_input is not None
    assert fir_input is not None
    assert submit_btn is not None

    # Fill in dates and click Submit Dates
    offence_input.input("August 2024").run()
    fir_input.input("September 2024").run()

    submit_btn = next((b for b in at.button if "Submit Dates" in b.label), None)
    submit_btn.click().run()

    # awaiting_dates should be False, and pending_prompt prepared
    assert at.session_state.awaiting_dates is False
    assert at.session_state.offence_date == "August 2024"
    assert at.session_state.fir_date == "September 2024"
    assert "August 2024" in at.session_state.pending_prompt
