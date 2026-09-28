"""
Insights (Feature 16) + Proactive Intelligence (Feature 17).

Every insight is a directly computed observation over real, existing
data - duplicates, low confidence, recent contradictions, profile
gaps, unindexed documents. Nothing here is a guess about the user;
consistent with graph/timeline/profile, if it isn't computable from
stored facts, it isn't an insight. These are suggestions only -
nothing here modifies any data.
"""

from backend.services.memory_service import get_memories_detailed, get_contradictions
from backend.services.profile_service import build_profile
from backend.documents.document_service import list_documents

LOW_CONFIDENCE_THRESHOLD = 0.5
RECENT_CONTRADICTIONS_LIMIT = 5


def generate_insights(user_id=None):
    insights = []

    memories = get_memories_detailed(include_inactive=False, user_id=user_id)

    # ---------------- Duplicate memories ----------------
    seen_text = {}
    for m in memories:
        key = m["memory"].strip().lower()
        seen_text.setdefault(key, []).append(m)

    for key, group in seen_text.items():
        if len(group) > 1:
            insights.append({
                "type": "duplicate_memory",
                "severity": "low",
                "message": f'You have {len(group)} duplicate memories saved for: "{group[0]["memory"]}"',
                "memory_ids": [m["id"] for m in group],
            })

    # ---------------- Low-confidence facts ----------------
    low_confidence = [m for m in memories if (m["confidence"] or 1.0) < LOW_CONFIDENCE_THRESHOLD]
    if low_confidence:
        insights.append({
            "type": "low_confidence_facts",
            "severity": "medium",
            "message": (
                f"{len(low_confidence)} saved fact(s) were stated vaguely and have low "
                "confidence - you may want to confirm or correct them in the Memory Center."
            ),
            "memory_ids": [m["id"] for m in low_confidence],
        })

    # ---------------- Recent contradictions ----------------
    contradictions = get_contradictions(limit=RECENT_CONTRADICTIONS_LIMIT, user_id=user_id)
    for c in contradictions:
        insights.append({
            "type": "recent_contradiction",
            "severity": "medium",
            "message": (
                f'Your {c["memory_type"] or "saved"} info changed: '
                f'"{c["previous_value"]}" -> "{c["current_value"]}"'
            ),
            "memory_id": c["memory_id"],
            "changed_at": c["changed_at"],
        })

    # ---------------- Profile gaps ----------------
    profile = build_profile(user_id=user_id)
    if profile["missing_sections"]:
        insights.append({
            "type": "profile_gap",
            "severity": "low",
            "message": (
                "Your profile has no information yet about: "
                + ", ".join(s["label"] for s in profile["missing_sections"])
            ),
        })

    # ---------------- Unindexed documents ----------------
    documents = list_documents(user_id=user_id)
    unindexed = [d for d in documents if not d["indexed"]]
    for doc in unindexed:
        insights.append({
            "type": "unindexed_document",
            "severity": "high",
            "message": f'"{doc["filename"]}" has no indexed content, so it can\'t be searched or answered from.',
            "document_id": doc["id"],
        })

    missing_files = [d for d in documents if not d["file_exists"]]
    for doc in missing_files:
        insights.append({
            "type": "missing_document_file",
            "severity": "high",
            "message": f'"{doc["filename"]}" is recorded but the file is missing on disk.',
            "document_id": doc["id"],
        })

    return insights
