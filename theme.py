"""
theme.py
--------
Centralized visual theme for the Resume Analyzer — redesigned to match
the target look: soft lavender surfaces, a violet/purple accent, a true
pill-style segmented control, a clean upload dropzone, and a styled
range slider with a value badge.

Everything still funnels through inject_global_css() + a few small
helper functions (card, radial_gauge, badge, status_line, segmented,
upload_hint) so app.py's structure barely changes — mostly you wrap
existing widgets in the new helper containers.
"""

COLORS = {
    # Surfaces
    "bg": "#FFFFFF",
    "panel": "#F8FAFC",
    "panel_alt": "#F8FAFC",

    # Text
    "text_primary": "#111827",
    "text_muted": "#6B7280",

    # Accent (blue) — original palette, unchanged
    "accent": "#2563EB",
    "accent_dark": "#1D4ED8",
    "accent_light": "#3B82F6",
    "accent_text_on": "#FFFFFF",
    "accent_bg": "#EFF6FF",

    # Success (green)
    "success_fill": "#059669",
    "success_text": "#047857",
    "success_bg": "#D1FAE5",

    # Warning (amber)
    "warning_fill": "#D97706",
    "warning_text": "#B45309",
    "warning_bg": "#FEF3C7",

    # Danger
    "danger_fill": "#DC2626",
    "danger_text": "#B91C1C",
    "danger_bg": "#FEE2E2",

    # Neutral chip background used for role/tool icon squares
    "chip_bg": "#F3F4F6",

    "border": "#E5E7EB",
    "border_strong": "#D1D5DB",
}


