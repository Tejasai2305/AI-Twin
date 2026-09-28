"""
Dashboard (Feature 15).

Pure aggregation layer: every number here is computed by calling the
service that already owns that data (memory_service, graph_service,
timeline_service, document_service, profile_service). This file adds
no new source of truth - it only composes existing ones, so nothing
can drift out of sync with the real Memory Center / Graph / Timeline
pages.
"""

from backend.database.database import get_connection
from backend.services.memory_service import get_memories_detailed
from backend.services.graph_service import get_graph_summary
from backend.services.timeline_service import get_timeline
from backend.services.profile_service import build_profile
from backend.documents.document_service import list_documents


def build_dashboard(user_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("SELECT COUNT(*) FROM conversations WHERE user_id = ?", (user_id,))
    else:
        cursor.execute("SELECT COUNT(*) FROM conversations WHERE user_id IS NULL")
    conversation_count = cursor.fetchone()[0]
    conn.close()

    memories = get_memories_detailed(include_inactive=False, user_id=user_id)
    documents = list_documents(user_id=user_id)
    graph_summary = get_graph_summary(user_id=user_id)
    profile = build_profile(user_id=user_id)
    recent_activity = get_timeline(limit=8, user_id=user_id)

    # A lightweight "skills" and "projects" count, since those are
    # named explicitly in the brief as dashboard cards - both are
    # just memory_type slices, not a new data source.
    skill_count = sum(1 for m in memories if m["memory_type"] == "technical_skill")
    project_count = sum(1 for m in memories if m["memory_type"] == "project")

    return {
        "totals": {
            "conversations": conversation_count,
            "memories": len(memories),
            "documents": len(documents),
            "skills": skill_count,
            "projects": project_count,
        },
        "graph_summary": graph_summary,
        "profile_summary": {
            "total_facts": profile["total_facts"],
            "sections_present": [s["label"] for s in profile["sections"]],
            "sections_missing": [s["label"] for s in profile["missing_sections"]],
        },
        "recent_activity": recent_activity,
    }
