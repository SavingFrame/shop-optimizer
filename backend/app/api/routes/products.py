import uuid
from typing import ClassVar

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import SessionDep
from app.models.price_observation import PriceObservation, PriceObservationPublic
from app.models.product import Product, ProductPublic, ProductsPublic
from app.models.retailer import RetailerPublic
from app.models.store import StorePublic

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=ProductsPublic)
def read_products(session: SessionDep, skip: int = 0, limit: int = 20):

    count_statement = select(func.count()).select_from(Product)
    count = session.exec(count_statement).one()

    statement = select(Product).order_by(Product.id).offset(skip).limit(limit)
    products = session.exec(statement).all()

    return ProductsPublic(count=count, data=products)


@router.get("/{product_id}", response_model=ProductPublic)
def read_product(product_id: uuid.UUID, session: SessionDep):
    statement = select(Product).where(Product.id == product_id)
    product = session.exec(statement).one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


class NestedPriceObservation(PriceObservationPublic):
    product: ClassVar
    retailer: RetailerPublic
    store: StorePublic


@router.get(
    "/{product_id}/price-observations", response_model=list[NestedPriceObservation]
)
def product_price_observations(product_id: uuid.UUID, session: SessionDep):
    statement = select(PriceObservation).where(
        PriceObservation.product_id == product_id
    )
    price_observations = session.exec(statement).all()
    return price_observations
