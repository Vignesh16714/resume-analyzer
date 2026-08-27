"""
ats_scorer.py
-------------
Computes a "structure score" that estimates how ATS-friendly a resume's
formatting and organization are, then combines it with the keyword-match
score (from keyword_extractor.py) into a single overall ATS score.

This is a transparent, rule-based scorer (not a black box), which is
actually a *feature* for this use case: users get an explainable
breakdown of exactly which checks passed/failed, mirroring how real ATS
parsing heuristics work (section detection, contact info, length, etc.)
"""

from typing import Dict, List, Tuple

from config import (
    EXPECTED_SECTIONS,
    MIN_RESUME_WORDS,
    MAX_RESUME_WORDS,
    WEIGHT_KEYWORD_MATCH,
    WEIGHT_STRUCTURE,
)
from utils import word_count, find_contact_info


def score_structure(text: str) -> Tuple[float, Dict[str, bool]]:
    """
    Runs a series of independent pass/fail checks and converts the
    fraction passed into a 0-100 structure score.

    Returns:
        score   -- 0-100
        checks  -- dict of check_name -> bool, for transparent UI display
    """
    text_lower = text.lower()
    checks: Dict[str, bool] = {}

    # 1. Section headings present
    sections_found = [s for s in EXPECTED_SECTIONS if s in text_lower]
    checks["Has at least 3 standard sections (Experience, Education, Skills, ...)"] = (
        len(sections_found) >= 3
    )

    # 2. Contact info present (critical — ATS rejects resumes it can't route)
    has_email, has_phone = find_contact_info(text)
    checks["Contains an email address"] = has_email
    checks["Contains a phone number"] = has_phone

    # 3. Reasonable length — too short lacks detail, too long gets truncated
    wc = word_count(text)
    checks[f"Resume length is reasonable ({MIN_RESUME_WORDS}-{MAX_RESUME_WORDS} words)"] = (
        MIN_RESUME_WORDS <= wc <= MAX_RESUME_WORDS
    )

    # 4. Uses bullet points (common ATS-friendly formatting signal)
    bullet_markers = ["•", "- ", "* ", "◦", "‣"]
    has_bullets = any(marker in text for marker in bullet_markers)
    checks["Uses bullet points for readability"] = has_bullets

    # 5. Avoids obvious table/column artifacts that break text extraction
    #    (heuristic: excessive consecutive tab/pipe characters often mean
    #    a multi-column layout that confuses ATS parsers)
    suspicious_layout = text.count("\t") > 20 or text.count("|") > 20
    checks["Avoids complex multi-column / table layouts"] = not suspicious_layout

    # 6. Has a clear name / header line (first non-empty line isn't a bullet)
    first_line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    checks["Starts with a clear header (name/title)"] = (
        len(first_line.split()) <= 6 and not first_line.startswith(("•", "-", "*"))
    )

    passed = sum(1 for v in checks.values() if v)
    score = round((passed / len(checks)) * 100, 1)
    return score, checks


def compute_overall_score(keyword_score: float, structure_score: float) -> float:
    """Weighted blend of the two sub-scores into a single ATS score."""
    overall = keyword_score * WEIGHT_KEYWORD_MATCH + structure_score * WEIGHT_STRUCTURE
    return round(overall, 1)


def generate_rule_based_suggestions(
    checks: Dict[str, bool], missing_keywords: List[str]
) -> List[str]:
    """
    Translates failed checks / missing keywords into concrete, actionable
    suggestions. Used directly by the "template" feedback backend, and
    also fed as context into the LLM backends for grounding.
    """
    suggestions = []

    if not checks.get("Contains an email address", True):
        suggestions.append("Add a professional email address near the top of your resume.")
    if not checks.get("Contains a phone number", True):
        suggestions.append("Add a phone number so recruiters can reach you directly.")
    if not checks.get("Has at least 3 standard sections (Experience, Education, Skills, ...)", True):
        suggestions.append(
            "Add clear section headings (e.g. 'Experience', 'Education', 'Skills') "
            "so ATS software can correctly categorize your content."
        )
    if not checks.get("Uses bullet points for readability", True):
        suggestions.append(
            "Use bullet points to describe your responsibilities and achievements "
            "instead of long paragraphs — this improves both ATS parsing and readability."
        )
    if not checks.get("Avoids complex multi-column / table layouts", True):
        suggestions.append(
            "Simplify your layout — avoid multi-column formats or tables, since many "
            "ATS parsers read PDFs left-to-right and can scramble column-based content."
        )
    if not checks.get("Starts with a clear header (name/title)", True):
        suggestions.append("Start your resume with a clean header containing your name and title.")

    length_check = next((k for k in checks if k.startswith("Resume length")), None)
    if length_check and not checks[length_check]:
        suggestions.append(
            "Adjust your resume length — aim for roughly 1 page (400-800 words) "
            "for early/mid-career roles, or up to 2 pages for senior roles."
        )

    if missing_keywords:
        top_missing = ", ".join(missing_keywords[:8])
        suggestions.append(
            f"Consider adding these job-relevant keywords if they genuinely apply "
            f"to your experience: {top_missing}."
        )

    if not suggestions:
        suggestions.append(
            "Great work — your resume passes all core structural and ATS checks. "
            "Focus next on quantifying achievements with concrete metrics (%, $, time saved)."
        )

    return suggestions
