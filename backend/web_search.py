import urllib.request
import json
import urllib.parse
from duckduckgo_search import DDGS

def search_global_web(query: str, max_results: int = 4):
    results = []
    
    # 1. Primary: DuckDuckGo Search
    try:
        with DDGS() as ddgs:
            ddg_gen = ddgs.text(query, max_results=max_results)
            if ddg_gen:
                for r in ddg_gen:
                    results.append({
                        "title": r.get("title", ""),
                        "snippet": r.get("body", "") or r.get("snippet", ""),
                        "link": r.get("href", "") or r.get("link", "")
                    })
    except Exception as e:
        print(f"[Web Search Warning] DDGS failed: {e}")

    # 2. Secondary Fallback: Wikipedia / Open API if DDG blocks
    if not results:
        try:
            encoded = urllib.parse.quote(query)
            wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={encoded}&limit={max_results}&namespace=0&format=json"
            req = urllib.request.Request(wiki_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if len(data) >= 4 and len(data[1]) > 0:
                    for title, snippet, link in zip(data[1], data[2], data[3]):
                        if snippet:
                            results.append({
                                "title": title,
                                "snippet": snippet,
                                "link": link
                            })
        except Exception as e2:
            print(f"[Web Search Fallback Error]: {e2}")

    return results