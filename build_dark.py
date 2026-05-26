"""Generate dark.html from the orbit-version index.html.

Light index.html shows Features + Engines + Pricing.
dark.html shows ONLY the Engines section in dark mode.

Dark mode is enabled by:
  1. Adding class="dark" to <html>  — triggers existing Tailwind v4 dark variants
     baked into the compiled CSS that ships in the page.
  2. Hiding Features and Pricing sections.
  3. Injecting a <style> block that overrides orbit-SVG inline color attrs
     so the white plates / black ring strokes invert against the dark bg.
"""

import re
from pathlib import Path

SRC = Path(__file__).parent / "index.html"
DST = Path(__file__).parent / "dark.html"


CORE_KEEP = "Powered by the best open-source inference engines"
TO_HIDE = (
    "Everything you need to deploy AI models at scale",
    "Choose a plan that fits your needs",
)

DARK_OVERRIDES = """
<style id="ripple-dark-overrides">
  html.dark,
  html.dark body,
  html.dark .bg-white,
  html.dark .bg-gray-50,
  html.dark .bg-gray-50\\/70,
  html.dark .bg-gray-100 { background: #0B0F19 !important; }
  html.dark .bg-white\\/40 { background: rgba(255,255,255,0.04) !important; }

  /* Section + heading text */
  html.dark h2,
  html.dark .text-gray-900 { color: #F9FAFB !important; }
  html.dark .text-gray-600,
  html.dark .text-gray-500 { color: #94A3B8 !important; }
  html.dark .border-gray-200\\/70,
  html.dark .border-gray-200 { border-color: #141C2E !important; }
  /* Tailwind divide-x / divide-y utilities set border-color on the children via
     the parent's divide-gray-200* class. The parent class doesn't apply directly
     to the child element, so the .border-gray-200 rule above doesn't catch it. */
  html.dark .divide-gray-200\\/70 > *,
  html.dark .divide-gray-200 > *,
  html.dark .divide-dashed > * { border-color: #141C2E !important; }

  /* Pill chip for "Engines" — keep the green tint but readable on dark */
  html.dark .bg-emerald-400\\/10 { background-color: rgba(52, 211, 153, 0.15) !important; }
  html.dark .text-emerald-600 { color: #34D399 !important; }

  /* Orbit SVG: override ALL white-filled circles to a dark gray slightly
     lighter than the bg. The slot/center plates show as solid plates that
     contrast with the bg; the ripple rings (with fill-opacity) become
     subtle radial bands fading outward, matching the light-mode intent. */
  html.dark svg.hub-orbit circle[fill="white"] { fill: #1F2937; }
  html.dark svg.hub-orbit circle[stroke="#000"] { stroke: rgba(229, 231, 235, 0.55); }
  html.dark svg.hub-orbit circle[stroke="rgba(0,0,0,0.10)"] { stroke: rgba(255, 255, 255, 0.18); }

  /* Header */
  html.dark header { background: #0B0F19; border-color: #141C2E !important; }
  html.dark header a, html.dark header span,
  html.dark header li > a { color: #E5E7EB !important; }
  html.dark header button { background: #E5E7EB !important; color: #0B0F19 !important; }
</style>
"""


def main() -> None:
    html = SRC.read_text(encoding="utf-8")

    # 1. Force-enable dark mode on <html>
    html = re.sub(
        r'<html(\s+[^>]*)?>',
        lambda m: f'<html{m.group(1) or ""} class="dark">' if 'class=' not in (m.group(1) or "")
                  else m.group(0).replace('class="', 'class="dark '),
        html, count=1,
    )

    # 2. Inject dark-mode CSS overrides right before </head>
    html = html.replace("</head>", DARK_OVERRIDES + "</head>", 1)

    # 3. Mark the engines section so we can apply targeted background CSS
    #    (we identify it by its h2 phrase, then add a data attribute).
    def tag_engines_section(m):
        section_html = m.group(0)
        if CORE_KEEP in section_html:
            return section_html.replace('<section', '<section data-engine-section', 1)
        return section_html
    html = re.sub(
        r'<section\b[^>]*>.*?</section>',
        tag_engines_section,
        html, flags=re.DOTALL,
    )

    # 4. Hide every top-level <section> whose content does not contain the
    #    Engines heading. Inside the section that DOES contain it, also hide
    #    the Pricing row (Engines and Pricing share a single SvelteKit
    #    <section> in the source markup).
    def iter_top_sections(s, body_start):
        pos = body_start
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

    body_start = html.find("<body>")
    body_end = html.find("</body>") + len("</body>")
    body = html[body_start:body_end]

    new_body_parts: list[str] = []
    cursor = 0
    for s, e in iter_top_sections(body, 0):
        new_body_parts.append(body[cursor:s])
        sec_html = body[s:e]
        # Inspect only the opening <section ...> tag (not inner content) when
        # deciding whether display:none has already been applied to it.
        opener_end = sec_html.find(">")
        section_opener = sec_html[: opener_end + 1] if opener_end != -1 else sec_html
        if CORE_KEEP not in sec_html:
            if 'style="display:none"' not in section_opener:
                sec_html = re.sub(
                    r"<section\b", '<section style="display:none"', sec_html, count=1,
                )
        else:
            # Walk inner content rows; hide rows whose body lacks CORE_KEEP.
            row_spans = list(iter_top_rows(sec_html))
            for r_s, r_e in reversed(row_spans):
                row_html = sec_html[r_s:r_e]
                row_opener_end = row_html.find(">")
                row_opener = row_html[: row_opener_end + 1] if row_opener_end != -1 else row_html
                if CORE_KEEP not in row_html:
                    if 'style="display:none"' not in row_opener:
                        row_html = re.sub(
                            r"<div\b", '<div style="display:none"', row_html, count=1,
                        )
                        sec_html = sec_html[:r_s] + row_html + sec_html[r_e:]
        new_body_parts.append(sec_html)
        cursor = e
    new_body_parts.append(body[cursor:])
    new_body = "".join(new_body_parts)
    html = html[:body_start] + new_body + html[body_end:]

    DST.write_text(html, encoding="utf-8")
    print(f"Wrote {DST} ({len(html):,} chars)")


if __name__ == "__main__":
    main()
