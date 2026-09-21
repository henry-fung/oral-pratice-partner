"""Role-aware news/community retrieval and bounded evidence extraction."""
import hashlib
import html
import ipaddress
import os
import re
import socket
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree

import requests

DEFAULT_NEWS_RSS_URL = "https://news.google.com/rss/search?q={query}&hl={hl}&gl={gl}&ceid={gl}:{lang}"
MAX_EXTRACTED_CHARS = 12000
ROLE_QUERIES = {"ai_engineer": ["AI agents", "LLM deployment", "RAG systems"], "business_dev": ["software engineering", "cloud platform"], "business_trade": ["international trade", "shipping logistics"], "traveler": ["travel transport", "flight disruption"], "student": ["higher education", "student housing"], "ielts": ["education and society"], "toefl": ["university research"], "daily": ["consumer technology", "public services"]}
LANGUAGE_LOCALES = {"en": ("en-US", "US", "en"), "ja": ("ja", "JP", "ja"), "fr": ("fr", "FR", "fr"), "es": ("es", "ES", "es"), "de": ("de", "DE", "de"), "ko": ("ko", "KR", "ko")}
TECHNICAL_ROLES = {"ai_engineer", "business_dev"}

class _TextExtractor(HTMLParser):
    def __init__(self): super().__init__(); self.parts = []; self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg", "nav", "footer", "header"}: self.skip += 1
    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "svg", "nav", "footer", "header"} and self.skip: self.skip -= 1
        elif tag in {"p", "div", "li", "article", "section", "h1", "h2", "h3", "br"}: self.parts.append("\n")
    def handle_data(self, data):
        if not self.skip: self.parts.append(data)

def _text(element, name): return html.unescape((element.findtext(name) if element is not None else "") or "").strip()
def _clean(value): return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", value)).strip()
def interest_key(interests):
    value = "|".join(sorted(item.strip().lower() for item in interests if item.strip()))
    return hashlib.sha256(value.encode()).hexdigest()[:24] if value else ""

class NewsService:
    def role_terms(self, role, custom_role_name, interests):
        terms = list(interests) + ROLE_QUERIES.get(role, [])
        if role == "custom" and custom_role_name: terms.insert(0, custom_role_name)
        return terms[:4] or ["current events"]

    def fetch_topics(self, limit=30): return self._google_news("current events", "en", limit)

    def fetch_candidates(self, role, language, interests, custom_role_name=None, limit=20):
        terms = self.role_terms(role, custom_role_name, interests); candidates = []
        for term in terms: candidates.extend(self._google_news(term, language, max(5, limit // len(terms))))
        if language == "en" and role in TECHNICAL_ROLES:
            query = " ".join(terms[:2]); candidates.extend(self._hacker_news(query, 8)); candidates.extend(self._stack_exchange(query, 8))
        unique = {}
        for item in candidates: unique.setdefault(item["source_url"], item)
        return list(unique.values())[:limit]

    def _google_news(self, query, language, limit):
        hl, gl, lang = LANGUAGE_LOCALES.get(language, LANGUAGE_LOCALES["en"])
        url = os.getenv("NEWS_RSS_URL", DEFAULT_NEWS_RSS_URL).format(query=quote_plus(query), hl=hl, gl=gl, lang=lang)
        with urlopen(Request(url, headers={"User-Agent": "OralPracticePartner/1.0"}), timeout=10) as response: root = ElementTree.fromstring(response.read())
        results = []
        for item in root.findall("./channel/item"):
            title, link = _text(item, "title"), _text(item, "link")
            if not title or not link: continue
            try: published_at = parsedate_to_datetime(_text(item, "pubDate")).replace(tzinfo=None)
            except (TypeError, ValueError): published_at = None
            source = item.find("source")
            results.append({"headline": title[:500], "summary": _clean(_text(item, "description"))[:2000], "source_name": (source.text or "").strip()[:200] if source is not None else urlparse(link).netloc, "source_url": link[:2000], "published_at": published_at, "content_language": language, "source_type": "news", "content_category": "news"})
            if len(results) >= limit: break
        return results

    def _hacker_news(self, query, limit):
        data = requests.get("https://hn.algolia.com/api/v1/search", params={"query": query, "tags": "story", "hitsPerPage": limit}, timeout=10).json()
        return [{"headline": hit.get("title") or "", "summary": hit.get("story_text") or "", "source_name": "Hacker News", "source_url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}", "published_at": None, "content_language": "en", "source_type": "community", "content_category": "technical_discussion"} for hit in data.get("hits", []) if hit.get("title")]

    def _stack_exchange(self, query, limit):
        data = requests.get("https://api.stackexchange.com/2.3/search/advanced", params={"site": "stackoverflow", "q": query, "pagesize": limit, "order": "desc", "sort": "relevance"}, timeout=10).json()
        return [{"headline": _clean(item.get("title", "")), "summary": "", "source_name": "Stack Overflow", "source_url": item.get("link", ""), "published_at": None, "content_language": "en", "source_type": "community", "content_category": "technical_discussion"} for item in data.get("items", []) if item.get("title") and item.get("link")]

    def extract_evidence(self, topic):
        text, status = self._safe_fetch_text(topic["source_url"])
        if not text: text, status = topic.get("summary", ""), "summary_only"
        text = text[:MAX_EXTRACTED_CHARS]; sentences = [s.strip() for s in re.split(r"(?<=[.!?。！？])\s+", text) if len(s.strip()) > 35]
        excerpts = sentences[:3]; terms = sorted(set(re.findall(r"\b[A-Za-z][A-Za-z0-9+.#/-]{2,}\b", text)))[:30]
        return {"extracted_text": text, "extraction_status": status, "evidence": {"excerpts": excerpts, "facts": excerpts[:5], "technical_terms": terms, "source_url": topic["source_url"], "source_name": topic.get("source_name", "")}}

    def _safe_fetch_text(self, url):
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname: return "", "blocked"
        try:
            if not self._is_public_host(parsed.hostname): return "", "blocked"
            response = requests.get(url, timeout=10, headers={"User-Agent": "OralPracticePartner/1.0"}, allow_redirects=True); final = urlparse(response.url)
            if final.scheme not in {"http", "https"} or not final.hostname or not self._is_public_host(final.hostname): return "", "blocked"
            response.raise_for_status(); parser = _TextExtractor(); parser.feed(response.text)
            return _clean(" ".join(parser.parts)), "extracted"
        except (requests.RequestException, OSError, ValueError): return "", "unavailable"

    @staticmethod
    def _is_public_host(hostname):
        for record in socket.getaddrinfo(hostname, None):
            address = ipaddress.ip_address(record[4][0])
            if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
                return False
        return True
