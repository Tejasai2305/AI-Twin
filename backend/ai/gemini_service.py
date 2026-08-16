from email.mime import text
import os
import time
import json

from dotenv import load_dotenv
from google import genai
from google.genai.errors import ServerError

# -----------------------------
# Load Environment Variables
# -----------------------------
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)

# -----------------------------
# Common Formatting Instructions
# -----------------------------
FORMATTING_RULES = """
IMPORTANT:

- Always reply using GitHub Flavored Markdown.
- Wrap every code example inside fenced Markdown code blocks.
- Always specify the programming language.
- Use headings when appropriate.
- Use bullet lists where useful.
- Use numbered lists for step-by-step instructions.
- Use Markdown tables when comparing things.

When writing code, ALWAYS format it as a fenced Markdown code block.
"""


# -----------------------------
# Non-Streaming Gemini
# -----------------------------
def ask_gemini(prompt):
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt + "\n\n" + FORMATTING_RULES,
    )

    print("\n========== RAW GEMINI ==========")
    print(repr(response.text))
    print("================================\n")

    return response.text


# -----------------------------
# Streaming Gemini
# -----------------------------
def ask_gemini_stream(prompt):
    max_retries = 3

    for attempt in range(max_retries):
        try:
            stream = client.models.generate_content_stream(
                model="gemini-3.1-flash-lite",
                contents=prompt + "\n\n" + FORMATTING_RULES,
            )

            for chunk in stream:
                if chunk.text:
                    print(repr(chunk.text))
                    text = chunk.text

                    text = text.replace("```python", "\n```python")
                    text = text.replace("```javascript", "\n```javascript")
                    text = text.replace("```java", "\n```java")
                    text = text.replace("```cpp", "\n```cpp")
                    text = text.replace("```c", "\n```c")

                    yield   text

            return

        except ServerError as e:
            print(
                f"Gemini ServerError (attempt {attempt + 1}/{max_retries}): {e}"
            )

            if attempt == max_retries - 1:
                yield (
                    "\n\nSorry, the AI service is temporarily unavailable. "
                    "Please try again in a few moments."
                )
                return

            time.sleep(2)

        except Exception as e:
            print("Gemini Error:", e)
            yield f"\n\nUnexpected error: {e}"
            return


