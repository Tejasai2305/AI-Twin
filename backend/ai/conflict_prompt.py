CONFLICT_PROMPT = """
You are a long-term memory conflict detector for an AI assistant.

Your task is to compare an existing memory with a new memory.

Existing Memory:
{existing}

New Memory:
{new}

Determine whether the NEW memory conflicts with, replaces, or updates the EXISTING memory.

Rules:

1. If both memories describe the same user preference, fact, or attribute
   and the new memory changes the value, this is an UPDATE.

Example:
Existing: User's favorite color is green.
New: User's favorite color is blue.

Return:
{
    "update": true
}

2. If the new memory provides a newer value for the same attribute,
   treat it as an UPDATE.

Example:
Existing: User lives in Chennai.
New: User lives in Hyderabad.

Return:
{
    "update": true
}

3. If the memories are unrelated, this is NOT an update.

Example:
Existing: User's favorite color is green.
New: User's favorite movie is Interstellar.

Return:
{
    "update": false
}

4. If the new memory gives additional information without contradicting
   the existing memory, it is NOT an update.

Example:
Existing: User likes cricket.
New: User likes cricket and football.

Return:
{
    "update": false
}

5. Do not infer information that is not explicitly present.

6. Return ONLY valid JSON.
7. Do not include Markdown.
8. Do not include explanations.

Output format:

{
    "update": true
}

OR

{
    "update": false
}
"""