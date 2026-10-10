import json

from dealscout.domain import FieldSource, PropertyType, Readiness
from dealscout.extract.structured import read_structured

# Hand-written pages in the shape each Portal uses. No real advert is copied here.


def rumah123_page(**home_overrides) -> str:
    home = {
        "@type": ["SingleFamilyResidence", "Product"],
        "sku": "hos1",
        "description": "Land Area: 55 m2   Building Area: 60 m2",
        "address": {"addressLocality": "Bintaro, Tangerang Selatan"},
        "numberOfBedrooms": 2,
        "numberOfBathroomsTotal": 2,
        "floorSize": {"@type": "QuantitativeValue", "value": 60},
        "offers": {"price": "875000000", "priceCurrency": "IDR"},
    } | home_overrides
    graph = {"@graph": [{"@type": ["WebPage", "RealEstateListing"], "name": "A house", "mainEntity": home}]}
    return f'<html><script type="application/ld+json">{json.dumps(graph)}</script></html>'


def ninety_nine_page(**attribute_overrides) -> str:
    attributes = {
        "property_type": {"value": "rumah"},
        "market_type": {"value": "secondary"},
        "bedrooms": 2,
        "bathrooms": 2,
        "land_area": {"value": "57", "unit": "m2"},
        "builtup_area": {"value": "60", "unit": "m2"},
        "electricity": {"value": "0", "unit": "Watt"},
        "certificate": {"value": "PPJB"},
        "floors": 2,
        "year_built": 0,
    } | attribute_overrides
    data = {
        "id": "abc",
        "title": "Rumah di BSD",
        "description": "Luas Bangunan 62m2",
        "price": {"price": 1_100_000_000},
        "attributes": attributes,
        "location": {"city": {"name": "Tangerang Selatan"}, "district": {"name": "BSD"}},
    }
    state = {"props": {"pageProps": {"data": data}}}
    return f'<html><script id="__NEXT_DATA__" type="application/json">{json.dumps(state)}</script></html>'


def test_rumah123_states_everything_but_land_and_readiness():
    record = read_structured(rumah123_page(), "https://www.rumah123.com/en/property/x-hos1/", "rumah123")
    assert record.price_rp == 875_000_000
    assert record.building_m2 == 60
    assert (record.bedrooms, record.bathrooms) == (2, 2)
    assert record.area == "Bintaro"
    assert record.property_type is PropertyType.HOUSE
    assert record.missing_required() == ["land_m2", "readiness"]
    assert record.sources["price_rp"] is FieldSource.STRUCTURED
    assert record.description == "Land Area: 55 m2 Building Area: 60 m2"


def test_rumah123_new_launch_is_indent():
    url = "https://www.rumah123.com/en/new-launch/property/depok/x/hos2/"
    assert read_structured(rumah123_page(), url, "rumah123").readiness is Readiness.INDENT


def test_99co_states_every_required_field():
    record = read_structured(ninety_nine_page(), "https://www.99.co/id/properti/x", "99co")
    assert record.missing_required() == []
    assert record.price_rp == 1_100_000_000
    assert (record.land_m2, record.building_m2) == (57, 60)
    assert record.area == "BSD/Serpong"
    assert record.readiness is Readiness.READY
    assert record.certificate == "PPJB"


def test_zero_means_not_stated():
    record = read_structured(ninety_nine_page(), "https://www.99.co/id/properti/x", "99co")
    assert record.electricity_w is None
    assert record.year_built is None
    assert "electricity_w" not in record.sources


def test_non_house_is_marked_other():
    page = ninety_nine_page(property_type={"value": "kost"})
    assert read_structured(page, "https://www.99.co/id/properti/x", "99co").property_type is PropertyType.OTHER


def test_page_without_structured_data_yields_an_empty_record():
    record = read_structured("<html><body>nothing</body></html>", "https://www.99.co/id/properti/x", "99co")
    assert len(record.missing_required()) == 8


def pinhome_page(**home_overrides) -> str:
    home = {
        "@type": "SingleFamilyResidence",
        "name": "A house in Bintaro",
        "description": "Rumah di Bintaro.",
        "address": {"addressLocality": "Pesanggrahan", "addressRegion": "Kota Jakarta Selatan"},
        "floorSize": {"@type": "QuantitativeValue", "value": "60", "unitCode": "MTK"},
        "numberOfBedrooms": "2",
        "numberOfBathroomsTotal": "2",
    } | home_overrides
    graph = {
        "@graph": [
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home"},
                    {"@type": "ListItem", "position": 7, "name": "Bintaro"},
                ],
            },
            {
                "@type": "RealEstateListing",
                "name": "A house in Bintaro",
                "description": "Rumah di Bintaro.",
                "offers": {
                    "price": "875000000",
                    "priceCurrency": "IDR",
                    "itemCondition": "https://schema.org/UsedCondition",
                    "itemOffered": home,
                },
            },
        ]
    }
    og = '<meta property="og:description" content="Rumah Non Furnished dengan 2 kamar tidur serta luas tanah 55 m² di Bintaro">'
    return f'<html><head>{og}</head><script type="application/ld+json">{json.dumps(graph)}</script></html>'


