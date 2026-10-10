from datetime import date
from pathlib import Path

from dealscout.collect.corpus import INCLUDED_PORTALS, build_corpus, select_urls


def _write_csv(path: Path) -> None:
    path.write_text(
        """url,source,last_seen
https://www.rumah123.com/en/property/a,rumah123,2026-10-10
https://www.rumah123.com/en/property/b,rumah123,2026-10-01
https://www.99.co/id/properti/c,99.co,2026-10-09
https://www.pinhome.id/dijual/rumah-sekunder/unit/d,pinhome,2026-09-28
https://masuksini.com/detail-properti/MS-1/e/,masuksini,2026-10-05
https://idrumah.com/properti/tangerang-selatan/1-f/,idrumah,2026-10-08
https://www.olx.co.id/item/g,OLX,2026-10-10
https://www.lamudi.co.id/house/h,lamudi,2026-10-10
https://www.rumah123.com/en/property/old,rumah123,2026-09-20
https://www.rumah123.com/en/property/a,rumah123,2026-10-09
""",
        encoding="utf-8",
    )


def test_corpus_keeps_last_fourteen_days_readable_portals_and_olx(tmp_path: Path):
    raw = tmp_path / "raw"
    raw.mkdir()
    _write_csv(raw / "tracker.csv")
    out = tmp_path / "corpus.txt"
    urls = build_corpus(raw, out, as_of=date(2026, 10, 10))
    assert urls == [
        "https://www.rumah123.com/en/property/a",
        "https://www.rumah123.com/en/property/b",
        "https://www.99.co/id/properti/c",
        "https://www.pinhome.id/dijual/rumah-sekunder/unit/d",
        "https://masuksini.com/detail-properti/MS-1/e/",
        "https://idrumah.com/properti/tangerang-selatan/1-f/",
        "https://www.olx.co.id/item/g",
    ]
    assert "olx" in INCLUDED_PORTALS
    written = [line for line in out.read_text(encoding="utf-8").splitlines() if line]
    assert written == urls
    assert "https://www.lamudi.co.id/house/h" not in urls
    assert "https://www.rumah123.com/en/property/old" not in urls
    assert urls.count("https://www.rumah123.com/en/property/a") == 1


def test_select_urls_drops_rows_outside_the_window():
    rows = [
        {"url": "https://www.rumah123.com/a", "portal": "rumah123", "date": "2026-09-26"},
        {"url": "https://www.rumah123.com/b", "portal": "rumah123", "date": "2026-09-25"},
    ]
    urls = select_urls(rows, as_of=date(2026, 10, 10))
    assert urls == ["https://www.rumah123.com/a"]
