"""
tab6_suno_rights.py — Suno Monthly Quota & Commercial Rights Tracker.
Allows tracking and verifying which generated songs and versions have been unlocked/downloaded
from the monthly quota to guarantee full commercial ownership.

Optimized for ultra-fast, zero-lag performance using focused Song Inspector and on-demand audio rendering.
"""

import json
from html import escape
from typing import Dict, Any, List
import streamlit as st

from data.services.suno_rights_service import (
    load_manifest,
    load_rights_status,
    save_rights_status,
    toggle_track_rights,
    set_song_all_tracks,
    calculate_metrics,
    get_audio_file_path,
)
from presentation.components.identity import icon_svg


def _init_rights_state():
    if "suno_rights_status" not in st.session_state:
        st.session_state["suno_rights_status"] = load_rights_status()


def _on_toggle_track(track_title: str):
    key = f"chk_rights_{track_title}"
    val = st.session_state.get(key, False)
    toggle_track_rights(track_title, val)
    st.session_state["suno_rights_status"] = load_rights_status()


def _mark_song_all(song: Dict[str, Any], secured: bool):
    set_song_all_tracks(song, secured)
    st.session_state["suno_rights_status"] = load_rights_status()
    for v in song.get("versions", []):
        t = v.get("title")
        if t:
            st.session_state[f"chk_rights_{t}"] = secured


def render_tab_suno_rights():
    """Render the high-performance Suno Quota & Commercial Rights Tracker tab."""
    _init_rights_state()
    manifest = load_manifest()
    songs = manifest.get("songs", [])

    if not songs:
        st.warning("لم يتم العثور على ملف `suno_library_manifest.json`. يرجى التأكد من مسار المانيفست أولاً.")
        return

    status = st.session_state["suno_rights_status"]
    metrics = calculate_metrics(manifest, status)

    # 1. Hero Card & Statistics
    pct = metrics["progress_pct"]
    bar_color = "#10B981" if pct == 100 else ("#0066CC" if pct >= 50 else "#855600")

    st.html(f'''<article class="library-song-card" style="margin-bottom: 20px;">
<div class="library-song-heading">
  <div class="library-song-identity">
    <span class="library-song-mark">{icon_svg()}</span>
    <div class="library-song-meta">
      <div class="studio-eyebrow">AUDINGO / COMMERCIAL RIGHTS & QUOTA TRACKER</div>
      <div class="library-title-row">
        <h3>Suno Commercial Rights Tracker</h3>
        <span style="background: rgba(0, 102, 204, 0.12); color: #0066CC; border: 1px solid rgba(0, 102, 204, 0.3); padding: 2px 10px; border-radius: 9999px; font-size: 0.76rem; font-weight: 700;">
          Quota Rights Mode
        </span>
      </div>
      <p>تتبع فتح وتحميل إصدارات الأغاني من الكوتا الشهرية لضمان حقوق الملكية والاستخدام التجاري الكامل للأغاني</p>
    </div>
  </div>
</div>

<div class="suno-rights-progress-wrapper" style="margin-top: 18px; padding-top: 14px; border-top: 1px solid var(--studio-line);">
  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 0.85rem; font-weight: 600;">
    <span>إجمالي الحقوق المفتوحة من الكوتا: <strong style="color: {bar_color};">{metrics['secured_tracks']}</strong> / {metrics['total_tracks']} إصدار</span>
    <span style="color: {bar_color}; font-variant-numeric: tabular-nums;">{pct}% مكتمل</span>
  </div>
  <div style="height: 8px; border-radius: 6px; background: rgba(255, 255, 255, 0.08); overflow: hidden;">
    <div style="width: {pct}%; height: 100%; border-radius: 6px; background: {bar_color}; transition: width 0.3s ease;"></div>
  </div>
</div>

<div class="library-song-stats">
  <div class="library-stat-total"><b>{metrics['total_songs']}</b><span>إجمالي الأغاني</span></div>
  <div class="library-stat-authenticity"><b>{metrics['total_tracks']}</b><span>إجمالي الإصدارات</span></div>
  <div class="library-stat-target"><b style="color: #10B981;">{metrics['secured_tracks']}</b><span>تم فتح الحقوق ✅</span></div>
  <div class="library-stat-extra"><b style="color: #F59E0B;">{metrics['pending_tracks']}</b><span>متبقي للفتح ⏳</span></div>
  <div class="library-stat-bonus"><b style="color: #6366F1;">{metrics['fully_secured_songs']}</b><span>أغاني مكتملة 100%</span></div>
</div>
</article>''')

    # 2. View Mode Selector
    view_mode = st.segmented_control(
        "نظام العرض",
        options=["فحص أغنية محددة (Song Inspector)", "دليل كل الأغاني (Directory Overview)"],
        default="فحص أغنية محددة (Song Inspector)",
        key="suno_rights_view_mode",
        width="stretch",
    )

    if view_mode == "فحص أغنية محددة (Song Inspector)":
        _render_song_inspector(songs, status)
    else:
        _render_directory_overview(songs, status)

    # 3. Export / Backup Toolbar
    st.divider()
    c_exp1, c_exp2 = st.columns([3, 7], vertical_alignment="center")
    with c_exp1:
        st.download_button(
            label="📥 تصدير تقرير الحقوق (JSON)",
            data=json.dumps(status, indent=2, ensure_ascii=False),
            file_name="suno_rights_status.json",
            mime="application/json",
            width="stretch",
            help="تحميل نسخة احتياطية من حالة جميع الأغاني والإصدارات المحفوظة",
        )
    with c_exp2:
        st.caption("يتم حفظ جميع التغييرات تلقائياً وبشكل فوري في ملف `suno_rights_status.json` على جهازك.")


