"""A visible appearance button backed by Streamlit's native theme switcher.

Streamlit 1.63 has no public Python setter for the browser's theme. Keep the
small frontend adapter here, using its stable test IDs rather than React internals.
Native theme selection preserves widgets and persists the browser preference.
"""
import streamlit as st
from presentation.theme import LIGHT, DARK

_SWITCH = st.components.v2.component(
    "audingo_appearance",
    html='<button type="button" id="appearance"></button><span id="notice" role="status"></span>',
    css="""
    button { display:flex; align-items:center; justify-content:center; gap:8px;
      width:100%; min-height:44px; padding:10px 16px; border-radius:24px;
      border:1px solid var(--st-border-color); background:var(--st-secondary-background-color);
      color:var(--st-text-color); font:500 14px var(--st-font); cursor:pointer; }
    button:hover { border-color:var(--st-primary-color); }
    button:focus-visible { outline:3px solid var(--st-primary-color); outline-offset:2px; }
    #notice { display:block; font:12px var(--st-font); color:var(--st-text-color); }
    """,
    js="""
    export default function ({parentElement, data, setStateValue}) {
      const button = parentElement.querySelector('#appearance');
      const notice = parentElement.querySelector('#notice');
      const doc = parentElement.ownerDocument;
      const key = 'audingo-appearance';
      const applyTokens = mode => {
        for (const [name, value] of Object.entries(data.palettes[mode])) {
          doc.documentElement.style.setProperty('--studio-' + name, value);
        }
      };
      const pending = doc.documentElement.dataset.audingoPendingTheme;
      const currentMode = pending || data.mode;
      applyTokens(currentMode);
      if (pending === data.mode) delete doc.documentElement.dataset.audingoPendingTheme;
      let observer, timer;
      function setLabel(mode) {
        const path = mode === 'dark'
          ? '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/>'
          : '<path d="M20 15a9 9 0 0 1-11-11 9 9 0 1 0 11 11Z"/>';
        button.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true">' + path + '</svg><span>' + (mode === 'dark' ? 'Light theme' : 'Dark theme') + '</span>';
        button.setAttribute('aria-label', mode === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
      }
      setLabel(currentMode);
      const stop = () => { observer?.disconnect(); clearTimeout(timer); };
      function select(mode) {
        stop();
        button.disabled = true;
        const nativeButton = doc.querySelector('[data-testid="stMainMenuButton"]');
        if (!nativeButton) { fallback(); return; }
        function choose() {
          const choice = doc.querySelector(`[data-testid="stMainMenuItem-theme-${mode === 'dark' ? 'Dark' : 'Light'}"]`);
          if (!choice) return false;
          stop();
          doc.documentElement.dataset.audingoPendingTheme = mode;
          applyTokens(mode);
          choice.click();
          if (nativeButton.getAttribute('aria-expanded') === 'true') nativeButton.click();
          try { localStorage.setItem(key, mode); } catch (_) {}
          button.disabled = false;
          setLabel(mode);
          button.focus({preventScroll:true});
          // Wait for the native React theme commit before sending client context.
          requestAnimationFrame(() => requestAnimationFrame(() => setStateValue('mode', mode)));
          return true;
        }
        function fallback() {
          stop(); button.disabled = false;
          notice.textContent = 'Choose Light or Dark in the main menu above.';
        }
        observer = new MutationObserver(choose);
        observer.observe(doc.body, {childList:true, subtree:true});
        if (nativeButton.getAttribute('aria-expanded') !== 'true') nativeButton.click();
        if (!choose()) timer = setTimeout(fallback, 2000);
      }
      button.onclick = () => select(currentMode === 'dark' ? 'light' : 'dark');
      // Default to dark once; respect subsequent browser choices.
      let preference;
      try { preference = localStorage.getItem(key); } catch (_) {}
      if (!preference && data.mode !== 'dark') select('dark');
      else if (!preference) { try { localStorage.setItem(key, 'dark'); } catch (_) {} }
      return stop;
    }
    """,
)


def render_appearance_switch():
    """Mount before applying presentation tokens so a click updates this rerun."""
    with st.sidebar:
        mode = st.context.theme.type or "dark"
        _SWITCH(data={"mode": mode, "palettes": {"light": LIGHT, "dark": DARK}},
                key="appearance", on_mode_change=lambda: None)
    st.session_state["ui_theme_mode"] = mode
