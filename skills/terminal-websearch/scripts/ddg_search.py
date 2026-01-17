#!/usr/bin/env python3

import argparse
import html
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import List, Optional


DDG_HTML_URL = "https://html.duckduckgo.com/html/"


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


class DuckDuckGoHTMLParser(HTMLParser):
    """Best-effort parser for DuckDuckGo's /html endpoint.

    This exists as a fallback when `ddgr` isn't installed.
    """

    def __init__(self) -> None:
        super().__init__()
        self._in_result = False
        self._in_title_link = False
        self._in_snippet = False

        self._cur_title_parts: List[str] = []
        self._cur_url: Optional[str] = None
        self._cur_snippet_parts: List[str] = []

        self.results: List[SearchResult] = []

    def handle_starttag(self, tag: str, attrs):
        attrs_dict = dict(attrs)

        if tag == "div" and "class" in attrs_dict:
            cls = attrs_dict["class"]
            if "result" in cls.split():
                self._start_result()

        if not self._in_result:
            return

        if tag == "a" and "class" in attrs_dict:
            cls = attrs_dict["class"]
            if "result__a" in cls.split():
                self._in_title_link = True
                href = attrs_dict.get("href")
                if href:
                    self._cur_url = _normalize_ddg_href(href)

        if tag in {"a", "div", "span"} and "class" in attrs_dict:
            cls = attrs_dict["class"]
            if any(c in cls.split() for c in ["result__snippet", "result__extras__snippet"]):
                self._in_snippet = True

    def handle_endtag(self, tag: str):
        if not self._in_result:
            return

        if tag == "a" and self._in_title_link:
            self._in_title_link = False

        if self._in_snippet and tag in {"a", "div", "span"}:
            self._in_snippet = False

        if tag == "div" and self._in_result:
            self._maybe_finalize_result()

    def handle_data(self, data: str):
        if not self._in_result:
            return

        if self._in_title_link:
            self._cur_title_parts.append(data)

        if self._in_snippet:
            self._cur_snippet_parts.append(data)

    def _start_result(self) -> None:
        self._in_result = True
        self._in_title_link = False
        self._in_snippet = False
        self._cur_title_parts = []
        self._cur_url = None
        self._cur_snippet_parts = []

    def _maybe_finalize_result(self) -> None:
        title = _clean_text("".join(self._cur_title_parts))
        url = (self._cur_url or "").strip()
        snippet = _clean_text("".join(self._cur_snippet_parts))

        if title and url:
            self.results.append(SearchResult(title=title, url=url, snippet=snippet))
            self._in_result = False


def _clean_text(s: str) -> str:
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _normalize_ddg_href(href: str) -> str:
    try:
        parsed = urllib.parse.urlparse(href)
        if parsed.path == "/l/":
            qs = urllib.parse.parse_qs(parsed.query)
            uddg = qs.get("uddg", [None])[0]
            if uddg:
                return urllib.parse.unquote(uddg)
        if parsed.scheme in {"http", "https"}:
            return href
        return urllib.parse.urljoin(DDG_HTML_URL, href)
    except Exception:
        return href


def ddg_search(query: str, timeout_s: int = 15) -> List[SearchResult]:
    params = urllib.parse.urlencode({"q": query})
    url = f"{DDG_HTML_URL}?{params}"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh) mo-skills/terminal-websearch",
            "Accept": "text/html,application/xhtml+xml",
        },
        method="GET",
    )

    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        body = resp.read().decode("utf-8", errors="replace")

    parser = DuckDuckGoHTMLParser()
    parser.feed(body)
    return parser.results


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Fallback terminal web search (DuckDuckGo HTML).")
    ap.add_argument("query", nargs="+", help="Search query")
    ap.add_argument("-n", "--num", type=int, default=5, help="Number of results")
    ap.add_argument("--timeout", type=int, default=15, help="Request timeout seconds")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = ap.parse_args(argv)

    query = " ".join(args.query).strip()
    results = ddg_search(query, timeout_s=args.timeout)[: max(args.num, 0)]

    if args.json:
        import json

        print(json.dumps([r.__dict__ for r in results], ensure_ascii=False, indent=2))
        return 0

    if not results:
        print("No results (or parser blocked).", file=sys.stderr)
        return 2

    for i, r in enumerate(results, start=1):
        print(f"{i}. {r.title}")
        print(f"   {r.url}")
        if r.snippet:
            print(f"   {r.snippet}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
