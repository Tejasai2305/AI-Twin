import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

response = client.search(
    query="Latest AI news",
    search_depth="basic",
)

print(response)