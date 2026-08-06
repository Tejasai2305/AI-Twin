import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

models_to_try = [
    "gemini-2.0-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
]

for model in models_to_try:
    print(f"\nTesting {model}")

    try:
        response = client.models.generate_content(
            model=model,
            contents="Reply with exactly: Hello"
        )

        print("SUCCESS!")
        print(response.text)
        break

    except Exception as e:
        print(type(e).__name__)
        print(e)