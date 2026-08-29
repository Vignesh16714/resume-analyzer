"""
resume_health_scorer.py
------------------------
Powers the "Resume Health Check" tab: scores an uploaded resume against a
FIXED internal rubric (no job description involved) across four weighted
components — Content, Keywords, Formatting, Skills — and explains exactly
where points were lost and how to close the gap.

Same reliability philosophy as ats_scorer.py and llm_feedback.py:

  * The rule-based scorer (score_resume_health) is deterministic, has ZERO
    external dependencies, and ALWAYS works — this is the default and the
    only thing that runs when config.FEEDBACK_BACKEND == "template".
  * An optional LLM-enhanced mode kicks in when FEEDBACK_BACKEND != "template".
    It reuses the exact same backend call functions already defined in
    llm_feedback.py (_ollama_feedback / _huggingface_feedback) and asks
    for a JSON payload of per-component scores/checklist findings/
    explanations for THIS specific resume. The call is wrapped in the same
    try/except + automatic-fallback-to-rule-based pattern already used for
    feedback generation, so a flaky/offline LLM or malformed JSON can
    never crash the app or block the user from getting a health check.

Every check below maps 1:1 to a single checklist line rendered in the
"Detailed Breakdown" cards in app.py (✓ green / ✗ red, reusing
theme.status_line's existing color pattern), and each component's 0-100
sub-score is simply (checks_passed / total_checks) * 100 — identical in
spirit to ats_scorer.score_structure(), just run once per rubric
component instead of once for the whole resume.
"""

import json
import logging
import re
from typing import Dict, List, Tuple

from config import DEFAULT_SKILL_VOCAB, EXPECTED_SECTIONS, FEEDBACK_BACKEND
from utils import word_count
from keyword_extractor import extract_keywords
from llm_feedback import _ollama_feedback, _huggingface_feedback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Rubric weights (must sum to 1.0) & display metadata
# ----------------------------------------------------------------------
COMPONENT_WEIGHTS = {
    "Content": 0.35,
    "Keywords": 0.25,
    "Formatting": 0.25,
    "Skills": 0.15,
}

COMPONENT_ICONS = {
    "Content": "📝",
    "Keywords": "🔑",
    "Formatting": "🧱",
    "Skills": "🛠️",
}

# The "recruiter-grade" cutoff referenced throughout the tab's UI copy
# ("Needs work · N pts from 85", "85+ is the recruiter-grade line...").
RECRUITER_GRADE_LINE = 85

_SOFT_SKILLS = [
    "communication", "leadership", "teamwork", "problem-solving", "problem solving",
    "adaptability", "time management", "collaboration", "mentoring", "ownership",
    "critical thinking", "creativity", "organization", "conflict resolution",
]

# Generic filler phrases that only help a resume when paired with actual
# supporting evidence elsewhere — used alone, they're a red flag for both
# human reviewers and ATS keyword scanners.
_CLICHE_PHRASES = [
    "hardworking", "team player", "detail-oriented", "detail oriented",
    "go-getter", "self-starter", "results-driven", "results oriented",
    "think outside the box", "fast learner", "people person",
]

_BULLET_MARKERS = ("•", "- ", "* ", "◦", "‣")

_DATE_RANGE_RE = re.compile(
    r"(19|20)\d{2}\s*[-–—]{1,2}\s*((19|20)\d{2}|present|current)", re.IGNORECASE
)
_MONTH_DATE_RE = re.compile(
    r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(19|20)\d{2}\b",
    re.IGNORECASE,
)
_SLASH_DATE_RE = re.compile(r"\b(0[1-9]|1[0-2])\s*/\s*(19|20)\d{2}\b")
_NUMERIC_ACHIEVEMENT_RE = re.compile(r"\d|%|\$")


# ------------------------------------------------------------------
# Small shared text-parsing helpers (heuristic, not a full resume
# parser — good enough to gauge presence/absence and rough structure,
# consistent with the "transparent, explainable heuristics" spirit
# already used throughout ats_scorer.py).
# ------------------------------------------------------------------
def _split_lines(text: str) -> List[str]:
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def _bullet_lines(text: str) -> List[str]:
    return [ln for ln in _split_lines(text) if ln.lstrip().startswith(_BULLET_MARKERS)]


def _section_body(text: str, heading_terms: set) -> str:
    """
    Returns the text between the first line matching one of `heading_terms`
    (case-insensitive, treated as a standalone heading line) and the next
    line that looks like one of EXPECTED_SECTIONS' headings. Returns ""
    if no matching heading is found.
    """
    lines = _split_lines(text)
    start = None
    for i, ln in enumerate(lines):
        low = ln.lower().strip(" :")
        if low in heading_terms:
            start = i + 1
            break
    if start is None:
        return ""
    body = []
    for ln in lines[start:]:
        low = ln.lower().strip(" :")
        if low in EXPECTED_SECTIONS:
            break
        body.append(ln)
    return " ".join(body)


