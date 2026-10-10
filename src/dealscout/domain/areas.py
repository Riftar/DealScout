"""The Areas DealScout prices, and the names Portals use for them."""

import re

# Canonical Area -> names seen on Portals, most specific first within each Area.
AREAS: dict[str, tuple[str, ...]] = {
    "Gading Serpong": ("gading serpong",),
    "BSD/Serpong": ("bsd", "serpong"),
    "Bintaro": ("bintaro",),
    "Depok": ("depok", "sawangan"),
    "Sleman": ("sleman", "maguwoharjo", "kaliurang"),
    "Bantul": ("bantul", "banguntapan", "kasihan", "sewon", "pandak"),
    "Yogyakarta": ("yogyakarta", "jogja", "kotagede", "mergangsan"),
}


def normalize_area(*names: str | None) -> str | None:
    """Map Portal location names to one Area. Earlier names win over later ones."""
    for name in names:
        if not name:
            continue
        text = name.lower()
        for area, aliases in AREAS.items():
            if any(re.search(rf"\b{re.escape(alias)}\b", text) for alias in aliases):
                return area
    return None