def _render_song_inspector(songs: List[Dict[str, Any]], status: Dict[str, Any]):
    """Focused, instant view showing 1 song at a time with Prev/Next arrows."""
    song_map = {str(s.get("number")): s for s in songs}
    song_keys = list(song_map.keys())

    if "rights_inspector_song" not in st.session_state or st.session_state["rights_inspector_song"] not in song_keys:
        st.session_state["rights_inspector_song"] = song_keys[0]

    curr_key = st.session_state["rights_inspector_song"]
    try:
        curr_idx = song_keys.index(curr_key)
    except ValueError:
        curr_idx = 0
        st.session_state["rights_inspector_song"] = song_keys[0]

    def _go_prev():
        c_k = st.session_state.get("rights_inspector_song")
        idx = song_keys.index(c_k) if c_k in song_keys else 0
        if idx > 0:
            st.session_state["rights_inspector_song"] = song_keys[idx - 1]

    def _go_next():
        c_k = st.session_state.get("rights_inspector_song")
        idx = song_keys.index(c_k) if c_k in song_keys else 0
        if idx < len(song_keys) - 1:
            st.session_state["rights_inspector_song"] = song_keys[idx + 1]

    def _format_option(k: str) -> str:
        s = song_map.get(k, {})
        s_num = s.get("number", "")
        s_name = s.get("name", "")
        versions = s.get("versions", [])
        s_count = sum(1 for v in versions if status.get(v.get("title", ""), {}).get("secured"))
        total_v = len(versions)
        status_flag = "✅ مكتمل" if s_count == total_v else (f"⏳ {s_count}/{total_v}" if s_count > 0 else f"⭕ 0/{total_v}")
        return f"#{s_num} • {s_name}  ·  ({status_flag})"

    c_prev, c_sel, c_next = st.columns([0.8, 8.4, 0.8], vertical_alignment="bottom")
    with c_prev:
        st.button(
            "",
            icon=":material/arrow_back:",
            key="btn_rights_prev_song",
            on_click=_go_prev,
            disabled=(curr_idx <= 0),
            help="Previous song (الأغنية السابقة)",
            width="stretch",
        )
    with c_sel:
        selected_song_num = st.selectbox(
            "اختر أغنية لفحص إصداراتها",
            options=song_keys,
            format_func=_format_option,
            key="rights_inspector_song",
        )
    with c_next:
        st.button(
            "",
            icon=":material/arrow_forward:",
            key="btn_rights_next_song",
            on_click=_go_next,
            disabled=(curr_idx >= len(song_keys) - 1),
            help="Next song (الأغنية التالية)",
            width="stretch",
        )

    # Render Active Song Details
    selected_song = song_map[selected_song_num]
    s_num = selected_song.get("number", "")
    s_name = selected_song.get("name", "")
    folder = selected_song.get("folder", "")
    versions = selected_song.get("versions", [])

    s_count = sum(1 for v in versions if status.get(v.get("title", ""), {}).get("secured"))
    total_v = len(versions)

    # Header Card for Selected Song
    if s_count == total_v:
        badge_html = f'<span style="background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.35); padding: 3px 12px; border-radius: 9999px; font-size: 0.82rem; font-weight: 700;">✅ Full Rights Secured ({s_count}/{total_v})</span>'
    elif s_count > 0:
        badge_html = f'<span style="background: rgba(0, 102, 204, 0.15); color: #0066CC; border: 1px solid rgba(0, 102, 204, 0.35); padding: 3px 12px; border-radius: 9999px; font-size: 0.82rem; font-weight: 700;">⏳ In Progress ({s_count}/{total_v} Secured)</span>'
    else:
        badge_html = f'<span style="background: rgba(245, 158, 11, 0.15); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.35); padding: 3px 12px; border-radius: 9999px; font-size: 0.82rem; font-weight: 700;">⭕ Pending All ({total_v} versions)</span>'

    st.html(f'''<div style="background: var(--studio-surface); border: 1px solid var(--studio-line); border-radius: 16px; padding: 18px 22px; margin: 14px 0;">
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
  <div>
    <div class="studio-eyebrow">SONG #{s_num} / AUDINGO QUOTA CHECK</div>
    <h3 style="margin: 2px 0 0; color: var(--studio-ink); font-size: 1.45rem;">{escape(s_name)}</h3>
  </div>
  <div>{badge_html}</div>
</div>
</div>''')

    # Batch Actions for this song
    c_btn1, c_btn2, c_sp = st.columns([2.5, 2.5, 5])
    with c_btn1:
        if st.button(
            "✓ تحديد كل النسخ كـ مفتوحة",
            key=f"btn_mark_all_{s_num}",
            width="stretch",
            disabled=(s_count == total_v),
            help=f"فتح حقوق جميع الـ {total_v} إصدارات لهذه الأغنية بضغطة واحدة",
        ):
            _mark_song_all(selected_song, True)
            st.rerun()
    with c_btn2:
        if st.button(
            "✕ إلغاء تحديد الكل",
            key=f"btn_unmark_all_{s_num}",
            width="stretch",
            disabled=(s_count == 0),
            help="إلغاء تحديد كل الإصدارات لهذه الأغنية",
        ):
            _mark_song_all(selected_song, False)
            st.rerun()

    st.write("")

    # Versions List for this song
    for v in versions:
        v_title = str(v.get("title") or "")
        dur_str = str(v.get("suno_duration_str") or "--:--")
        local_f = v.get("local_file")
        is_secured = bool(status.get(v_title, {}).get("secured"))

        c_chk, c_copy, c_audio = st.columns([5.5, 2.5, 2], vertical_alignment="center")

        with c_chk:
            chk_key = f"chk_rights_{v_title}"
            st.checkbox(
                f"**{v_title}**  ·  ⏱️ {dur_str}",
                value=is_secured,
                key=chk_key,
                on_change=_on_toggle_track,
                args=(v_title,),
                help="حدد لتأكيد فتحك لهذه النسخة من كوتا سونو وضمان حقوقها",
            )

        with c_copy:
            title_escaped = escape(v_title)
            st.html(f'''<button class="library-copy-title-btn" type="button" title="نسخ اسم الإصدار للبحث عنه في سونو" data-title="{title_escaped}" onclick="(function(btn){{
                const t = btn.getAttribute('data-title');
                const lbl = btn.querySelector('.lib-copy-lbl');
                function success(){{
                    btn.classList.add('copied');
                    if (lbl) lbl.textContent = 'Copied!';
                    setTimeout(function(){{
                        btn.classList.remove('copied');
                        if (lbl) lbl.textContent = 'Copy for Suno';
                    }}, 1800);
                }}
                if (navigator.clipboard && navigator.clipboard.writeText) {{
                    navigator.clipboard.writeText(t).then(success).catch(function(){{
                        const ta = document.createElement('textarea');
                        ta.value = t;
                        document.body.appendChild(ta);
                        ta.select();
                        document.execCommand('copy');
                        document.body.removeChild(ta);
                        success();
                    }});
                }} else {{
                    const ta = document.createElement('textarea');
                    ta.value = t;
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand('copy');
                    document.body.removeChild(ta);
                    success();
                }}
            }})(this)">
                <svg class="copy-icon" viewBox="0 0 24 24" width="13" height="13" stroke="currentColor" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                </svg>
                <svg class="check-icon" viewBox="0 0 24 24" width="13" height="13" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <span class="lib-copy-lbl">Copy for Suno</span>
            </button>''')

        with c_audio:
            audio_path = get_audio_file_path(folder, local_f)
            if audio_path:
                with st.popover("🎧 استماع", width="stretch"):
                    st.caption(f"تشغيل: {v_title}")
                    st.audio(audio_path)
            else:
                st.caption("—")


