"""The only door to a Portal: plain requests that honour robots.txt and crawl delays."""

import hashlib
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from dealscout.domain import Snapshot

USER_AGENT = "DealScoutBot/0.1 (+https://github.com/Riftar/DealScout; hackathon research)"
DEFAULT_DELAY_SECONDS = 3.0
# A page smaller than this carries no listing: it is an empty shell or a block page.
MIN_USEFUL_BYTES = 10_000

PORTALS = {
    "rumah123.com": "rumah123",
    "99.co": "99co",
    "pinhome.id": "pinhome",
    "masuksini.com": "masuksini",
    "idrumah.com": "idrumah",
    "olx.co.id": "olx",
    "lamudi.co.id": "lamudi",
}


def portal_of(url: str) -> str:
    host = (urlsplit(url).hostname or "").removeprefix("www.")
    for domain, name in PORTALS.items():
        if host == domain or host.endswith("." + domain):
            return name
    return host


class Fetcher:
    def __init__(self, snapshot_dir: Path, client: httpx.Client | None = None, sleep=time.sleep):
        self.snapshot_dir = snapshot_dir
        self.client = client or httpx.Client(
            headers={"User-Agent": USER_AGENT, "Accept-Language": "id,en;q=0.8"},
            follow_redirects=True,
            timeout=30,
        )
        self._sleep = sleep
        self._robots: dict[str, RobotFileParser | None] = {}
        self._last_request: dict[str, float] = {}

    def _robots_for(self, url: str) -> RobotFileParser | None:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._robots:
            parser: RobotFileParser | None = RobotFileParser()
            try:
                response = self.client.get(f"{origin}/robots.txt")
                if response.status_code >= 400:
                    parser = None  # no robots.txt: nothing is disallowed
                else:
                    parser.parse(response.text.splitlines())
            except httpx.HTTPError:
                parser = None
            self._robots[origin] = parser
        return self._robots[origin]

    def _wait_turn(self, url: str, robots: RobotFileParser | None) -> None:
        host = urlsplit(url).netloc
        delay = DEFAULT_DELAY_SECONDS
        if robots is not None:
            delay = max(delay, float(robots.crawl_delay(USER_AGENT) or 0))
        elapsed = time.monotonic() - self._last_request.get(host, float("-inf"))
        if elapsed < delay:
            self._sleep(delay - elapsed)
        self._last_request[host] = time.monotonic()

    def fetch(self, url: str) -> Snapshot:
        """Fetch one Listing page and save it. An unusable page comes back as Unreachable."""
        portal = portal_of(url)
        now = datetime.now(UTC)

        def unreachable(reason: str, status: int = 0, size: int = 0) -> Snapshot:
            return Snapshot(
                url=url, portal=portal, fetched_at=now, http_status=status,
                content_bytes=size, unreachable_reason=reason,
            )

        robots = self._robots_for(url)
        if robots is not None and not robots.can_fetch(USER_AGENT, url):
            return unreachable("disallowed by robots.txt")
        self._wait_turn(url, robots)
        try:
            response = self.client.get(url)
        except httpx.HTTPError as error:
            return unreachable(f"request failed: {type(error).__name__}")
        body = response.content
        if response.status_code != 200:
            return unreachable(f"http {response.status_code}", response.status_code, len(body))
        if len(body) < MIN_USEFUL_BYTES:
            return unreachable("page is an empty shell", 200, len(body))

        digest = hashlib.sha256(body).hexdigest()
        path = self.snapshot_dir / portal / f"{digest[:16]}.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        return Snapshot(
            url=url, portal=portal, fetched_at=now, http_status=200,
            path=path.as_posix(), sha256=digest, content_bytes=len(body),
        )
