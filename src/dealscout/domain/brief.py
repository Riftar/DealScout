from pydantic import BaseModel, Field


class Brief(BaseModel):
    """The house a buyer describes. Area and budget are hard limits; sizes and bedrooms are soft."""

    area: str
    budget_rp: int = Field(gt=0)
    headroom: float = Field(default=0.05, ge=0, le=0.10)
    land_m2: float | None = Field(default=None, gt=0)
    building_m2: float | None = Field(default=None, gt=0)
    bedrooms: int | None = Field(default=None, ge=0)
    soft_tolerance: float = Field(default=0.20, ge=0, le=1)

    @property
    def price_ceiling_rp(self) -> int:
        """Budget plus Headroom: the highest asking price still considered."""
        return round(self.budget_rp * (1 + self.headroom))
