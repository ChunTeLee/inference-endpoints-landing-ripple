# Inference Endpoints — ripple / orbit version

Static replica of the Inference Endpoints landing page with the orbit-style
engines panel (rotating engine logos around a center IE chevron, surrounded
by concentric "ripple" rings that fade outward).

## Live preview

- **Light** (full Features + Engines + Pricing): https://chuntelee.github.io/inference-endpoints-landing-ripple/
- **Dark, engines only**: https://chuntelee.github.io/inference-endpoints-landing-ripple/dark.html

## What's here

- `index.html` — the light version (Features + Engines + Pricing). Static
  HTML extracted from commit `325bd67` of the parent replica repo (last
  orbit version on `main` before the cube-pattern merge).
- `dark.html` — the dark version (engines section only). Generated from
  `index.html` by `build_dark.py`.
- `build_dark.py` — re-runnable transformer that takes `index.html` and
  produces `dark.html`: forces `class="dark"` on `<html>`, hides every
  non-Engines section / content row, and injects CSS overrides for the
  orbit-SVG inline colour attributes so the white plates / black ring
  strokes invert against the dark bg.
- `assets/` — mirrored images, favicons, and engine logos.

## Dark-mode design

Palette is taken from huggingface.co/pricing in dark mode:

- Body background: `#0B0F19`
- Card surface / orbit plates: `#1F2937` (gray-800)
- Headings: `#F9FAFB` (gray-50)
- Body text: `#94A3B8` (slate-400)
- Borders: `rgba(255,255,255,0.08)`

Engine logo plates and ripple rings are darkened via CSS attribute selectors
(`circle[fill="white"]`) — the SVG itself is unchanged.
