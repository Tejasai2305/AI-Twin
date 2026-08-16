import json

from backend.ai.gemini_service import ask_gemini
from backend.ai.memory_manager_prompt import MEMORY_MANAGER_PROMPT


def decide_memory_action(existing_memories, new_memory):
    """
    Decide whether the new memory should:
    - add
    - update
    - ignore
    - merge
    """

    # --------------------------------------------------
    # Build existing memories text
    # --------------------------------------------------

    memory_text = ""

    for memory in existing_memories:
        memory_text += (
            f"ID: {memory['id']}\n"
            f"Memory: {memory['memory']}\n\n"
        )

    # --------------------------------------------------
    # IMPORTANT
    #
    # Do NOT use .format() here.
    #
    # MEMORY_MANAGER_PROMPT contains JSON examples
    # with { } braces. .format() interprets those
    # braces as Python placeholders and causes:
    #
    # KeyError: '"action"'
    #
    # We replace only our two actual placeholders.
    # --------------------------------------------------

    prompt = MEMORY_MANAGER_PROMPT

    prompt = prompt.replace(
        "{memories}",
        memory_text
    )

    prompt = prompt.replace(
        "{new_memory}",
        new_memory
    )

    # --------------------------------------------------
    # Ask Gemini
    # --------------------------------------------------

    response = ask_gemini(prompt)

    print("\n========== MEMORY MANAGER ==========")
    print("Existing Memories:")
    print(memory_text)

    print("New Memory:")
    print(new_memory)

    print("\nGemini Decision:")
    print(response)
    print("====================================\n")

    # --------------------------------------------------
    # Parse Gemini response
    # --------------------------------------------------

    try:
        cleaned = response.strip()

        # Remove Markdown code fences if Gemini adds them
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "")
            cleaned = cleaned.replace("```", "")
            cleaned = cleaned.strip()

        decision = json.loads(cleaned)

        action = decision.get("action")

        # --------------------------------------------------
        # Validate action
        # --------------------------------------------------

        if action in ("add", "update", "ignore", "merge"):
            return decision

        print("Unknown memory action:", action)

        return {
            "action": "add"
        }

    except Exception as e:
        print("Memory manager JSON error:", e)
        print("Raw Gemini response:", response)

        return {
            "action": "add"
        }