def _render_directory_overview(songs: List[Dict[str, Any]], status: Dict[str, Any]):
    """Lightweight, fast directory view of all 133 songs with search and pagination."""
    c_search, c_filter = st.columns([6, 4], vertical_alignment="bottom")
    with c_search:
        q = st.text_input(
            "بحث في الأغاني",
            placeholder="ابحث برقم الأغنية أو اسمها (مثل: 133, Signed, 58)...",
            key="rights_dir_search",
        ).strip().lower()

    with c_filter:
        f_mode = st.segmented_control(
            "تصفية الحالة",
            options=["الكل", "متبقي فقط", "مكتمل فقط"],
            default="الكل",
            key="rights_dir_filter",
            width="stretch",
        )

    matched_songs = []
    for s in songs:
        s_num = str(s.get("number", "")).lower()
        s_name = str(s.get("name", "")).lower()
        versions = s.get("versions", [])

        if q and q not in s_num and q not in s_name:
            continue

        s_count = sum(1 for v in versions if status.get(v.get("title", ""), {}).get("secured"))
        total_v = len(versions)

        if f_mode == "متبقي فقط" and s_count == total_v:
            continue
        if f_mode == "مكتمل فقط" and s_count == 0:
            continue

        matched_songs.append((s, s_count, total_v))

    st.caption(f"تم العثور على **{len(matched_songs)}** أغنية")

    if not matched_songs:
        st.info("لا توجد نتائج مطابقة لبحثك.")
        return

    # Pagination: 15 songs per page
    PAGE_SIZE = 15
    total_pages = max(1, (len(matched_songs) + PAGE_SIZE - 1) // PAGE_SIZE)
    curr_page = 1
    if total_pages > 1:
        c_p1, c_p2 = st.columns([3, 7], vertical_alignment="center")
        with c_p1:
            curr_page = st.number_input(f"الصفحة (من {total_pages})", min_value=1, max_value=total_pages, value=1, step=1, key="rights_dir_page")
        with c_p2:
            st.caption(f"عرض الأغاني من {(curr_page-1)*PAGE_SIZE + 1} إلى {min(curr_page*PAGE_SIZE, len(matched_songs))}")

    start_idx = (curr_page - 1) * PAGE_SIZE
    page_songs = matched_songs[start_idx : start_idx + PAGE_SIZE]

    # Compact directory list
    for s, s_count, total_v in page_songs:
        s_num = s.get("number", "")
        s_name = s.get("name", "")
        pct = round(s_count / total_v * 100) if total_v > 0 else 0

        c_info, c_stat, c_act = st.columns([5, 3, 2], vertical_alignment="center")

        with c_info:
            st.markdown(f"**#{s_num} • {s_name}**")
            st.caption(f"{total_v} إصدارات")

        with c_stat:
            if s_count == total_v:
                st.markdown(f"<span style='color: #10B981; font-weight: 700;'>✅ مكتمل ({s_count}/{total_v})</span>", unsafe_allow_html=True)
            elif s_count > 0:
                st.markdown(f"<span style='color: #0066CC; font-weight: 700;'>⏳ {s_count}/{total_v} ({pct}%)</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color: #F59E0B; font-weight: 700;'>⭕ 0/{total_v} متبقي</span>", unsafe_allow_html=True)

        with c_act:
            def _select_song_to_inspect(num=s_num):
                st.session_state["rights_inspector_song"] = str(num)
                st.session_state["suno_rights_view_mode"] = "فحص أغنية محددة (Song Inspector)"

            st.button("فحص الأغنية 🔎", key=f"btn_open_song_{s_num}", on_click=_select_song_to_inspect, width="stretch")

        st.markdown("<hr style='margin: 4px 0; border: none; border-top: 1px solid rgba(255, 255, 255, 0.05);'>", unsafe_allow_html=True)
