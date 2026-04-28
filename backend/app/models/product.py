import uuid
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.price_observation import PriceObservation


class ProductBase(SQLModel):
    barcode: str | None = Field(
        default=None,
        unique=True,
        index=True,
        max_length=32,
        description="Cross retailer product identifier when present. Original CSV column: barkod or BARKOD.",
    )
    name: str = Field(
        index=True,
        max_length=255,
        description="Canonical or first seen product name. Original CSV column: naziv or NAZIV PROIZVODA.",
    )
    brand: str | None = Field(
        default=None,
        index=True,
        max_length=64,
        description="Original CSV column: marka or MARKA PROIZVODA.",
    )
    net_quantity: str | None = Field(
        default=None,
        max_length=32,
        description="Raw net quantity from the CSV. Original CSV column: neto količina or NETO KOLIČINA.",
    )
    unit_of_measure: str | None = Field(
        default=None,
        max_length=16,
        description="Original CSV column: jedinica mjere or JEDINICA MJERE.",
    )
    category: str | None = Field(
        default=None,
        index=True,
        max_length=64,
        description="Original CSV column: kategorija proizvoda or KATEGORIJA PROIZVODA.",
    )


class Product(ProductBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    price_observations: list["PriceObservation"] = Relationship(
        back_populates="product",
    )


class ProductCreate(ProductBase):
    pass


class ProductPublic(ProductBase):
    id: uuid.UUID


class ProductsPublic(SQLModel):
    data: list[ProductPublic]
    count: int
