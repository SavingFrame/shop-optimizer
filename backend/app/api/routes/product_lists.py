import uuid
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status
from sqlmodel import SQLModel, delete, func, select

from app.api.deps import CurrentUser, SessionDep
from app.models.common import get_datetime_utc
from app.models.price_observation import PriceObservation
from app.models.product import Product, ProductPublic
from app.models.product_list import (
    ProductList,
    ProductListBase,
    ProductListItem,
    ProductListItemPublic,
    ProductListPublic,
    ProductListsPublic,
)
from app.models.receipt import Receipt, ReceiptItem
from app.models.retailer import Retailer, RetailerPublic

router = APIRouter(prefix="/product-lists", tags=["product-lists"])


class ProductListUpdate(SQLModel):
    name: str | None = None
    description: str | None = None


class ProductListItemCreate(SQLModel):
    product_id: uuid.UUID
    quantity: Decimal = Decimal("1")
    note: str | None = None


class ProductListItemUpdate(SQLModel):
    quantity: Decimal | None = None
    note: str | None = None


class ProductListItemDetailPublic(ProductListItemPublic):
    product: ProductPublic


class ProductListRetailerPriceHistoryPoint(SQLModel):
    retailer: RetailerPublic
    observed_date: date
    total_price_eur: Decimal
    matched_item_count: int
    total_item_count: int
    has_missing_prices: bool
    has_special_sale: bool


@router.post("", response_model=ProductListPublic)
def create_product_list(
    list_in: ProductListBase,
    session: SessionDep,
    current_user: CurrentUser,
) -> ProductList:
    existing_list = session.exec(
        select(ProductList).where(
            ProductList.user_id == current_user.id,
            ProductList.name == list_in.name,
        )
    ).first()
    if existing_list is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product list with this name already exists",
        )

    product_list = ProductList(
        user_id=current_user.id,
        name=list_in.name,
        description=list_in.description,
    )
    session.add(product_list)
    session.commit()
    session.refresh(product_list)
    return product_list


@router.post("/from-receipt/{receipt_id}", response_model=ProductListPublic)
def create_product_list_from_receipt(
    receipt_id: uuid.UUID,
    list_in: ProductListBase,
    session: SessionDep,
    current_user: CurrentUser,
) -> ProductList:
    receipt = session.exec(
        select(Receipt).where(
            Receipt.id == receipt_id,
            Receipt.user_id == current_user.id,
        )
    ).first()
    if receipt is None:
        raise HTTPException(status_code=404, detail="Receipt not found")

    existing_list = session.exec(
        select(ProductList).where(
            ProductList.user_id == current_user.id,
            ProductList.name == list_in.name,
        )
    ).first()
    if existing_list is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product list with this name already exists",
        )

    receipt_items = session.exec(
        select(ReceiptItem)
        .where(
            ReceiptItem.receipt_id == receipt.id,
            ReceiptItem.is_skipped == False,  # noqa: E712
            ReceiptItem.product_id.is_not(None),
        )
        .order_by(ReceiptItem.line_number)
    ).all()
    if not receipt_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Receipt has no matched items to add to a product list",
        )

    quantities: dict[uuid.UUID, Decimal] = {}
    for item in receipt_items:
        if item.product_id is None:
            continue
        quantities[item.product_id] = (
            quantities.get(item.product_id, Decimal("0")) + item.quantity
        )

    product_list = ProductList(
        user_id=current_user.id,
        name=list_in.name,
        description=list_in.description,
    )
    session.add(product_list)
    session.flush()

    for product_id, quantity in quantities.items():
        session.add(
            ProductListItem(
                product_list_id=product_list.id,
                product_id=product_id,
                quantity=quantity,
            )
        )

    session.commit()
    session.refresh(product_list)
    return product_list