def masuksini_page(**home_overrides) -> str:
    home = {
        "@type": "House",
        "numberOfBedrooms": 2,
        "numberOfBathroomsTotal": 2,
        "floorSize": {"@type": "QuantitativeValue", "value": 60, "unitCode": "MTK"},
        "address": {
            "streetAddress": "Fleek Hauz BSD City",
            "addressLocality": "Kabupaten Tangerang",
        },
    } | home_overrides
    nodes = [
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"position": 1, "item": {"name": "Beranda"}},
                {"position": 6, "item": {"name": "BSD Greenwich Park"}},
            ],
        },
        {
            "@type": ["RealEstateListing", "Product"],
            "name": "A house in BSD",
            "sku": "MS-1",
            "description": "Rumah di BSD.",
            "category": "Rumah Dijual",
            "offers": {
                "price": 875000000,
                "priceCurrency": "IDR",
                "itemCondition": "https://schema.org/UsedCondition",
            },
            "mainEntity": home,
            "additionalProperty": [
                {"@type": "PropertyValue", "name": "Luas Tanah", "value": 55, "unitText": "sqm"},
                {"@type": "PropertyValue", "name": "Tipe Properti", "value": "Rumah"},
            ],
        },
    ]
    return f'<html><script type="application/ld+json">{json.dumps(nodes)}</script></html>'


def idrumah_page() -> str:
    return """<html><body>
    <ul><li itemprop="itemListElement"><span itemprop="name">Rumah</span></li></ul>
    <h1 class="listing-title">Rumah siap huni di Bintaro</h1>
    <div class="listing-main-head">Jual Harga Rp. 875 Juta</div>
    <div class="listing-location">Bintaro, Tangerang Selatan</div>
    <div class="listing-description">Rumah di Bintaro dekat stasiun.</div>
    <div class="listing-spec"><table><tr><td>Luas Tanah</td><td>55 M<sup>2</sup></td></tr>
    <tr><td>Luas Bangunan</td><td>60 M<sup>2</sup></td></tr>
    <tr><td>Kamar Tidur</td><td>2</td></tr>
    <tr><td>Kamar Mandi</td><td>2</td></tr>
    <tr><td>Tingkat</td><td>2</td></tr></table></div>
    </body></html>"""


def test_pinhome_states_required_fields_from_json_ld_and_og():
    url = "https://www.pinhome.id/dijual/rumah-sekunder/unit/a-house-in-bintaro"
    record = read_structured(pinhome_page(), url, "pinhome")
    assert record.missing_required() == []
    assert record.price_rp == 875_000_000
    assert (record.land_m2, record.building_m2) == (55, 60)
    assert (record.bedrooms, record.bathrooms) == (2, 2)
    assert record.area == "Bintaro"
    assert record.property_type is PropertyType.HOUSE
    assert record.readiness is Readiness.READY
    assert record.sources["land_m2"] is FieldSource.STRUCTURED


def test_masuksini_reads_land_from_additional_property():
    url = "https://masuksini.com/detail-properti/MS-1/a-house-in-bsd/"
    record = read_structured(masuksini_page(), url, "masuksini")
    assert record.missing_required() == []
    assert record.listing_id == "MS-1"
    assert (record.land_m2, record.building_m2) == (55, 60)
    assert record.area == "BSD/Serpong"
    assert record.readiness is Readiness.READY
    assert record.property_type is PropertyType.HOUSE


def test_idrumah_reads_the_spec_table():
    url = "https://idrumah.com/properti/tangerang-selatan/8396-a-house-in-bintaro/"
    record = read_structured(idrumah_page(), url, "idrumah")
    assert record.price_rp == 875_000_000
    assert (record.land_m2, record.building_m2) == (55, 60)
    assert (record.bedrooms, record.bathrooms) == (2, 2)
    assert record.area == "Bintaro"
    assert record.property_type is PropertyType.HOUSE
    assert record.listing_id == "8396"
    assert record.floors == 2
    assert record.missing_required() == ["readiness"]
