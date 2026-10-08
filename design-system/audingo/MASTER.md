# Audingo — quiet creative workspace

Direction: Apple-inspired light surfaces, spacious typography, monochrome outline
icons, and purposeful blue accents. Keep Audingo's own name and waveform identity.

Applied UI/UX Pro Max's productivity-workspace guidance: clear hierarchy, consistent
icons, readable contrast, visible keyboard focus, responsive cards, and reduced
motion. The user's requested Apple-inspired palette overrides the search tool's
generic teal/orange productivity palette and marketing-page recommendations.

| Role | Value |
| --- | --- |
| Canvas | `#F5F5F7` |
| Surface | `#FFFFFF` |
| Primary text | `#1D1D1F` |
| Secondary text | `#6E6E73` |
| Action / focus | `#0066CC` |
| Border | `#D2D2D7` |
| Positive | `#216E39` |
| Caution | `#855600` |
| Critical | `#B42318` |

Use the local system font stack (Apple system fonts when available, Segoe UI on
Windows). No external font download. Use 16px body text, restrained heading
weights, 12–20px corners, and pill-shaped buttons. Maintain 44px action targets.

Native widget theme: `.streamlit/config.toml`. Existing custom presentation:
`presentation/theme.css`. Domain icons: `presentation/components/identity.py`.
Decorative SVGs use data-URI images because Streamlit's HTML sanitizer removes
inline SVG. Navigation and action labels use Material Symbols Rounded.

Domain cards use three, two, or one column depending on viewport width. Mobile
navigation wraps. Respect reduced motion and retain Streamlit sidebar controls.
Do not change machine-readable status emoji in refinement data; these are part
of the existing pipeline contract.

Validation: compile checks, Streamlit AppTest rendering and dictionary filters
against a database copy, browser review at desktop and 375px. Live Gemini calls
and destructive actions are outside visual validation.
