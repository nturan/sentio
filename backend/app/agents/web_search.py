"""
Web Search Tool - uses Tavily API for AI-optimized web search.
"""

import os
from langchain_core.tools import tool
from tavily import TavilyClient


@tool
async def web_search(query: str, num_results: int = 5) -> str:
    """
    Search the web for information on a topic.
    Returns formatted markdown results with sources.

    Args:
        query: The search query
        num_results: Number of results to return (default 5, max 10)
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY not configured. Please add it to the .env file."

    try:
        client = TavilyClient(api_key=api_key)

        # Limit results to reasonable range
        num_results = min(max(1, num_results), 10)

        results = client.search(
            query=query,
            max_results=num_results,
            include_raw_content=False,
            search_depth="basic"
        )

        if not results.get("results"):
            return f"No results found for: {query}"

        # Format as markdown
        output = f"## Web Search Results: {query}\n\n"
        sources = []

        for i, result in enumerate(results.get("results", []), 1):
            title = result.get("title", "Untitled")
            content = result.get("content", "No description available")
            url = result.get("url", "")

            output += f"### {i}. {title}\n"
            output += f"{content}\n\n"

            if url:
                sources.append({"title": title, "url": url})

        # Add sources section
        if sources:
            output += "---\n\n## Sources\n"
            for source in sources:
                output += f"- [{source['title']}]({source['url']})\n"

        return output

    except Exception as e:
        return f"Web search error: {str(e)}"
