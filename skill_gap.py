"""
skill_gap.py
------------
Powers the "Skill Gap" tab: given resume text and a target skill list
(sourced from a pasted job description, a chosen role, or a chosen tool),
figures out which target skills the resume already demonstrates and
which are missing — then turns that into a coverage score and a rough
study-time estimate.

Everything here is deterministic and offline (no LLM call), matching the
"curated built-in lists" choice for this feature — the same reliability
philosophy as ats_scorer.py and the "template" feedback backend.
"""

from typing import Dict, List, Tuple

from keyword_extractor import extract_keywords

# Rough average hours to go from "unfamiliar" to "resume-ready" for a
# skill at each priority tier. Deliberately approximate — this powers a
# ballpark timeline estimate, not a certified curriculum.
_PRIORITY_HOURS = {"core": 25, "important": 15, "nice-to-have": 8}
_PRIORITY_RANK = {"core": 0, "important": 1, "nice-to-have": 2}


def build_target_skills_from_jd(job_description: str, top_n: int = 18) -> List[Dict]:
    """
    Turns a pasted job description into a target-skill list shaped like
    the curated ROLE_SKILL_MAP / TOOL_SKILL_MAP entries, so the same
    compute_skill_gap() logic works for all three modes.

    Since a JD has no hand-authored priority tags, keywords are ranked by
    how prominently they appear in the JD (via keyword_extractor's
    frequency ranking) and bucketed into thirds: the top third is treated
    as "core", the middle third "important", the rest "nice-to-have".
    """
    keywords = extract_keywords(job_description, top_n=top_n)
    n = len(keywords)
    skills = []
    for i, kw in enumerate(keywords):
        if i < n / 3:
            priority = "core"
        elif i < (2 * n) / 3:
            priority = "important"
        else:
            priority = "nice-to-have"
        skills.append({
            "name": kw,
            "priority": priority,
            "tip": f"This appears prominently in the job description — make sure your resume shows "
                   f"concrete, specific experience with {kw}, not just a passing mention.",
        })
    return skills


def compute_skill_gap(resume_text: str, target_skills: List[Dict]) -> Dict:
    """
    Compares resume text against a target skill list.

    Returns:
        {
            "matched":       [skill dict, ...],
            "missing":       [skill dict, ...]  (sorted core -> important -> nice-to-have),
            "coverage_pct":  float (0-100),
        }
    """
    resume_lower = resume_text.lower()
    matched, missing = [], []

    for skill in target_skills:
        candidates = [skill["name"]] + skill.get("aliases", [])
        found = any(candidate.lower() in resume_lower for candidate in candidates)
        (matched if found else missing).append(skill)

    missing.sort(key=lambda s: _PRIORITY_RANK.get(s.get("priority", "important"), 1))
    matched.sort(key=lambda s: _PRIORITY_RANK.get(s.get("priority", "important"), 1))

    coverage_pct = round((len(matched) / len(target_skills)) * 100, 1) if target_skills else 0.0

    return {"matched": matched, "missing": missing, "coverage_pct": coverage_pct}


def estimate_time_to_close(missing_skills: List[Dict], study_hours_per_week: float) -> Tuple[float, int]:
    """
    Rough estimate of how long it would take to close the given missing
    skills at the person's available weekly study hours.

    Returns:
        (weeks, total_hours) -- weeks is None if study_hours_per_week <= 0.
    """
    total_hours = sum(_PRIORITY_HOURS.get(s.get("priority", "important"), 15) for s in missing_skills)
    if study_hours_per_week <= 0:
        return None, total_hours
    weeks = round(total_hours / study_hours_per_week, 1)
    return weeks, total_hours


def summarize_gap(target_label: str, matched: List[Dict], missing: List[Dict], coverage_pct: float) -> str:
    """
    Short, deterministic plain-text summary of the gap analysis — same
    "always works, no network dependency" spirit as ats_scorer's
    generate_rule_based_suggestions().
    """
    if coverage_pct >= 80:
        tone = f"Strong alignment with {target_label} — your resume already covers most of the expected skills."
    elif coverage_pct >= 50:
        tone = f"Reasonable overlap with {target_label}, but a few key gaps are holding your resume back."
    else:
        tone = f"Your resume currently shows limited overlap with {target_label} — there's a clear path to close it."

    core_missing = [s["name"] for s in missing if s.get("priority") == "core"]
    lines = [f"{tone} Coverage: {coverage_pct:.0f}% ({len(matched)}/{len(matched) + len(missing)} skills found)."]
    if core_missing:
        lines.append(f"Highest priority: add clear, specific evidence of {', '.join(core_missing)}.")
    return " ".join(lines)