# ------------------------------------------------------------------
# Component scorers — each returns (score 0-100, checks dict)
# ------------------------------------------------------------------
def _score_content(text: str) -> Tuple[float, Dict[str, bool]]:
    text_lower = text.lower()
    checks: Dict[str, bool] = {}

    sections_found = [s for s in EXPECTED_SECTIONS if s in text_lower]
    checks["Includes at least 3 core resume sections"] = len(sections_found) >= 3

    bullets = _bullet_lines(text)
    # Number of date ranges (e.g. "2021 - 2023", "2022 - Present") is used
    # as a proxy for "how many roles/entries are listed" so we can gauge
    # bullet density per role without a full resume parser.
    role_markers = len(_DATE_RANGE_RE.findall(text)) or 1
    bullets_per_role = len(bullets) / role_markers
    checks["Averages 3+ bullet points per role listed"] = bullets_per_role >= 3

    summary_body = _section_body(text, {"summary", "objective"})
    checks["Has a substantive professional summary (20+ words)"] = word_count(summary_body) >= 20

    if bullets:
        quantified = sum(1 for b in bullets if _NUMERIC_ACHIEVEMENT_RE.search(b))
        ratio = quantified / len(bullets)
    else:
        ratio = 0.0
    checks["At least 30% of bullets include a quantified result (#, %, $)"] = ratio >= 0.3

    passed = sum(1 for v in checks.values() if v)
    score = round((passed / len(checks)) * 100, 1)
    return score, checks


