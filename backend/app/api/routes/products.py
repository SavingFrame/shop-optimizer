import re
import uuid
from datetime import date
from decimal import Decimal
from typing import ClassVar

from fastapi import APIRouter, HTTPException
from sqlalchemy import literal_column
from sqlmodel import SQLModel, func, select

from app.api.deps import SessionDep
from app.models.price_observation import PriceObservation, PriceObservationPublic
from app.models.product import Product, ProductPublic, ProductsPublic
from app.models.product_search import ProductSearchIndex
from app.models.retailer import Retailer, RetailerPublic
from app.models.store import StorePublic

router = APIRouter(prefix="/products", tags=["products"])

SEARCH_TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


def build_product_fts_query(search: str) -> str | None:
    tokens = SEARCH_TOKEN_PATTERN.findall(search)
    if not tokens:
        return None
    return " ".join(f'"{token}"*' for token in tokens)


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

    fts_query = build_product_fts_query(search)
    product_rowid = literal_column("product.rowid")
    product_fts = literal_column("product_fts")

    matching_ids: list[uuid.UUID] = []

    barcode_statement = select(Product.id).where(Product.barcode == search)
    barcode_id = session.exec(barcode_statement).one_or_none()
    if barcode_id is not None:
        matching_ids.append(barcode_id)

    if fts_query is not None:
        fts_statement = (
            select(Product.id)
            .join(ProductSearchIndex, product_rowid == ProductSearchIndex.rowid)
            .where(product_fts.op("MATCH")(fts_query))
            .order_by(func.bm25(product_fts))
        )
        fts_ids = session.exec(fts_statement).all()
        matching_ids.extend(fts_ids)

    unique_matching_ids = list(dict.fromkeys(matching_ids))
    count = len(unique_matching_ids)
    page_ids = unique_matching_ids[skip : skip + limit]

    if not page_ids:
        return ProductsPublic(count=count, data=[])

    products = session.exec(select(Product).where(Product.id.in_(page_ids))).all()
    products_by_id = {product.id: product for product in products}
    ordered_products = [
        products_by_id[product_id]
        for product_id in page_ids
        if product_id in products_by_id
    ]

    return ProductsPublic(count=count, data=ordered_products)


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
            func.max(PriceObservation.is_special_sale).label("has_special_sale"),
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
            func.max(PriceObservation.is_special_sale).label("has_special_sale"),
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
