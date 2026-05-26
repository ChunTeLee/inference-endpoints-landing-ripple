"""Generate a unified index.html with a built-in light/dark toggle button.

  - Light:  Features + Engines + Pricing
  - Dark:   Engines only (Features + Pricing hidden via CSS in .dark)
  - Toggle: button in the header. State persists in localStorage and is
            applied synchronously before paint to avoid a light flash.

This replaces the previous two-file setup (index.html + dark.html).
"""

import re
from pathlib import Path

SRC = Path(__file__).parent / "_light_source.html"  # pristine light copy
OUT = Path(__file__).parent / "index.html"

CORE_KEEP = "Powered by the best open-source inference engines"
DEPLOY_PHRASE = "One-click deployment"
PRICING_PHRASE = "Choose a plan that fits your needs"


def iter_top_sections(s):
    pos = 0
    while pos < len(s):
        m = re.search(r"<section\b[^>]*>", s[pos:])
        if not m:
            return
        start = pos + m.start()
        depth = 1
        i = pos + m.end()
        while i < len(s) and depth > 0:
            n = re.search(r"<(/?)section\b[^>]*>", s[i:])
            if not n:
                return
            depth += -1 if n.group(1) == "/" else 1
            i += n.end()
        yield start, i
        pos = i


def iter_top_rows(s):
    pat = re.compile(r'<div[^>]*class="[^"]*mx-auto\s+grid\s+max-w-7xl[^"]*"[^>]*>')
    pos = 0
    while pos < len(s):
        m = pat.search(s, pos)
        if not m:
            return
        start = m.start()
        depth = 1
        i = m.end()
        while i < len(s) and depth > 0:
            n = re.search(r"<(/?)div\b[^>]*>", s[i:])
            if not n:
                return
            depth += -1 if n.group(1) == "/" else 1
            i += n.end()
        yield start, i
        pos = i


# Inline icons + button. Sized for the existing header layout.
TOGGLE_BUTTON = """
<li>
  <button id="theme-toggle" type="button" aria-label="Toggle dark mode"
          class="flex size-8 items-center justify-center rounded-full border border-gray-200/70 text-gray-700 hover:bg-gray-100 dark:border-[#141C2E] dark:text-gray-200 dark:hover:bg-[#141C2E]">
    <svg class="theme-icon theme-icon-sun size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="4"/>
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>
    </svg>
    <svg class="theme-icon theme-icon-moon size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
    </svg>
  </button>
</li>
"""

# Inline pre-paint init: read localStorage and set .dark before CSS applies.
PRE_PAINT_SCRIPT = """<script>
(function(){
  try {
    var KEY = 'ie-ripple-theme';
    var t = localStorage.getItem(KEY) || 'light';
    if (t === 'dark') document.documentElement.classList.add('dark');
  } catch(e){}
})();
</script>"""

# Click handler (runs after DOM is parsed).
CLICK_SCRIPT = """<script>
document.addEventListener('DOMContentLoaded', function(){
  var btn = document.getElementById('theme-toggle');
  if (!btn) return;
  btn.addEventListener('click', function(){
    var root = document.documentElement;
    var dark = root.classList.toggle('dark');
    try { localStorage.setItem('ie-ripple-theme', dark ? 'dark' : 'light'); } catch(e){}
  });
});
</script>"""

