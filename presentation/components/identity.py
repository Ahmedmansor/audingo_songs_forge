"""Consistent vector marks for the studio and its vocabulary domains."""
from html import escape
from base64 import b64encode

_PATHS = {
    "wave": '<path d="M3 10v4m4-8v12m5-16v20m5-16v12m4-8v4"/>',
    "Basic / Neutral": '<rect x="4" y="4" width="6" height="6" rx="2"/><rect x="14" y="4" width="6" height="6" rx="2"/><rect x="4" y="14" width="6" height="6" rx="2"/><rect x="14" y="14" width="6" height="6" rx="2"/>',
    "Science, Tech & Academia": '<path d="M9 3h6m-5 0v7L5 18a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-8V3M8 15h8"/>',
    "Emotions & Relationships": '<path d="M20 5c-3-3-6-1-8 1-2-2-5-4-8-1-4 4 0 9 8 15 8-6 12-11 8-15Z"/>',
    "Street & Daily Life": '<path d="m3 11 9-8 9 8M5 10v11h14V10M10 21v-7h4v7"/>',
    "Law, Politics & Society": '<path d="m3 7 9-4 9 4H3Zm2 3v8m7-8v8m7-8v8M3 21h18"/>',
    "Business & Career": '<rect x="3" y="7" width="18" height="14" rx="3"/><path d="M8 7V4h8v3M3 12c5 4 13 4 18 0M12 12v4"/>',
}


def icon_svg(name="wave", color=None):
    """Decorative outline icon with an adjacent visible label."""
    if color is None:
        import streamlit as st
        from presentation.theme import palette
        color = palette(st.session_state.get("ui_theme_mode", "dark"))["blue"]
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" '
            f'fill="none" stroke="{escape(color, quote=True)}" stroke-width="1.6" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            + _PATHS.get(name, _PATHS["wave"]) + '</svg>')
    # st.html sanitizes inline SVG; an image preserves the vector safely.
    encoded = b64encode(svg.encode()).decode()
    return f'<img class="studio-icon" src="data:image/svg+xml;base64,{encoded}" width="24" height="24" alt="" aria-hidden="true">'


def domain_card(name, data):
    percent = max(0, min(float(data.get("percent_used", 0)), 100))
    return f'''<article class="domain-card">
<div class="domain-top"><span class="icon-tile">{icon_svg(name)}</span><h4>{escape(name)}</h4></div>
<div class="domain-value">{data.get("unused", 0):,}<span>words remaining</span></div>
<div class="domain-track" role="progressbar" aria-label="{escape(name)} mastery" aria-valuenow="{percent:.1f}" aria-valuemin="0" aria-valuemax="100"><span style="width:{percent:.1f}%"></span></div>
<div class="domain-caption"><span>{percent:.1f}% mastered</span><span>{data.get("used", 0):,} / {data.get("total", 0):,}</span></div>
</article>'''
