import json
import os

from langchain_core.tools import tool
from tavily import TavilyClient


@tool
def web_search(q: str, max_results: int = 5) -> str:
    """
    Tavily로 최신/추가 정보를 검색합니다.
    반환(JSON 문자열): {"results":[{"id","title","url","snippet"}]}
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return json.dumps({"error": "TAVILY_API_KEY 미설정"}, ensure_ascii=False)

    tv = TavilyClient(api_key=api_key)
    res: dict = tv.search(query=q, max_results=max_results)
    items: list[dict] = res.get("results", [])

    data = []
    for i, item in enumerate(items, start=1):
        data.append(
            {
                "id": f"W{i}",
                "title": (item.get("title") or "제목 없음").strip(),
                "url": (item.get("url") or "").strip(),
                "snippet": (item.get("content") or item.get("snippet") or "").strip()[:500],
            }
        )
    return json.dumps({"results": data}, ensure_ascii=False)
