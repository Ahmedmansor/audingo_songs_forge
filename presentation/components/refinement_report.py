"""Read-only, theme-aware view of the critic snapshot saved with a song."""

import json
import streamlit as st
from domain.services.refinement_archive import parse_refinement_snapshot, report_matches_lyrics


def render_saved_refinement_report(raw, lyrics: str, song_id: int):
    st.markdown("##### :material/fact_check: Saved refinement & critic report")
    snapshot = parse_refinement_snapshot(raw)
    if snapshot is None:
        st.caption("لا يوجد تقرير ناقد محفوظ مع هذه الأغنية.")
        return

    report = snapshot["report"]
    if not report_matches_lyrics(snapshot, lyrics):
        st.warning("كلمات الأغنية اتعدلت بعد حفظ النقد. التقرير أدناه يخص النسخة التي قيّمها الناقد، وليس الكلمات الحالية.")
    mode = "Critic only" if snapshot.get("mode") == "critic_only" else "Refinement pipeline"
    st.caption(f"{mode} · {report.get('critic_name') or 'Critic'} · {report.get('domain') or 'Unspecified domain'}")
    a, b = st.columns(2)
    a.metric("Authenticity score", f"{report.get('overall_score', 0)}%")
    model = report.get("model_used") or report.get("final_model_used") or "Not recorded"
    b.metric("Model", model)
    if report.get("evaluated_at"):
        st.caption(f"Evaluated: {report['evaluated_at']}")
    st.caption(f"Archived: {snapshot.get('archived_at', 'Not recorded')}")
    rows = []
    for index, item in enumerate(report.get("line_breakdown", []), 1):
        score = item.get("score", 0)
        try:
            value = int(round(float(score)))
        except (ValueError, TypeError):
            value = 0
        status = "🟢 Passed" if value >= 90 else "🟡 Review" if value >= 75 else "🔴 Rewrite"
        rows.append({
            "Line #": item.get("number", index),
            "Lyrics": item.get("line", ""),
            "Score (%)": value,
            "Status": status,
            "Critic feedback": item.get("comment") or item.get("issue") or "none",
        })
    st.dataframe(rows, hide_index=True, width="stretch", key=f"saved_critic_lines_{song_id}")
    dropped = report.get("words_dropped") or report.get("dropped_words") or []
    if dropped:
        st.write("**Words flagged / dropped:** " + ", ".join(dropped))
    context = report.get("context")
    if context:
        with st.expander("Context used by the critic"):
            st.json(context)
    if "iterations_used" in report:
        st.caption(f"Iterations: {report['iterations_used']} · API requests: {report.get('total_requests', 0)}")
    with st.expander("Lyrics evaluated by the critic"):
        st.code(snapshot.get("evaluated_lyrics", ""), language=None)
    with st.expander("Full saved report"):
        st.json(snapshot)
    st.download_button(
        "Download critic report", data=json.dumps(snapshot, ensure_ascii=False, indent=2),
        file_name=f"song_{song_id}_critic_report.json", mime="application/json",
        key=f"download_critic_{song_id}", icon=":material/download:",
    )
