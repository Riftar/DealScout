"""Read what a Snapshot states in its own structured data, in code, before any model is asked."""

import json
import re
from typing import Any

from selectolax.lexbor import LexborHTMLParser

from dealscout.domain import FieldSource, ListingRecord, PropertyType, Readiness, normalize_area


def _number(value: Any) -> float | None:
    if isinstance(value, dict):
        value = value.get("value")
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(str(value).replace(",", "").strip())
    except ValueError:
        return None
    return number if number > 0 else None


def _whole(value: Any) -> int | None:
    number = _number(value)
    return int(number) if number is not None else None


def _json_ld(tree: LexborHTMLParser) -> list[dict]:
    nodes: list[dict] = []
    for script in tree.css('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.text())
        except json.JSONDecodeError:
            continue
        for item in data if isinstance(data, list) else [data]:
            if isinstance(item, dict):
                nodes.extend(item.get("@graph", [item]))
    return [node for node in nodes if isinstance(node, dict)]


def _has_type(node: dict, name: str) -> bool:
    kinds = node.get("@type", [])
    return name in (kinds if isinstance(kinds, list) else [kinds])


def _breadcrumb_names(nodes: list[dict]) -> list[str]:
    names: list[str] = []
    for node in nodes:
        if _has_type(node, "BreadcrumbList"):
            for item in node.get("itemListElement", []):
                name = item.get("name") or (item.get("item") or {}).get("name") if isinstance(item.get("item"), dict) else item.get("name")
                if name:
                    names.append(name)
    return names[::-1]  # most specific first


def _set(record: ListingRecord, field: str, value: Any) -> None:
    if value is not None and getattr(record, field) is None:
        setattr(record, field, value)
        record.sources[field] = FieldSource.STRUCTURED


def _read_rumah123(record: ListingRecord, nodes: list[dict]) -> None:
    for node in nodes:
        if not _has_type(node, "RealEstateListing"):
            continue
        home = node.get("mainEntity") or {}
        offer = home.get("offers") or {}
        if offer.get("priceCurrency", "IDR") == "IDR":
            _set(record, "price_rp", _whole(offer.get("price")))
        _set(record, "building_m2", _number(home.get("floorSize")))
        _set(record, "bedrooms", _whole(home.get("numberOfBedrooms")))
        _set(record, "bathrooms", _whole(home.get("numberOfBathroomsTotal")))
        _set(record, "listing_id", home.get("sku"))
        _set(record, "title", node.get("name"))
        _set(record, "description", home.get("description") or node.get("description"))
        locality = (home.get("address") or {}).get("addressLocality")
        _set(record, "detail_location", locality)
        _set(record, "area", normalize_area(locality, *_breadcrumb_names(nodes)))
        if _has_type(home, "SingleFamilyResidence"):
            _set(record, "property_type", PropertyType.HOUSE)
    if "/new-launch/" in record.url:
        _set(record, "readiness", Readiness.INDENT)


def _read_99co(record: ListingRecord, tree: LexborHTMLParser, nodes: list[dict]) -> None:
    script = tree.css_first("script#__NEXT_DATA__")
    try:
        data = json.loads(script.text())["props"]["pageProps"]["data"] if script else {}
    except (json.JSONDecodeError, KeyError, TypeError):
        data = {}
    attributes = data.get("attributes") or {}
    _set(record, "price_rp", _whole((data.get("price") or {}).get("price")))
    _set(record, "land_m2", _number(attributes.get("land_area")))
    _set(record, "building_m2", _number(attributes.get("builtup_area")))
    _set(record, "bedrooms", _whole(attributes.get("bedrooms")))
    _set(record, "bathrooms", _whole(attributes.get("bathrooms")))
    _set(record, "floors", _whole(attributes.get("floors")))
    _set(record, "electricity_w", _whole(attributes.get("electricity")))
    _set(record, "year_built", _whole(attributes.get("year_built")))
    _set(record, "certificate", (attributes.get("certificate") or {}).get("value") or None)
    _set(record, "listing_id", str(data["id"]) if data.get("id") else None)
    _set(record, "title", data.get("title"))
    _set(record, "description", data.get("description"))
    kind = ((attributes.get("property_type") or {}).get("value") or "").lower()
    if kind:
        _set(record, "property_type", PropertyType.HOUSE if kind == "rumah" else PropertyType.OTHER)
    market = ((attributes.get("market_type") or {}).get("value") or "").lower()
    if market:
        _set(record, "readiness", Readiness.READY if market == "secondary" else Readiness.INDENT)
    location = data.get("location") or {}
    district = (location.get("district") or {}).get("name")
    city = (location.get("city") or {}).get("name")
    _set(record, "detail_location", ", ".join(part for part in (district, city) if part) or None)
    _set(record, "area", normalize_area(district, city, *_breadcrumb_names(nodes)))
    # Fall back to the page's Product data when the page state is missing.
    for node in nodes:
        if _has_type(node, "Product"):
            _set(record, "price_rp", _whole((node.get("offers") or {}).get("price")))
            _set(record, "title", node.get("name"))
            _set(record, "description", node.get("description"))


_CLEAN_SPACE = re.compile(r"[ \t\r\f\v]+")


def read_structured(html: str, url: str, portal: str) -> ListingRecord:
    """A Listing Record holding only what the page's structured data states."""
    record = ListingRecord(url=url, portal=portal)
    tree = LexborHTMLParser(html)
    nodes = _json_ld(tree)
    if portal == "rumah123":
        _read_rumah123(record, nodes)
    elif portal == "99co":
        _read_99co(record, tree, nodes)
    if record.description:
        record.description = _CLEAN_SPACE.sub(" ", record.description).strip()
    return record
