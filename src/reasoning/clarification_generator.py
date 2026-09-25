"""
NyayaPath — Clarification Question Generator

Generates the mandatory clarifying questions when the user's story
does not contain sufficient temporal information to determine the
applicable code regime.

Per PRD Section 6.1, two questions are asked when relevant:
  1. Roughly when did the events / alleged offence take place?
  2. When was the FIR / complaint registered?
"""

from __future__ import annotations


CLARIFICATION_PROMPT = (
    "To provide you with the most accurate procedural information, I need "
    "to understand the timeline of your situation. This is important because "
    "India's criminal laws changed on **1 July 2024** — the applicable code "
    "depends on when the events occurred.\n\n"
    "Could you please share:\n\n"
    "1. **Roughly when did the events or alleged incidents take place?**\n"
    "   _(For example: \"around March 2024\" or \"over the last six months\" "
    "or \"in 2023\")_\n\n"
    "2. **When was the FIR or formal complaint registered?**\n"
    "   _(For example: \"last month\" or \"August 2024\" — if applicable)_\n\n"
    "If you don't know the exact dates, an approximate timeframe is helpful. "
    "If you're unsure, just let me know and I'll provide general guidance "
    "that covers both the old and new legal frameworks."
)


def get_clarification_prompt() -> str:
    """Return the standard clarification prompt."""
    return CLARIFICATION_PROMPT
