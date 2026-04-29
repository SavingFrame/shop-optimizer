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
from app.models.product_alias import ProductAlias
from app.models.retailer import Retailer, RetailerPublic
from app.models.store import StorePublic

router = APIRouter(prefix="/products", tags=["products"])


def serialize_products_with_latest_price(
    rows: list[tuple[Product, Decimal]],
) -> list[ProductPublic]:
    products = []
    for product, latest_price_eur in rows:
        product_public = ProductPublic.model_validate(product)
        product_public.latest_price_eur = latest_price_eur
        products.append(product_public)

    return products


@router.get("", response_model=ProductsPublic)
def read_products(
    session: SessionDep,
    skip: int = 0,
    limit: int = 20,
    q: str | None = None,
):
    search = q.strip() if q else None

    coverage_date = func.current_date() - 1

    latest_product_price_subquery = (
        select(PriceObservation.price_eur)
        .where(PriceObservation.product_id == Product.id)
        .order_by(desc(PriceObservation.observed_date), PriceObservation.id)
        .limit(1)
        .scalar_subquery()
    )

    if not search:
        count_statement = select(
            func.count(func.distinct(PriceObservation.product_id)),
        ).where(PriceObservation.observed_date == coverage_date)
        count = session.exec(count_statement).one()

        product_coverage = (
            select(
                PriceObservation.product_id.label("product_id"),
                func.count(func.distinct(PriceObservation.retailer_id)).label(
                    "retailer_count",
                ),
                func.count().label("observation_count"),
            )
            .where(PriceObservation.observed_date == coverage_date)
            .group_by(PriceObservation.product_id)
            .cte("product_coverage")
        )
        has_image = (Product.image_url.is_not(None)) & (Product.image_url != "")

        statement = (
            select(
                Product,
                latest_product_price_subquery.label("latest_price_eur"),
            )
            .join(product_coverage, product_coverage.c.product_id == Product.id)
            .order_by(
                has_image.desc(),
                desc(product_coverage.c.retailer_count),
                desc(product_coverage.c.observation_count),
                Product.id,
            )
            .offset(skip)
            .limit(limit)
        )
        rows = session.exec(statement).all()

        return ProductsPublic(
            count=count,
            data=serialize_products_with_latest_price(rows),
        )

    search_pattern = f"%{search}%"
    alias_search_filter = or_(
        ProductAlias.retailer_product_code == search,
        ProductAlias.alias_name.ilike(search_pattern),
        ProductAlias.normalized_alias_name.ilike(search_pattern),
        ProductAlias.alias_name.op("%")(search),
        ProductAlias.normalized_alias_name.op("%")(search),
    )
    alias_similarity_score = func.greatest(
        func.similarity(func.coalesce(ProductAlias.alias_name, ""), search),
        func.word_similarity(search, func.coalesce(ProductAlias.alias_name, "")),
        func.similarity(func.coalesce(ProductAlias.normalized_alias_name, ""), search),
        func.word_similarity(
            search,
            func.coalesce(ProductAlias.normalized_alias_name, ""),
        ),
    )
    alias_scores = (
        select(
            ProductAlias.product_id.label("product_id"),
            func.max(alias_similarity_score).label("alias_score"),
        )
        .where(alias_search_filter)
        .group_by(ProductAlias.product_id)
        .cte("alias_scores")
    )
    product_search_filter = or_(
        Product.barcode == search,
        Product.name.ilike(search_pattern),
        Product.brand.ilike(search_pattern),
        Product.category.ilike(search_pattern),
        Product.name.op("%")(search),
        Product.brand.op("%")(search),
        Product.category.op("%")(search),
        alias_scores.c.product_id.is_not(None),
    )
    similarity_score = func.greatest(
        func.similarity(func.coalesce(Product.name, ""), search),
        func.similarity(func.coalesce(Product.brand, ""), search),
        func.similarity(func.coalesce(Product.category, ""), search),
        func.coalesce(alias_scores.c.alias_score, 0),
    )
    has_image = (Product.image_url.is_not(None)) & (Product.image_url != "")

    count_statement = (
        select(func.count())
        .select_from(Product)
        .outerjoin(alias_scores, alias_scores.c.product_id == Product.id)
        .where(product_search_filter)
    )
    count = session.exec(count_statement).one()

    product_coverage = (
        select(
            PriceObservation.product_id.label("product_id"),
            func.count(func.distinct(PriceObservation.retailer_id)).label(
                "retailer_count",
            ),
            func.count().label("observation_count"),
        )
        .where(PriceObservation.observed_date == coverage_date)
        .group_by(PriceObservation.product_id)
        .cte("product_coverage")
    )

    statement = (
        select(
            Product,
            latest_product_price_subquery.label("latest_price_eur"),
        )
        .outerjoin(alias_scores, alias_scores.c.product_id == Product.id)
        .outerjoin(product_coverage, product_coverage.c.product_id == Product.id)
        .where(product_search_filter)
        .order_by(
            case((Product.barcode == search, 0), else_=1),
            desc(similarity_score),
            has_image.desc(),
            desc(func.coalesce(product_coverage.c.retailer_count, 0)),
            desc(func.coalesce(product_coverage.c.observation_count, 0)),
            Product.id,
        )
        .offset(skip)
        .limit(limit)
    )
    rows = session.exec(statement).all()

    return ProductsPublic(
        count=count,
        data=serialize_products_with_latest_price(rows),
    )


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
