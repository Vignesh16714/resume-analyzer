"""
tech_icons.py
-------------
Small, self-contained SVG logos for the tool/tech-stack picker in the
"Skill Gap" tab (By Tool mode). Bundled directly as strings — no image
files to ship, no CDN fetch — so they render instantly and never depend
on external network access, matching the rest of this project's
"always works offline" philosophy (same reasoning as components.py's
CSS-only hero animation and keyword_extractor.py's regex fallback).

These are simplified, hand-drawn recreations of each brand's mark (not
pixel copies of the official trademarked artwork), used purely so users
can visually identify the tool at a glance — the same way any IDE or
dev tool shows a small tech icon next to a tool's name.

Keys match skills_data.TOOL_ICONS exactly. components.inject_tool_logos()
swaps the emoji for the matching SVG at render time and silently leaves
any tool it has no logo for as-is (falling back to its emoji), so this
dict never needs to cover every TOOL_SKILL_MAP entry to be safe.
"""

TECH_LOGOS = {
    "React": """<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="2.2" fill="#61DAFB"/>
        <g fill="none" stroke="#61DAFB" stroke-width="1.3">
          <ellipse cx="12" cy="12" rx="10" ry="4.2"/>
          <ellipse cx="12" cy="12" rx="10" ry="4.2" transform="rotate(60 12 12)"/>
          <ellipse cx="12" cy="12" rx="10" ry="4.2" transform="rotate(120 12 12)"/>
        </g>
      </svg>""",

    "Docker": """<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <g fill="#2496ED">
          <rect x="2" y="11" width="3" height="3"/>
          <rect x="6" y="11" width="3" height="3"/>
          <rect x="10" y="11" width="3" height="3"/>
          <rect x="10" y="7" width="3" height="3"/>
          <rect x="14" y="11" width="3" height="3"/>
          <rect x="14" y="7" width="3" height="3"/>
          <rect x="18" y="11" width="3" height="3"/>
          <path d="M1 14c0 4 3.5 7 10.5 7 7.5 0 12-3.7 13-9-1 .3-2.4.2-3-.6-1 1-2.5.9-3.2 0-1.2 1.3-3 .9-3.7-.1-1.4.9-3.1.6-3.8-.3-1.7.7-3.6.6-4.4-.4C4.4 11 1 12 1 14z"/>
        </g>
      </svg>""",

    "Python": """<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2c-4 0-3.8 1.7-3.8 1.7v1.8h3.9v.6H6.6S4 5.8 4 9.9s2.3 4 2.3 4h1.4v-2S7.6 9.6 9.9 9.6h3.9s2.2 0 2.2-2.2V4S16.3 2 12 2z" fill="#3776AB"/>
        <path d="M12 22c4 0 3.8-1.7 3.8-1.7v-1.8h-3.9v-.6h5.5S20 18.2 20 14.1s-2.3-4-2.3-4h-1.4v2s.1 2.3-2.2 2.3H10.2s-2.2 0-2.2 2.2V20S7.7 22 12 22z" fill="#FFD43B"/>
        <circle cx="9.3" cy="4.5" r=".7" fill="#fff"/>
        <circle cx="14.7" cy="19.5" r=".7" fill="#fff"/>
      </svg>""",

    "Kubernetes": """<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2l8.3 3-1.4 8.8L12 22l-6.9-8.2L3.7 5z" fill="none" stroke="#326CE6" stroke-width="1.4"/>
        <circle cx="12" cy="12" r="3.2" fill="none" stroke="#326CE6" stroke-width="1.2"/>
        <g stroke="#326CE6" stroke-width="1" stroke-linecap="round">
          <line x1="12" y1="5.5" x2="12" y2="8.8"/>
          <line x1="17.2" y1="9" x2="14.4" y2="10.7"/>
          <line x1="15.4" y1="16" x2="13.4" y2="13.2"/>
          <line x1="8.6" y1="16" x2="10.6" y2="13.2"/>
          <line x1="6.8" y1="9" x2="9.6" y2="10.7"/>
        </g>
      </svg>""",

    "AWS": """<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <text x="2" y="13" font-family="Arial, sans-serif" font-size="9" font-weight="700" fill="#232F3E">aws</text>
        <path d="M2 17c5 2.4 12.5 2.4 19 0" fill="none" stroke="#FF9900" stroke-width="1.6" stroke-linecap="round"/>
        <path d="M19.5 15.6l2 1.2-1.9 1.4" fill="none" stroke="#FF9900" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>""",

    # Not a single company's trademark, so this is a plain neural-network
    # glyph rather than a borrowed brand mark (e.g. TensorFlow's) standing
    # in for a whole category — kept for visual consistency with the other
    # tool logos, but easy to delete from this dict if you'd rather leave
    # "Machine Learning" as its emoji.
    "Machine Learning": """<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <g fill="#7C3AED">
          <circle cx="5" cy="6" r="1.6"/>
          <circle cx="5" cy="12" r="1.6"/>
          <circle cx="5" cy="18" r="1.6"/>
          <circle cx="12" cy="9" r="1.6"/>
          <circle cx="12" cy="15" r="1.6"/>
          <circle cx="19" cy="12" r="1.8"/>
        </g>
        <g stroke="#A78BFA" stroke-width="1">
          <line x1="6.4" y1="6" x2="10.7" y2="8.6"/>
          <line x1="6.4" y1="12" x2="10.7" y2="9.4"/>
          <line x1="6.4" y1="12" x2="10.7" y2="14.6"/>
          <line x1="6.4" y1="18" x2="10.7" y2="15.4"/>
          <line x1="13.4" y1="9.4" x2="17.5" y2="11.6"/>
          <line x1="13.4" y1="14.6" x2="17.5" y2="12.4"/>
        </g>
      </svg>""",
}
