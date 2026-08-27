"""
llm_feedback.py
----------------
Turns raw scores + rule-based suggestions into a friendly, readable
feedback paragraph. Three interchangeable backends (set via
config.FEEDBACK_BACKEND):

  "template"    -> deterministic, zero-dependency string formatting.
                   Always works, recommended default for HF Spaces free tier.
  "ollama"      -> calls a locally running Ollama server for natural,
                   varied language. Best for local development.
  "huggingface" -> uses a local transformers text2text-generation pipeline
                   (flan-t5-base by default).

All backends ultimately funnel through generate_feedback(), so app.py
never needs to know which one is active. Every network/model call is
wrapped in try/except with an automatic fallback to the template
backend — a flaky/offline LLM should never crash the app or block the
user from getting *some* feedback.
"""

import json
import logging
from typing import Dict, List

import requests

from config import FEEDBACK_BACKEND, OLLAMA_MODEL, OLLAMA_URL, HF_FEEDBACK_MODEL
from ats_scorer import generate_rule_based_suggestions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_hf_pipeline = None  # lazy-loaded singleton so we don't reload the model per call


def _template_feedback(
    ats_score: float,
    keyword_score: float,
    structure_score: float,
    checks: Dict[str, bool],
    missing_keywords: List[str],
) -> str:
    """Pure Python, deterministic feedback — no external calls, never fails."""
    suggestions = generate_rule_based_suggestions(checks, missing_keywords)

    if ats_score >= 80:
        tone = "Your resume is in strong shape for ATS systems."
    elif ats_score >= 60:
        tone = "Your resume is reasonably solid but has room to improve."
    else:
        tone = "Your resume needs some key improvements to pass ATS filters reliably."

    lines = [
        f"{tone} Overall ATS score: {ats_score}/100 "
        f"(Keyword match: {keyword_score}/100, Structure: {structure_score}/100).",
        "",
        "Suggestions:",
    ]
    lines += [f"- {s}" for s in suggestions]
    return "\n".join(lines)


def _ollama_feedback(prompt: str) -> str:
    """Calls a local Ollama server. Raises on any failure (caller handles fallback)."""
    response = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip()


def _huggingface_feedback(prompt: str) -> str:
    """Runs a local transformers text2text-generation pipeline. Lazy-loaded."""
    global _hf_pipeline
    if _hf_pipeline is None:
        from transformers import pipeline  # heavy import kept local & lazy

        _hf_pipeline = pipeline("text2text-generation", model=HF_FEEDBACK_MODEL)

    result = _hf_pipeline(prompt, max_new_tokens=200, do_sample=False)
    return result[0]["generated_text"].strip()


def _build_prompt(
    ats_score: float,
    keyword_score: float,
    structure_score: float,
    matched_keywords: List[str],
    missing_keywords: List[str],
    checks: Dict[str, bool],
) -> str:
    failed_checks = [k for k, v in checks.items() if not v]
    return (
        "You are an expert resume coach. A resume was scored by an automated "
        f"ATS analyzer with an overall score of {ats_score}/100 "
        f"(keyword match {keyword_score}/100, structure {structure_score}/100).\n"
        f"Matched keywords: {', '.join(matched_keywords) or 'none'}.\n"
        f"Missing keywords: {', '.join(missing_keywords) or 'none'}.\n"
        f"Failed structural checks: {', '.join(failed_checks) or 'none'}.\n\n"
        "Write a short, encouraging, specific paragraph (5-7 sentences) of "
        "actionable feedback for the candidate, referencing the concrete "
        "missing keywords and failed checks above."
    )


def generate_feedback(
    ats_score: float,
    keyword_score: float,
    structure_score: float,
    matched_keywords: List[str],
    missing_keywords: List[str],
    checks: Dict[str, bool],
) -> str:
    """
    Main entry point used by app.py. Dispatches to the configured backend
    and ALWAYS falls back to the template backend on any failure, so the
    user is never left without feedback (and the app never crashes).
    """
    if FEEDBACK_BACKEND == "template":
        return _template_feedback(ats_score, keyword_score, structure_score, checks, missing_keywords)

    prompt = _build_prompt(
        ats_score, keyword_score, structure_score, matched_keywords, missing_keywords, checks
    )

    try:
        if FEEDBACK_BACKEND == "ollama":
            text = _ollama_feedback(prompt)
        elif FEEDBACK_BACKEND == "huggingface":
            text = _huggingface_feedback(prompt)
        else:
            raise ValueError(f"Unknown FEEDBACK_BACKEND: {FEEDBACK_BACKEND}")

        if not text:
            raise ValueError("Empty response from LLM backend.")
        return text

    except Exception as exc:
        logger.warning(
            "LLM feedback backend '%s' failed (%s) — falling back to template feedback.",
            FEEDBACK_BACKEND,
            exc,
        )
        return _template_feedback(ats_score, keyword_score, structure_score, checks, missing_keywords)
