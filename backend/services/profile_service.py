"""
AI Twin Profile (Feature 11).

Grounding rule (same principle as graph_service.py and
timeline_service.py): the profile is assembled live from active,
verified memories. Nothing here is invented - a section is empty if
there is no memory of that type, rather than being filled with a
guess. "Editing" the profile means editing the underlying memory
(via the Memory Center / existing memory endpoints), so this stays
a single source of truth instead of a second copy of the same facts.
"""

from backend.services.memory_service import get_memories_detailed

# memory_type -> profile section label
SECTION_LABELS = {
    "personal": "About",
    "education": "Education",
    "career": "Career",
    "technical_skill": "Technical Skills",
    "project": "Projects",
    "experience": "Experience / Internships",
    "achievement": "Achievements",
    "goal": "Goals",
    "preference": "Interests & Preferences",
    "contact": "Contact",
    "other": "Other",
}

# Display order for the profile page.
SECTION_ORDER = [
    "personal", "education", "career", "experience", "project",
    "technical_skill", "achievement", "goal", "preference",
    "contact", "other",
]


def build_profile(user_id=None):
    memories = get_memories_detailed(include_inactive=False, user_id=user_id)

    sections = {
        key: {
            "type": key,
            "label": SECTION_LABELS[key],
            "items": [],
        }
        for key in SECTION_ORDER
    }

    for memory in memories:
        section_key = memory["memory_type"] if memory["memory_type"] in sections else "other"
        sections[section_key]["items"].append({
            "id": memory["id"],
            "text": memory["memory"],
            "confidence": memory["confidence"],
            "source": memory["source"],
            "importance": memory["importance"],
            "updated_at": memory["updated_at"],
        })

    for section in sections.values():
        section["items"].sort(key=lambda i: (-i["importance"], -(i["confidence"] or 0)))

    # Only return sections that actually have something - an empty
    # section would otherwise imply a gap that might not be real
    # (the user may just not have mentioned it yet).
    non_empty = [sections[key] for key in SECTION_ORDER if sections[key]["items"]]
    empty_section_types = [key for key in SECTION_ORDER if not sections[key]["items"]]

    return {
        "sections": non_empty,
        "missing_sections": [
            {"type": t, "label": SECTION_LABELS[t]} for t in empty_section_types
            if t != "other"
        ],
        "total_facts": len(memories),
    }
