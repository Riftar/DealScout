"""End-to-end Run on fakes: happy path, unreachable retry, quarantine, resume."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from dealscout.domain import Brief, PropertyType, Readiness, Shortlist, Snapshot, Status
from dealscout.run.fakes import read_text, run_checks, write_report
from dealscout.run.graph import build_graph, run_brief
from dealscout.run.seams import Seams


def _page(land: float, building: float, price: int, area: str = "Bintaro") -> str:
    """Minimal HTML with description the fake Scout can read."""
    return (
        f"<html><body><p>Rumah siap huni di {area}. "
        f"Luas tanah: {land} m2. Luas bangunan: {building} m2. "
        f"Kamar tidur: 3. Kamar mandi: 2. Harga Rp {price}.</p></body></html>"
    )


class FakeFetcher:
    def __init__(self, pages: dict[str, str | None], snapshot_dir: Path):
        self.pages = pages
        self.snapshot_dir = snapshot_dir
        self.calls: list[str] = []

    def fetch(self, url: str) -> Snapshot:
        self.calls.append(url)
        portal = "test"
        now = datetime.now(UTC)
        html = self.pages.get(url)
        if html is None:
            return Snapshot(
                url=url,
                portal=portal,
                fetched_at=now,
                http_status=0,
                unreachable_reason="request failed: Timeout",
            )
        path = self.snapshot_dir / f"{len(self.calls)}.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
        return Snapshot(
            url=url,
            portal=portal,
            fetched_at=now,
            http_status=200,
            path=path.as_posix(),
            content_bytes=len(html.encode()),
            sha256="x",
        )


def _structured(html: str, url: str, portal: str):
    """Tiny structured reader that leaves sizes to the text fake."""
    from dealscout.domain import ListingRecord

    price = 900_000_000
    if "Harga Rp" in html:
        try:
            price = int(html.split("Harga Rp")[1].split(".")[0].strip().replace(",", ""))
        except ValueError:
            pass
    area = "Bintaro"
    for name in ("Bintaro", "BSD/Serpong", "Depok"):
        if name in html:
            area = name
            break
    return ListingRecord(
        url=url,
        portal=portal,
        price_rp=price,
        area=area,
        property_type=PropertyType.HOUSE,
        bedrooms=None,
        bathrooms=None,
        land_m2=None,
        building_m2=None,
        readiness=None,
        title="test",
        description=html,
    )


def _seams(fetcher: FakeFetcher) -> Seams:
    return Seams(
        fetcher_factory=lambda _dir: fetcher,
        read_structured=_structured,
        read_text=read_text,
        run_checks=run_checks,
        verify=lambda record, html, model=None: [],
        arbitrate=__import__("dealscout.run.fakes", fromlist=["arbitrate"]).arbitrate,
        market_price=__import__("dealscout.run.fakes", fromlist=["market_price"]).market_price,
        value=__import__("dealscout.run.fakes", fromlist=["value"]).value,
        shortlist=__import__("dealscout.run.fakes", fromlist=["shortlist"]).shortlist,
        write_report=write_report,
        scout_model=None,
        verifier_model=None,
    )


def test_run_end_to_end_on_fakes(tmp_path: Path):
    urls = [
        "https://example.test/a",
        "https://example.test/b",
        "https://example.test/c",
        "https://example.test/dead",
    ]
    # Three comps in Bintaro at market; one unreachable that recovers on retry.
    pages = {
        urls[0]: _page(100, 80, 800_000_000),
        urls[1]: _page(110, 85, 1_200_000_000),
        urls[2]: _page(90, 70, 950_000_000),
        urls[3]: None,  # first fetch fails
    }
    snap_dir = tmp_path / "snapshots"
    fetcher = FakeFetcher(pages, snap_dir)

    # Second fetch of the dead URL succeeds.
    original_fetch = fetcher.fetch

    def fetch_with_recovery(url: str) -> Snapshot:
        snap = original_fetch(url)
        if url == urls[3] and fetcher.calls.count(url) >= 2:
            html = _page(95, 75, 700_000_000)
            path = snap_dir / "recovered.html"
            path.write_text(html, encoding="utf-8")
            return Snapshot(
                url=url,
                portal="test",
                fetched_at=datetime.now(UTC),
                http_status=200,
                path=path.as_posix(),
                content_bytes=len(html),
                sha256="y",
            )
        return snap

    fetcher.fetch = fetch_with_recovery  # type: ignore[method-assign]

    brief = Brief(area="Bintaro", budget_rp=1_500_000_000)
    final = run_brief(
        brief,
        urls,
        snapshot_dir=snap_dir,
        out_dir=tmp_path / "out",
        state_dir=tmp_path / "state",
        seams=_seams(fetcher),
        thread_id="test-e2e",
    )
    shortlist = Shortlist.model_validate(final["shortlist"])
    assert shortlist.confirmed == 4
    assert shortlist.unreachable == 0
    assert shortlist.quarantined == 0
    assert Path(final["report_path"]).is_file()
    assert (tmp_path / "out" / "shortlist.json").is_file()
    # At least one Deal below market among the four.
    assert shortlist.deals
    assert urls[3] in fetcher.calls
    assert fetcher.calls.count(urls[3]) == 2


def test_unreachable_after_one_retry(tmp_path: Path):
    url = "https://example.test/gone"
    fetcher = FakeFetcher({url: None}, tmp_path / "snapshots")
    brief = Brief(area="Bintaro", budget_rp=1_500_000_000)
    final = run_brief(
        brief,
        [url],
        snapshot_dir=tmp_path / "snapshots",
        out_dir=tmp_path / "out",
        state_dir=tmp_path / "state",
        seams=_seams(fetcher),
        thread_id="test-unreachable",
    )
    shortlist = Shortlist.model_validate(final["shortlist"])
    assert shortlist.unreachable == 1
    assert shortlist.confirmed == 0
    assert fetcher.calls.count(url) == 2
    unreachable = final["unreachable"]
    assert unreachable[0]["status"] == Status.UNREACHABLE.value


def test_quarantine_when_required_fields_stay_missing(tmp_path: Path):
    url = "https://example.test/thin"
    html = "<html><body><p>No sizes here, siap huni.</p></body></html>"
    fetcher = FakeFetcher({url: html}, tmp_path / "snapshots")

    def thin_structured(page: str, page_url: str, portal: str):
        from dealscout.domain import ListingRecord

        return ListingRecord(
            url=page_url,
            portal=portal,
            price_rp=500_000_000,
            area="Bintaro",
            property_type=PropertyType.HOUSE,
            description=page,
            readiness=Readiness.READY,
        )

    seams = _seams(fetcher)
    seams.read_structured = thin_structured
    brief = Brief(area="Bintaro", budget_rp=1_500_000_000)
    final = run_brief(
        brief,
        [url],
        snapshot_dir=tmp_path / "snapshots",
        out_dir=tmp_path / "out",
        state_dir=tmp_path / "state",
        seams=seams,
        thread_id="test-quarantine",
    )
    shortlist = Shortlist.model_validate(final["shortlist"])
    assert shortlist.quarantined == 1
    assert shortlist.confirmed == 0
    assert final["quarantined"][0]["status"] == Status.QUARANTINED.value


def test_checkpoint_resume_skips_completed_collect(tmp_path: Path):
    urls = [
        "https://example.test/a",
        "https://example.test/b",
        "https://example.test/c",
    ]
    pages = {u: _page(100 + i * 5, 80, 900_000_000 + i * 50_000_000) for i, u in enumerate(urls)}
    snap_dir = tmp_path / "snapshots"
    fetcher = FakeFetcher(pages, snap_dir)
    seams = _seams(fetcher)
    state_dir = tmp_path / "state"
    db = state_dir / "runs.sqlite"
    state_dir.mkdir(parents=True)
    brief = Brief(area="Bintaro", budget_rp=2_000_000_000)

    from langgraph.checkpoint.sqlite import SqliteSaver

    initial = {
        "brief": brief.model_dump(mode="json"),
        "urls": urls,
        "snapshots": [],
        "records": [],
        "confirmed": [],
        "quarantined": [],
        "unreachable": [],
        "fetch_retries": {},
        "check_retries": {},
        "snapshot_dir": snap_dir.as_posix(),
        "out_dir": (tmp_path / "out").as_posix(),
    }
    config = {"configurable": {"thread_id": "resume-1"}}
    with SqliteSaver.from_conn_string(str(db)) as checkpointer:
        checkpointer.setup()
        app = build_graph(seams, checkpointer)
        # Run only through collect.
        for chunk in app.stream(initial, config=config, stream_mode="updates"):
            if "collect" in chunk:
                break

    calls_after_collect = list(fetcher.calls)
    assert len(calls_after_collect) == 3

    with SqliteSaver.from_conn_string(str(db)) as checkpointer:
        app = build_graph(seams, checkpointer)
        final = app.invoke(None, config=config)

    assert fetcher.calls == calls_after_collect  # collect not repeated
    shortlist = Shortlist.model_validate(final["shortlist"])
    assert shortlist.confirmed == 3
    assert Path(final["report_path"]).is_file()
    saved = json.loads((tmp_path / "out" / "shortlist.json").read_text(encoding="utf-8"))
    assert saved["confirmed"] == 3
