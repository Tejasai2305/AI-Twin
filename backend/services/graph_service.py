"""
Personal Knowledge Graph (Feature 5).

Design choice: the graph is computed on demand directly from the
`memories` table rather than persisted in separate node/edge tables.

Why: a persisted graph is a second copy of the same facts, and any
memory add/update/deactivate/supersede would need to keep it in sync.
That's an easy way to end up with a graph that quietly drifts from
what's actually true. Since `memories` already has everything needed
(type, text, active/inactive, timestamps), we build the graph fresh
from it every time it's requested. It's always correct and there is
nothing extra to migrate or maintain.

Grounding rule: every node/edge here is derived directly from a
stored memory. Nothing is invented - there is no NLP entity
extraction guessing at sub-entities inside a memory sentence, because
that risks fabricating relationships the user never actually stated.
"""

from backend.services.memory_service import get_memories_detailed

# How each memory_type reads as a relationship from the user.
RELATION_LABELS = {
    "personal": "has_property",
    "education": "has_education",
    "career": "has_career",
    "technical_skill": "has_skill",
    "project": "worked_on",
    "preference": "prefers",
    "goal": "has_goal",
    "achievement": "achieved",
    "experience": "has_experience",
    "contact": "has_contact",
    "other": "related_to",
}


def build_graph(include_inactive=False, user_id=None):
    """
    Returns {"nodes": [...], "edges": [...]}.

    Node shape:
      { id, label, type, category, is_active, confidence, memory_id }
    Edge shape:
      { id, source, target, relation, is_active }

    "user" is always the single root node. Every memory becomes one
    node connected to "user" by an edge labeled per its memory_type.
    Category nodes (e.g. "education", "technical_skill") are added as
    an optional middle layer so the graph reads as:

        User -> [category] -> [individual memory/fact]

    which keeps large graphs organized without inventing any facts -
    the category is just the memory_type grouping that's already
    stored on each memory.
    """

    memories = get_memories_detailed(include_inactive=include_inactive, user_id=user_id)

    nodes = [
        {
            "id": "user",
            "label": "You",
            "type": "user",
            "category": "user",
            "is_active": True,
            "confidence": None,
            "memory_id": None,
        }
    ]
    edges = []

    seen_categories = set()

    for memory in memories:
        category = memory["memory_type"] or "other"
        category_node_id = f"category-{category}"

        if category not in seen_categories:
            seen_categories.add(category)
            nodes.append(
                {
                    "id": category_node_id,
                    "label": category.replace("_", " ").title(),
                    "type": "category",
                    "category": category,
                    "is_active": True,
                    "confidence": None,
                    "memory_id": None,
                }
            )
            edges.append(
                {
                    "id": f"user-{category_node_id}",
                    "source": "user",
                    "target": category_node_id,
                    "relation": RELATION_LABELS.get(category, "related_to"),
                    "is_active": True,
                }
            )

        memory_node_id = f"memory-{memory['id']}"

        nodes.append(
            {
                "id": memory_node_id,
                "label": memory["memory"],
                "type": "fact",
                "category": category,
                "is_active": memory["is_active"],
                "confidence": memory["confidence"],
                "memory_id": memory["id"],
            }
        )

        edges.append(
            {
                "id": f"{category_node_id}-{memory_node_id}",
                "source": category_node_id,
                "target": memory_node_id,
                "relation": RELATION_LABELS.get(category, "related_to"),
                "is_active": memory["is_active"],
            }
        )

    return {"nodes": nodes, "edges": edges}


def get_graph_summary(user_id=None):
    """
    Lightweight counts for the dashboard (Feature 15), computed from
    the same live source so it can never disagree with the full graph.
    """
    graph = build_graph(include_inactive=False, user_id=user_id)

    category_counts = {}
    for node in graph["nodes"]:
        if node["type"] == "fact":
            category_counts[node["category"]] = category_counts.get(node["category"], 0) + 1

    return {
        "total_facts": sum(category_counts.values()),
        "total_categories": len(category_counts),
        "by_category": category_counts,
    }
