"""Build the Listing URL corpus from the builder's tracker export."""

from __future__ import annotations

import csv
from datetime import date, datetime, timedelta
from pathlib import Path

from dealscout.collect.fetcher import portal_of

# The five Portals that returned a full page, plus OLX so the Run must mark those Unreachable.
INCLUDED_PORTALS = frozenset({"rumah123", "99co", "pinhome", "masuksini", "idrumah", "olx"})
WINDOW_DAYS = 14

_PORTAL_ALIASES = {
    "rumah123": "rumah123",
    "99.co": "99co",
    "99co": "99co",
    "pinhome": "pinhome",
    "masuksini": "masuksini",
    "masuk sini": "masuksini",
    "idrumah": "idrumah",
    "id rumah": "idrumah",
    "olx": "olx",
    "lamudi": "lamudi",
    "jualrumahjakarta": "jualrumahjakarta",
}

_URL_HEADERS = ("url", "listing_url", "link")
_PORTAL_HEADERS = ("source", "portal", "portal_name")
_DATE_HEADERS = ("last_seen", "first_seen", "date", "scraped_at", "timestamp", "created_at")
_DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d %b %Y",
    "%d %B %Y",
    "%m/%d/%Y",
)


def _header_map(fieldnames: list[str] | None) -> dict[str, str]:
    return {name.strip().lower(): name for name in (fieldnames or [])}


def _cell(row: dict[str, str], headers: dict[str, str], candidates: tuple[str, ...]) -> str:
    for candidate in candidates:
        key = headers.get(candidate)
        if key is not None:
            return (row.get(key) or "").strip()
    return ""


def _parse_date(raw: str) -> date | None:
    text = raw.strip()
    if not text:
        return None
    if "T" in text:
        text = text.replace("Z", "")
        try:
            return datetime.fromisoformat(text).date()
        except ValueError:
            pass
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text[:19] if fmt.startswith("%Y-%m-%d %H") else text, fmt).date()
        except ValueError:
            continue
    return None


def _portal(source: str, url: str) -> str:
    alias = _PORTAL_ALIASES.get(source.strip().lower())
    if alias:
        return alias
    return portal_of(url)


def iter_export_rows(raw_dir: Path) -> list[dict[str, str]]:
    csvs = sorted(path for path in raw_dir.glob("*.csv") if path.is_file())
    if not csvs:
        raise FileNotFoundError(f"no CSV export in {raw_dir}")
    rows: list[dict[str, str]] = []
    for path in csvs:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = _header_map(reader.fieldnames)
            for row in reader:
                url = _cell(row, headers, _URL_HEADERS)
                if not url:
                    continue
                rows.append(
                    {
                        "url": url,
                        "portal": _portal(_cell(row, headers, _PORTAL_HEADERS), url),
                        "date": _cell(row, headers, _DATE_HEADERS),
                    }
                )
    return rows


def select_urls(rows: list[dict[str, str]], as_of: date, window_days: int = WINDOW_DAYS) -> list[str]:
    cutoff = as_of - timedelta(days=window_days)
    seen: set[str] = set()
    urls: list[str] = []
    for row in rows:
        when = _parse_date(row["date"])
        if when is None or when < cutoff or when > as_of:
            continue
        if row["portal"] not in INCLUDED_PORTALS:
            continue
        url = row["url"]
        if url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return urls


def build_corpus(raw_dir: Path, out_path: Path, *, as_of: date | None = None) -> list[str]:
    """Write de-duplicated Listing URLs from the last 14 days to out_path. Returns the URLs."""
    urls = select_urls(iter_export_rows(raw_dir), as_of or date.today())
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(urls) + ("\n" if urls else ""), encoding="utf-8")
    return urls
