"""Fetch and parse Slickdeals RSS feeds."""

from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime

RSS_URL = "https://slickdeals.net/newsearch.php"
USER_AGENT = "Mozilla/5.0 (compatible; pyslickdeals/2.0)"
TIMEOUT = 20


@dataclass
class Deal:
    id: str
    title: str
    link: str
    description: str
    published: datetime | None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["published"] = self.published.isoformat() if self.published else None
        return d


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def feed_url(query: str | None = None, popular: bool = False) -> str:
    params = {"searcharea": "deals", "searchin": "first", "rss": "1"}
    if query:
        params["q"] = query
    else:
        params["mode"] = "popdeals" if popular else "frontpage"
    return RSS_URL + "?" + urllib.parse.urlencode(params)


def _clean_link(link: str) -> str:
    """Drop the utm_* tracking params the feed appends."""
    parts = urllib.parse.urlsplit(link)
    query = [
        (k, v)
        for k, v in urllib.parse.parse_qsl(parts.query)
        if not k.startswith("utm_")
    ]
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query)))


def _thread_id(guid: str, link: str) -> str:
    m = re.search(r"(\d+)", guid) or re.search(r"/f/(\d+)", link)
    return m.group(1) if m else guid


def parse_feed(xml_bytes: bytes) -> list[Deal]:
    root = ET.fromstring(xml_bytes)
    deals = []
    for item in root.iter("item"):
        title = html.unescape((item.findtext("title") or "").strip())
        link = _clean_link((item.findtext("link") or "").strip())
        desc = html.unescape((item.findtext("description") or "").strip())
        guid = (item.findtext("guid") or "").strip()
        pub = item.findtext("pubDate")
        try:
            published = parsedate_to_datetime(pub) if pub else None
        except (TypeError, ValueError):
            published = None
        deals.append(Deal(_thread_id(guid, link), title, link, desc, published))
    return deals


def fetch_deals(query: str | None = None, popular: bool = False) -> list[Deal]:
    return parse_feed(_get(feed_url(query, popular)))

