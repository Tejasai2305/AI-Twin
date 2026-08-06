import json
from backend.ai.gemini import client

MODEL = "gemini-3.1-flash-lite"


def extract_memory(user_message):
    prompt = f"""
You are an AI memory extractor.

Your task is to decide whether the user's message contains long-term information that should be remembered.

Return ONLY valid JSON.

The JSON MUST ALWAYS follow this exact schema:

If it should be remembered:

{{
    "remember": true,
    "memory": "<one sentence describing the memory>"
}}

If it should NOT be remembered:

{{
    "remember": false
}}

Examples:

User: My name is Teja.
Output:
{{"remember": true, "memory": "User's name is Teja."}}

User: My favorite color is blue.
Output:
{{"remember": true, "memory": "User's favorite color is blue."}}

User: I am a third-year ECE student.
Output:
{{"remember": true, "memory": "User is a third-year ECE student."}}

User: I ate pizza today.
Output:
{{"remember": false}}

User:
{user_message}
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )

        text = response.text.strip()

        # Remove markdown if Gemini returns ```json ... ```
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        data = json.loads(text)

        # Handle old/incorrect Gemini outputs
        if "remember" not in data:
            if "preferences" in data:
                prefs = data["preferences"]

                if "favorite_color" in prefs:
                    return {
                        "remember": True,
                        "memory": f"User's favorite color is {prefs['favorite_color']}."
                    }

            return {"remember": False}

        return data

    except Exception as e:
        print("Memory extraction failed:", e)
        return {"remember": False}