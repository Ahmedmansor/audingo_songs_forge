"""
tab6_suno_rights.py — Suno Monthly Quota & Commercial Rights Tracker.
Allows tracking and verifying which generated songs and versions have been unlocked/downloaded
from the monthly quota to guarantee full commercial ownership.
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
    # Also update any active checkbox keys in session_state
    for v in song.get("versions", []):
        t = v.get("title")
        if t:
            st.session_state[f"chk_rights_{t}"] = secured


def render_tab_suno_rights():
    """Render the Suno Quota & Commercial Rights Tracker tab."""
    _init_rights_state()
    manifest = load_manifest()
    songs = manifest.get("songs", [])

    if not songs:
        st.warning("لم يتم العثور على ملف `suno_library_manifest.json`. يرجى التأكد من تشغيل السكربت لتوليد المانيفست أولاً.")
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

    # 2. Controls, Search, and Filters
    c_search, c_filter, c_view = st.columns([4.5, 3.5, 2], vertical_alignment="bottom")

    with c_search:
        search_query = st.text_input(
            "بحث في الأغاني أو الإصدارات",
            placeholder="ابحث برقم الأغنية أو اسمها (مثل: 133, Signed, We Pulled, 58)...",
            key="rights_search_query",
        ).strip().lower()

    with c_filter:
        filter_mode = st.segmented_control(
            "تصفية الحالة",
            options=["الكل", "متبقي فقط", "مكتمل فقط"],
            default="الكل",
            key="rights_filter_mode",
            width="stretch"
        )

    with c_view:
        view_mode = st.segmented_control(
            "طريقة العرض",
            options=["حسب الأغنية", "قائمة الإصدارات"],
            default="حسب الأغنية",
            key="rights_view_mode",
            width="stretch"
        )

    # Filter logic
    filtered_songs = []
    for s in songs:
        s_num = str(s.get("number", "")).lower()
        s_name = str(s.get("name", "")).lower()
        versions = s.get("versions", [])

        # Match search query
        song_matches_search = (
            not search_query
            or search_query in s_num
            or search_query in s_name
            or any(search_query in str(v.get("title", "")).lower() for v in versions)
        )
        if not song_matches_search:
            continue

        # Match filter mode
        s_secured_count = sum(1 for v in versions if status.get(v.get("title", ""), {}).get("secured"))
        has_pending = s_secured_count < len(versions)
        has_secured = s_secured_count > 0

        if filter_mode == "متبقي فقط" and not has_pending:
            continue
        if filter_mode == "مكتمل فقط" and not has_secured:
            continue

        filtered_songs.append(s)

    st.caption(f"عرض **{len(filtered_songs)}** أغنية من أصل {len(songs)}")

    # 3. Render Content Based on View Mode
    if view_mode == "حسب الأغنية":
        _render_grouped_view(filtered_songs, status, search_query, filter_mode)
    else:
        _render_flat_tracks_view(filtered_songs, status, search_query, filter_mode)

    # 4. Export / Backup Toolbar
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


def _render_grouped_view(songs: List[Dict[str, Any]], status: Dict[str, Any], search_query: str, filter_mode: str):
    """Render songs grouped in expandable cards with version lists and batch actions."""
    for s in songs:
        s_num = s.get("number", "")
        s_name = s.get("name", "")
        folder = s.get("folder", "")
        versions = s.get("versions", [])

        s_count = sum(1 for v in versions if status.get(v.get("title", ""), {}).get("secured"))
        total_v = len(versions)

        # Song header badge
        if s_count == total_v:
            badge = "✅ حقوق كاملة (مكتمل)"
            border_style = "border-left: 4px solid #10B981;"
        elif s_count > 0:
            badge = f"⏳ جاري الفتح ({s_count}/{total_v})"
            border_style = "border-left: 4px solid #0066CC;"
        else:
            badge = f"⭕ متبقي بالكامل (0/{total_v})"
            border_style = "border-left: 4px solid #F59E0B;"

        expander_title = f"#{s_num} • {s_name}  ·  ({s_count}/{total_v} تم فتحهم)  ·  {badge}"

        with st.expander(expander_title, expanded=(s_count < total_v and len(songs) <= 5)):
            # Batch action buttons
            c_actions1, c_actions2, c_spacer = st.columns([2.5, 2.5, 5])
            with c_actions1:
                if st.button(
                    "✓ تحديد كل النسخ كـ مفتوحة",
                    key=f"btn_sec_all_{s_num}",
                    width="stretch",
                    disabled=(s_count == total_v),
                    help=f"فتح حقوق جميع الـ {total_v} إصدارات لهذه الأغنية بضغطة واحدة"
                ):
                    _mark_song_all(s, True)
                    st.rerun()

            with c_actions2:
                if st.button(
                    "✕ إلغاء تحديد الكل",
                    key=f"btn_unsec_all_{s_num}",
                    width="stretch",
                    disabled=(s_count == 0),
                    help="إلغاء تحديد كل الإصدارات لهذه الأغنية"
                ):
                    _mark_song_all(s, False)
                    st.rerun()

            st.write("")

            # Render versions
            for v in versions:
                v_title = v.get("title", "")
                v_ver = v.get("version", "")
                dur_str = v.get("suno_duration_str", "")
                local_f = v.get("local_file", "")
                is_secured = bool(status.get(v_title, {}).get("secured"))

                # Filter condition inside song if active
                if filter_mode == "متبقي فقط" and is_secured:
                    continue
                if filter_mode == "مكتمل فقط" and not is_secured:
                    continue

                c_chk, c_copy, c_audio = st.columns([6, 2, 2], vertical_alignment="center")

                with c_chk:
                    chk_key = f"chk_rights_{v_title}"
                    st.checkbox(
                        f"**{v_title}**  ·  ⏱️ {dur_str}",
                        value=is_secured,
                        key=chk_key,
                        on_change=_on_toggle_track,
                        args=(v_title,),
                        help="اضغط هنا لتأكيد أنك قمت بفتح/تحميل هذه النسخة من كوتا سونو وضمان حقوقها",
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
                        st.caption("الملف غير متوفر محلياً")


def _render_flat_tracks_view(songs: List[Dict[str, Any]], status: Dict[str, Any], search_query: str, filter_mode: str):
    """Render a flat, linear track list across all matching songs for quick batch review."""
    flat_tracks = []
    for s in songs:
        folder = s.get("folder", "")
        for v in s.get("versions", []):
            v_title = v.get("title", "")
            is_secured = bool(status.get(v_title, {}).get("secured"))

            if filter_mode == "متبقي فقط" and is_secured:
                continue
            if filter_mode == "مكتمل فقط" and not is_secured:
                continue
            if search_query and search_query not in v_title.lower() and search_query not in s.get("name", "").lower():
                continue

            flat_tracks.append((s, v, folder, is_secured))

    st.caption(f"إجمالي الإصدارات المعروضة: **{len(flat_tracks)}** إصدار")

    if not flat_tracks:
        st.info("لا توجد إصدارات مطابقة للتصفية الحالية.")
        return

    for s, v, folder, is_secured in flat_tracks:
        v_title = v.get("title", "")
        dur_str = v.get("suno_duration_str", "")
        local_f = v.get("local_file", "")

        c_chk, c_copy, c_audio = st.columns([6, 2, 2], vertical_alignment="center")

        with c_chk:
            chk_key = f"chk_rights_{v_title}"
            st.checkbox(
                f"**{v_title}**  ·  ⏱️ {dur_str}  ·  ({s.get('name')})",
                value=is_secured,
                key=chk_key,
                on_change=_on_toggle_track,
                args=(v_title,),
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
                st.caption("غير متوفر")