DARK_STYLES = """<style id="ripple-dark-overrides">
  /* Toggle icon swap */
  html.dark .theme-icon-sun, html:not(.dark) .theme-icon-moon { display: none; }

  /* Dark palette pulled from huggingface.co/pricing dark mode */
  html.dark,
  html.dark body,
  html.dark .bg-white,
  html.dark .bg-gray-50,
  html.dark .bg-gray-50\\/70,
  html.dark .bg-gray-100 { background: #0B0F19 !important; }
  html.dark .bg-white\\/40 { background: rgba(255,255,255,0.04) !important; }

  html.dark h2,
  html.dark .text-gray-900 { color: #F9FAFB !important; }
  html.dark .text-gray-600,
  html.dark .text-gray-500 { color: #94A3B8 !important; }

  /* Structural grid border + dividers — solid #141C2E to match HF pricing */
  html.dark .border-gray-200\\/70,
  html.dark .border-gray-200 { border-color: #141C2E !important; }
  html.dark .divide-gray-200\\/70 > *,
  html.dark .divide-gray-200 > *,
  html.dark .divide-dashed > * { border-color: #141C2E !important; }

  /* Pill chips (Engines = green; left visible only in dark) */
  html.dark .bg-emerald-400\\/10 { background-color: rgba(52,211,153,0.15) !important; }
  html.dark .text-emerald-600 { color: #34D399 !important; }

  /* Orbit SVG: convert white plates/rings to a dark gray slightly lighter
     than the bg. Slot/center plates become solid plates; ripple rings
     (with fill-opacity) become subtle radial bands fading outward. */
  html.dark svg.hub-orbit circle[fill="white"] { fill: #1F2937; }
  html.dark svg.hub-orbit circle[stroke="#000"] { stroke: rgba(229,231,235,0.55); }
  html.dark svg.hub-orbit circle[stroke="rgba(0,0,0,0.10)"] { stroke: rgba(255,255,255,0.18); }

  /* Header */
  html.dark header { background: #0B0F19; border-color: #141C2E !important; }
  html.dark header a, html.dark header span,
  html.dark header li > a { color: #E5E7EB !important; }
  html.dark header button:not(#theme-toggle) { background: #E5E7EB !important; color: #0B0F19 !important; }

  /* Hide Features + Pricing in dark mode */
  html.dark [data-light-only] { display: none !important; }
</style>"""


def main():
    html = SRC.read_text(encoding="utf-8")

    # 1. Tag the Features section with data-light-only.
    #    Section 2 (Deployment + Features) — already has Deployment row hidden
    #    by trim_to_core_sections. In dark mode we want the whole section gone.
    body_start = html.find("<body>")
    body_end = html.find("</body>") + len("</body>")
    body = html[body_start:body_end]

    parts = []
    cursor = 0
    for s, e in iter_top_sections(body):
        parts.append(body[cursor:s])
        sec_html = body[s:e]
        if "Everything you need to deploy AI models at scale" in sec_html and CORE_KEEP not in sec_html:
            # Features-only section (Deployment row already hidden inside it).
            sec_html = re.sub(r"<section\b", '<section data-light-only', sec_html, count=1)
        elif CORE_KEEP in sec_html and PRICING_PHRASE in sec_html:
            # Engines + Pricing combined section. Walk inner rows and tag
            # the Pricing row.
            row_spans = list(iter_top_rows(sec_html))
            for r_s, r_e in reversed(row_spans):
                row_html = sec_html[r_s:r_e]
                if PRICING_PHRASE in row_html and CORE_KEEP not in row_html:
                    row_html = re.sub(r"<div\b", '<div data-light-only', row_html, count=1)
                    sec_html = sec_html[:r_s] + row_html + sec_html[r_e:]
        parts.append(sec_html)
        cursor = e
    parts.append(body[cursor:])
    body = "".join(parts)
    html = html[:body_start] + body + html[body_end:]

    # 2. Pre-paint theme-init script + dark styles right before </head>.
    html = html.replace(
        "</head>",
        PRE_PAINT_SCRIPT + DARK_STYLES + "</head>",
        1,
    )

    # 3. Inject toggle button into the header's <ul>.
    html = re.sub(
        r'(<ul class="flex items-center[^"]*">)',
        r'\1' + TOGGLE_BUTTON,
        html,
        count=1,
    )

    # 4. Click handler at end of body.
    html = html.replace("</body>", CLICK_SCRIPT + "</body>", 1)

    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT} ({len(html):,} chars)")


if __name__ == "__main__":
    main()
