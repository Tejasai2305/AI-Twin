import os
import re

from dotenv import load_dotenv
from backend.ai.gemini_service import generate_content


def generate_title(first_message: str):

    text = first_message.strip()
    lower = text.lower()

    # -----------------------------
    # Rule-based titles
    # -----------------------------

        
    import re

    book_match = re.search(r"favorite book is (.+)", lower)
    if book_match:
        return book_match.group(1).title()

    movie_match = re.search(r"favorite movie is (.+)", lower)
    if movie_match:
        return movie_match.group(1).title()

    color_match = re.search(r"favorite color is (.+)", lower)
    if color_match:
        return color_match.group(1).title()
    if lower.startswith("explain "):
        return text.replace("Explain", "").strip()

    if lower.startswith("what is "):
        return text.replace("What is", "").replace("?", "").strip()

    if lower.startswith("how to "):
        return text.replace("How to", "").strip()
    if "learn machine learning" in lower:
        return "Machine Learning"

    if lower.startswith("what is "):
        return text[8:].strip().title()

    if lower.startswith("who is "):
        return text[7:].strip().title()

    if lower.startswith("how to "):
        return text[7:].strip().title()

    if lower.startswith("explain "):
        return text[8:].strip().title()

    if lower.startswith("compare "):
        return "Comparison"

    # -----------------------------
    # Gemini fallback
    # -----------------------------

    prompt = f"""
You are an AI that generates chat titles.

Your job is to extract the MAIN TOPIC from the user's message.

Rules:
- Maximum 2 or 3 words.
- Return only the topic.
- Remove words like:
  Explain
  Tell me
  What is
  How to
  I want to know
  Algorithm
  About
- Prefer the important noun or entity.

Examples:

Explain Random Forest algorithm
-> Random Forest

Tell me about FastAPI
-> FastAPI

What is SQL?
-> SQL

How to learn Python?
-> Python

My favorite movie is Interstellar
-> Interstellar

My favorite book is Atomic Habits
-> Atomic Habits

User:
{first_message}
"""

    try:
        title = generate_content(prompt).strip()

        if title:
                print("AI Title:", title)
                return title

    except Exception as e:
        print("Title Generator:", e)

    # -----------------------------
    # Final fallback
    # -----------------------------

    words = re.findall(r"[A-Za-z0-9]+", text)

    return " ".join(words[:3]) if words else "New Chat"