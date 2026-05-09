"""
Web search module — fetches results from the internet via Tavily API.
"""

from __future__ import annotations

import logging

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)

TAVILY_URL = "https://api.tavily.com/search"


async def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the web via Tavily API.

    Returns list of {text, source, url}.
    """
    api_key = settings.TAVILY_API_KEY
    if not api_key:
        logger.warning("Tavily API key not configured")
        return []

    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "include_answer": True,
        "search_depth": "basic",
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(TAVILY_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.warning(f"Tavily search failed: {e}")
        return []

    results: list[dict] = []

    # Direct answer (if Tavily provides one)
    answer = data.get("answer", "")
    if answer:
        results.append({
            "text": answer,
            "source": "Tavily",
            "url": "",
        })

    # Search results
    for item in data.get("results", [])[:max_results]:
        content = item.get("content", "")
        title = item.get("title", "")
        text = f"{title}\n{content}".strip() if title else content
        results.append({
            "text": text,
            "source": item.get("url", "互联网"),
            "url": item.get("url", ""),
        })

    if results:
        logger.info(f"Tavily search: returned {len(results)} results")
    else:
        logger.info("Tavily search: no results")

    return results[:max_results]
