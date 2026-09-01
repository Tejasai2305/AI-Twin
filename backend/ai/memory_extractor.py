import json

from backend.ai.gemini_service import ask_gemini


def extract_memory(user_message):
    prompt = f"""
You are an AI long-term memory extractor.

Your job is to decide whether the user's message contains information
that is genuinely useful to remember across future conversations.

Only store stable, long-term information about the user.

DO NOT store temporary, session-specific, or one-time information.

NEVER remember:
- passwords
- PINs
- OTPs
- API keys
- tokens
- secret codes
- temporary codes
- test words
- verification codes
- one-time instructions
- today's tasks
- temporary tasks
- temporary plans
- meeting times
- deadlines
- short-lived project details
- information explicitly described as temporary or secret
- information that is only relevant to the current conversation

Examples that SHOULD be remembered:

User: My name is Teja.
Output:
{{"remember": true, "memory": "User's name is Teja."}}

User: My favorite color is blue.
Output:
{{"remember": true, "memory": "User's favorite color is blue."}}

User: My favorite food is biryani.
Output:
{{"remember": true, "memory": "User's favorite food is biryani."}}

User: I am working on a project called AQIVision.
Output:
{{"remember": true, "memory": "User is working on a project called AQIVision."}}

Examples that MUST NOT be remembered:

User: My temporary code is BLUE-729.
Output:
{{"remember": false}}

User: My secret test word is ORANGE-123.
Output:
{{"remember": false}}

User: The password for this session is abc123.
Output:
{{"remember": false}}

User: Today's meeting is at 5 PM.
Output:
{{"remember": false}}

User: I ate pizza today.
Output:
{{"remember": false}}

User: Remind me to submit this tomorrow.
Output:
{{"remember": false}}

Important:
- When in doubt, do NOT remember the information.
- Never store secrets or credentials.
- Return ONLY valid JSON.
- Do not add explanations.
- The JSON MUST follow exactly one of these schemas:

If it should be remembered:
{{
    "remember": true,
    "memory": "<one sentence describing the stable information>"
}}

If it should NOT be remembered:
{{
    "remember": false
}}

User message:
{user_message}
"""

    try:
        text = ask_gemini(prompt).strip()

        # Remove markdown code fences if Gemini returns them
        if text.startswith("```"):
            text = text.replace("```json", "")
            text = text.replace("```", "").strip()

        data = json.loads(text)

        if not isinstance(data, dict):
            return {"remember": False}

        # Validate remember field
        if data.get("remember") is not True:
            return {"remember": False}

        # Memory must be present and non-empty
        memory = data.get("memory")

        if not isinstance(memory, str) or not memory.strip():
            return {"remember": False}

        return {
            "remember": True,
            "memory": memory.strip()
        }

    except Exception as e:
        print("Memory extraction failed:", e)
        return {"remember": False}