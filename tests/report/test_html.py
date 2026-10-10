from pathlib import Path

from dealscout.domain import Shortlist
from dealscout.report.html import write_report

from tests.report.helpers import handmade_shortlist


def test_write_report_writes_html_and_json(tmp_path: Path):
    shortlist = handmade_shortlist()
    html_path = write_report(shortlist, tmp_path)
    json_path = tmp_path / "shortlist.json"
    assert html_path == tmp_path / "report.html"
    assert html_path.is_file()
    assert json_path.is_file()
    page = html_path.read_text(encoding="utf-8")
    payload = json_path.read_text(encoding="utf-8")
    assert "DealScout Shortlist" in page
    assert shortlist.brief.area in page
    assert "quarantined_listings" in payload
    assert "unreachable_listings" in payload


def test_html_is_self_contained(tmp_path: Path):
    page = write_report(handmade_shortlist(), tmp_path).read_text(encoding="utf-8")
    lowered = page.lower()
    assert "<style>" in lowered
    assert "cdn." not in lowered
    assert "googleapis.com" not in lowered
    assert "unpkg.com" not in lowered
    assert "<link " not in lowered
    assert "<script src" not in lowered


def test_each_deal_shows_rank_prices_comps_and_dossier(tmp_path: Path):
    page = write_report(handmade_shortlist(), tmp_path).read_text(encoding="utf-8")
    assert "Deal 1" in page
    assert "Deal 2" in page
    assert "asking price" in page
    assert "expected price" in page
    assert "Below Market" in page
    assert "Comps used" in page
    assert "https://example.test/comp/a" in page
    assert "Dossier" in page
    assert "quoted words from the page" in page
    assert "Luas tanah: 100 m2" in page
    assert "structured" in page
    assert "Rp 700.000.000" in page


def test_quarantined_and_unreachable_show_reasons(tmp_path: Path):
    page = write_report(handmade_shortlist(), tmp_path).read_text(encoding="utf-8")
    assert "Quarantined Listings" in page
    assert "land_m2 is missing" in page
    assert "Unreachable Listings" in page
    assert "request failed: Timeout" in page
    assert "https://www.olx.co.id/item/gone" in page


def test_page_escapes_quotes_from_the_listing(tmp_path: Path):
    page = write_report(handmade_shortlist(), tmp_path).read_text(encoding="utf-8")
    assert "<script>" not in page.split("<style>")[0]
    assert "&quot;siap huni&quot;" in page
    assert "&amp;" in page


def test_write_report_without_extras_still_opens(tmp_path: Path):
    filled = handmade_shortlist()
    shortlist = Shortlist(
        brief=filled.brief,
        deals=filled.deals,
        considered=filled.considered,
        confirmed=filled.confirmed,
        quarantined=filled.quarantined,
        unreachable=filled.unreachable,
    )
    path = write_report(shortlist, tmp_path)
    page = path.read_text(encoding="utf-8")
    assert path.is_file()
    assert "Quarantined Listings" in page
    assert "Unreachable Listings" in page
