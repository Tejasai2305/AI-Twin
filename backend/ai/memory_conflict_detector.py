import json

from backend.ai.gemini_service import ask_gemini


def detect_memory_conflict(new_memory, existing_memories):
    """
    Decide whether a new memory should:
    - insert
    - update
    - ignore
    """

    if not existing_memories:
        return {
            "action": "insert"
        }

    memories = "\n".join(
        f"{i+1}. {m}"
        for i, m in enumerate(existing_memories)
    )

    prompt = f"""
You are an AI memory manager.

Existing Memories:
{memories}

New Memory:
{new_memory}

Determine whether the new memory:

1. Updates an existing memory
2. Is completely new
3. Should be ignored because it already exists

Return ONLY valid JSON.

Examples:

{{
"action":"insert"
}}

{{
"action":"ignore"
}}

{{
"action":"update",
"existing_memory":"User's favorite color is red."
}}
"""

    response = ask_gemini(prompt)

    try:
        return json.loads(response)
    except Exception:
        return {
            "action": "insert"
        }