def inject_global_css() -> None:
    import streamlit as st

    c = COLORS
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                         "Helvetica Neue", Arial, sans-serif;
        }}
        .stApp {{ background-color: {c['bg']}; color: {c['text_primary']}; }}
        h1, h2, h3, h4 {{ color: {c['text_primary']}; font-weight: 700; letter-spacing: -0.015em; }}
        p, li, span, label, .stMarkdown {{ color: {c['text_primary']}; }}
        [data-testid="stCaptionContainer"], .stCaption, small {{ color: {c['text_muted']} !important; }}
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}

        /* ---- Card containers (st.container(key="card_...")) ------------ */
        div[class*="st-key-card_"] {{
            background-color: {c['bg']};
            border: 1px solid {c['border']};
            border-radius: 18px;
            padding: 1.6rem 1.6rem 1.35rem 1.6rem;
            margin-bottom: 1.25rem;
            box-shadow: 0 1px 3px rgba(17, 24, 39, 0.04);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
            animation: rbFadeInUp 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
        }}
        div[class*="st-key-card_"]:hover {{
            transform: translateY(-3px);
            box-shadow: 0 14px 28px rgba(17, 24, 39, 0.08);
        }}
        @keyframes rbFadeInUp {{
            from {{ opacity: 0; transform: translateY(16px); }}
            to   {{ opacity: 1; transform: translateY(0); }}
        }}
        @media (prefers-reduced-motion: reduce) {{
            div[class*="st-key-card_"] {{ animation: none; }}
        }}

        /* ---- Primary / gradient buttons ---------------------------------- */
        .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, {c['accent_light']}, {c['accent_dark']});
            color: {c['accent_text_on']};
            border: none;
            border-radius: 12px;
            font-weight: 600;
            padding: 0.75rem 1.4rem;
            box-shadow: 0 6px 16px rgba(124, 58, 237, 0.28);
            transition: transform 0.12s ease-out, box-shadow 0.2s ease-out;
        }}
        .stButton > button[kind="primary"]:hover {{
            box-shadow: 0 12px 26px rgba(124, 58, 237, 0.38);
            transform: translateY(-1px);
        }}
        .stButton > button[kind="primary"]:active {{
            transform: scale(0.97);
        }}
        .stButton > button[kind="secondary"] {{
            background: {c['bg']};
            color: {c['text_primary']};
            border: 1.5px solid {c['border_strong']};
            border-radius: 14px;
            font-weight: 600;
            padding: 1.1rem 1rem;
            box-shadow: none;
            transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
        }}
        .stButton > button[kind="secondary"]:hover {{
            border-color: {c['accent']};
            box-shadow: 0 8px 20px rgba(124, 58, 237, 0.10);
            transform: translateY(-2px);
        }}

        /* ---- Segmented control (Custom JD / By Role / By Tool) ----------- */
        div[class*="st-key-segmented_"] {{
            background: {c['chip_bg']};
            border-radius: 14px;
            padding: 5px;
        }}
        div[class*="st-key-segmented_"] div[data-testid="stHorizontalBlock"] {{
            gap: 4px;
        }}
        div[class*="st-key-segmented_"] .stButton > button {{
            border-radius: 10px !important;
            padding: 0.55rem 1rem !important;
            font-weight: 600;
        }}
        div[class*="st-key-segmented_"] .stButton > button[kind="secondary"] {{
            background: transparent !important;
            color: {c['text_muted']} !important;
            border: none !important;
            box-shadow: none !important;
            transform: none !important;
        }}
        div[class*="st-key-segmented_"] .stButton > button[kind="primary"] {{
            background: {c['bg']} !important;
            color: {c['accent']} !important;
            border: none !important;
            box-shadow: 0 1px 4px rgba(17, 24, 39, 0.12) !important;
        }}

        /* ---- Role / Tool picker cards (still st.button, styled bigger) --- */
        div[class*="st-key-picker_"] .stButton > button[kind="secondary"] {{
            min-height: 96px;
            font-size: 0.98rem;
        }}
        div[class*="st-key-picker_"] .stButton > button[kind="primary"] {{
            min-height: 96px;
            font-size: 0.98rem;
            background: {c['accent_bg']} !important;
            color: {c['accent_dark']} !important;
            border: 1.5px solid {c['accent']} !important;
            box-shadow: 0 8px 20px rgba(124, 58, 237, 0.14) !important;
        }}

        /* ---- Tabs -------------------------------------------------------- */
        .stTabs [data-baseweb="tab"] {{ color: {c['text_muted']}; font-weight: 600; }}
        .stTabs [aria-selected="true"] {{ color: {c['accent']} !important; }}

        /* ---- File uploader dropzone --------------------------------------- */
        [data-testid="stFileUploaderDropzone"] {{
            background-color: {c['panel']};
            border: 1.5px dashed {c['border_strong']};
            border-radius: 16px;
            transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }}
        [data-testid="stFileUploaderDropzone"]:hover {{
            border-color: {c['accent']};
            transform: translateY(-2px);
            box-shadow: 0 10px 22px rgba(124, 58, 237, 0.10);
        }}
        [data-testid="stFileUploaderDropzone"].rb-dragover {{
            border-color: {c['accent']} !important;
            background-color: {c['accent_bg']} !important;
        }}
        [data-testid="stFileUploaderDropzone"] svg {{
            color: {c['accent']} !important;
            fill: {c['accent']} !important;
        }}
        [data-testid="stFileUploaderDropzoneInstructions"] span,
        [data-testid="stFileUploaderDropzoneInstructions"] small {{
            color: {c['text_muted']};
        }}
        [data-testid="stBaseButton-secondary"][kind="secondary"] {{
            border-radius: 10px;
        }}

        textarea, .stTextArea textarea {{
            border-radius: 12px !important;
            border-color: {c['border']} !important;
        }}
        .stTextArea textarea:focus {{ box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.15); }}

        /* ---- Slider card + purple thumb/track ----------------------------- */
        div[class*="st-key-slidercard_"] {{
            background: {c['panel_alt']};
            border-radius: 16px;
            padding: 1.1rem 1.3rem 0.9rem 1.3rem;
        }}
        [data-baseweb="slider"] div[role="slider"] {{
            background-color: {c['accent']} !important;
            box-shadow: 0 0 0 5px rgba(124, 58, 237, 0.15) !important;
        }}
        [data-baseweb="slider"] > div > div:nth-child(2) {{
            background: {c['accent']} !important;
        }}

        /* ---- Badges / chips ---------------------------------------------- */
        .rb-badge {{
            display: inline-block;
            padding: 0.2rem 0.65rem;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 600;
            margin: 0.15rem 0.3rem 0.15rem 0;
            border: 1px solid transparent;
            transition: transform 0.15s ease;
        }}
        .rb-badge:hover {{ transform: translateY(-2px); }}

        /* ---- Radial gauge wrapper ------------------------------------------ */
        .rb-gauge-wrap {{
            display: flex; flex-direction: column; align-items: center; gap: 0.5rem;
            animation: rbFadeInUp 0.6s cubic-bezier(0.22, 1, 0.36, 1) both;
        }}
        .rb-gauge-label {{ font-weight: 600; color: {c['text_primary']}; font-size: 0.92rem; text-align: center; }}

        /* ---- Slider header row (icon + label ... value pill) -------------- */
        .rb-slider-header {{
            display: flex; align-items: center; justify-content: space-between;
            margin-bottom: 0.6rem;
        }}
        .rb-slider-title {{
            display: flex; align-items: center; gap: 0.5rem;
            font-weight: 700; color: {c['text_primary']};
        }}
        .rb-slider-value {{
            font-weight: 800; color: {c['accent']}; font-size: 1.1rem;
        }}
        .rb-slider-minmax {{
            display: flex; justify-content: space-between;
            font-size: 0.82rem; color: {c['text_muted']}; margin-top: 0.2rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def card(key: str):
    import streamlit as st
    return st.container(border=True, key=f"card_{key}")


def segmented(key: str):
    """Wraps a row of st.button(type=primary/secondary) so they render as
    a pill-style segmented control (used for Custom JD / By Role / By Tool)."""
    import streamlit as st
    return st.container(key=f"segmented_{key}")


def picker_group(key: str):
    """Wraps a grid of role/tool st.button choices so they render as
    bigger, card-style options."""
    import streamlit as st
    return st.container(key=f"picker_{key}")


def slider_card(key: str, label: str, value, icon: str = "⏱️"):
    """
    Renders the lavender 'Available study hours/week'-style header
    (icon + label on the left, current value on the right) and returns
    the container to put the st.slider inside, plus writes the min/max
    caption row after — call slider_card_footer() after the slider.
    """
    import streamlit as st
    ctx = st.container(key=f"slidercard_{key}")
    with ctx:
        st.markdown(
            f"""<div class="rb-slider-header">
                    <div class="rb-slider-title">{icon} {label}</div>
                    <div class="rb-slider-value">{value}h</div>
                </div>""",
            unsafe_allow_html=True,
        )
    return ctx


def slider_minmax_caption(min_val, max_val, unit: str = "h") -> None:
    import streamlit as st
    st.markdown(
        f"""<div class="rb-slider-minmax">
                <span>{min_val}{unit} (min)</span><span>{max_val}{unit} (max)</span>
            </div>""",
        unsafe_allow_html=True,
    )


def score_kind(value: float) -> str:
    if value >= 80:
        return "success"
    elif value >= 50:
        return "warning"
    else:
        return "danger"


def radial_gauge(label: str, value: float, kind: str = "accent", max_value: float = 100,
                  size: int = 150, stroke: int = 12, gauge_id: str = "") -> None:
    import streamlit as st

    c = COLORS
    fill_map = {"accent": c["accent"], "success": c["success_fill"],
                "warning": c["warning_fill"], "danger": c["danger_fill"]}
    text_map = {"accent": c["accent"], "success": c["success_text"],
                "warning": c["warning_text"], "danger": c["danger_text"]}
    fill_color = fill_map.get(kind, c["accent"])
    text_color = text_map.get(kind, c["accent"])

    radius = (size - stroke) / 2
    circumference = 2 * 3.14159265358979 * radius
    pct = max(0, min(100, (value / max_value) * 100))
    target_offset = circumference * (1 - pct / 100)
    cx = cy = size / 2

    anim_name = f"rbGaugeFill_{gauge_id or label}".replace(" ", "_").replace("/", "_").replace("&", "")
    anim_name = "".join(ch for ch in anim_name if ch.isalnum() or ch == "_")

    html = f"""
    <div class="rb-gauge-wrap">
      <style>
        @keyframes {anim_name} {{
          from {{ stroke-dashoffset: {circumference:.2f}; }}
          to   {{ stroke-dashoffset: {target_offset:.2f}; }}
        }}
      </style>
      <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" role="img"
           aria-label="{label}: {value:.0f} out of {max_value:.0f}">
        <circle cx="{cx}" cy="{cy}" r="{radius}" fill="none"
                stroke="{c['border']}" stroke-width="{stroke}" />
        <circle cx="{cx}" cy="{cy}" r="{radius}" fill="none"
                stroke="{fill_color}" stroke-width="{stroke}" stroke-linecap="round"
                stroke-dasharray="{circumference:.2f}"
                stroke-dashoffset="{circumference:.2f}"
                transform="rotate(-90 {cx} {cy})"
                style="animation: {anim_name} 1.1s cubic-bezier(0.22, 1, 0.36, 1) 0.1s forwards;" />
        <text x="50%" y="46%" text-anchor="middle" dominant-baseline="middle"
              font-family="Inter, sans-serif" font-size="{size * 0.22:.0f}" font-weight="800"
              fill="{c['text_primary']}">{value:.0f}</text>
        <text x="50%" y="63%" text-anchor="middle" dominant-baseline="middle"
              font-family="Inter, sans-serif" font-size="{size * 0.11:.0f}" font-weight="600"
              fill="{text_color}">/ {max_value:.0f}</text>
      </svg>
      <div class="rb-gauge-label">{label}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def badge(text: str, kind: str = "accent") -> str:
    c = COLORS
    styles = {
        "accent": (c["accent_bg"], c["accent_dark"], c["accent"]),
        "success": (c["success_bg"], c["success_text"], c["success_fill"]),
        "warning": (c["warning_bg"], c["warning_text"], c["warning_fill"]),
        "danger": (c["danger_bg"], c["danger_text"], c["danger_fill"]),
    }
    bg, fg, border = styles.get(kind, styles["accent"])
    return (
        f'<span class="rb-badge" style="background-color:{bg}; color:{fg}; '
        f'border-color:{border};">{text}</span>'
    )


def status_line(passed: bool, text: str) -> str:
    c = COLORS
    if passed:
        return f'<div style="color:{c["success_text"]}; margin:0.25rem 0;">✅ {text}</div>'
    return f'<div style="color:{c["danger_text"]}; margin:0.25rem 0;">❌ {text}</div>'
