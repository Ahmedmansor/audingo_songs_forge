"""
dialogs.py — Modal confirmation dialogs for deleting songs, deleting variants, and overwriting packages.
"""

import streamlit as st
import db
import gemini_client


@st.dialog("⚠️ Confirm Song Deletion")
def confirm_delete_song_dialog(song_id: int, song_title: str, row_num: int):
    """Safety confirmation modal before executing atomic delete and rollback."""
    st.markdown(f"#### 🗑️ Are you sure you want to delete Song #{row_num}?")
    st.warning(
        f"**Song Title:** {song_title}\n\n"
        f"⚠️ **Atomic Safe Rollback will occur:**\n"
        f"- Target & Bonus vocabulary will have their `usage_count` decremented (-1) in the NGSL dictionary.\n"
        f"- Non-NGSL extra words will have their occurrences decremented (-1).\n"
        f"- The song and all its recorded metadata will be permanently removed."
    )
    dlg_c1, dlg_c2 = st.columns(2)
    with dlg_c1:
        if st.button("🔥 Yes, Confirm Delete", type="primary", use_container_width=True, key=f"dlg_confirm_del_{song_id}"):
            if db.delete_song(song_id, rollback_words=True):
                st.session_state["lib_toast_msg"] = f"Song #{row_num} ('{song_title}') deleted and dictionary counters rolled back."
                st.rerun()
    with dlg_c2:
        if st.button("❌ Cancel", use_container_width=True, key=f"dlg_cancel_del_{song_id}"):
            st.rerun()


@st.dialog("⚠️ Confirm Track Variant Deletion")
def confirm_delete_variant_dialog(variant_id: int, genre: str, vocalist: str):
    """Safety confirmation modal before deleting a track variant package."""
    st.markdown("#### 🗑️ Delete Track Variant Package?")
    st.warning(
        f"Are you sure you want to delete the production package for **{genre}** ({vocalist})?\n\n"
        f"This will permanently delete both the Suno music prompt and the poster art prompt. This action cannot be undone."
    )
    dlg_c1, dlg_c2 = st.columns(2)
    with dlg_c1:
        if st.button("🔥 Yes, Delete Variant", type="primary", use_container_width=True, key=f"dlg_confirm_del_variant_{variant_id}"):
            if db.delete_track_variant(variant_id):
                st.session_state["lib_toast_msg"] = f"Track variant for '{genre}' ({vocalist}) was deleted."
                st.rerun()
    with dlg_c2:
        if st.button("❌ Cancel", use_container_width=True, key=f"dlg_cancel_del_variant_{variant_id}"):
            st.rerun()


@st.dialog("⚠️ Warning: Style Package Already Exists")
def confirm_overwrite_variant_dialog(song_id: int, song_title: str, lyrics_text: str, genre: str, vocalist: str):
    """Safety confirmation modal before overwriting an existing track variant."""
    st.markdown("#### ⚠️ Style Package Already Exists!")
    st.warning(
        f"A production package for **'{song_title}'** in **{genre}** with **{vocalist}** vocals already exists.\n\n"
        f"Generating a new package will **overwrite** both the current Suno music prompt and Midjourney/DALL-E poster prompt with freshly generated versions.\n\n"
        f"Are you sure you want to proceed and overwrite?"
    )
    dlg_c1, dlg_c2 = st.columns(2)
    clean_g = "".join(c for c in genre if c.isalnum())
    with dlg_c1:
        if st.button("⚡ Yes, Overwrite & Regenerate", type="primary", use_container_width=True, key=f"dlg_confirm_ovr_{song_id}_{clean_g}_{vocalist}"):
            with st.spinner(f"Generating new package for '{genre}' ({vocalist})..."):
                res = gemini_client.generate_track_variant(
                    title=song_title,
                    lyrics=lyrics_text,
                    genre=genre,
                    vocalist=vocalist
                )
                if res.get("success"):
                    new_suno_p = res.get("suno_prompt", "").strip()
                    new_poster_p = res.get("poster_prompt", "").strip()
                    db.upsert_track_variant(
                        song_id=song_id,
                        genre=genre,
                        vocalist=vocalist,
                        suno_prompt=new_suno_p,
                        poster_prompt=new_poster_p
                    )
                    st.session_state["lib_toast_msg"] = f"Track package for '{genre}' ({vocalist}) overwritten & updated!"
                    st.rerun()
                else:
                    st.error(f"Failed to generate package: {res.get('error')}")
    with dlg_c2:
        if st.button("❌ Cancel", use_container_width=True, key=f"dlg_cancel_ovr_{song_id}_{clean_g}_{vocalist}"):
            st.rerun()
