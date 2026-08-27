"""
components.py
--------------
Everything that needs raw HTML/CSS/JS beyond what st.markdown's sanitized
subset allows lives here, isolated behind st.components.v1.html so it
can't break the rest of the app if a browser quirk shows up.

Two components:

  render_hero()          -- the full-width animated hero banner. Pure CSS
                             (no external Lottie fetch, so it never depends
                             on network access or a CDN being reachable) —
                             a looping magnifying-glass-over-document scan
                             animation plus a typewriter subtitle. The
                             subtitle's *first* phrase is written into the
                             DOM immediately (not only via JS), so if the
                             embedded <script> fails to execute for any
                             reason, the hero still reads as a normal,
                             correctly styled headline instead of blank
                             space.

  enable_button_tilt()    -- a zero-height, invisible component that
                             attaches a mousemove-tracking 3D tilt to every
                             Streamlit button, and a drag-enter/leave class
                             toggle to the file-upload dropzone. Because
                             components.html() renders in a same-origin
                             iframe, it can safely reach `window.parent.document`
                             to enhance the *real* Streamlit widgets outside
                             the iframe. All of this is additive: the CSS in
                             theme.py already gives buttons a sensible static
                             hover/press style, so if this script doesn't run
                             (e.g. in constrained embeds), nothing looks broken
                             — the buttons simply lose the cursor-tracked tilt
                             and fall back to the CSS-only hover state.
"""

import streamlit.components.v1 as components


