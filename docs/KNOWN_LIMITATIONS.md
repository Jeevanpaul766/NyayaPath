# NyayaPath — Known Limitations

This document transparently lists the limitations of NyayaPath as a portfolio project. Listing these items signals awareness of the gap between a portfolio demonstration and a production system.

---

## Fundamental Limitations

1. **This is NOT legal advice.** NyayaPath provides general educational information only. Every legal case is unique and requires assessment by a qualified advocate.

2. **Portfolio scope only.** This system is not publicly deployed, does not accept real clients, and exists solely to demonstrate AI engineering capabilities.

---

## Technical Limitations

### Legal Coverage
- **Only 15 provisions** are mapped (IPC/CrPC to BNS/BNSS). A production system would need 30-40+ provisions covering additional offence categories.
- **Ambiguous regime handling is limited** to an honest hedging paragraph. Full dual-framing (showing both IPC and BNS provisions side-by-side with proper context) is not implemented.
- **No coverage of civil law, family court procedures, or consumer disputes.** Only criminal/quasi-criminal matters are addressed.

### Institutional Data
- **No district-level DLSA lookup.** Only national-level NALSA and state-level SLSA are referenced.
- **Legal aid eligibility criteria** are presented in general terms without jurisdiction-specific thresholds.

### Model Capabilities
- **Qwen2.5:7b has inherent limitations** in reasoning quality compared to larger models. Edge cases may produce suboptimal classifications.
- **Single model architecture** — no ensemble or cross-validation between models.
- **No fine-tuning** on Indian legal corpus.

### System Design
- **Session-only memory** — no conversation persistence across browser sessions.
- **No authentication** — any user can access the system.
- **No rate limiting** — vulnerable to abuse in a production setting.
- **Single retry** for both search and output check — production systems would implement exponential backoff with circuit breakers.
- **English only** — no Hindi, Tamil, Bengali, or other Indian language support.

### Search & Retrieval
- **Tavily free tier** — limited API calls and may have availability issues.
- **Domain whitelist** may miss relevant content from legal blogs, Bar Council sites, or state government portals.
- **No local document store** — relies entirely on live search.

### Safety System
- **Action-based classifier is LLM-dependent** — misclassification is possible for subtle or ambiguously phrased requests.
- **Crisis detection may false-positive** on extreme legal distress that doesn't involve self-harm risk.
- **No human-in-the-loop** escalation path beyond suggesting the user contact a lawyer.

---

## Production Gap Summary

| Portfolio Version | Production Requirement |
|---|---|
| 15 provisions | 30-40+ provisions |
| Ambiguous = hedging paragraph | Full dual-framing response |
| NALSA only | DLSA directory (600+ districts) |
| English only | Multilingual (Hindi + regional) |
| Single retry | Exponential backoff + circuit breaker |
| No persistence | Encrypted session storage |
| No auth | Secure authentication + RBAC |
| 25 eval cases (7 categories) | 50+ cases with automated tone scoring |
| 7b model | 14b+ with fine-tuning |
| No legal review | Formal legal review of all outputs |
