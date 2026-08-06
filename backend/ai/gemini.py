import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)


def ask_gemini(prompt):
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
    )
    return response.text


def ask_gemini_stream(prompt):
    stream = client.models.generate_content_stream(
        model="gemini-3.1-flash-lite",
        contents=prompt,
    )

    for chunk in stream:
        if chunk.text:
            yield chunk.text