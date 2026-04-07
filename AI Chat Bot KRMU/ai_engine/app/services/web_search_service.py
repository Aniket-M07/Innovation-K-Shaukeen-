import html
import json
import re
from dataclasses import dataclass
from urllib.parse import quote_plus, urljoin
from urllib.request import Request, urlopen

from app.core.config import settings


@dataclass
class WebResult:
  title: str
  url: str
  snippet: str


class WebSearchService:
  def search(self, query: str, max_results: int | None = None) -> list[dict[str, str]]:
    if not settings.web_search_enabled:
      return []

    result_limit = max(1, min(int(max_results or settings.web_search_max_results), 10))
    if settings.web_search_provider.lower() != "duckduckgo":
      return []

    try:
      results = self._search_duckduckgo_json(query, result_limit)
      if results:
        return results
      return self._search_duckduckgo_html(query, result_limit)
    except Exception:
      return []

  def _search_duckduckgo_json(self, query: str, max_results: int) -> list[dict[str, str]]:
    search_url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_redirect=1&no_html=1"
    request = Request(
      search_url,
      headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
      },
    )

    with urlopen(request, timeout=max(1, settings.web_search_timeout_ms // 1000)) as response:
      payload = json.loads(response.read().decode("utf-8", errors="ignore"))

    results: list[dict[str, str]] = []

    abstract_text = (payload.get("AbstractText") or "").strip()
    abstract_url = (payload.get("AbstractURL") or "").strip()
    heading = (payload.get("Heading") or query).strip()
    if abstract_text:
      results.append({"title": heading, "url": abstract_url or "https://duckduckgo.com", "snippet": abstract_text})

    def collect_related(topics: list[dict]) -> None:
      for item in topics:
        if len(results) >= max_results:
          return
        if "Topics" in item:
          collect_related(item.get("Topics") or [])
          continue

        text = (item.get("Text") or "").strip()
        url = (item.get("FirstURL") or "").strip()
        if text and url:
          title = text.split(" - ", 1)[0].strip() if " - " in text else text[:80]
          results.append({"title": title, "url": url, "snippet": text})

    collect_related(payload.get("RelatedTopics") or [])

    return results[:max_results]

  def _search_duckduckgo_html(self, query: str, max_results: int) -> list[dict[str, str]]:
    search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    request = Request(
      search_url,
      headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
      },
    )

    with urlopen(request, timeout=max(1, settings.web_search_timeout_ms // 1000)) as response:
      html_text = response.read().decode("utf-8", errors="ignore")

    blocks = re.findall(r'<a[^>]*class="result__a"[^>]*href="(.*?)"[^>]*>(.*?)</a>.*?<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', html_text, flags=re.S)
    results: list[dict[str, str]] = []

    for href, title_html, snippet_html in blocks[:max_results]:
      title = html.unescape(re.sub(r"<.*?>", "", title_html)).strip()
      snippet = html.unescape(re.sub(r"<.*?>", "", snippet_html)).strip()
      url = html.unescape(href)
      if url.startswith("//"):
        url = f"https:{url}"
      elif url.startswith("/"):
        url = urljoin("https://duckduckgo.com", url)

      if title and snippet and url:
        results.append({"title": title, "url": url, "snippet": snippet})

    return results