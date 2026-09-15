"""
widgets.py — Reusable UI widgets and presentation components.
"""

import json
import datetime
from typing import Dict, Any, List, Optional
import streamlit as st
import streamlit.components.v1 as components
from constants import DOMAINS, DOMAIN_CONFIG


def format_cairo_display_time(raw_ts: str) -> str:
    """Format raw timestamp into an elegant modern date & time string."""
    if not raw_ts:
        return ""
    try:
        clean_ts = str(raw_ts).replace("T", " ")
        dt = datetime.datetime.fromisoformat(clean_ts)
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return str(raw_ts)


def render_copy_words_toolbar(words: List[str]):
    """Renders a sleek, modern one-click copy toolbar for active target words."""
    if not words:
        return

    words_count = len(words)
    words_csv = ", ".join(words)
    words_list = "\n".join(words)
    words_csv_json = json.dumps(words_csv)
    words_list_json = json.dumps(words_list)

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
      * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      }}
      body, html {{
        background: transparent;
        overflow: hidden;
        height: 100%;
        display: flex;
        justify-content: flex-end;
        align-items: center;
      }}
      .toolbar-wrap {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 2px;
      }}
      .copy-btn {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 7px;
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: #FFFFFF;
        border: 1px solid rgba(255, 255, 255, 0.25);
        padding: 7px 15px;
        border-radius: 9px;
        font-size: 0.86rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 8px rgba(79, 70, 229, 0.28);
        outline: none;
        user-select: none;
        white-space: nowrap;
        text-decoration: none;
      }}
      .copy-btn:hover {{
        background: linear-gradient(135deg, #4338CA 0%, #6D28D9 100%);
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.42);
        transform: translateY(-1px);
      }}
      .copy-btn:active {{
        transform: translateY(0) scale(0.97);
      }}
      .copy-btn.copied {{
        background: linear-gradient(135deg, #059669 0%, #10B981 100%) !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.45) !important;
        border-color: rgba(52, 211, 153, 0.5) !important;
      }}
      .copy-btn-secondary {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 5px;
        background: #FFFFFF;
        color: #334155;
        border: 1px solid #CBD5E1;
        padding: 7px 12px;
        border-radius: 9px;
        font-size: 0.82rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        outline: none;
        user-select: none;
        white-space: nowrap;
      }}
      .copy-btn-secondary:hover {{
        background: #F8FAFC;
        color: #0F172A;
        border-color: #94A3B8;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.12);
        transform: translateY(-1px);
      }}
      .copy-btn-secondary:active {{
        transform: translateY(0) scale(0.97);
      }}
      .copy-btn-secondary.copied {{
        background: #ECFDF5 !important;
        color: #065F46 !important;
        border-color: #34D399 !important;
        box-shadow: 0 2px 10px rgba(16, 185, 129, 0.25) !important;
      }}
      .badge-pill {{
        background: rgba(255, 255, 255, 0.22);
        font-size: 0.72rem;
        font-weight: 700;
        padding: 1px 6px;
        border-radius: 10px;
      }}
      .icon {{
        flex-shrink: 0;
        transition: transform 0.2s ease;
      }}
      .copy-btn:hover .icon, .copy-btn-secondary:hover .icon {{
        transform: scale(1.1);
      }}
    </style>
    </head>
    <body>
    <div class="toolbar-wrap">
      <button id="copy-csv-btn" class="copy-btn" onclick="copyWords('csv')" title="Copy words separated by commas">
        <svg class="icon" viewBox="0 0 24 24" width="15" height="15" stroke="currentColor" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
        <span id="csv-label">Copy {words_count} Words</span>
        <span class="badge-pill">CSV</span>
      </button>

      <button id="copy-list-btn" class="copy-btn-secondary" onclick="copyWords('list')" title="Copy words one per line">
        <svg class="icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <line x1="8" y1="6" x2="21" y2="6"></line>
          <line x1="8" y1="12" x2="21" y2="12"></line>
          <line x1="8" y1="18" x2="21" y2="18"></line>
          <line x1="3" y1="6" x2="3.01" y2="6"></line>
          <line x1="3" y1="12" x2="3.01" y2="12"></line>
          <line x1="3" y1="18" x2="3.01" y2="18"></line>
        </svg>
        <span id="list-label">As List</span>
      </button>
    </div>

    <script>
      const wordsCSV = {words_csv_json};
      const wordsList = {words_list_json};

      function copyWords(mode) {{
        const text = mode === 'csv' ? wordsCSV : wordsList;
        const btn = document.getElementById(mode === 'csv' ? 'copy-csv-btn' : 'copy-list-btn');
        const label = document.getElementById(mode === 'csv' ? 'csv-label' : 'list-label');
        const origText = label.textContent;

        function indicateSuccess() {{
          btn.classList.add('copied');
          label.textContent = mode === 'csv' ? '✅ Copied {words_count} Words!' : '✅ Copied List!';
          setTimeout(() => {{
            btn.classList.remove('copied');
            label.textContent = origText;
          }}, 2200);
        }}

        if (navigator.clipboard && navigator.clipboard.writeText) {{
          navigator.clipboard.writeText(text)
            .then(indicateSuccess)
            .catch(() => fallback(text, indicateSuccess));
        }} else {{
          fallback(text, indicateSuccess);
        }}
      }}

      function fallback(text, onSuccess) {{
        try {{
          if (window.parent && window.parent.navigator && window.parent.navigator.clipboard) {{
            window.parent.navigator.clipboard.writeText(text)
              .then(onSuccess)
              .catch(() => execCopy(text, onSuccess));
            return;
          }}
        }} catch(e) {{}}
        execCopy(text, onSuccess);
      }}

      function execCopy(text, onSuccess) {{
        try {{
          const el = document.createElement('textarea');
          el.value = text;
          el.setAttribute('readonly', '');
          el.style.position = 'fixed';
          el.style.left = '-9999px';
          el.style.top = '-9999px';
          document.body.appendChild(el);
          el.focus();
          el.select();
          const res = document.execCommand('copy');
          document.body.removeChild(el);
          if (res) onSuccess();
        }} catch(err) {{
          console.error('Copy fallback failed:', err);
        }}
      }}
    </script>
    </body>
    </html>
    """
    components.html(html_code, height=44, scrolling=False)


def render_domain_breakdown_section(
    domain_data: Dict[str, Any],
    title: str = "🎯 Song Vocabulary Domain Register",
    compact: bool = False
):
    """Render a visual stacked progress bar and percentage badges for vocabulary domains."""
    if not domain_data or domain_data.get("total_words", 0) == 0:
        return

    domains_dict = domain_data.get("domains", {})
    primary_domain = domain_data.get("primary_domain", DOMAINS[0])
    primary_pct = domain_data.get("primary_percent", 0.0)
    is_high_formal = domain_data.get("is_high_formal", False)
    formal_pct = domain_data.get("formal_percent", 0.0)

    bar_segments = []
    for d in DOMAINS:
        info = domains_dict.get(d, {})
        pct = info.get("percent", 0.0)
        cnt = info.get("count", 0)
        if pct > 0:
            cfg = DOMAIN_CONFIG.get(d, {})
            color = cfg.get("color", "#6366F1")
            bar_segments.append(
                f'<div style="width: {pct}%; height: 100%; background: {color};" title="{cfg.get("emoji","")} {d}: {pct}% ({cnt} words)"></div>'
            )

    bar_html = "".join(bar_segments)

    badges_html = []
    for d in DOMAINS:
        info = domains_dict.get(d, {})
        pct = info.get("percent", 0.0)
        cnt = info.get("count", 0)
        if cnt > 0:
            cfg = DOMAIN_CONFIG.get(d, {})
            color = cfg.get("color", "#94A3B8")
            bg = cfg.get("bg", "rgba(148, 163, 184, 0.15)")
            border = cfg.get("border", "rgba(148, 163, 184, 0.3)")
            emoji = cfg.get("emoji", "")
            badges_html.append(
                f'<span style="background: {bg}; color: {color}; border: 1px solid {border}; padding: 3px 9px; border-radius: 12px; font-size: 0.8rem; font-weight: 700; display: inline-flex; align-items: center; gap: 4px;">'
                f'{emoji} {d}: <b>{pct}%</b> <small style="opacity: 0.8;">({cnt})</small>'
                f'</span>'
            )

    all_badges_html = " ".join(badges_html)

    edu_note_html = ""
    if is_high_formal:
        edu_note_html = (
            f'<div style="background: rgba(59, 130, 246, 0.09); border-left: 4px solid #3B82F6; border-radius: 8px; padding: 10px 14px; margin-top: 10px; font-size: 0.88rem; color: #BFDBFE; line-height: 1.55;">'
            f'💡 <b>ESL Learning Context Note:</b><br>'
            f'This song embeds a notable concentration of <b>Business & Society ({formal_pct}%)</b> vocabulary. '
            f'These formal terms are woven into a musical story to make them easier to remember and use in professional workplaces and interviews.'
            f'</div>'
        )

    if compact:
        box_html = (
            f'<div style="background: rgba(15, 23, 42, 0.55); border: 1px solid rgba(148, 163, 184, 0.18); border-radius: 10px; padding: 10px 14px; margin: 10px 0;">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; flex-wrap: wrap; gap: 6px;">'
            f'<span style="font-size: 0.85rem; font-weight: 700; color: #F1F5F9;">{title}</span>'
            f'<span style="font-size: 0.78rem; font-weight: 700; color: {DOMAIN_CONFIG.get(primary_domain, {}).get("color", "#38BDF8")};">'
            f'Primary: {DOMAIN_CONFIG.get(primary_domain, {}).get("emoji", "")} {primary_domain} ({primary_pct}%)'
            f'</span>'
            f'</div>'
            f'<div style="width: 100%; height: 8px; border-radius: 6px; overflow: hidden; display: flex; background: rgba(51, 65, 85, 0.5); margin-bottom: 8px;">'
            f'{bar_html}'
            f'</div>'
            f'<div style="display: flex; flex-wrap: wrap; gap: 6px; align-items: center;">'
            f'{all_badges_html}'
            f'</div>'
            f'{edu_note_html}'
            f'</div>'
        )
        st.markdown(box_html, unsafe_allow_html=True)
    else:
        box_html = (
            f'<div style="background: rgba(15, 23, 42, 0.65); border: 1px solid rgba(148, 163, 184, 0.22); border-radius: 12px; padding: 14px 18px; margin: 12px 0 16px 0;">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 8px;">'
            f'<span style="font-size: 0.95rem; font-weight: 700; color: #F8FAFC;">{title}</span>'
            f'<span style="background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(129, 140, 248, 0.4); padding: 3px 10px; border-radius: 12px; font-size: 0.82rem; font-weight: 700; color: #C7D2FE;">'
            f'🎯 Dominant Register: {DOMAIN_CONFIG.get(primary_domain, {}).get("emoji", "")} <b>{primary_domain}</b> ({primary_pct}%)'
            f'</span>'
            f'</div>'
            f'<div style="width: 100%; height: 10px; border-radius: 8px; overflow: hidden; display: flex; background: rgba(51, 65, 85, 0.6); margin-bottom: 10px;">'
            f'{bar_html}'
            f'</div>'
            f'<div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center;">'
            f'{all_badges_html}'
            f'</div>'
            f'{edu_note_html}'
            f'</div>'
        )
        st.markdown(box_html, unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading NLP Models...")
def load_nlp():
    """Cached spaCy NLP model loader."""
    import spacy
    try:
        return spacy.load("en_core_web_sm")
    except Exception:
        from spacy.cli import download
        download("en_core_web_sm")
        return spacy.load("en_core_web_sm")
