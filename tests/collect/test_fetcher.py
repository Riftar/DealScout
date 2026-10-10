import httpx

from dealscout.collect.fetcher import Fetcher, portal_of

ROBOTS = "User-agent: *\nDisallow: /search/\nCrawl-delay: 5\n"
PAGE = b"<html>" + b"x" * 20_000 + b"</html>"


def make_fetcher(tmp_path, pages, sleeps):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text=ROBOTS)
        status, body = pages.get(request.url.path, (404, b"missing"))
        return httpx.Response(status, content=body)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    return Fetcher(tmp_path, client=client, sleep=sleeps.append)


def test_saves_a_snapshot_of_a_full_page(tmp_path):
    fetcher = make_fetcher(tmp_path, {"/property/a": (200, PAGE)}, [])
    snapshot = fetcher.fetch("https://www.rumah123.com/property/a")
    assert snapshot.reachable
    assert snapshot.portal == "rumah123"
    assert snapshot.content_bytes == len(PAGE)
    assert (tmp_path / "rumah123").is_dir()


def test_robots_disallow_makes_the_listing_unreachable(tmp_path):
    fetcher = make_fetcher(tmp_path, {"/search/a": (200, PAGE)}, [])
    snapshot = fetcher.fetch("https://www.rumah123.com/search/a")
    assert snapshot.unreachable_reason == "disallowed by robots.txt"


def test_empty_shell_is_unreachable(tmp_path):
    fetcher = make_fetcher(tmp_path, {"/item/a": (200, b"<html></html>")}, [])
    snapshot = fetcher.fetch("https://www.olx.co.id/item/a")
    assert snapshot.unreachable_reason == "page is an empty shell"
    assert snapshot.path is None


def test_http_error_is_unreachable(tmp_path):
    fetcher = make_fetcher(tmp_path, {}, [])
    snapshot = fetcher.fetch("https://www.99.co/id/properti/gone")
    assert snapshot.unreachable_reason == "http 404"


def test_second_request_to_a_host_waits_for_the_crawl_delay(tmp_path):
    sleeps: list[float] = []
    fetcher = make_fetcher(tmp_path, {"/property/a": (200, PAGE)}, sleeps)
    fetcher.fetch("https://www.rumah123.com/property/a")
    fetcher.fetch("https://www.rumah123.com/property/a")
    assert len(sleeps) == 1
    assert 4.5 < sleeps[0] <= 5


def test_portal_names():
    assert portal_of("https://www.99.co/id/properti/x") == "99co"
    assert portal_of("https://m.olx.co.id/item/x") == "olx"
