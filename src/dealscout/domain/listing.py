from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Readiness(StrEnum):
    READY = "ready"
    INDENT = "indent"


class PropertyType(StrEnum):
    HOUSE = "house"
    OTHER = "other"


class Status(StrEnum):
    """Where a Listing stands after the Check step."""

    CONFIRMED = "confirmed"
    QUARANTINED = "quarantined"
    UNREACHABLE = "unreachable"


class FieldSource(StrEnum):
    """How a field's value was read from the Snapshot."""

    STRUCTURED = "structured"  # JSON-LD or meta tags, read in code
    MODEL = "model"  # read by the Scout's model
    ARBITER = "arbiter"  # settled by the Arbiter after a Disagreement


class Listing(BaseModel):
    """One advert on a Portal, before anything has been read from it."""

    url: str
    portal: str
    listing_id: str | None = None


class Snapshot(BaseModel):
    """A saved copy of a Listing's page. Stays on local disk."""

    url: str
    portal: str
    fetched_at: datetime
    http_status: int
    path: str | None = None
    sha256: str | None = None
    content_bytes: int = 0
    unreachable_reason: str | None = None

    @property
    def reachable(self) -> bool:
        return self.unreachable_reason is None


# A Listing Record can only be Confirmed when every one of these is set.
REQUIRED_FIELDS: tuple[str, ...] = (
    "price_rp",
    "land_m2",
    "building_m2",
    "bedrooms",
    "bathrooms",
    "area",
    "property_type",
    "readiness",
)


class ListingRecord(BaseModel):
    """What one Listing says, as read from its Snapshot."""

    url: str
    portal: str
    listing_id: str | None = None

    price_rp: int | None = None
    land_m2: float | None = None
    building_m2: float | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    area: str | None = None
    property_type: PropertyType | None = None
    readiness: Readiness | None = None

    # Kept when the page states them.
    title: str | None = None
    detail_location: str | None = None
    certificate: str | None = None
    floors: int | None = None
    furnishing: str | None = None
    electricity_w: int | None = None
    year_built: int | None = None

    # Tracked by DealScout.
    sources: dict[str, FieldSource] = Field(default_factory=dict)
    evidence: dict[str, str] = Field(default_factory=dict)  # field -> quote from the page
    status: Status | None = None
    status_reason: str | None = None
    duplicate_of: str | None = None

    def missing_required(self) -> list[str]:
        return [name for name in REQUIRED_FIELDS if getattr(self, name) is None]

    @property
    def price_per_land_m2(self) -> float | None:
        if self.price_rp is None or not self.land_m2:
            return None
        return self.price_rp / self.land_m2

    @property
    def price_per_building_m2(self) -> float | None:
        if self.price_rp is None or not self.building_m2:
            return None
        return self.price_rp / self.building_m2


class CheckFailure(BaseModel):
    """One Extraction Check that a Listing Record did not pass."""

    check: str
    field: str | None = None
    detail: str


class Disagreement(BaseModel):
    """A field the Scout and the Verifier read differently from the same Snapshot."""

    field: str
    scout_value: str | None
    verifier_value: str | None
    resolved_value: str | None = None
    resolved_by: FieldSource | None = None
    note: str | None = None
