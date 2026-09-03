import os
import time


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

DOCUMENT FACTUAL ACCURACY RULES:

- When the user's question is about information contained in the provided
  notes, PDFs, or documents, use the retrieved document content as the
  authoritative source.
- Extract factual answers directly from the retrieved document content.
- Do NOT replace document facts with general knowledge.
- Do NOT guess or infer missing information.
- Do NOT alter, correct, reinterpret, or "improve" names, student IDs,
  project titles, technical specifications, component names, numbers,
  measurements, pin numbers, processor cores, dates, or other factual values.
- Preserve names, IDs, numbers, labels, and technical terminology exactly
  as they appear in the retrieved document.
- If the retrieved document explicitly contains the answer, answer from it.
- If the retrieved document does not contain enough information to answer,
  clearly state that the information is not available in the retrieved
  document.
- When multiple retrieved chunks contain relevant information, combine them
  carefully without inventing additional information.
- Never claim that information is absent when the retrieved context
  explicitly contains it.

When writing code, ALWAYS format it as a fenced Markdown code block.
"""

# -----------------------------
# Non-Streaming Gemini
# -----------------------------
def ask_gemini(prompt):
    start_time = time.perf_counter()

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt + "\n\n" + FORMATTING_RULES,
    )

    elapsed = time.perf_counter() - start_time

    print(
        f"\nGemini response time: {elapsed:.2f} seconds"
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