def _score_keywords(text: str) -> Tuple[float, Dict[str, bool]]:
    """
    Scores general keyword richness — NOT matched against a job
    description (that's what the "Analyze Resume" tab already does).
    This gauges how technically dense and evidence-backed the resume's
    own language is on its own terms.
    """
    text_lower = text.lower()
    checks: Dict[str, bool] = {}

    wc = max(word_count(text), 1)
    vocab_hits = [s for s in DEFAULT_SKILL_VOCAB if s in text_lower]
    density = len(vocab_hits) / wc * 100
    checks["Strong technical keyword density relative to resume length"] = density >= 1.0

    bullets = _bullet_lines(text)
    bullet_text = " ".join(bullets).lower()
    if vocab_hits:
        woven = sum(1 for kw in vocab_hits if kw in bullet_text)
        is_woven = woven >= max(1, len(vocab_hits) // 2)
    else:
        is_woven = False
    checks["Keywords are woven into bullet/description text, not just listed"] = is_woven

    soft_hits = [s for s in _SOFT_SKILLS if s in text_lower]
    checks["Reasonable soft-skill keyword coverage"] = len(soft_hits) >= 2

    cliches_present = sum(1 for phrase in _CLICHE_PHRASES if phrase in text_lower)
    checks["Avoids generic filler phrases used without supporting evidence"] = cliches_present <= 1

    passed = sum(1 for v in checks.values() if v)
    score = round((passed / len(checks)) * 100, 1)
    return score, checks


def _score_formatting(text: str) -> Tuple[float, Dict[str, bool]]:
    """Extends ats_scorer.score_structure()'s layout heuristics with a
    few more ATS-parsing-friendliness checks specific to this rubric."""
    checks: Dict[str, bool] = {}

    # Same multi-column/table heuristic used in ats_scorer.score_structure.
    suspicious_layout = text.count("\t") > 20 or text.count("|") > 20
    checks["Avoids complex multi-column / table layouts"] = not suspicious_layout

    special_chars = len(re.findall(r"[^\w\s.,;:()\-'\"/&%$#@•\n]", text))
    checks["Avoids excessive special characters/symbols/emoji"] = special_chars <= 10

    date_styles = set()
    if _MONTH_DATE_RE.search(text):
        date_styles.add("month_year")
    if _SLASH_DATE_RE.search(text):
        date_styles.add("slash")
    if re.search(r"\b(19|20)\d{2}\s*[-–—]\s*(19|20)\d{2}\b", text):
        date_styles.add("year_range")
    checks["Uses a consistent date format throughout"] = len(date_styles) <= 1

    double_spaces = "  " in text
    missing_space_after_punct = bool(re.search(r"[.,;:][A-Za-z]", text))
    checks["No obvious spacing issues (double spaces, missing spaces after punctuation)"] = (
        not double_spaces and not missing_space_after_punct
    )

    passed = sum(1 for v in checks.values() if v)
    score = round((passed / len(checks)) * 100, 1)
    return score, checks


def _score_skills(text: str) -> Tuple[float, Dict[str, bool]]:
    text_lower = text.lower()
    checks: Dict[str, bool] = {}

    skills_body = _section_body(text, {"skills", "technical skills", "core competencies"})
    structured = bool(re.search(r"[,|/•]", skills_body)) if skills_body else False
    checks["Skills section is clearly structured (comma/pipe separated or categorized)"] = structured

    vocab_hits = [s for s in DEFAULT_SKILL_VOCAB if s in text_lower]
    checks["Shows meaningful overlap with common technical skills"] = len(vocab_hits) >= 5

    extracted = extract_keywords(text, top_n=40)
    checks["Lists at least ~20 distinct skills/keywords"] = len(set(extracted)) >= 20

    soft_hits = [s for s in _SOFT_SKILLS if s in text_lower]
    checks["Shows a reasonable mix of soft skills"] = len(soft_hits) >= 2

    passed = sum(1 for v in checks.values() if v)
    score = round((passed / len(checks)) * 100, 1)
    return score, checks


_SCORERS = {
    "Content": _score_content,
    "Keywords": _score_keywords,
    "Formatting": _score_formatting,
    "Skills": _score_skills,
}

_COMPONENT_BLURBS = {
    "Content": "how completely your experience is documented — sections, bullet depth, "
               "a real summary, and quantified results.",
    "Keywords": "how much of your resume's own language matches the technical and "
                "soft-skill vocabulary recruiters and ATS parsers scan for.",
    "Formatting": "whether your layout, spacing, and dates are clean and consistent "
                  "enough for an ATS parser to read correctly.",
    "Skills": "whether your skills section is structured, sufficiently broad, and "
              "balances technical depth with soft skills.",
}


def _explanation_for(component: str, checks: Dict[str, bool]) -> str:
    """Short, deterministic plain-English explanation naming the biggest
    single opportunity for this component — same 'always works, no
    network dependency' spirit as ats_scorer.generate_rule_based_suggestions."""
    failed = [k for k, v in checks.items() if not v]
    blurb = _COMPONENT_BLURBS.get(component, "")
    if not failed:
        return f"Solid work here — every {component.lower()} check on our rubric passed."
    lead = failed[0][0].lower() + failed[0][1:]
    return f"This component measures {blurb} The biggest opportunity: {lead}."


# ------------------------------------------------------------------
# Rule-based rubric scorer (always available, zero dependencies)
# ------------------------------------------------------------------
def score_resume_health(text: str) -> Dict:
    """
    Deterministic, zero-dependency rubric scorer. ALWAYS works — no
    network calls, no ML model. Runs each component's checklist
    separately, converts checks_passed/total into a 0-100 sub-score
    (identical pattern to ats_scorer.score_structure()), then blends the
    four sub-scores by COMPONENT_WEIGHTS into a single overall score.

    Returns a dict shaped for direct consumption by app.py's Resume
    Health Check tab (and for JSON-serializing into db.py):
        {
            "overall_score": float,
            "components": {
                "Content": {
                    "score": float, "weight": float, "checks": {...},
                    "explanation": str, "points_lost": float,
                },
                ... "Keywords", "Formatting", "Skills" ...
            },
        }
    """
    components = {}
    overall = 0.0
    for name, fn in _SCORERS.items():
        score, checks = fn(text)
        weight = COMPONENT_WEIGHTS[name]
        overall += score * weight
        points_lost = round((100 - score) * weight, 1)
        components[name] = {
            "score": score,
            "weight": weight,
            "checks": checks,
            "explanation": _explanation_for(name, checks),
            "points_lost": points_lost,
        }

    return {"overall_score": round(overall, 1), "components": components}


# ------------------------------------------------------------------
# Optional LLM-enhanced mode
# ------------------------------------------------------------------
def _build_llm_prompt(text: str) -> str:
    checks_spec = {name: list(fn(text)[1].keys()) for name, fn in _SCORERS.items()}
    return (
        "You are an expert ATS resume auditor. Score the resume below against "
        "this FIXED rubric of four components with fixed weights: "
        "Content (35%), Keywords (25%), Formatting (25%), Skills (15%). "
        "For each component, evaluate exactly the checklist items given below "
        "(true/false per item), give a 0-100 sub-score, and a 1-2 sentence "
        "plain-English explanation of your finding for THIS specific resume.\n\n"
        f"Checklist items per component: {json.dumps(checks_spec)}\n\n"
        "Respond with ONLY a JSON object, no prose, no markdown code fences, in "
        "exactly this shape:\n"
        '{"Content": {"score": 0-100, "explanation": "...", '
        '"checks": {"<item text>": true/false, ...}}, '
        '"Keywords": {...}, "Formatting": {...}, "Skills": {...}}\n\n'
        f"Resume text:\n{text[:6000]}"
    )


def _parse_llm_response(raw: str, fallback_checks: Dict[str, Dict[str, bool]]) -> Dict:
    """Strictly validates the LLM's JSON reply. Raises on any malformed or
    out-of-range data so the caller's except-block falls back to the
    rule-based scorer instead of showing garbage to the user."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        first_line, _, rest = cleaned.partition("\n")
        cleaned = rest if first_line.strip().lower() in ("json", "") else cleaned
    parsed = json.loads(cleaned)

    components = {}
    overall = 0.0
    for name in COMPONENT_WEIGHTS:
        if name not in parsed:
            raise ValueError(f"LLM response missing component '{name}'")
        entry = parsed[name]
        score = float(entry["score"])
        if not (0 <= score <= 100):
            raise ValueError(f"LLM score for '{name}' out of range: {score}")

        raw_checks = entry.get("checks") or fallback_checks[name]
        checks = {str(k): bool(v) for k, v in raw_checks.items()}
        if not checks:
            checks = fallback_checks[name]

        explanation = str(entry.get("explanation", "")).strip() or _explanation_for(name, checks)
        weight = COMPONENT_WEIGHTS[name]
        overall += score * weight
        points_lost = round((100 - score) * weight, 1)
        components[name] = {
            "score": round(score, 1),
            "weight": weight,
            "checks": checks,
            "explanation": explanation,
            "points_lost": points_lost,
        }

    return {"overall_score": round(overall, 1), "components": components}


def generate_resume_health(text: str) -> Dict:
    """
    Main entry point used by app.py's Resume Health Check tab. Mirrors
    llm_feedback.generate_feedback()'s dispatch + try/except +
    automatic-fallback pattern exactly:

      * If FEEDBACK_BACKEND == "template", the deterministic rule-based
        scorer runs directly (no LLM involved at all).
      * Otherwise, the configured backend (ollama / huggingface) is asked
        for a richer, resume-specific JSON scoring payload. Any failure —
        network error, timeout, malformed/unparseable JSON, out-of-range
        scores — is caught and logged, and this ALWAYS falls back to the
        rule-based rubric scorer so the tab never crashes and never
        blocks the user from getting a health check.
    """
    rule_based = score_resume_health(text)
    if FEEDBACK_BACKEND == "template":
        return rule_based

    fallback_checks = {name: comp["checks"] for name, comp in rule_based["components"].items()}
    prompt = _build_llm_prompt(text)

    try:
        if FEEDBACK_BACKEND == "ollama":
            raw = _ollama_feedback(prompt)
        elif FEEDBACK_BACKEND == "huggingface":
            raw = _huggingface_feedback(prompt)
        else:
            raise ValueError(f"Unknown FEEDBACK_BACKEND: {FEEDBACK_BACKEND}")

        if not raw:
            raise ValueError("Empty response from LLM backend.")
        return _parse_llm_response(raw, fallback_checks)

    except Exception as exc:
        logger.warning(
            "LLM-enhanced resume health scoring via backend '%s' failed (%s) — "
            "falling back to rule-based rubric scoring.",
            FEEDBACK_BACKEND,
            exc,
        )
        return rule_based


# ------------------------------------------------------------------
# Small display helpers used directly by app.py
# ------------------------------------------------------------------
def status_tier(score: float) -> Tuple[str, str]:
    """
    Maps an overall score to (kind, label) for the hero status badge,
    using the same success/accent/warning/danger tiers as theme.score_kind
    elsewhere in the app, just with an extra tier split at the
    recruiter-grade line.
    """
    if score >= RECRUITER_GRADE_LINE:
        return "success", "Recruiter-ready"
    elif score >= 70:
        return "accent", "Good"
    elif score >= 50:
        return "warning", "Needs work"
    else:
        return "danger", "Needs major work"


def rank_components_by_points_lost(components: Dict[str, Dict]) -> List[Tuple[str, Dict]]:
    """Returns (component_name, component_dict) pairs sorted so the
    biggest point-loser comes first — drives the "Where you lost points"
    panel's ordering and the "BIGGEST DRAG" / "CRITICAL" badges."""
    return sorted(components.items(), key=lambda kv: kv[1]["points_lost"], reverse=True)
