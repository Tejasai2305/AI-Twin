import json
import re


def extract_json(text: str):
    """
    Extract the first JSON object from an LLM response.
    """

    if not text:
        return None

    # Remove markdown fences if present
    text = text.replace("```json", "")
    text = text.replace("```", "")

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        return None

    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None