def render_hero(colors: dict, height: int = 360) -> None:
    c = colors
    html = f"""
    <div id="rb-hero">
      <style>
        * {{ box-sizing: border-box; }}
        #rb-hero {{
          position: relative;
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          overflow: hidden;
          border-radius: 20px;
          background: linear-gradient(180deg, #FFFFFF 0%, {c['panel']} 100%);
          padding: 2.4rem 1.5rem 1.6rem 1.5rem;
          text-align: center;
        }}
        /* Soft, slow-drifting blob background — decorative only, low opacity,
           CSS-only so it costs nothing and can't fail to load. */
        .rb-blob {{
          position: absolute;
          border-radius: 50%;
          filter: blur(50px);
          opacity: 0.35;
          pointer-events: none;
          z-index: 0;
        }}
        .rb-blob-a {{
          width: 320px; height: 320px; top: -120px; left: -80px;
          background: radial-gradient(circle, {c['accent']}, transparent 70%);
          animation: rbDrift1 14s ease-in-out infinite alternate;
        }}
        .rb-blob-b {{
          width: 280px; height: 280px; bottom: -140px; right: -60px;
          background: radial-gradient(circle, {c['success_fill']}, transparent 70%);
          animation: rbDrift2 16s ease-in-out infinite alternate;
        }}
        @keyframes rbDrift1 {{
          from {{ transform: translate(0, 0); }}
          to   {{ transform: translate(40px, 30px); }}
        }}
        @keyframes rbDrift2 {{
          from {{ transform: translate(0, 0); }}
          to   {{ transform: translate(-30px, -25px); }}
        }}

        .rb-hero-inner {{ position: relative; z-index: 1; }}
        .rb-hero-title {{
          font-size: clamp(1.9rem, 4vw, 2.7rem);
          font-weight: 800;
          letter-spacing: -0.02em;
          color: {c['text_primary']};
          margin: 0 0 0.6rem 0;
          animation: rbFadeIn 0.7s ease both;
        }}
        .rb-hero-sub {{
          font-size: clamp(1rem, 2vw, 1.15rem);
          font-weight: 500;
          color: {c['text_muted']};
          min-height: 1.6em;
          margin: 0 0 1.4rem 0;
          animation: rbFadeIn 0.9s ease both;
        }}
        .rb-cursor {{
          display: inline-block;
          margin-left: 2px;
          color: {c['accent']};
          animation: rbBlink 1s step-end infinite;
        }}
        @keyframes rbFadeIn {{
          from {{ opacity: 0; transform: translateY(8px); }}
          to   {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes rbBlink {{
          0%, 100% {{ opacity: 1; }}
          50% {{ opacity: 0; }}
        }}
        @media (prefers-reduced-motion: reduce) {{
          .rb-blob, .rb-cursor {{ animation: none; }}
        }}

        /* ---- Scanning illustration: document + sweeping glow + magnifier --- */
        .rb-scan-wrap {{
          position: relative;
          width: 220px;
          height: 150px;
          margin: 0 auto;
        }}
        .rb-doc {{
          position: absolute;
          left: 50%;
          top: 0;
          transform: translateX(-50%);
          width: 130px;
          height: 150px;
          background: #FFFFFF;
          border: 2px solid {c['border']};
          border-radius: 10px;
          box-shadow: 0 10px 24px rgba(17, 24, 39, 0.08);
          overflow: hidden;
        }}
        .rb-doc-line {{
          height: 8px;
          margin: 14px 14px 0 14px;
          border-radius: 4px;
          background: {c['border']};
        }}
        .rb-doc-line.short {{ width: 45%; }}
        .rb-scanline {{
          position: absolute;
          left: 0; right: 0;
          height: 26px;
          background: linear-gradient(180deg, transparent, rgba(37,99,235,0.28), transparent);
          animation: rbScanMove 2.6s ease-in-out infinite;
        }}
        @keyframes rbScanMove {{
          0%   {{ top: -10%; opacity: 0; }}
          10%  {{ opacity: 1; }}
          90%  {{ opacity: 1; }}
          100% {{ top: 100%; opacity: 0; }}
        }}
        .rb-magnifier {{
          position: absolute;
          width: 54px;
          height: 54px;
          animation: rbMagMove 3.4s ease-in-out infinite;
          filter: drop-shadow(0 6px 10px rgba(37,99,235,0.25));
        }}
        @keyframes rbMagMove {{
          0%   {{ top: 6px;  left: 30px; }}
          25%  {{ top: 40px; left: 120px; }}
          50%  {{ top: 90px; left: 60px; }}
          75%  {{ top: 50px; left: 10px; }}
          100% {{ top: 6px;  left: 30px; }}
        }}
      </style>

      <div class="rb-hero-inner">
        <h1 class="rb-hero-title">AI-Powered Resume Analyzer</h1>
        <div class="rb-hero-sub"><span id="rb-typewriter">Extract, score, and improve your resume's ATS compatibility.</span><span class="rb-cursor">|</span></div>

        <div class="rb-scan-wrap">
          <div class="rb-blob rb-blob-a"></div>
          <div class="rb-blob rb-blob-b"></div>
          <div class="rb-doc">
            <div class="rb-doc-line" style="margin-top:16px;"></div>
            <div class="rb-doc-line"></div>
            <div class="rb-doc-line short"></div>
            <div class="rb-doc-line" style="margin-top:20px;"></div>
            <div class="rb-doc-line"></div>
            <div class="rb-doc-line short"></div>
            <div class="rb-scanline"></div>
          </div>
          <svg class="rb-magnifier" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
            <circle cx="26" cy="26" r="16" fill="rgba(37,99,235,0.08)"
                    stroke="{c['accent']}" stroke-width="4" />
            <line x1="38" y1="38" x2="56" y2="56" stroke="{c['accent']}"
                  stroke-width="5" stroke-linecap="round" />
          </svg>
        </div>
      </div>

      <script>
        (function() {{
          var phrases = [
            "Extract, score, and improve your resume's ATS compatibility.",
            "Match your resume against any job description in seconds.",
            "Get clear, actionable feedback recruiters' filters agree with."
          ];
          var el = document.getElementById('rb-typewriter');
          if (!el) return;
          var pIdx = 0, cIdx = phrases[0].length, deleting = true;

          function tick() {{
            var current = phrases[pIdx];
            if (!deleting) {{
              cIdx++;
              el.textContent = current.slice(0, cIdx);
              if (cIdx >= current.length) {{
                deleting = true;
                setTimeout(tick, 1800);
                return;
              }}
            }} else {{
              cIdx--;
              el.textContent = current.slice(0, cIdx);
              if (cIdx <= 0) {{
                deleting = false;
                pIdx = (pIdx + 1) % phrases.length;
                setTimeout(tick, 400);
                return;
              }}
            }}
            setTimeout(tick, deleting ? 28 : 42);
          }}
          setTimeout(tick, 1400);
        }})();
      </script>
    </div>
    """
    components.html(html, height=height, scrolling=False)


