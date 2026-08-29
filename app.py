"""
app.py
------
Streamlit entry point for the AI-Powered Resume Analyzer.

Workflow implemented here:
  1. User uploads a resume (PDF/DOCX) and optionally pastes a job description.
  2. utils.py extracts and cleans the raw text.
  3. keyword_extractor.py computes keyword match against the job description.
  4. ats_scorer.py computes a structural/formatting ATS score.
  5. llm_feedback.py turns the scores into human-readable feedback.
  6. db.py persists the resume + analysis.
  7. Results are rendered as an animated hero + radial gauges + Plotly charts.

Visual design lives in theme.py (palette, global CSS, card/gauge/badge
helpers) and components.py (the animated hero banner + a small JS
enhancer for 3D button tilt and upload drag-over styling), so this file
focuses on layout and pipeline logic.

Run with:  streamlit run app.py
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

import db
from utils import validate_file, extract_text, clean_text, ResumeParsingError
from keyword_extractor import compute_keyword_match
from ats_scorer import score_structure, compute_overall_score
from llm_feedback import generate_feedback
from config import FEEDBACK_BACKEND
from theme import (
    COLORS, inject_global_css, card, radial_gauge, score_kind, badge,
    status_line, segmented, picker_group, slider_card, slider_minmax_caption,
    target_progress_bar, points_lost_bar,
)
from components import (
    render_hero, enable_button_tilt, restyle_uploader_copy, animate_gauge_counts,
    inject_tool_logos,
)
from tech_icons import TECH_LOGOS
from skills_data import ROLE_SKILL_MAP, TOOL_SKILL_MAP, ROLE_ICONS, TOOL_ICONS
from skill_gap import build_target_skills_from_jd, compute_skill_gap, estimate_time_to_close, summarize_gap
from resume_health_scorer import (
    generate_resume_health, status_tier, rank_components_by_points_lost,
    RECRUITER_GRADE_LINE, COMPONENT_ICONS,
)

# ------------------------------------------------------------------
# Page setup, theme injection & one-time DB initialization
# ------------------------------------------------------------------
st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")
inject_global_css()
db.init_db()

# Animated hero banner (self-contained CSS/JS — degrades to a static,
# correctly styled headline if the embedded script doesn't run) and the
# invisible enhancer that gives every st.button a cursor-tracked 3D tilt
# and gives the file-upload dropzone a highlight-on-drag state.
render_hero(COLORS)
enable_button_tilt()
restyle_uploader_copy()
animate_gauge_counts()
# Swaps the emoji on each "By Tool" picker button (Skill Gap tab) for a
# real bundled SVG logo (React, Docker, Python, Kubernetes, AWS, ...).
# Degrades to the plain emoji if this can't run — see components.py.
inject_tool_logos(TECH_LOGOS, TOOL_ICONS)

st.caption(f"Feedback backend: **{FEEDBACK_BACKEND}**")

tab_analyze, tab_skillgap, tab_health = st.tabs(
    ["🔍 Analyze Resume", "🎯 Skill Gap", "🩺 Resume Health Check"]
)

# A small chart layout template so every Plotly chart matches the theme's
# fonts/colors instead of Plotly's default gray/blue palette.
CHART_FONT = dict(family="Inter, -apple-system, Segoe UI, Roboto, sans-serif", color=COLORS["text_primary"])

MAX_RADAR_SKILLS = 14  # keep the polar chart legible even for JD mode's ~18 skills


def render_skill_radar(target_skills, matched, missing, target_label):
    """
    Builds a two-trace Scatterpolar ("radar"/"spider") chart: a dotted
    outer ring showing the full target skill profile (always 100 — i.e.
    "fully covered"), and a filled inner shape showing which of those
    skills the resume actually demonstrates (100 = matched, 0 = missing).
    The gap between the two shapes *is* the skill gap, visually.

    target_skills is used (rather than gap["matched"]/["missing"] alone)
    so the axis order matches how skills were originally ranked/curated,
    not the priority-sorted order compute_skill_gap() returns them in.
    """
    matched_names = {s["name"] for s in matched}
    truncated = len(target_skills) > MAX_RADAR_SKILLS
    skills_for_chart = target_skills[:MAX_RADAR_SKILLS]

    labels = [s["name"] for s in skills_for_chart]
    resume_values = [100 if s["name"] in matched_names else 0 for s in skills_for_chart]
    target_values = [100] * len(labels)

    # Close the polygon by repeating the first point at the end.
    labels_loop = labels + labels[:1]
    resume_loop = resume_values + resume_values[:1]
    target_loop = target_values + target_values[:1]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=target_loop, theta=labels_loop, name=f"Target: {target_label}",
        fill="toself", fillcolor="rgba(124, 58, 237, 0.06)",
        line=dict(color=COLORS["border_strong"], dash="dot", width=1.5),
        hoverinfo="skip",
    ))
    fig.add_trace(go.Scatterpolar(
        r=resume_loop, theta=labels_loop, name="Your Resume",
        fill="toself", fillcolor="rgba(37, 99, 235, 0.28)",
        line=dict(color=COLORS["accent"], width=2.5),
        marker=dict(size=6, color=COLORS["accent"]),
        hovertemplate="%{theta}: %{customdata}<extra></extra>",
        customdata=["Covered" if v == 100 else "Missing" for v in resume_values] + (
            ["Covered" if resume_values[0] == 100 else "Missing"] if resume_values else []
        ),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor=COLORS["panel"],
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=False,
                             gridcolor=COLORS["border"]),
            angularaxis=dict(gridcolor=COLORS["border"],
                              tickfont=dict(size=11, color=COLORS["text_primary"])),
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5,
                    font=CHART_FONT),
        paper_bgcolor=COLORS["bg"],
        font=CHART_FONT,
        margin=dict(l=50, r=50, t=30, b=30),
        height=440,
    )
    return fig, truncated

# ====================================================================
# TAB 1 — Analyze a new resume
# ====================================================================
with tab_analyze:
    # Results now live in session_state so they persist across reruns
    # triggered by *any* widget interaction on the page, not just the
    # Analyze button — and so the Score Breakdown gauges have something
    # to render (real values or zeroed defaults) on every single render.
    if "ar_results" not in st.session_state:
        st.session_state.ar_results = None

    col_left, col_right = st.columns([1, 1])

    with col_left:
        with card("upload"):
            st.subheader("1. Upload your resume")
            uploaded_file = st.file_uploader("PDF or DOCX", type=["pdf", "docx"])

            st.subheader("2. Paste the target job description (optional)")
            job_description = st.text_area(
                "Pasting a job description gives you a much more accurate keyword match score.",
                height=220,
                placeholder="Paste the job posting text here...",
            )

            analyze_clicked = st.button("🚀 Analyze Resume", type="primary", width="stretch")

    with col_right:
        st.subheader("Results")
        results = st.session_state.ar_results

        with card("overall_score"):
            # --- Three animated SVG radial gauges, side by side. Always
            # rendered — zeroed out until an analysis has been run, then
            # updated in place from session_state on every rerun. ---
            st.markdown("#### Score Breakdown")
            g1, g2, g3 = st.columns(3)
            if results is None:
                with g1:
                    radial_gauge("Overall ATS Score", 0, kind="accent", gauge_id="overall")
                with g2:
                    radial_gauge("Keyword Match", 0, kind="accent", gauge_id="keyword")
                with g3:
                    radial_gauge("Structure & Formatting", 0, kind="accent", gauge_id="structure")
                st.caption("Upload a resume and click Analyze Resume to see your scores here.")
            else:
                with g1:
                    radial_gauge("Overall ATS Score", results["overall_score"],
                                 kind=score_kind(results["overall_score"]), gauge_id="overall")
                with g2:
                    radial_gauge("Keyword Match", results["keyword_score"],
                                 kind=score_kind(results["keyword_score"]), gauge_id="keyword")
                with g3:
                    radial_gauge("Structure & Formatting", results["structure_score"],
                                 kind=score_kind(results["structure_score"]), gauge_id="structure")

    if analyze_clicked:
        if uploaded_file is None:
            st.warning("Please upload a resume file first.")
        else:
            try:
                file_bytes = uploaded_file.read()

                # --- Step 1: validate + extract text (error-handled) -------
                validate_file(uploaded_file.name, file_bytes)
                with st.spinner("Extracting text from resume..."):
                    raw_text = extract_text(uploaded_file.name, file_bytes)
                    clean = clean_text(raw_text)

                # --- Step 2: keyword analysis -------------------------------
                with st.spinner("Analyzing keywords..."):
                    keyword_score, matched, missing = compute_keyword_match(clean, job_description)

                # --- Step 3: structure / ATS formatting analysis -----------
                with st.spinner("Scoring ATS structure & formatting..."):
                    structure_score, checks = score_structure(clean)
                    overall_score = compute_overall_score(keyword_score, structure_score)

                # --- Step 4: generate feedback -------------------------------
                with st.spinner("Generating feedback..."):
                    feedback_text = generate_feedback(
                        overall_score, keyword_score, structure_score, matched, missing, checks
                    )

                # --- Step 5: persist to DB -----------------------------------
                resume_id = db.save_resume(uploaded_file.name, clean)
                analysis_id = db.save_analysis(
                    resume_id=resume_id,
                    job_description=job_description,
                    ats_score=overall_score,
                    keyword_score=keyword_score,
                    structure_score=structure_score,
                    matched_keywords=matched,
                    missing_keywords=missing,
                    feedback=feedback_text,
                )

                # --- Step 6: stash results in session_state, then rerun so
                # the Score Breakdown gauges (rendered above, before this
                # block runs) pick up the real values on the fresh pass. ---
                st.session_state.ar_results = {
                    "overall_score": overall_score,
                    "keyword_score": keyword_score,
                    "structure_score": structure_score,
                    "matched": matched,
                    "missing": missing,
                    "checks": checks,
                    "feedback_text": feedback_text,
                    "analysis_id": analysis_id,
                }
                st.rerun()

            except ResumeParsingError as e:
                # Expected, user-facing errors (bad file type, empty file, etc.)
                st.error(f"⚠️ {e}")
            except Exception as e:
                # Unexpected errors — still shown to the user, not a raw traceback crash.
                st.error(f"An unexpected error occurred while analyzing the resume: {e}")

    # --- Full-width results below the upload form + Score Breakdown ------
    # Reads from session_state so this renders identically whether it was
    # just-computed above or is simply persisting from an earlier run.
    results = st.session_state.ar_results
    if results is not None:
        st.success(f"Analysis complete! (saved as record #{results['analysis_id']})")

        with card("keyword_coverage"):
            st.markdown("#### Keyword Coverage")
            matched = results["matched"]
            missing = results["missing"]

            kc_left, kc_mid, kc_right = st.columns([1, 2, 1])
            with kc_mid:
                if matched or missing:
                    donut_fig = px.pie(
                        names=["Matched", "Missing"],
                        values=[len(matched), len(missing)],
                        hole=0.55,
                        color_discrete_sequence=[COLORS["success_fill"], COLORS["warning_fill"]],
                    )
                    donut_fig.update_layout(
                        height=300, margin=dict(l=10, r=10, t=10, b=10),
                        paper_bgcolor=COLORS["panel"], font=CHART_FONT,
                        legend=dict(font=CHART_FONT),
                    )
                    st.plotly_chart(donut_fig, width="stretch")

                kw_col1, kw_col2 = st.columns(2)
                with kw_col1:
                    st.markdown(f"**{badge('✅ Matched', 'success')}**", unsafe_allow_html=True)
                    if matched:
                        st.markdown(
                            " ".join(badge(kw, "success") for kw in matched),
                            unsafe_allow_html=True,
                        )
                    else:
                        st.caption("None found")
                with kw_col2:
                    st.markdown(f"**{badge('❌ Missing', 'warning')}**", unsafe_allow_html=True)
                    if missing:
                        st.markdown(
                            " ".join(badge(kw, "warning") for kw in missing),
                            unsafe_allow_html=True,
                        )
                    else:
                        st.caption("None — great coverage!")

        bottom_left, bottom_right = st.columns(2)
        with bottom_left:
            with card("checklist"):
                st.markdown("#### Formatting & Structure Checklist")
                checklist_html = "".join(
                    status_line(passed, check_name) for check_name, passed in results["checks"].items()
                )
                st.markdown(checklist_html, unsafe_allow_html=True)

        with bottom_right:
            with card("feedback"):
                st.markdown("#### 💡 AI Feedback & Suggestions")
                st.markdown(
                    f"<div style='color:{COLORS['text_primary']}; line-height:1.6; "
                    f"white-space:pre-wrap;'>{results['feedback_text']}</div>",
                    unsafe_allow_html=True,
                )

# ====================================================================
# TAB 2 — Skill Gap analysis
# ====================================================================
with tab_skillgap:
    # Default session state for the mode selector and the role/tool picks.
    if "sg_mode" not in st.session_state:
        st.session_state.sg_mode = "Custom JD"
    if "sg_role" not in st.session_state:
        st.session_state.sg_role = None
    if "sg_tool" not in st.session_state:
        st.session_state.sg_tool = None

    with card("sg_resume"):
        st.subheader("1. Upload your resume")
        sg_resume_file = st.file_uploader(
            "PDF or DOCX", type=["pdf", "docx"], key="sg_resume_uploader"
        )

        st.subheader("2. How should we determine the target skills?")

        # --- Segmented Custom JD / By Role / By Tool control -------------
        with segmented("sg_mode"):
            m1, m2, m3 = st.columns(3)
            with m1:
                if st.button("📄 Custom JD", width="stretch",
                              type="primary" if st.session_state.sg_mode == "Custom JD" else "secondary"):
                    st.session_state.sg_mode = "Custom JD"
                    st.rerun()
            with m2:
                if st.button("💼 By Role", width="stretch",
                              type="primary" if st.session_state.sg_mode == "By Role" else "secondary"):
                    st.session_state.sg_mode = "By Role"
                    st.rerun()
            with m3:
                if st.button("⚡ By Tool", width="stretch",
                              type="primary" if st.session_state.sg_mode == "By Tool" else "secondary"):
                    st.session_state.sg_mode = "By Tool"
                    st.rerun()

        sg_job_description = ""

        if st.session_state.sg_mode == "Custom JD":
            st.caption("Paste the full job description to extract its expected skills.")
            sg_job_description = st.text_area(
                "Job Description", height=180,
                placeholder="Paste the full job description here...",
                key="sg_jd_text",
            )

        elif st.session_state.sg_mode == "By Role":
            st.caption("Select the role you're targeting to match against industry standards.")
            role_names = list(ROLE_SKILL_MAP.keys())
            with picker_group("sg_role"):
                for row_start in range(0, len(role_names), 3):
                    row_roles = role_names[row_start:row_start + 3]
                    cols = st.columns(3)
                    for col, role in zip(cols, row_roles):
                        with col:
                            is_selected = st.session_state.sg_role == role
                            if st.button(
                                f"{ROLE_ICONS.get(role, '💼')}\n\n{role}",
                                key=f"sg_role_btn_{role}", width="stretch",
                                type="primary" if is_selected else "secondary",
                            ):
                                st.session_state.sg_role = role
                                st.rerun()

        else:  # By Tool
            st.caption("Select a tool or technology to evaluate your readiness for that stack.")
            tool_names = list(TOOL_SKILL_MAP.keys())
            with picker_group("sg_tool"):
                for row_start in range(0, len(tool_names), 3):
                    row_tools = tool_names[row_start:row_start + 3]
                    cols = st.columns(3)
                    for col, tool in zip(cols, row_tools):
                        with col:
                            is_selected = st.session_state.sg_tool == tool
                            if st.button(
                                f"{TOOL_ICONS.get(tool, '⚡')}\n\n{tool}",
                                key=f"sg_tool_btn_{tool}", width="stretch",
                                type="primary" if is_selected else "secondary",
                            ):
                                st.session_state.sg_tool = tool
                                st.rerun()

        st.subheader("3. Available study hours per week")
        _current_hours = st.session_state.get("sg_hours", 10)
        with slider_card("sg_hours", "Available study hours/week", _current_hours, icon="⏱️"):
            sg_study_hours = st.slider(
                "Available study hours/week", min_value=1, max_value=40, value=_current_hours,
                key="sg_hours", label_visibility="collapsed",
            )
            slider_minmax_caption(1, 40)

        sg_analyze_clicked = st.button(
            "⚡ Analyze Skill Gap", type="primary", width="stretch", key="sg_analyze_btn"
        )

    st.subheader("Results")
    sg_results_placeholder = st.container()

    if sg_analyze_clicked:
        mode = st.session_state.sg_mode
        target_label = None
        target_skills = None

        if sg_resume_file is None:
            st.warning("Please upload a resume first.")
        elif mode == "Custom JD" and not sg_job_description.strip():
            st.warning("Please paste a job description, or switch to 'By Role' / 'By Tool'.")
        elif mode == "By Role" and not st.session_state.sg_role:
            st.warning("Please select a role.")
        elif mode == "By Tool" and not st.session_state.sg_tool:
            st.warning("Please select a tool.")
        else:
            try:
                sg_file_bytes = sg_resume_file.read()
                validate_file(sg_resume_file.name, sg_file_bytes)
                with st.spinner("Reading resume..."):
                    sg_raw_text = extract_text(sg_resume_file.name, sg_file_bytes)
                    sg_clean_text = clean_text(sg_raw_text)

                with st.spinner("Building target skill profile..."):
                    if mode == "Custom JD":
                        target_label = "this job description"
                        target_skills = build_target_skills_from_jd(sg_job_description)
                    elif mode == "By Role":
                        target_label = st.session_state.sg_role
                        target_skills = ROLE_SKILL_MAP[st.session_state.sg_role]
                    else:
                        target_label = st.session_state.sg_tool
                        target_skills = TOOL_SKILL_MAP[st.session_state.sg_tool]

                with st.spinner("Computing skill gap..."):
                    gap = compute_skill_gap(sg_clean_text, target_skills)
                    weeks, total_hours = estimate_time_to_close(gap["missing"], sg_study_hours)
                    summary_text = summarize_gap(
                        target_label, gap["matched"], gap["missing"], gap["coverage_pct"]
                    )

                with sg_results_placeholder:
                    st.success("Skill gap analysis complete!")

                    with card("sg_coverage"):
                        st.markdown("#### Skill Coverage")
                        radial_gauge(
                            f"Coverage vs {target_label}", gap["coverage_pct"],
                            kind=score_kind(gap["coverage_pct"]), gauge_id="sg_coverage",
                        )
                        st.markdown(
                            f"<div style='color:{COLORS['text_primary']}; line-height:1.6; margin-top:0.6rem;'>"
                            f"{summary_text}</div>",
                            unsafe_allow_html=True,
                        )
                        if weeks is not None and gap["missing"]:
                            st.markdown(
                                f"<div style='color:{COLORS['text_muted']}; margin-top:0.5rem;'>"
                                f"⏱️ At <b>{sg_study_hours}h/week</b>, closing this gap "
                                f"(~{total_hours}h of focused learning) would take roughly "
                                f"<b>{weeks} weeks</b>.</div>",
                                unsafe_allow_html=True,
                            )

                    with card("sg_radar"):
                        st.markdown("#### 🕸️ Skill Profile Radar")
                        radar_fig, radar_truncated = render_skill_radar(
                            target_skills, gap["matched"], gap["missing"], target_label
                        )
                        st.plotly_chart(radar_fig, width="stretch")
                        st.caption(
                            "The dotted outline is the full target skill profile; the filled "
                            "shape is where your resume currently reaches it. Any gap between "
                            "the two is a skill worth closing."
                            + (f" Showing the top {MAX_RADAR_SKILLS} of {len(target_skills)} "
                               f"target skills for readability." if radar_truncated else "")
                        )

                    with card("sg_matched"):
                        st.markdown("#### ✅ Skills You Already Show")
                        if gap["matched"]:
                            st.markdown(
                                " ".join(badge(s["name"], "success") for s in gap["matched"]),
                                unsafe_allow_html=True,
                            )
                        else:
                            st.caption("None of the target skills were found yet — see the gaps below.")

                    with card("sg_missing"):
                        st.markdown("#### 🎯 Skills to Focus On")
                        if not gap["missing"]:
                            st.caption("No gaps found — great coverage!")
                        else:
                            priority_kind = {"core": "danger", "important": "warning", "nice-to-have": "accent"}
                            priority_label = {
                                "core": "Core — highest priority",
                                "important": "Important",
                                "nice-to-have": "Nice to have",
                            }
                            current_priority = None
                            for skill in gap["missing"]:
                                p = skill.get("priority", "important")
                                if p != current_priority:
                                    current_priority = p
                                    st.markdown(f"**{priority_label.get(p, p.title())}**")
                                st.markdown(
                                    f"{badge(skill['name'], priority_kind.get(p, 'accent'))} "
                                    f"<span style='color:{COLORS['text_muted']};'>{skill.get('tip', '')}</span>",
                                    unsafe_allow_html=True,
                                )

            except ResumeParsingError as e:
                st.error(f"⚠️ {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred while analyzing skill gap: {e}")

# ====================================================================
# TAB 3 — Resume Health Check (fixed internal rubric, no JD needed)
# ====================================================================
with tab_health:
    # Results live in session_state, same pattern as tab_analyze/tab_skillgap,
    # so they persist across reruns triggered by any widget on the page.
    if "hc_results" not in st.session_state:
        st.session_state.hc_results = None

    with card("hc_upload"):
        st.subheader("1. Upload your resume")
        st.caption(
            "No job description needed here — this scores your resume against "
            "a fixed internal rubric (Content, Keywords, Formatting, Skills)."
        )
        hc_resume_file = st.file_uploader("PDF or DOCX", type=["pdf", "docx"], key="hc_resume_uploader")
        hc_analyze_clicked = st.button(
            "🩺 Run Health Check", type="primary", width="stretch", key="hc_analyze_btn"
        )

    if hc_analyze_clicked:
        if hc_resume_file is None:
            st.warning("Please upload a resume file first.")
        else:
            try:
                hc_file_bytes = hc_resume_file.read()

                validate_file(hc_resume_file.name, hc_file_bytes)
                with st.spinner("Reading resume..."):
                    hc_raw_text = extract_text(hc_resume_file.name, hc_file_bytes)
                    hc_clean_text = clean_text(hc_raw_text)

                with st.spinner("Scoring against the rubric..."):
                    health = generate_resume_health(hc_clean_text)

                hc_resume_id = db.save_resume(hc_resume_file.name, hc_clean_text)
                hc_check_id = db.save_health_check(
                    resume_id=hc_resume_id,
                    overall_score=health["overall_score"],
                    component_scores=health,
                )

                st.session_state.hc_results = {**health, "check_id": hc_check_id}
                st.rerun()

            except ResumeParsingError as e:
                st.error(f"⚠️ {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred while running the health check: {e}")

    hc_results = st.session_state.hc_results
    if hc_results is not None:
        overall = hc_results["overall_score"]
        components = hc_results["components"]
        ranked = rank_components_by_points_lost(components)

        kind, label = status_tier(overall)
        points_to_target = max(0.0, round(RECRUITER_GRADE_LINE - overall, 1))
        total_lost = round(100 - overall, 1)
        total_recoverable = round(sum(c["points_lost"] for c in components.values()), 1)

        # --- 1. Hero result: gauge + status badge + caption --------------
        with card("hc_hero"):
            st.markdown(f"#### Your resume scored **{overall:.0f}** out of 100")
            hero_l, hero_mid, hero_r = st.columns([1, 1, 1])
            with hero_mid:
                radial_gauge(
                    "Overall Score", overall, kind=kind, gauge_id="health_overall",
                    size=190, target_tick=RECRUITER_GRADE_LINE,
                )
                if points_to_target > 0:
                    badge_text = f"{label} · {points_to_target:.0f} pts from {RECRUITER_GRADE_LINE}"
                else:
                    badge_text = label
                st.markdown(
                    f"<div style='text-align:center; margin-top:0.5rem;'>{badge(badge_text, kind)}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div style='text-align:center; margin-top:0.4rem; color:{COLORS['text_muted']}; "
                    f"font-size:0.85rem;'>{RECRUITER_GRADE_LINE}+ is the recruiter-grade line on our rubric.</div>",
                    unsafe_allow_html=True,
                )

        # --- 2. Where you lost points -------------------------------------
        with card("hc_points_lost"):
            head_l, head_r = st.columns([3, 1])
            with head_l:
                st.markdown("#### Where you lost points")
            with head_r:
                st.markdown(
                    f"<div style='text-align:right; font-weight:800; color:{COLORS['danger_text']}; "
                    f"font-size:1.05rem; margin-top:0.3rem;'>-{total_lost:.0f} of 100</div>",
                    unsafe_allow_html=True,
                )

            max_lost = max((c["points_lost"] for _, c in ranked), default=0)
            for i, (name, comp) in enumerate(ranked):
                row_l, row_r = st.columns([5, 1])
                with row_l:
                    title = f"**{COMPONENT_ICONS.get(name, '')} {name}**"
                    st.markdown(title)
                    if i == 0 and comp["points_lost"] > 0:
                        st.markdown(badge("BIGGEST DRAG", "danger"), unsafe_allow_html=True)
                    st.caption(f"Scored {comp['score']:.0f}/100 · {comp['weight'] * 100:.0f}% weight")
                    points_lost_bar(comp["points_lost"], max_lost, kind="danger" if i == 0 else "warning")
                with row_r:
                    st.markdown(
                        f"<div style='text-align:right; font-weight:800; color:{COLORS['danger_text']}; "
                        f"font-size:1.15rem; margin-top:1.2rem;'>-{comp['points_lost']:.0f}</div>",
                        unsafe_allow_html=True,
                    )

        # --- 3. Points-to-target progress bar -----------------------------
        with card("hc_target"):
            st.markdown(
                f"#### You need {points_to_target:.0f} points. "
                f"Your fixes are worth up to {total_recoverable:.0f}."
            )
            target_progress_bar(overall, RECRUITER_GRADE_LINE)
            st.markdown(
                f"<div style='color:{COLORS['text_muted']}; font-size:0.88rem; margin-top:0.4rem;'>"
                f"You only need {points_to_target:.0f} points to clear the line — and you have up to "
                f"{total_recoverable:.0f} points of fixes in hand.</div>",
                unsafe_allow_html=True,
            )

        # --- 4. Per-component detail cards (2-column grid) ----------------
        st.markdown("#### Detailed Breakdown")
        top_two_names = {name for name, comp in ranked[:2] if comp["points_lost"] > 0}
        comp_names = list(components.keys())

        for row_start in range(0, len(comp_names), 2):
            row_names = comp_names[row_start:row_start + 2]
            detail_cols = st.columns(2)
            for col, name in zip(detail_cols, row_names):
                comp = components[name]
                with col:
                    with card(f"hc_detail_{name.lower()}"):
                        dh_l, dh_r = st.columns([3, 2])
                        with dh_l:
                            st.markdown(f"##### {COMPONENT_ICONS.get(name, '')} {name}")
                            if comp["points_lost"] > 0:
                                if name in top_two_names:
                                    st.markdown(badge("CRITICAL", "danger"), unsafe_allow_html=True)
                                else:
                                    st.markdown(badge("COSTING POINTS", "warning"), unsafe_allow_html=True)
                        with dh_r:
                            st.markdown(
                                f"<div style='text-align:right;'>"
                                f"<div style='font-weight:800; font-size:1.15rem; color:{COLORS['text_primary']};'>"
                                f"{comp['score']:.0f}/100</div>"
                                f"<div style='color:{COLORS['danger_text']}; font-weight:700; font-size:0.9rem;'>"
                                f"-{comp['points_lost']:.0f} pts</div>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )

                        st.markdown(
                            f"<div style='color:{COLORS['text_muted']}; line-height:1.5; "
                            f"margin: 0.5rem 0 0.9rem 0;'>{comp['explanation']}</div>",
                            unsafe_allow_html=True,
                        )

                        checklist_html = "".join(
                            status_line(passed, check_name) for check_name, passed in comp["checks"].items()
                        )
                        st.markdown(checklist_html, unsafe_allow_html=True)

                        st.markdown(
                            f"<div style='display:flex; justify-content:space-between; margin-top:0.9rem; "
                            f"padding-top:0.6rem; border-top:1px solid {COLORS['border']}; "
                            f"color:{COLORS['text_muted']}; font-size:0.85rem;'>"
                            f"<span>Component weight {comp['weight'] * 100:.0f}%</span>"
                            f"<span>Points lost: -{comp['points_lost']:.0f}</span>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )