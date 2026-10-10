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
_LAND_IN_TEXT = re.compile(r"luas\s*tanah\s+(\d+(?:[.,]\d+)?)\s*m", re.I)
_RUPIAH = re.compile(r"rp\.?\s*([\d.,]+)\s*(miliar|milyar|juta)?", re.I)
_IDRUMAH_ID = re.compile(r"/(\d+)(?:-[^/]*)?/?$", re.I)
_IDRUMAH_SPEC = {
    "luas tanah": "land_m2",
    "luas bangunan": "building_m2",
    "kamar tidur": "bedrooms",
    "kamar mandi": "bathrooms",
    "tingkat": "floors",
}


def _id_decimal(raw: str) -> float | None:
    if "," in raw and "." in raw:
        return _number(raw.replace(".", "").replace(",", "."))
    if "," in raw:
        parts = raw.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            return _number(raw.replace(",", "."))
        return _number(raw.replace(",", ""))
    if "." in raw:
        parts = raw.split(".")
        if len(parts) == 2 and len(parts[1]) <= 2:
            return _number(raw)
        return _number(raw.replace(".", ""))
    return _number(raw)


def parse_rupiah(text: str | None) -> int | None:
    """Whole Rupiah from Portal display text such as 'Rp. 700 Juta' or 'Rp 2,5 Miliar'."""
    if not text:
        return None
    match = _RUPIAH.search(_CLEAN_SPACE.sub(" ", text.replace("\xa0", " ")))
    if not match:
        return _whole(re.sub(r"[^\d]", "", text) or None)
    raw, unit = match.group(1), (match.group(2) or "").lower()
    if unit:
        amount = _id_decimal(raw)
        if amount is None:
            return None
        factor = 1_000_000_000 if unit.startswith("mili") else 1_000_000
        value = int(round(amount * factor))
        return value if value > 0 else None
    digits = re.sub(r"[^\d]", "", raw)
    return _whole(digits or None)


def _readiness_from_condition(condition: Any) -> Readiness | None:
    text = str(condition or "").lower()
    if "usedcondition" in text:
        return Readiness.READY
    if "newcondition" in text:
        return Readiness.INDENT
    return None


def _house_or_other(*names: str | None) -> PropertyType | None:
    blob = " ".join(n for n in names if n).lower()
    if not blob:
        return None
    if any(word in blob for word in ("kost", "kosan", "apartemen", "apartment", "ruko", "kios")):
        return PropertyType.OTHER
    if "rumah" in blob or "house" in blob or "singlefamily" in blob:
        return PropertyType.HOUSE
    return None


def _read_pinhome(record: ListingRecord, tree: LexborHTMLParser, nodes: list[dict]) -> None:
    og = tree.css_first('meta[property="og:description"]')
    og_text = (og.attributes or {}).get("content") if og else None
    if og_text:
        land = _LAND_IN_TEXT.search(og_text)
        if land:
            _set(record, "land_m2", _number(land.group(1).replace(",", ".")))

    crumbs = _breadcrumb_names(nodes)
    for node in nodes:
        if _has_type(node, "RealEstateListing"):
            offers = node.get("offers") or {}
            home = offers.get("itemOffered") or {}
            if offers.get("priceCurrency", "IDR") == "IDR":
                _set(record, "price_rp", _whole(offers.get("price")))
            _set(record, "building_m2", _number((home.get("floorSize") or {}).get("value") if isinstance(home.get("floorSize"), dict) else home.get("floorSize")))
            _set(record, "bedrooms", _whole(home.get("numberOfBedrooms")))
            _set(record, "bathrooms", _whole(home.get("numberOfBathroomsTotal")))
            _set(record, "title", node.get("name") or home.get("name"))
            _set(record, "description", home.get("description") or node.get("description"))
            address = home.get("address") or {}
            locality = address.get("addressLocality")
            region = address.get("addressRegion")
            _set(record, "detail_location", ", ".join(part for part in (locality, region) if part) or None)
            _set(record, "area", normalize_area(node.get("name"), home.get("name"), locality, region, *crumbs))
            kind = home.get("@type")
            kind_text = " ".join(kind if isinstance(kind, list) else [kind or ""])
            _set(record, "property_type", _house_or_other(kind_text, node.get("name"), record.url))
            _set(record, "readiness", _readiness_from_condition(offers.get("itemCondition")))
        if _has_type(node, "Product"):
            offer = node.get("offers") or {}
            if offer.get("priceCurrency", "IDR") == "IDR":
                _set(record, "price_rp", _whole(offer.get("price")))
            _set(record, "title", node.get("name"))
            _set(record, "description", node.get("description"))
            _set(record, "readiness", _readiness_from_condition(offer.get("itemCondition")))
            _set(record, "property_type", _house_or_other(node.get("name"), record.url))

    path = record.url.lower()
    if "sekunder" in path or "seken" in path:
        _set(record, "readiness", Readiness.READY)
    elif "primer" in path or "rumah-baru" in path:
        _set(record, "readiness", Readiness.INDENT)


def _read_masuksini(record: ListingRecord, nodes: list[dict]) -> None:
    crumbs = _breadcrumb_names(nodes)
    for node in nodes:
        if not (_has_type(node, "RealEstateListing") or _has_type(node, "Product")):
            continue
        if node.get("@type") == "Organization" or _has_type(node, "Organization"):
            continue
        if _has_type(node, "RealEstateAgent"):
            continue
        offer = node.get("offers") or {}
        home = node.get("mainEntity") or {}
        if offer.get("priceCurrency", "IDR") == "IDR":
            _set(record, "price_rp", _whole(offer.get("price")))
        _set(record, "listing_id", node.get("sku"))
        _set(record, "title", node.get("name"))
        _set(record, "description", node.get("description") or home.get("description"))
        floor = home.get("floorSize") if isinstance(home.get("floorSize"), dict) else None
        _set(record, "building_m2", _number((floor or {}).get("value") if floor else home.get("floorSize")))
        _set(record, "bedrooms", _whole(home.get("numberOfBedrooms")))
        _set(record, "bathrooms", _whole(home.get("numberOfBathroomsTotal")))
        for prop in node.get("additionalProperty") or []:
            name = (prop.get("name") or "").lower()
            if "tanah" in name:
                _set(record, "land_m2", _number(prop.get("value")))
            elif "bangunan" in name:
                _set(record, "building_m2", _number(prop.get("value")))
            elif "properti" in name or "tipe" in name:
                _set(record, "property_type", _house_or_other(str(prop.get("value") or "")))
        address = home.get("address") or {}
        street = address.get("streetAddress")
        locality = address.get("addressLocality")
        _set(record, "detail_location", ", ".join(part for part in (street, locality) if part) or None)
        _set(record, "area", normalize_area(street, locality, node.get("name"), *crumbs))
        home_type = home.get("@type")
        home_kind = " ".join(home_type if isinstance(home_type, list) else [home_type or ""])
        _set(record, "property_type", _house_or_other(home_kind, node.get("category"), node.get("name")))
        _set(record, "readiness", _readiness_from_condition(offer.get("itemCondition")))


def _cell_text(node) -> str:
    return _CLEAN_SPACE.sub(" ", (node.text() if node is not None else "") or "").strip()


def _read_idrumah(record: ListingRecord, tree: LexborHTMLParser) -> None:
    title = tree.css_first("h1.listing-title") or tree.css_first("h1")
    title_text = _cell_text(title) or None
    _set(record, "title", title_text)
    description = tree.css_first(".listing-description")
    _set(record, "description", _cell_text(description) or None)
    location = tree.css_first(".listing-location")
    location_text = _cell_text(location) or None
    _set(record, "detail_location", location_text)
    crumbs = [_cell_text(node) for node in tree.css("[itemprop=name]")]
    _set(record, "area", normalize_area(title_text, location_text, *crumbs))
    head = tree.css_first(".listing-main-head")
    _set(record, "price_rp", parse_rupiah(_cell_text(head) if head else None))
    for row in tree.css(".listing-spec tr"):
        cells = row.css("td")
        if len(cells) < 2:
            continue
        label = _cell_text(cells[0]).lower()
        raw = _cell_text(cells[1])
        field = _IDRUMAH_SPEC.get(label)
        amount = re.search(r"(\d+(?:[.,]\d+)?)", raw)
        if field in {"land_m2", "building_m2"}:
            _set(record, field, _number(amount.group(1).replace(",", ".") if amount else None))
        elif field in {"bedrooms", "bathrooms", "floors"}:
            _set(record, field, _whole(amount.group(1) if amount else None))
    listing_id = _IDRUMAH_ID.search(record.url)
    _set(record, "listing_id", listing_id.group(1) if listing_id else None)
    _set(record, "property_type", _house_or_other(title_text, *crumbs, record.url))


def read_structured(html: str, url: str, portal: str) -> ListingRecord:
    """A Listing Record holding only what the page's structured data states."""
    record = ListingRecord(url=url, portal=portal)
    tree = LexborHTMLParser(html)
    nodes = _json_ld(tree)
    if portal == "rumah123":
        _read_rumah123(record, nodes)
    elif portal == "99co":
        _read_99co(record, tree, nodes)
    elif portal == "pinhome":
        _read_pinhome(record, tree, nodes)
    elif portal == "masuksini":
        _read_masuksini(record, nodes)
    elif portal == "idrumah":
        _read_idrumah(record, tree)
    if record.description:
        record.description = _CLEAN_SPACE.sub(" ", record.description).strip()
    return record
