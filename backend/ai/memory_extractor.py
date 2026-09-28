import json

from backend.ai.gemini_service import ask_gemini

VALID_TYPES = (
    "personal", "education", "career", "technical_skill", "project",
    "preference", "goal", "achievement", "experience", "contact", "other",
)


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

If it should be remembered, also classify it into exactly one
memory_type from this fixed list:

{", ".join(VALID_TYPES)}

- "education": degrees, colleges, CGPA, courses
- "career": jobs, employers, roles held over time
- "technical_skill": programming languages, tools, frameworks
- "project": named projects the user built or is building
- "preference": favorites, likes/dislikes, tastes
- "goal": things the user wants to achieve
- "achievement": awards, completed milestones, certifications
- "experience": internships, work experience entries
- "personal": name, age, location, relationships
- "contact": contact details
- "other": anything that doesn't clearly fit above

Also give a confidence score from 0.0 to 1.0 for how clearly and
explicitly the user stated this as a stable fact (not a guess or
one-off remark). A direct first-person statement of fact ("My CGPA
is 8.9") should be high confidence (0.85-0.95). Something implied or
vague should be lower (0.4-0.6).

Examples that SHOULD be remembered:

User: My name is Teja.
Output:
{{"remember": true, "memory": "User's name is Teja.", "memory_type": "personal", "confidence": 0.95}}

User: My favorite color is blue.
Output:
{{"remember": true, "memory": "User's favorite color is blue.", "memory_type": "preference", "confidence": 0.9}}

User: My CGPA is 8.8.
Output:
{{"remember": true, "memory": "User's CGPA is 8.8.", "memory_type": "education", "confidence": 0.9}}

User: I am working on a project called AQIVision.
Output:
{{"remember": true, "memory": "User is working on a project called AQIVision.", "memory_type": "project", "confidence": 0.85}}

User: I worked as a Machine Learning Intern at a startup last summer.
Output:
{{"remember": true, "memory": "User worked as a Machine Learning Intern.", "memory_type": "experience", "confidence": 0.85}}

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
    "memory": "<one sentence describing the stable information>",
    "memory_type": "<one of the fixed types above>",
    "confidence": <number between 0.0 and 1.0>
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

        memory_type = data.get("memory_type")
        if memory_type not in VALID_TYPES:
            memory_type = "other"

        try:
            confidence = float(data.get("confidence", 0.7))
        except (TypeError, ValueError):
            confidence = 0.7
        confidence = max(0.0, min(1.0, confidence))

        return {
            "remember": True,
            "memory": memory.strip(),
            "memory_type": memory_type,
            "confidence": confidence,
            # The original user text is kept as evidence so the
            # Memory Center / evidence panel can show "why this was
            # saved" without re-querying the LLM.
            "evidence": user_message.strip()[:1000],
        }

    except Exception as e:
        print("Memory extraction failed:", e)
        return {"remember": False}
