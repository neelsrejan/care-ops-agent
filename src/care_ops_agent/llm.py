"""Language-model backends (slimmed from invalid-agent llm.py).

``deterministic`` renders the template and never opens a socket (default, CI).
``ollama`` asks a local model for prose. Every draft goes through the
numeric-fidelity guard; a rejected or failed draft falls back to the template
and the rejection is recorded.
"""

from __future__ import annotations

from typing import Any

from care_ops_agent.config import Settings, load_settings
from care_ops_agent.guards.numeric_fidelity import check_narrative

SYSTEM_PROMPT = (
    "You are a program-operations writer for a SIMULATED provider-network onboarding program. "
    "Rewrite the draft for clarity. Use ONLY numbers that appear in the draft or facts. "
    "Never compute new numbers. Keep the 'SIMULATION' label."
)


def _ollama(settings: Settings, draft: str, facts: dict[str, Any]) -> str:
    import json

    import httpx

    body = {
        "model": settings.llm_model,
        "stream": False,
        "options": {"temperature": 0.1},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"FACTS:\n{json.dumps(facts, default=str)}\n\nDRAFT:\n{draft}"},
        ],
    }
    response = httpx.post(f"{settings.ollama_host}/api/chat", json=body, timeout=120.0)
    response.raise_for_status()
    return str(response.json()["message"]["content"])


def narrate(draft: str, facts: dict[str, Any], settings: Settings | None = None) -> dict[str, Any]:
    """Return {'text', 'backend', 'fidelity', 'fallback_reason'}."""
    settings = settings or load_settings()
    base = check_narrative(draft, facts)
    if not base.ok:
        raise ValueError(f"template produced numbers not in facts: {base.unknown}")
    if settings.rules_only:
        return {"text": draft, "backend": "deterministic", "fidelity": base.to_dict(), "fallback_reason": None}
    try:
        text = _ollama(settings, draft, facts)
    except Exception as exc:  # network, model missing
        return {"text": draft, "backend": "deterministic", "fidelity": base.to_dict(), "fallback_reason": f"llm error: {exc}"}
    result = check_narrative(text, facts)
    if not result.ok:
        return {"text": draft, "backend": "deterministic", "fidelity": base.to_dict(),
                "fallback_reason": f"fidelity rejected {result.unknown}"}
    return {"text": text, "backend": settings.llm_backend, "fidelity": result.to_dict(), "fallback_reason": None}
