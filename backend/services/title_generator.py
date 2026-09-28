import re

from backend.ai.gemini_service import ask_gemini


def generate_title(first_message: str):

    text = first_message.strip()
    lower = text.lower()

    # ----------------------------------------------------
    # Rule-based titles (fast & accurate)
    # ----------------------------------------------------

    patterns = [
        (r"favorite book is (.+)", lambda m: m.group(1).title()),
        (r"favorite movie is (.+)", lambda m: m.group(1).title()),
        (r"favorite color is (.+)", lambda m: m.group(1).title()),
        (r"favorite food is (.+)", lambda m: m.group(1).title()),
        (r"favorite city is (.+)", lambda m: m.group(1).title()),
    ]

    for pattern, func in patterns:
        match = re.search(pattern, lower)
        if match:
            return func(match)

    # ----------------------------------------------------
    # Common question patterns
    # ----------------------------------------------------

    prefixes = [
        "what is ",
        "who is ",
        "how to ",
        "explain ",
        "tell me about ",
        "describe ",
        "learn ",
    ]

    for prefix in prefixes:
        if lower.startswith(prefix):
            title = text[len(prefix):]

            # remove common trailing phrases
            title = re.sub(
                r"\b(in detail|with examples|for beginners|tutorial|guide)\b",
                "",
                title,
                flags=re.IGNORECASE,
            )

            title = title.replace("?", "")
            title = title.replace(".", "")
            title = re.sub(r"\s+", " ", title).strip()

            # Keep only first two words
            words = title.split()
            if len(words) > 2:
                title = " ".join(words[:2])

            return title.title()

    # ----------------------------------------------------
    # Gemini fallback
    # ----------------------------------------------------

    prompt = f"""
You generate chat titles.

Return ONLY the main topic.

Rules:
- Maximum 2 words.
- No punctuation.
- No markdown.
- No quotes.
- No explanation.
- Ignore filler words like:
Explain
Describe
Tell me
What is
How to
In detail
With examples
Tutorial
Guide

Examples

Explain Random Forest in detail with examples.
Random Forest

Tell me about FastAPI
FastAPI

How to learn Python?
Python

What is SQL?
SQL

Who invented Python?
Python

User message:
{first_message}

Title:
"""

    try:

        title = ask_gemini(prompt).strip()

        # Keep only first line
        title = title.splitlines()[0]

        # Remove markdown
        title = title.replace("#", "")
        title = title.replace("*", "")
        title = title.replace("`", "")
        title = title.replace('"', "")
        title = title.replace("'", "")

        title = title.strip()

        print("AI Title:", repr(title))

        if title:
            return title

    except Exception as e:
        print("Title Generator:", e)

    # ----------------------------------------------------
    # Final fallback
    # ----------------------------------------------------

    words = re.findall(r"[A-Za-z0-9]+", text)

    if len(words) >= 2:
        return " ".join(words[:2]).title()

    if len(words) == 1:
        return words[0].title()

    return "New Chat"