"""Write a Shortlist and Dossier as one static HTML file and a JSON file beside it."""

from __future__ import annotations

import html
import json
from pathlib import Path

from dealscout.domain import REQUIRED_FIELDS, Deal, ListingRecord, Shortlist

HTML_NAME = "report.html"
JSON_NAME = "shortlist.json"

_FIELD_LABELS = {
    "price_rp": "price",
    "land_m2": "land size",
    "building_m2": "building size",
    "bedrooms": "bedrooms",
    "bathrooms": "bathrooms",
    "area": "Area",
    "property_type": "property type",
    "readiness": "Readiness",
}


class ReportShortlist(Shortlist):
    """Hand-made Shortlist for report tests. Lists now live on the Shortlist contract."""


def write_report(shortlist: Shortlist, out_dir: Path) -> Path:
    """Write report.html and shortlist.json into out_dir. Returns the HTML path."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    quarantined = _held_aside(shortlist, "quarantined_listings")
    unreachable = _held_aside(shortlist, "unreachable_listings")
    payload = _payload(shortlist, quarantined, unreachable)
    json_path = out_dir / JSON_NAME
    html_path = out_dir / HTML_NAME
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    html_path.write_text(_render(shortlist, quarantined, unreachable), encoding="utf-8")
    return html_path


def _held_aside(shortlist: Shortlist, name: str) -> list[ListingRecord]:
    raw = getattr(shortlist, name, None)
    if not raw:
        extra = getattr(shortlist, "__pydantic_extra__", None) or {}
        raw = extra.get(name)
    if not raw:
        return []
    rows: list[ListingRecord] = []
    for item in raw:
        if isinstance(item, ListingRecord):
            rows.append(item)
        else:
            rows.append(ListingRecord.model_validate(item))
    return rows


def _payload(
    shortlist: Shortlist,
    quarantined: list[ListingRecord],
    unreachable: list[ListingRecord],
) -> dict:
    body = shortlist.model_dump(mode="json")
    body["quarantined_listings"] = [r.model_dump(mode="json") for r in quarantined]
    body["unreachable_listings"] = [r.model_dump(mode="json") for r in unreachable]
    records = [deal.record.model_dump(mode="json") for deal in shortlist.deals]
    records.extend(body["quarantined_listings"])
    records.extend(body["unreachable_listings"])
    body["records"] = records
    return body


def _render(
    shortlist: Shortlist,
    quarantined: list[ListingRecord],
    unreachable: list[ListingRecord],
) -> str:
    brief = shortlist.brief
    deals_html = "".join(_deal_block(deal, brief.budget_rp) for deal in shortlist.deals) or (
        '<p class="empty">No Deals on this Shortlist.</p>'
    )
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>DealScout Shortlist — {_esc(brief.area)}</title>\n"
        f"<style>{_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        "<header>\n"
        '<p class="mark">DealScout</p>\n'
        f"<h1>Shortlist for {_esc(brief.area)}</h1>\n"
        f'<p class="lede"><strong>Brief</strong> · Area {_esc(brief.area)} · '
        f"budget {_rp(brief.budget_rp)} · Headroom {brief.headroom:.0%} · "
        f"ceiling {_rp(brief.price_ceiling_rp)}"
        f"{_brief_soft(brief)}</p>\n"
        "<ul class='counts'>\n"
        f"<li><span>{len(shortlist.deals)}</span> Deals</li>\n"
        f"<li><span>{shortlist.confirmed}</span> Confirmed</li>\n"
        f"<li><span>{shortlist.quarantined}</span> Quarantined</li>\n"
        f"<li><span>{shortlist.unreachable}</span> Unreachable</li>\n"
        f"<li><span>{shortlist.considered}</span> considered</li>\n"
        "</ul>\n"
        "</header>\n"
        "<main>\n"
        "<h2>Deals</h2>\n"
        f"{deals_html}\n"
        "<h2>Quarantined Listings</h2>\n"
        f"{_held_table(quarantined, shortlist.quarantined, 'Quarantined')}\n"
        "<h2>Unreachable Listings</h2>\n"
        f"{_held_table(unreachable, shortlist.unreachable, 'Unreachable')}\n"
        "</main>\n"
        "</body>\n"
        "</html>\n"
    )


def _brief_soft(brief) -> str:
    bits = []
    if brief.land_m2:
        bits.append(f"land {brief.land_m2:g} m²")
    if brief.building_m2:
        bits.append(f"building {brief.building_m2:g} m²")
    if brief.bedrooms is not None:
        bits.append(f"bedrooms {brief.bedrooms}")
    return (" · " + " · ".join(bits)) if bits else ""


def _deal_block(deal: Deal, budget_rp: int) -> str:
    record = deal.record
    valuation = deal.valuation
    rank = deal.rank if deal.rank is not None else "—"
    asking = record.price_rp
    expected = valuation.expected_price_rp
    below = _below_market(valuation.ratio)
    over = ""
    if asking is not None and asking > budget_rp:
        over = (
            "<p class='over'>Asking price is over budget, still inside Headroom.</p>\n"
        )
    soft = ""
    if deal.soft_misses:
        soft = (
            f"<p class='soft'>Soft misses vs the Brief: "
            f"{_esc(', '.join(deal.soft_misses))}.</p>\n"
        )
    heading = _esc(record.title) if record.title else _link(record.url)
    listing_line = _link(record.url) if record.title else ""
    portal = f"Portal {_esc(record.portal)}"
    if record.listing_id:
        portal += f" · Listing {_esc(record.listing_id)}"
    return (
        f"<article class='deal' id='deal-{_esc(str(rank))}'>\n"
        f"<p class='kicker'>Deal {_esc(str(rank))} · rank {_esc(str(rank))}</p>\n"
        f"<h3>{heading}</h3>\n"
        f"<p class='portal'>{listing_line}{' · ' if listing_line else ''}{portal}</p>\n"
        "<dl class='meta'>\n"
        f"<div><dt>rank</dt><dd>{_esc(str(rank))}</dd></div>\n"
        f"<div><dt>asking price</dt><dd>{_rp(asking)}</dd></div>\n"
        f"<div><dt>expected price</dt><dd>{_rp(expected)}</dd></div>\n"
        f"<div><dt>Below Market</dt><dd class='below'>{_esc(below)}</dd></div>\n"
        f"<div><dt>Valuation</dt><dd>{_esc(valuation.tier.value.replace('_', ' '))}</dd></div>\n"
        "</dl>\n"
        f"{over}{soft}"
        f"{_comps_block(valuation)}\n"
        "<h3>Dossier</h3>\n"
        "<p class='hint'>Each required field, where it was read from, and the quoted words from the page.</p>\n"
        f"{_dossier_table(record)}\n"
        "</article>\n"
    )


def _comps_block(valuation) -> str:
    urls = valuation.market.comp_urls
    if not urls:
        return "<h3>Comps</h3>\n<p class='empty'>No Comps on this Valuation.</p>"
    rows = "".join(
        f"<tr><td>{i}</td><td>{_link(url)}</td></tr>" for i, url in enumerate(urls, start=1)
    )
    return (
        "<h3>Comps used</h3>\n"
        f"<p>{valuation.market.comp_count} Comps in {_esc(valuation.market.area)}. "
        f"Market Price {_rp(int(round(valuation.market.median_rp_per_land_m2)))} / m² land, "
        f"{_rp(int(round(valuation.market.median_rp_per_building_m2)))} / m² building.</p>\n"
        "<table class='comps'><thead><tr><th>#</th><th>Listing</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def _dossier_table(record: ListingRecord) -> str:
    rows = []
    for field in REQUIRED_FIELDS:
        value = getattr(record, field)
        source = record.sources.get(field)
        source_text = source.value if source is not None else "not stated"
        quote = record.evidence.get(field) or "—"
        rows.append(
            "<tr>"
            f"<td>{_esc(_FIELD_LABELS.get(field, field))}</td>"
            f"<td>{_esc(_field_value(field, value))}</td>"
            f"<td>{_esc(source_text)}</td>"
            f"<td class='quote'>{_esc(quote)}</td>"
            "</tr>"
        )
    return (
        "<table class='dossier'><thead><tr>"
        "<th>field</th><th>value</th><th>read from</th><th>quoted words from the page</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def _held_table(records: list[ListingRecord], count: int, label: str) -> str:
    if not records:
        if count:
            return (
                f"<p class='empty'>{count} {label} Listing"
                f"{'s' if count != 1 else ''} counted, with no records attached.</p>"
            )
        return f"<p class='empty'>No {label} Listings.</p>"
    rows = []
    for record in records:
        reason = record.status_reason or "reason not recorded"
        standing = record.status.value if record.status is not None else label.lower()
        rows.append(
            "<tr>"
            f"<td>{_link(record.url)}</td>"
            f"<td>{_esc(standing)}</td>"
            f"<td class='reason'>{_esc(reason)}</td>"
            "</tr>"
        )
    return (
        "<table class='listings'><thead><tr>"
        "<th>Listing</th><th>standing</th><th>reason</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def _below_market(ratio: float) -> str:
    pct = max(0.0, (1.0 - ratio) * 100.0)
    return f"{pct:.1f}% below expected (ratio {ratio:.3f})"


def _field_value(field: str, value: object) -> str:
    if value is None:
        return "—"
    if field == "price_rp" and isinstance(value, int):
        return _rp(value)
    if field in {"land_m2", "building_m2"} and isinstance(value, (int, float)):
        return f"{value:g} m²"
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _rp(value: int | float | None) -> str:
    if value is None:
        return "—"
    return "Rp " + f"{int(round(value)):,}".replace(",", ".")


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _link(url: str, label: str | None = None) -> str:
    shown = label or url
    return f'<a href="{_esc(url)}">{_esc(shown)}</a>'


_CSS = """
:root {
  --ink: #1b1712;
  --muted: #5e574c;
  --paper: #f3ead9;
  --card: #fffaf1;
  --rule: #d3c6ae;
  --below: #8a3d14;
  --held: #4a4338;
}
* { box-sizing: border-box; }
body {
  margin: 0 auto;
  max-width: 52rem;
  padding: 2rem 1.25rem 4rem;
  background: var(--paper);
  color: var(--ink);
  font: 16px/1.45 "Segoe UI", "Iowan Old Style", Georgia, serif;
}
header { border-bottom: 2px solid var(--ink); padding-bottom: 1rem; margin-bottom: 1.25rem; }
.mark {
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-size: 0.72rem;
  margin: 0 0 0.35rem;
  color: var(--below);
}
h1 { font-size: 1.85rem; font-weight: 650; margin: 0 0 0.5rem; }
h2 { font-size: 1.15rem; margin: 2rem 0 0.75rem; border-bottom: 1px solid var(--rule); padding-bottom: 0.3rem; }
h3 { font-size: 1rem; margin: 1rem 0 0.4rem; }
.lede, .portal, .hint, .soft, .over { color: var(--muted); }
.counts { display: flex; flex-wrap: wrap; gap: 0.75rem 1.25rem; list-style: none; padding: 0; margin: 0.75rem 0 0; }
.counts span { font-weight: 700; margin-right: 0.25rem; }
.deal {
  background: var(--card);
  border: 1px solid var(--rule);
  padding: 1rem 1.1rem 1.15rem;
  margin: 0 0 1rem;
}
.kicker { font-size: 0.8rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--below); font-weight: 650; margin: 0 0 0.35rem; }
h3 { overflow-wrap: anywhere; }
.portal { margin: 0 0 0.5rem; font-size: 0.92rem; }
.meta { display: grid; grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr)); gap: 0.65rem 1rem; margin: 0.75rem 0; }
.meta div { margin: 0; }
dt { font-size: 0.72rem; letter-spacing: 0.05em; text-transform: uppercase; color: var(--muted); }
dd { margin: 0.15rem 0 0; font-size: 1.05rem; font-weight: 650; }
.below { color: var(--below); }
.comps, .dossier, .listings { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
.comps th, .comps td, .dossier th, .dossier td, .listings th, .listings td {
  text-align: left; vertical-align: top; padding: 0.4rem 0.5rem; border-bottom: 1px solid var(--rule);
}
.quote { font-style: italic; color: var(--held); }
.reason { color: var(--below); }
a { color: var(--below); }
.empty { color: var(--muted); }
"""
