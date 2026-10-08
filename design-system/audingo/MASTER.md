# Audingo — quiet creative workspace

Direction: Apple-inspired surfaces, spacious typography, monochrome outline icons,
and purposeful blue accents. Dark is the initial preference; a visible sidebar
button switches between light and dark. Keep Audingo's own name and waveform identity.

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

Native widget themes: `.streamlit/config.toml`. Semantic light/dark tokens:
`presentation/theme.py`. Existing custom presentation:
`presentation/theme.css`. Domain icons: `presentation/components/identity.py`.
Decorative SVGs use data-URI images because Streamlit's HTML sanitizer removes
inline SVG. Navigation and action labels use Material Symbols Rounded.

Domain cards use three, two, or one column depending on viewport width. Mobile
navigation wraps. Respect reduced motion and retain Streamlit sidebar controls.
Do not change machine-readable status emoji in refinement data; these are part
of the existing pipeline contract.

The appearance button uses a CCv2 adapter to Streamlit 1.63's native theme menu
(stable `stMainMenuButton` and `stMainMenuItem-theme-*` test IDs), since there is no
public Python theme setter. This changes native controls and canvas tables without
reloading the page or dropping unsaved inputs. Browser theme persistence remains
Streamlit's responsibility. The adapter is isolated in `components/appearance.py`
and falls back to the built-in menu if the frontend structure changes. Recheck it
when upgrading Streamlit. Temporary frontend token overrides keep custom cards
in sync while the server receives the native theme context.

Validation: compile checks, Streamlit AppTest rendering and dictionary filters
against a database copy, browser review at desktop and 375px. Appearance was checked in both directions,
with a filtered dictionary value retained, and dark preference retained after reload.
Both token palettes pass 4.5:1 contrast for primary, secondary, and status text. Live Gemini calls
and destructive actions are outside visual validation.

Library uses progressive disclosure: choose one song, read its compact summary,
then switch between Overview, Vocabulary, Critic, Production, and Edit. Lyrics,
mood analysis, vocabulary lists, and package editors start collapsed. Long lyrics
scroll within a bounded container. Production shows one saved package and one
prompt at a time. Keep native controls, rounded surface cards, restrained blue
accents, and consistent Material icons. Sidebar bars represent covered unique
words divided by the total for that domain; always pair the bar with counts and
a percentage. These counts describe archive coverage, not learner mastery.

Library summary numbers use semantic theme colors: total new words blue,
authenticity green, targets purple, new bonus teal, reused muted, and extra amber.
Keep their labels neutral and visible; color supplements the labels. The domain
breakdown appears directly in Overview only, without duplication in Vocabulary.
