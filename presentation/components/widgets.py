"""
widgets.py — Reusable UI widgets and presentation components.
"""

import json
import datetime
from html import escape
from typing import Dict, Any, List, Optional
import streamlit as st
import streamlit.components.v1 as components
from constants import DOMAINS, DOMAIN_CONFIG
from presentation.components.identity import icon_svg
from presentation.theme import palette


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

    tokens = palette(st.session_state.get("ui_theme_mode", "dark"))
    theme_variables = ";".join(f"--studio-{k}:{v}" for k, v in tokens.items())
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
      :root {{ {theme_variables} }}
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
        background: #0066CC;
        color: #FFFFFF;
        border: 1px solid var(--studio-line);
        padding: 7px 15px;
        border-radius: 20px;
        font-size: 0.86rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: none;
        min-height: 40px;
        user-select: none;
        white-space: nowrap;
        text-decoration: none;
      }}
      .copy-btn:hover {{
        background: var(--studio-blue);
        box-shadow: none;
        transform: translateY(-1px);
      }}
      .copy-btn:active {{
        transform: translateY(0) scale(0.97);
      }}
      .copy-btn.copied {{
        background: var(--studio-green) !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.45) !important;
        border-color: rgba(52, 211, 153, 0.5) !important;
      }}
      .copy-btn-secondary {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 5px;
        background: var(--studio-surface);
        color: var(--studio-ink);
        border: 1px solid var(--studio-line);
        padding: 7px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        min-height: 40px;
        user-select: none;
        white-space: nowrap;
      }}
      .copy-btn-secondary:hover {{
        background: var(--studio-bg);
        color: var(--studio-ink);
        border-color: var(--studio-muted);
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.12);
        transform: translateY(-1px);
      }}
      .copy-btn-secondary:active {{
        transform: translateY(0) scale(0.97);
      }}
      .copy-btn-secondary.copied {{
        background: var(--studio-green-bg) !important;
        color: var(--studio-green) !important;
        border-color: #34D399 !important;
        box-shadow: 0 2px 10px rgba(16, 185, 129, 0.25) !important;
      }}
      .badge-pill {{
        background: rgba(255,255,255,0.2);
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
      button:focus-visible {{ outline: 2px solid var(--studio-blue); outline-offset: 2px; }}
      @media (prefers-reduced-motion: reduce) {{
        *, *::before, *::after {{ transition: none !important; transform: none !important; }}
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


def render_simple_copy_button(
    text: str,
    label: str = "Copy",
    copied_label: str = "Copied!",
    button_id: Optional[Any] = None,
    align: str = "flex-end",
):
    """
    Renders a compact, one-click copy button without triggering page reruns.
    """
    if not text:
        return
    clean_text = text.strip()
    if not clean_text:
        return

    tokens = palette(st.session_state.get("ui_theme_mode", "dark"))
    theme_variables = ";".join(f"--studio-{k}:{v}" for k, v in tokens.items())
    text_json = json.dumps(clean_text)
    prefix = f"btn_copy_{button_id}_" if button_id is not None else "btn_copy_"
    justify_val = "flex-start" if align == "flex-start" else "flex-end"

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
      :root {{ {theme_variables} }}
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
        justify-content: {justify_val};
        align-items: center;
      }}
      .copy-btn {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        background: var(--studio-surface);
        color: var(--studio-ink);
        border: 1px solid var(--studio-line);
        padding: 5px 12px;
        border-radius: 18px;
        font-size: 0.8rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        min-height: 32px;
        user-select: none;
        white-space: nowrap;
      }}
      .copy-btn:hover {{
        background: var(--studio-bg);
        border-color: var(--studio-muted);
        transform: translateY(-1px);
      }}
      .copy-btn:active {{
        transform: translateY(0) scale(0.97);
      }}
      .copy-btn.copied {{
        background: var(--studio-green-bg) !important;
        color: var(--studio-green) !important;
        border-color: #34D399 !important;
      }}
      .icon {{
        flex-shrink: 0;
        transition: transform 0.2s ease;
      }}
      .copy-btn:hover .icon {{
        transform: scale(1.1);
      }}
      button:focus-visible {{ outline: 2px solid var(--studio-blue); outline-offset: 2px; }}
    </style>
    </head>
    <body>
      <button id="{prefix}btn" class="copy-btn" onclick="copyAction()" title="Copy to clipboard">
        <svg class="icon" viewBox="0 0 24 24" width="13" height="13" stroke="currentColor" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
        <span id="{prefix}label">{escape(label)}</span>
      </button>

    <script>
      const textToCopy = {text_json};
      function copyAction() {{
        const btn = document.getElementById('{prefix}btn');
        const lbl = document.getElementById('{prefix}label');
        const orig = lbl.textContent;
        function done() {{
          btn.classList.add('copied');
          lbl.textContent = '✅ {escape(copied_label)}';
          setTimeout(() => {{
            btn.classList.remove('copied');
            lbl.textContent = orig;
          }}, 2000);
        }}
        if (navigator.clipboard && navigator.clipboard.writeText) {{
          navigator.clipboard.writeText(textToCopy).then(done).catch(() => fallback(textToCopy, done));
        }} else {{
          fallback(textToCopy, done);
        }}
      }}
      function fallback(t, cb) {{
        try {{
          if (window.parent && window.parent.navigator && window.parent.navigator.clipboard) {{
            window.parent.navigator.clipboard.writeText(t).then(cb).catch(() => exec(t, cb));
            return;
          }}
        }} catch(e) {{}}
        exec(t, cb);
      }}
      function exec(t, cb) {{
        try {{
          const el = document.createElement('textarea');
          el.value = t;
          el.style.position = 'fixed';
          el.style.left = '-9999px';
          document.body.appendChild(el);
          el.select();
          document.execCommand('copy');
          document.body.removeChild(el);
          cb();
        }} catch(e) {{}}
      }}
    </script>
    </body>
    </html>
    """
    components.html(html_code, height=36, scrolling=False)


def render_library_lyrics_copy_toolbar(
    title: str,
    lyrics: str,
    song_id: Optional[Any] = None,
    align: str = "flex-start",
    primary_label: str = "Copy Title & Lyrics",
    secondary_label: str = "Lyrics Only",
):
    """
    Renders a sleek, modern one-click copy toolbar for Library songs.
    Copies:
      1. Primary: Song title followed by full lyrics underneath.
      2. Secondary: Lyrics only.
    """
    if not lyrics and not title:
        return

    clean_title = (title or "").strip()
    clean_lyrics = (lyrics or "").strip()
    combined_text = f"{clean_title}\n\n{clean_lyrics}" if clean_title else clean_lyrics

    tokens = palette(st.session_state.get("ui_theme_mode", "dark"))
    theme_variables = ";".join(f"--studio-{k}:{v}" for k, v in tokens.items())

    combined_json = json.dumps(combined_text)
    lyrics_json = json.dumps(clean_lyrics)
    prefix = f"lib_{song_id}_" if song_id is not None else "lib_"
    justify_val = "flex-start" if align == "flex-start" else "flex-end"

    escaped_primary = escape(primary_label)
    escaped_secondary = escape(secondary_label)

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
      :root {{ {theme_variables} }}
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
        justify-content: {justify_val};
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
        background: #0066CC;
        color: #FFFFFF;
        border: 1px solid var(--studio-line);
        padding: 7px 15px;
        border-radius: 20px;
        font-size: 0.86rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: none;
        min-height: 38px;
        user-select: none;
        white-space: nowrap;
        text-decoration: none;
      }}
      .copy-btn:hover {{
        background: var(--studio-blue);
        transform: translateY(-1px);
      }}
      .copy-btn:active {{
        transform: translateY(0) scale(0.97);
      }}
      .copy-btn.copied {{
        background: var(--studio-green) !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.45) !important;
        border-color: rgba(52, 211, 153, 0.5) !important;
      }}
      .copy-btn-secondary {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        background: var(--studio-surface);
        color: var(--studio-ink);
        border: 1px solid var(--studio-line);
        padding: 7px 13px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        min-height: 38px;
        user-select: none;
        white-space: nowrap;
      }}
      .copy-btn-secondary:hover {{
        background: var(--studio-bg);
        color: var(--studio-ink);
        border-color: var(--studio-muted);
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.12);
        transform: translateY(-1px);
      }}
      .copy-btn-secondary:active {{
        transform: translateY(0) scale(0.97);
      }}
      .copy-btn-secondary.copied {{
        background: var(--studio-green-bg) !important;
        color: var(--studio-green) !important;
        border-color: #34D399 !important;
        box-shadow: 0 2px 10px rgba(16, 185, 129, 0.25) !important;
      }}
      .icon {{
        flex-shrink: 0;
        transition: transform 0.2s ease;
      }}
      .copy-btn:hover .icon, .copy-btn-secondary:hover .icon {{
        transform: scale(1.1);
      }}
      button:focus-visible {{ outline: 2px solid var(--studio-blue); outline-offset: 2px; }}
      @media (prefers-reduced-motion: reduce) {{
        *, *::before, *::after {{ transition: none !important; transform: none !important; }}
      }}
    </style>
    </head>
    <body>
    <div class="toolbar-wrap">
      <button id="{prefix}copy-full-btn" class="copy-btn" onclick="copyAction('full')" title="Copy song title and full lyrics to clipboard">
        <svg class="icon" viewBox="0 0 24 24" width="15" height="15" stroke="currentColor" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
        <span id="{prefix}full-label">{escaped_primary}</span>
      </button>

      <button id="{prefix}copy-lyrics-btn" class="copy-btn-secondary" onclick="copyAction('lyrics')" title="Copy only the lyrics without title">
        <svg class="icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <line x1="8" y1="6" x2="21" y2="6"></line>
          <line x1="8" y1="12" x2="21" y2="12"></line>
          <line x1="8" y1="18" x2="21" y2="18"></line>
          <line x1="3" y1="6" x2="3.01" y2="6"></line>
          <line x1="3" y1="12" x2="3.01" y2="12"></line>
          <line x1="3" y1="18" x2="3.01" y2="18"></line>
        </svg>
        <span id="{prefix}lyrics-label">{escaped_secondary}</span>
      </button>
    </div>

    <script>
      const fullText = {combined_json};
      const lyricsOnlyText = {lyrics_json};

      function copyAction(mode) {{
        const text = mode === 'full' ? fullText : lyricsOnlyText;
        const btn = document.getElementById(mode === 'full' ? '{prefix}copy-full-btn' : '{prefix}copy-lyrics-btn');
        const label = document.getElementById(mode === 'full' ? '{prefix}full-label' : '{prefix}lyrics-label');
        const origText = label.textContent;

        function indicateSuccess() {{
          btn.classList.add('copied');
          label.textContent = '✅ Copied!';
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


def render_floating_audit_prompt_fab(target_words: Optional[List[str]] = None):
    """
    Renders a sleek, persistent floating action button (FAB) in the Studio tab.
    Clicking the button immediately copies the strict SONG AUDIT PROMPT to the clipboard.
    """
    from domain.services.prompt_service import build_song_audit_prompt

    prompt_text = build_song_audit_prompt(target_words=target_words)
    prompt_json = json.dumps(prompt_text)

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
      body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; }}
    </style>
    </head>
    <body>
    <script>
    (function() {{
      const promptText = {prompt_json};
      const doc = window.parent.document;
      if (!doc) return;

      const BTN_ID = 'audingo-floating-audit-btn';
      let btn = doc.getElementById(BTN_ID);

      if (!btn) {{
        btn = doc.createElement('button');
        btn.id = BTN_ID;
        btn.type = 'button';
        btn.setAttribute('aria-label', 'Copy Song Audit Prompt');
        doc.body.appendChild(btn);
      }}

      // Apply sleek, Apple-inspired styles with high z-index and subtle glassmorphic blur
      btn.style.position = 'fixed';
      btn.style.bottom = '26px';
      btn.style.right = '28px';
      btn.style.zIndex = '999999';
      btn.style.display = 'inline-flex';
      btn.style.alignItems = 'center';
      btn.style.justifyContent = 'center';
      btn.style.gap = '8px';
      btn.style.padding = '10px 18px';
      btn.style.borderRadius = '999px';
      btn.style.background = 'linear-gradient(135deg, #0066CC 0%, #004D99 100%)';
      btn.style.color = '#FFFFFF';
      btn.style.border = '1px solid rgba(255, 255, 255, 0.25)';
      btn.style.boxShadow = '0 8px 24px rgba(0, 102, 204, 0.4), 0 3px 8px rgba(0, 0, 0, 0.2)';
      btn.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';
      btn.style.fontSize = '0.86rem';
      btn.style.fontWeight = '650';
      btn.style.letterSpacing = '-0.01em';
      btn.style.cursor = 'pointer';
      btn.style.transition = 'all 0.22s cubic-bezier(0.4, 0, 0.2, 1)';
      btn.style.userSelect = 'none';

      const idleHtml = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg><span>📋 نسخ برومبت التدقيق (Audit Prompt)</span>';
      const successHtml = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"></polyline></svg><span>✅ تم النسخ إلى الحافظة!</span>';

      btn.innerHTML = idleHtml;

      btn.onmouseenter = function() {{
        btn.style.transform = 'translateY(-2px) scale(1.02)';
        btn.style.boxShadow = '0 12px 28px rgba(0, 102, 204, 0.5), 0 4px 10px rgba(0, 0, 0, 0.22)';
      }};
      btn.onmouseleave = function() {{
        btn.style.transform = 'translateY(0) scale(1)';
        btn.style.boxShadow = '0 8px 24px rgba(0, 102, 204, 0.4), 0 3px 8px rgba(0, 0, 0, 0.2)';
      }};

      function copyText() {{
        function indicate() {{
          btn.style.background = 'linear-gradient(135deg, #10B981 0%, #059669 100%)';
          btn.style.boxShadow = '0 8px 24px rgba(16, 185, 129, 0.45)';
          btn.innerHTML = successHtml;
          setTimeout(() => {{
            btn.style.background = 'linear-gradient(135deg, #0066CC 0%, #004D99 100%)';
            btn.style.boxShadow = '0 8px 24px rgba(0, 102, 204, 0.4), 0 3px 8px rgba(0, 0, 0, 0.2)';
            btn.innerHTML = idleHtml;
          }}, 2400);
        }}

        if (window.parent && window.parent.navigator && window.parent.navigator.clipboard) {{
          window.parent.navigator.clipboard.writeText(promptText)
            .then(indicate)
            .catch(() => execFallback(promptText, indicate));
        }} else if (navigator.clipboard && navigator.clipboard.writeText) {{
          navigator.clipboard.writeText(promptText)
            .then(indicate)
            .catch(() => execFallback(promptText, indicate));
        }} else {{
          execFallback(promptText, indicate);
        }}
      }}

      function execFallback(text, onSuccess) {{
        try {{
          const ta = doc.createElement('textarea');
          ta.value = text;
          ta.setAttribute('readonly', '');
          ta.style.position = 'fixed';
          ta.style.left = '-9999px';
          ta.style.top = '-9999px';
          doc.body.appendChild(ta);
          ta.focus();
          ta.select();
          const res = doc.execCommand('copy');
          doc.body.removeChild(ta);
          if (res) onSuccess();
        }} catch(e) {{
          console.error('Fallback copy error:', e);
        }}
      }}

      btn.onclick = copyText;

      // Automatically hide the button when switching to other tabs
      const tabs = doc.querySelectorAll('[data-testid="stTabs"] [role="tab"]');
      tabs.forEach(tab => {{
        tab.addEventListener('click', function() {{
          setTimeout(() => {{
            const activeTab = doc.querySelector('[data-testid="stTabs"] [aria-selected="true"]');
            if (activeTab && !activeTab.textContent.includes('Studio')) {{
              btn.style.display = 'none';
            }} else {{
              btn.style.display = 'inline-flex';
            }}
          }}, 120);
        }});
      }});
    }})();
    </script>
    </body>
    </html>
    """
    components.html(html_code, height=0, scrolling=False)


def render_floating_library_song_fab(
    song_id: int,
    row_num: int,
    title: str,
    is_suno_completed: bool = False,
):
    """
    Renders a sleek, persistent floating action button (FAB) in the Library tab.
    Displays the current song number and title (#50 • Never Too Late, Dad)
    when the user scrolls past the hero card / segmented control section.
    Clicking the button smoothly scrolls back up to the top of the song.
    """
    song_data = {
        "id": song_id,
        "row_num": row_num,
        "title": title or "Untitled Song",
        "is_suno_completed": bool(is_suno_completed),
    }
    song_data_json = json.dumps(song_data)

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
      body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; }}
    </style>
    </head>
    <body>
    <script>
    (function() {{
      const currentSong = {song_data_json};
      const doc = window.parent.document;
      const win = window.parent;
      if (!doc || !win) return;

      const BTN_ID = 'audingo-floating-library-song-btn';

      function escapeHtml(str) {{
        return (str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
      }}

      if (!win._audingoSongFabController) {{
        win._audingoSongFabController = {{
          currentSong: null,
          btn: null,

          init: function() {{
            let btn = doc.getElementById(BTN_ID);
            if (!btn) {{
              btn = doc.createElement('button');
              btn.id = BTN_ID;
              btn.type = 'button';
              btn.setAttribute('aria-label', 'Current song indicator and scroll to top');

              btn.style.position = 'fixed';
              btn.style.bottom = '26px';
              btn.style.right = '28px';
              btn.style.zIndex = '999998';
              btn.style.display = 'inline-flex';
              btn.style.alignItems = 'center';
              btn.style.justifyContent = 'center';
              btn.style.gap = '8px';
              btn.style.padding = '8px 16px';
              btn.style.minHeight = '42px';
              btn.style.borderRadius = '999px';
              btn.style.background = 'var(--studio-surface, #1e293b)';
              btn.style.color = 'var(--studio-ink, #ffffff)';
              btn.style.border = '1px solid var(--studio-line, rgba(255, 255, 255, 0.2))';
              btn.style.boxShadow = '0 10px 28px rgba(0, 0, 0, 0.32), 0 2px 6px rgba(0, 0, 0, 0.16)';
              btn.style.backdropFilter = 'blur(14px)';
              btn.style.webkitBackdropFilter = 'blur(14px)';
              btn.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';
              btn.style.fontSize = '0.86rem';
              btn.style.fontWeight = '600';
              btn.style.cursor = 'pointer';
              btn.style.userSelect = 'none';
              btn.style.maxWidth = 'calc(100vw - 56px)';
              btn.style.opacity = '0';
              btn.style.transform = 'translateY(18px) scale(0.96)';
              btn.style.pointerEvents = 'none';
              btn.style.transition = 'opacity 0.25s cubic-bezier(0.4, 0, 0.2, 1), transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.2s, box-shadow 0.2s';

              btn.onmouseenter = function() {{
                btn.style.transform = 'translateY(-2px) scale(1.02)';
                btn.style.borderColor = 'var(--studio-blue, #0066CC)';
                btn.style.boxShadow = '0 14px 32px rgba(0, 102, 204, 0.38), 0 4px 10px rgba(0, 0, 0, 0.22)';
                const arrow = btn.querySelector('.fab-arrow-up');
                if (arrow) arrow.style.transform = 'translateY(-2px)';
              }};
              btn.onmouseleave = function() {{
                btn.style.transform = 'translateY(0) scale(1)';
                btn.style.borderColor = 'var(--studio-line, rgba(255, 255, 255, 0.2))';
                btn.style.boxShadow = '0 10px 28px rgba(0, 0, 0, 0.32), 0 2px 6px rgba(0, 0, 0, 0.16)';
                const arrow = btn.querySelector('.fab-arrow-up');
                if (arrow) arrow.style.transform = 'translateY(0)';
              }};

              btn.onclick = function() {{
                const hero = doc.getElementById('library-song-hero-card') || doc.querySelector('.library-song-card') || doc.querySelector('[data-testid="stSelectbox"]');
                if (hero && hero.scrollIntoView) {{
                  hero.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }} else {{
                  win.scrollTo({{ top: 0, behavior: 'smooth' }});
                  const scrollables = [
                    doc.querySelector('[data-testid="stAppViewContainer"]'),
                    doc.querySelector('section.main'),
                    doc.querySelector('.main'),
                    doc.documentElement,
                    doc.body
                  ];
                  for (const el of scrollables) {{
                    if (el && el.scrollTop > 0) el.scrollTo({{ top: 0, behavior: 'smooth' }});
                  }}
                }}
              }};

              doc.body.appendChild(btn);
            }}
            this.btn = btn;

            const self = this;
            const handler = function() {{ self.checkVisibility(); }};

            win.addEventListener('scroll', handler, {{ capture: true, passive: true }});
            doc.addEventListener('scroll', handler, {{ capture: true, passive: true }});
            win.addEventListener('resize', handler, {{ passive: true }});

            const tabs = doc.querySelectorAll('[data-testid="stTabs"] [role="tab"]');
            tabs.forEach(tab => {{
              tab.addEventListener('click', () => setTimeout(handler, 120));
            }});

            const mo = new MutationObserver(() => {{ handler(); }});
            mo.observe(doc.body, {{ childList: true, subtree: true }});
          }},

          setSong: function(data) {{
            this.currentSong = data;
            let btn = doc.getElementById(BTN_ID);
            if (!btn) {{
              this.init();
              btn = this.btn;
            }} else {{
              this.btn = btn;
            }}
            if (!doc.body.contains(btn)) {{
              doc.body.appendChild(btn);
            }}

            const sunoHtml = data.is_suno_completed
              ? '<span style="background: rgba(16, 185, 129, 0.18); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.35); padding: 1px 6px; border-radius: 8px; font-size: 0.72rem; font-weight: 700; flex-shrink: 0;">✅ Suno</span>'
              : '';
            const safeTitle = escapeHtml(data.title);
            btn.title = '#' + data.row_num + ' • ' + data.title + ' — Click to scroll back to top';
            btn.innerHTML = [
              '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0; opacity:0.85;"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>',
              '<span style="background: #0066CC; color: #FFFFFF; padding: 2px 7px; border-radius: 10px; font-size: 0.75rem; font-weight: 700; flex-shrink: 0; letter-spacing: 0.02em;">#' + data.row_num + '</span>',
              '<span style="max-width: 210px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 650; color: var(--studio-ink, #FFFFFF);">' + safeTitle + '</span>',
              sunoHtml,
              '<svg class="fab-arrow-up" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0; opacity:0.85; transition: transform 0.2s ease;"><line x1="12" y1="19" x2="12" y2="5"></line><polyline points="5 12 12 5 19 12"></polyline></svg>'
            ].join('');

            this.checkVisibility();
          }},

          checkVisibility: function() {{
            const btn = this.btn || doc.getElementById(BTN_ID);
            if (!btn) return;

            const activeTab = doc.querySelector('[data-testid="stTabs"] [aria-selected="true"]');
            if (activeTab && !activeTab.textContent.toLowerCase().includes('library')) {{
              btn.style.display = 'none';
              btn.style.opacity = '0';
              btn.style.pointerEvents = 'none';
              return;
            }}

            const sentinel = doc.getElementById('library-song-hero-card') || doc.querySelector('.library-song-card');
            if (!sentinel) {{
              btn.style.display = 'none';
              btn.style.opacity = '0';
              btn.style.pointerEvents = 'none';
              return;
            }}

            // Always stay present and visible while in Library viewing a song!
            btn.style.display = 'inline-flex';
            btn.style.opacity = '1';
            btn.style.transform = 'translateY(0) scale(1)';
            btn.style.pointerEvents = 'auto';
          }}
        }};

        win._audingoSongFabController.init();
      }}

      win._audingoSongFabController.setSong(currentSong);
    }})();
    </script>
    </body>
    </html>
    """
    components.html(html_code, height=0, scrolling=False)


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
        words = sorted(list(set(info.get("words", []))))
        if pct > 0:
            cfg = DOMAIN_CONFIG.get(d, {})
            color = cfg.get("color", "#6366F1")
            words_preview = ", ".join(words[:15]) + ("..." if len(words) > 15 else "")
            title_attr = f"{cfg.get('emoji','')} {d}: {pct}% ({cnt} words) &#10;Words: {words_preview}"
            bar_segments.append(
                f'<div style="width: {pct}%; height: 100%; background: {color};" title="{title_attr}"></div>'
            )

    bar_html = "".join(bar_segments)

    badges_html = []
    for d in DOMAINS:
        info = domains_dict.get(d, {})
        pct = info.get("percent", 0.0)
        cnt = info.get("count", 0)
        words = sorted(list(set(info.get("words", []))))
        if cnt > 0:
            cfg = DOMAIN_CONFIG.get(d, {})
            color = cfg.get("color", "var(--studio-muted)")
            bg = cfg.get("bg", "rgba(148, 163, 184, 0.15)")
            border = cfg.get("border", "rgba(148, 163, 184, 0.3)")
            emoji = icon_svg(d)
            
            words_preview = ", ".join(words[:25]) + (f" ... (+{len(words)-25} more)" if len(words) > 25 else "")
            tooltip_str = escape(f"{d} ({cnt} words): {words_preview}", quote=True)
            
            badges_html.append(
                f'<span title="{tooltip_str}" style="background: {bg}; color: {color}; border: 1px solid {border}; padding: 3px 9px; border-radius: 12px; font-size: 0.8rem; font-weight: 700; display: inline-flex; align-items: center; gap: 4px; cursor: help;">'
                f'{emoji} {d}: <b>{pct}%</b> <small style="opacity: 0.8;">({cnt})</small>'
                f'</span>'
            )

    all_badges_html = " ".join(badges_html)

    edu_note_html = ""
    if is_high_formal:
        edu_note_html = (
            f'<div style="background: rgba(59, 130, 246, 0.09); border-left: 4px solid #3B82F6; border-radius: 8px; padding: 10px 14px; margin-top: 10px; font-size: 0.88rem; color: var(--studio-blue); line-height: 1.55;">'
            f'💡 <b>ESL Learning Context Note:</b><br>'
            f'This song embeds a notable concentration of <b>Professional & Academic ({formal_pct}%)</b> vocabulary. '
            f'These formal terms are woven into a musical story to make them easier to remember and use in professional workplaces, academia, and interviews.'
            f'</div>'
        )

    if compact:
        box_html = (
            f'<div style="background: var(--studio-bg); border: 1px solid rgba(148, 163, 184, 0.18); border-radius: 10px; padding: 10px 14px; margin: 10px 0;">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; flex-wrap: wrap; gap: 6px;">'
            f'<span style="font-size: 0.85rem; font-weight: 700; color: var(--studio-ink);">{title}</span>'
            f'<span style="font-size: 0.78rem; font-weight: 700; color: {DOMAIN_CONFIG.get(primary_domain, {}).get("color", "#38BDF8")};">'
            f'Primary: {DOMAIN_CONFIG.get(primary_domain, {}).get("emoji", "")} {primary_domain} ({primary_pct}%)'
            f'</span>'
            f'</div>'
            f'<div style="width: 100%; height: 8px; border-radius: 6px; overflow: hidden; display: flex; background: var(--studio-track); margin-bottom: 8px;">'
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
            f'<div style="background: var(--studio-bg); border: 1px solid rgba(148, 163, 184, 0.22); border-radius: 12px; padding: 14px 18px; margin: 12px 0 16px 0;">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 8px;">'
            f'<span style="font-size: 0.95rem; font-weight: 700; color: var(--studio-ink);">{title}</span>'
            f'<span style="background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(129, 140, 248, 0.4); padding: 3px 10px; border-radius: 12px; font-size: 0.82rem; font-weight: 700; color: var(--studio-blue);">'
            f'🎯 Dominant Register: {DOMAIN_CONFIG.get(primary_domain, {}).get("emoji", "")} <b>{primary_domain}</b> ({primary_pct}%)'
            f'</span>'
            f'</div>'
            f'<div style="width: 100%; height: 10px; border-radius: 8px; overflow: hidden; display: flex; background: var(--studio-track); margin-bottom: 10px;">'
            f'{bar_html}'
            f'</div>'
            f'<div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center;">'
            f'{all_badges_html}'
            f'</div>'
            f'{edu_note_html}'
            f'</div>'
        )
        st.markdown(box_html, unsafe_allow_html=True)

    # Render interactive words inventory grouped by domain
    active_domains = [d for d in DOMAINS if domains_dict.get(d, {}).get("count", 0) > 0]
    if active_domains:
        expander_label = "🔍 حصر وتفصيل كلمات كل مجال (View Words by Domain)" if not compact else "🔍 حصر كلمات القائمة حسب المجال"
        with st.expander(expander_label, expanded=False):
            # Sort: specialized domains first (ordered by word count descending), then Basic / Neutral
            sorted_domains = sorted(
                active_domains,
                key=lambda x: (1 if x == "Basic / Neutral" else 0, -domains_dict.get(x, {}).get("count", 0))
            )

            cols = st.columns(2) if not compact else [st.container()]
            for idx, d in enumerate(sorted_domains):
                col = cols[idx % len(cols)] if not compact else cols[0]
                info = domains_dict.get(d, {})
                cnt = info.get("count", 0)
                pct = info.get("percent", 0.0)
                words = sorted(list(set(info.get("words", []))))
                cfg = DOMAIN_CONFIG.get(d, {})
                color = cfg.get("color", "var(--studio-muted)")
                bg = cfg.get("bg", "rgba(148, 163, 184, 0.08)")
                border = cfg.get("border", "rgba(148, 163, 184, 0.25)")
                emoji = icon_svg(d)
                label_ar = cfg.get("label_ar", d)

                chips_html = " ".join([
                    f'<span style="background: var(--studio-bg); color: var(--studio-ink); border: 1px solid {border}; '
                    f'border-radius: 6px; padding: 2px 8px; font-size: 0.8rem; font-family: monospace; display: inline-block;">'
                    f'{w}'
                    f'</span>'
                    for w in words
                ])

                card_html = f"""
                <div style="background: {bg}; border: 1px solid {border}; border-left: 4px solid {color}; border-radius: 8px; padding: 9px 12px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-size: 0.86rem; font-weight: 700; color: {color};">
                            {emoji} {d} <small style="opacity: 0.75; font-weight: normal;">({label_ar})</small>
                        </span>
                        <span style="background: var(--studio-bg); color: {color}; font-size: 0.76rem; font-weight: 700; padding: 1px 7px; border-radius: 10px; border: 1px solid {border};">
                            {cnt} words · {pct}%
                        </span>
                    </div>
                    <div style="display: flex; flex-wrap: wrap; gap: 5px;">
                        {chips_html}
                    </div>
                </div>
                """
                with col:
                    st.markdown(card_html, unsafe_allow_html=True)


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