@router.get("", response_model=ProductListsPublic)
def read_product_lists(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> ProductListsPublic:
    count = session.exec(
        select(func.count())
        .select_from(ProductList)
        .where(ProductList.user_id == current_user.id)
    ).one()
    product_lists = session.exec(
        select(ProductList)
        .where(ProductList.user_id == current_user.id)
        .order_by(ProductList.created_at.desc())
        .offset(skip)
        .limit(limit)
    ).all()

    return ProductListsPublic(data=product_lists, count=count)


@router.get("/{product_list_id}", response_model=ProductListPublic)
def read_product_list(
    product_list_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> ProductList:
    return _get_user_product_list(session, current_user.id, product_list_id)


@router.patch("/{product_list_id}", response_model=ProductListPublic)
def update_product_list(
    product_list_id: uuid.UUID,
    list_in: ProductListUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> ProductList:
    product_list = _get_user_product_list(session, current_user.id, product_list_id)
    update_data = list_in.model_dump(exclude_unset=True)
    product_list.sqlmodel_update(update_data)
    product_list.updated_at = get_datetime_utc()
    session.add(product_list)
    session.commit()
    session.refresh(product_list)
    return product_list


@router.delete("/{product_list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_list(
    product_list_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> None:
    product_list = _get_user_product_list(session, current_user.id, product_list_id)
    session.exec(
        delete(ProductListItem).where(
            ProductListItem.product_list_id == product_list.id,
        )
    )
    session.delete(product_list)
    session.commit()


@router.get(
    "/{product_list_id}/price-history/retail/chart",
    response_model=list[ProductListRetailerPriceHistoryPoint],
)
def product_list_retail_price_history_chart(
    product_list_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> list[ProductListRetailerPriceHistoryPoint]:
    product_list = _get_user_product_list(session, current_user.id, product_list_id)
    total_item_count = session.exec(
        select(func.count())
        .select_from(ProductListItem)
        .where(ProductListItem.product_list_id == product_list.id)
    ).one()
    if total_item_count == 0:
        return []

    item_prices = (
        select(
            PriceObservation.retailer_id.label("retailer_id"),
            PriceObservation.observed_date.label("observed_date"),
            PriceObservation.product_id.label("product_id"),
            ProductListItem.quantity.label("quantity"),
            func.avg(PriceObservation.price_eur).label("average_price_eur"),
            func.bool_or(PriceObservation.is_special_sale).label("has_special_sale"),
        )
        .join(ProductListItem, ProductListItem.product_id == PriceObservation.product_id)
        .where(
            ProductListItem.product_list_id == product_list.id,
            PriceObservation.price_eur.is_not(None),
        )
        .group_by(
            PriceObservation.retailer_id,
            PriceObservation.observed_date,
            PriceObservation.product_id,
            ProductListItem.quantity,
        )
        .subquery()
    )

    statement = (
        select(
            Retailer,
            item_prices.c.observed_date,
            func.sum(item_prices.c.average_price_eur * item_prices.c.quantity).label(
                "total_price_eur",
            ),
            func.count(item_prices.c.product_id).label("matched_item_count"),
            func.bool_or(item_prices.c.has_special_sale).label("has_special_sale"),
        )
        .join(Retailer, Retailer.id == item_prices.c.retailer_id)
        .group_by(Retailer.id, Retailer.name, item_prices.c.observed_date)
        .order_by(item_prices.c.observed_date, Retailer.name)
    )

    rows = session.exec(statement).all()
    return [
        ProductListRetailerPriceHistoryPoint(
            retailer=retailer,
            observed_date=observed_date,
            total_price_eur=total_price_eur,
            matched_item_count=matched_item_count,
            total_item_count=total_item_count,
            has_missing_prices=matched_item_count < total_item_count,
            has_special_sale=bool(has_special_sale),
        )
        for (
            retailer,
            observed_date,
            total_price_eur,
            matched_item_count,
            has_special_sale,
        ) in rows
    ]


@router.get(
    "/{product_list_id}/items",
    response_model=list[ProductListItemDetailPublic],
)
def read_product_list_items(
    product_list_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> list[ProductListItem]:
    product_list = _get_user_product_list(session, current_user.id, product_list_id)
    return _get_product_list_items(session, product_list.id)


@router.post(
    "/{product_list_id}/items",
    response_model=ProductListItemDetailPublic,
)
def create_product_list_item(
    product_list_id: uuid.UUID,
    item_in: ProductListItemCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> ProductListItem:
    product_list = _get_user_product_list(session, current_user.id, product_list_id)
    product = session.get(Product, item_in.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    existing_item = session.exec(
        select(ProductListItem).where(
            ProductListItem.product_list_id == product_list.id,
            ProductListItem.product_id == product.id,
        )
    ).first()
    if existing_item is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product is already in this list",
        )

    item = ProductListItem(
        product_list_id=product_list.id,
        product_id=product.id,
        quantity=item_in.quantity,
        note=item_in.note,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.patch(
    "/{product_list_id}/items/{item_id}",
    response_model=ProductListItemDetailPublic,
)
def update_product_list_item(
    product_list_id: uuid.UUID,
    item_id: uuid.UUID,
    item_in: ProductListItemUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> ProductListItem:
    product_list = _get_user_product_list(session, current_user.id, product_list_id)
    item = _get_product_list_item(session, product_list.id, item_id)

    update_data = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_data)
    item.updated_at = get_datetime_utc()

    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete(
    "/{product_list_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_product_list_item(
    product_list_id: uuid.UUID,
    item_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> None:
    product_list = _get_user_product_list(session, current_user.id, product_list_id)
    item = _get_product_list_item(session, product_list.id, item_id)
    session.delete(item)
    session.commit()


def _get_user_product_list(
    session: SessionDep,
    user_id: uuid.UUID,
    product_list_id: uuid.UUID,
) -> ProductList:
    product_list = session.exec(
        select(ProductList).where(
            ProductList.id == product_list_id,
            ProductList.user_id == user_id,
        )
    ).first()
    if product_list is None:
        raise HTTPException(status_code=404, detail="Product list not found")
    return product_list


def _get_product_list_item(
    session: SessionDep,
    product_list_id: uuid.UUID,
    item_id: uuid.UUID,
) -> ProductListItem:
    item = session.exec(
        select(ProductListItem).where(
            ProductListItem.id == item_id,
            ProductListItem.product_list_id == product_list_id,
        )
    ).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Product list item not found")
    return item


def _get_product_list_items(
    session: SessionDep,
    product_list_id: uuid.UUID,
) -> list[ProductListItem]:
    return list(
        session.exec(
            select(ProductListItem)
            .where(ProductListItem.product_list_id == product_list_id)
            .order_by(ProductListItem.created_at, ProductListItem.id)
        ).all()
    )