def enable_button_tilt() -> None:
    """
    Invisible (zero-height) component that layers cursor-tracked 3D tilt
    onto every st.button and a drag-over highlight onto the file uploader.
    Safe to call once per page render — it re-scans on an interval so
    buttons/dropzones added after a rerun (e.g. once results appear) are
    picked up automatically without needing a page reload.
    """
    html = """
    <script>
      (function() {
        function enhanceButtons(doc) {
          var buttons = doc.querySelectorAll('.stButton > button');
          buttons.forEach(function(btn) {
            if (btn.dataset.rbTiltBound) return;
            btn.dataset.rbTiltBound = "1";
            btn.addEventListener('mousemove', function(e) {
              var rect = btn.getBoundingClientRect();
              var x = e.clientX - rect.left;
              var y = e.clientY - rect.top;
              var cx = rect.width / 2, cy = rect.height / 2;
              var rotY = ((x - cx) / cx) * 8;
              var rotX = -((y - cy) / cy) * 8;
              btn.style.transform = 'perspective(600px) rotateX(' + rotX + 'deg) rotateY(' + rotY + 'deg) scale(1.02)';
            });
            btn.addEventListener('mouseleave', function() {
              btn.style.transform = 'perspective(600px) rotateX(0deg) rotateY(0deg) scale(1)';
            });
          });
        }

        function enhanceDropzones(doc) {
          var zones = doc.querySelectorAll('[data-testid="stFileUploaderDropzone"]');
          zones.forEach(function(zone) {
            if (zone.dataset.rbDragBound) return;
            zone.dataset.rbDragBound = "1";
            ['dragenter', 'dragover'].forEach(function(evt) {
              zone.addEventListener(evt, function(e) {
                e.preventDefault();
                zone.classList.add('rb-dragover');
              });
            });
            ['dragleave', 'drop'].forEach(function(evt) {
              zone.addEventListener(evt, function() {
                zone.classList.remove('rb-dragover');
              });
            });
          });
        }

        function run() {
          try {
            var doc = window.parent.document;
            enhanceButtons(doc);
            enhanceDropzones(doc);
          } catch (err) {
            // Cross-origin or restricted embed: silently no-op.
            // Buttons/dropzones keep their CSS-only hover styling.
          }
        }

        run();
        setInterval(run, 1000);
      })();
    </script>
    """
    components.html(html, height=0, width=0)


def restyle_uploader_copy() -> None:
    """
    Rewrites the native Streamlit uploader's instruction text to match the
    target design ("Click to upload or drag & drop" / "PDF, DOCX or TXT •
    Max 10MB") without touching Streamlit internals — same safe DOM-patch
    pattern as enable_button_tilt(). Safe to call once per page render.
    """
    html = """
    <script>
      (function() {
        function patch(doc) {
          var zones = doc.querySelectorAll('[data-testid="stFileUploaderDropzoneInstructions"]');
          zones.forEach(function(zone) {
            if (zone.dataset.rbCopyPatched) return;
            var spans = zone.querySelectorAll('span');
            var smalls = zone.querySelectorAll('small');
            if (spans.length) {
              spans[0].innerHTML = '<b style="color:#7C3AED;">Click to upload</b> or drag &amp; drop';
            }
            if (smalls.length) {
              smalls[0].textContent = 'PDF, DOCX or TXT \\u2022 Max 10MB';
            }
            zone.dataset.rbCopyPatched = "1";
          });
        }
        function run() {
          try { patch(window.parent.document); } catch (err) { /* no-op */ }
        }
        run();
        setInterval(run, 1000);
      })();
    </script>
    """
    components.html(html, height=0, width=0)
