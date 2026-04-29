import uuid
from datetime import date
from decimal import Decimal
from typing import ClassVar

from fastapi import APIRouter, HTTPException
from sqlalchemy import case, desc, or_
from sqlmodel import SQLModel, func, select

from app.api.deps import SessionDep
from app.models.price_observation import PriceObservation, PriceObservationPublic
from app.models.product import Product, ProductPublic, ProductsPublic
from app.models.retailer import Retailer, RetailerPublic
from app.models.store import StorePublic

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/", response_model=ProductsPublic)
def read_products(
    session: SessionDep,
    skip: int = 0,
    limit: int = 20,
    q: str | None = None,
):
    search = q.strip() if q else None

    if not search:
        count_statement = select(func.count()).select_from(Product)
        count = session.exec(count_statement).one()

        statement = select(Product).order_by(Product.id).offset(skip).limit(limit)
        products = session.exec(statement).all()

        return ProductsPublic(count=count, data=products)

    search_pattern = f"%{search}%"
    search_filter = or_(
        Product.barcode == search,
        Product.name.ilike(search_pattern),
        Product.alternative_name.ilike(search_pattern),
        Product.brand.ilike(search_pattern),
        Product.category.ilike(search_pattern),
    )
    similarity_score = func.greatest(
        func.similarity(func.coalesce(Product.name, ""), search),
        func.similarity(func.coalesce(Product.alternative_name, ""), search),
        func.similarity(func.coalesce(Product.brand, ""), search),
        func.similarity(func.coalesce(Product.category, ""), search),
    )
    has_image = (Product.image_url.is_not(None)) & (Product.image_url != "")

    count_statement = select(func.count()).select_from(Product).where(search_filter)
    count = session.exec(count_statement).one()

    statement = (
        select(Product)
        .where(search_filter)
        .order_by(
            case((Product.barcode == search, 0), else_=1),
            desc(similarity_score),
            has_image.desc(),
            Product.id,
        )
        .offset(skip)
        .limit(limit)
    )
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


class RetailerPriceObservationSummary(SQLModel):
    retailer: RetailerPublic
    observed_date: date
    average_price_eur: Decimal | None
    min_price_eur: Decimal | None
    max_price_eur: Decimal | None
    average_unit_price_eur: Decimal
    min_unit_price_eur: Decimal
    max_unit_price_eur: Decimal
    store_count: int
    observation_count: int
    has_store_price_variance: bool
    has_special_sale: bool


class RetailerDailyRetailPriceHistoryPoint(SQLModel):
    retailer: RetailerPublic
    observed_date: date
    average_price_eur: Decimal | None
    min_price_eur: Decimal | None
    max_price_eur: Decimal | None
    has_special_sale: bool


@router.get(
    "/{product_id}/price-observations",
    response_model=list[NestedPriceObservation],
)
def product_price_observations(product_id: uuid.UUID, session: SessionDep):
    statement = (
        select(PriceObservation)
        .where(PriceObservation.product_id == product_id)
        .order_by(PriceObservation.price_eur)
    )
    price_observations = session.exec(statement).all()
    return price_observations


@router.get(
    "/{product_id}/price-history/retail/chart",
    response_model=list[RetailerDailyRetailPriceHistoryPoint],
)
def product_daily_retail_price_history_chart(
    product_id: uuid.UUID,
    session: SessionDep,
):
    statement = (
        select(
            Retailer,
            PriceObservation.observed_date,
            func.avg(PriceObservation.price_eur).label("average_price_eur"),
            func.min(PriceObservation.price_eur).label("min_price_eur"),
            func.max(PriceObservation.price_eur).label("max_price_eur"),
            func.bool_or(PriceObservation.is_special_sale).label("has_special_sale"),
        )
        .join(Retailer, Retailer.id == PriceObservation.retailer_id)
        .where(PriceObservation.product_id == product_id)
        .group_by(Retailer.id, Retailer.name, PriceObservation.observed_date)
        .order_by(PriceObservation.observed_date, Retailer.name)
    )

    rows = session.exec(statement).all()
    return [
        RetailerDailyRetailPriceHistoryPoint(
            retailer=retailer,
            observed_date=observed_date,
            average_price_eur=average_price_eur,
            min_price_eur=min_price_eur,
            max_price_eur=max_price_eur,
            has_special_sale=bool(has_special_sale),
        )
        for (
            retailer,
            observed_date,
            average_price_eur,
            min_price_eur,
            max_price_eur,
            has_special_sale,
        ) in rows
    ]


@router.get(
    "/{product_id}/price-observations/grouped",
    response_model=list[RetailerPriceObservationSummary],
)
def grouped_product_price_observations(product_id: uuid.UUID, session: SessionDep):
    latest_observations = (
        select(
            PriceObservation.retailer_id,
            func.max(PriceObservation.observed_date).label("observed_date"),
        )
        .where(PriceObservation.product_id == product_id)
        .group_by(PriceObservation.retailer_id)
        .subquery()
    )

    statement = (
        select(
            Retailer,
            latest_observations.c.observed_date,
            func.avg(PriceObservation.price_eur).label("average_price_eur"),
            func.min(PriceObservation.price_eur).label("min_price_eur"),
            func.max(PriceObservation.price_eur).label("max_price_eur"),
            func.count(
                func.distinct(func.coalesce(PriceObservation.price_eur, -1)),
            ).label("price_variant_count"),
            func.avg(PriceObservation.unit_price_eur).label("average_unit_price_eur"),
            func.min(PriceObservation.unit_price_eur).label("min_unit_price_eur"),
            func.max(PriceObservation.unit_price_eur).label("max_unit_price_eur"),
            func.bool_or(PriceObservation.is_special_sale).label("has_special_sale"),
            func.count(func.distinct(PriceObservation.store_id)).label("store_count"),
            func.count(PriceObservation.id).label("observation_count"),
        )
        .join(Retailer, Retailer.id == PriceObservation.retailer_id)
        .join(
            latest_observations,
            (latest_observations.c.retailer_id == PriceObservation.retailer_id)
            & (latest_observations.c.observed_date == PriceObservation.observed_date),
        )
        .where(PriceObservation.product_id == product_id)
        .group_by(Retailer.id, Retailer.name, latest_observations.c.observed_date)
        .order_by(func.avg(PriceObservation.price_eur))
    )

    rows = session.exec(statement).all()
    return [
        RetailerPriceObservationSummary(
            retailer=retailer,
            observed_date=observed_date,
            average_price_eur=average_price_eur,
            min_price_eur=min_price_eur,
            max_price_eur=max_price_eur,
            average_unit_price_eur=average_unit_price_eur,
            min_unit_price_eur=min_unit_price_eur,
            max_unit_price_eur=max_unit_price_eur,
            store_count=store_count,
            observation_count=observation_count,
            has_store_price_variance=price_variant_count > 1,
            has_special_sale=bool(has_special_sale),
        )
        for (
            retailer,
            observed_date,
            average_price_eur,
            min_price_eur,
            max_price_eur,
            price_variant_count,
            average_unit_price_eur,
            min_unit_price_eur,
            max_unit_price_eur,
            has_special_sale,
            store_count,
            observation_count,
        ) in rows
    ]
