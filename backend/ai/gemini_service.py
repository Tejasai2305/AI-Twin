import os

from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Read API key
API_KEY = os.getenv("GEMINI_API_KEY")

# Create Gemini client
client = genai.Client(api_key=API_KEY)


def ask_gemini(prompt):
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
    )

    return response.text
import time
from google.genai.errors import ServerError


def ask_gemini_stream(prompt):
    max_retries = 3

    for attempt in range(max_retries):
        try:
            stream = client.models.generate_content_stream(
                model="gemini-3.1-flash-lite",
                contents=prompt,
            )

            for chunk in stream:
                if chunk.text:
                    yield chunk.text

            return

        except ServerError as e:
            print(f"Gemini ServerError (attempt {attempt + 1}/{max_retries}): {e}")

            if attempt == max_retries - 1:
                yield "\n\nSorry, the AI service is temporarily unavailable. Please try again in a few moments."
                return

            time.sleep(2)

        except Exception as e:
            print("Gemini Error:", e)
            yield f"\n\nUnexpected error: {e}"
            return
def generate_content(prompt: str):
    """
    Generate a non-streaming Gemini response.
    """

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
    )

    return response.text