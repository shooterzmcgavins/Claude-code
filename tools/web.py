import urllib.request
import urllib.parse
import json
from html.parser import HTMLParser
from anthropic import beta_tool


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._skip = {"script", "style", "head", "nav", "footer", "aside"}
        self._depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self._skip:
            self._depth += 1

    def handle_endtag(self, tag):
        if tag in self._skip and self._depth > 0:
            self._depth -= 1

    def handle_data(self, data):
        if self._depth == 0:
            s = data.strip()
            if s:
                self.parts.append(s)


@beta_tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo and return results.

    Args:
        query: The search query.
        max_results: Maximum number of results to return (1-10).
    """
    max_results = min(max(1, max_results), 10)
    url = f"https://api.duckduckgo.com/?q={urllib.parse.quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "workspace-agent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return f"Search failed: {e}"

    results = []
    if data.get("AbstractText"):
        results.append(f"Summary: {data['AbstractText']}")
        if data.get("AbstractURL"):
            results.append(f"Source: {data['AbstractURL']}")
    for item in data.get("RelatedTopics", [])[:max_results]:
        if isinstance(item, dict) and item.get("Text"):
            results.append(f"- {item['Text'][:200]}\n  {item.get('FirstURL', '')}")
    return "\n".join(results) if results else f"No results for: {query}"


@beta_tool
def fetch_url(url: str, extract_text: bool = True) -> str:
    """Fetch the content of a URL.

    Args:
        url: The URL to fetch.
        extract_text: Extract readable text from HTML (True) or return raw content (False).
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "workspace-agent/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"Failed to fetch {url}: {e}"

    if extract_text and "html" in content_type.lower():
        extractor = _TextExtractor()
        extractor.feed(raw)
        text = " ".join(extractor.parts)
        return text[:5000] + ("..." if len(text) > 5000 else "")
    return raw[:5000] + ("..." if len(raw) > 5000 else "")
