import os

from dotenv import load_dotenv
from tavily import TavilyClient

from backend.ai.gemini_service import ask_gemini

load_dotenv()

client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


def execute(query: str):
    """
    Search the web and summarize the results.
    """

    try:

        response = client.search(
            query=query,
            search_depth="basic",
            max_results=5,
        )

        results = response["results"]

        context = ""

        for result in results:

            context += f"""
Title:
{result["title"]}

Content:
{result["content"]}

URL:
{result["url"]}

-------------------------
"""

        summary = ask_gemini(
            f"""
You are an AI assistant.

Summarize these search results into one accurate answer.

Search Results:

{context}

User Question:

{query}
"""
        )

        return {
            "success": True,
            "result": summary,
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e),
        }