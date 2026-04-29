import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlmodel import SQLModel, func, or_, select

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.models.product import Product, ProductPublic
from app.models.product_alias import ProductAlias
from app.models.receipt import (
    Receipt,
    ReceiptItem,
    ReceiptItemPublic,
    ReceiptPublic,
    ReceiptStatus,
)
from app.models.retailer import Retailer
from app.models.store import Store
from app.services.receipt_parser import ParsedReceiptItem, parse_spar_receipt

router = APIRouter(prefix="/receipts", tags=["receipts"])


class ReceiptItemReviewPublic(ReceiptItemPublic):
    product: ProductPublic | None = None


class ReceiptsPublic(SQLModel):
    data: list[ReceiptPublic]
    count: int


class ReceiptUpdate(SQLModel):
    status: ReceiptStatus | None = None


class ReceiptItemUpdate(SQLModel):
    product_id: uuid.UUID | None = None
    is_skipped: bool | None = None


@router.post("", response_model=Receipt)
async def create_receipt(
    session: SessionDep,
    current_user: CurrentUser,
    retailer_id: uuid.UUID = Form(...),
    store_id: uuid.UUID | None = Form(default=None),
    file: UploadFile = File(...),
) -> Any:
    retailer = session.get(Retailer, retailer_id)
    if retailer is None:
        raise HTTPException(status_code=404, detail="Retailer not found")
    if retailer.name.lower() not in {"spar", "interspar"}:
        raise HTTPException(status_code=400, detail="Only SPAR receipts are supported")

    if store_id is not None:
        store = session.get(Store, store_id)
        if store is None or store.retailer_id != retailer.id:
            raise HTTPException(status_code=400, detail="Invalid store for retailer")

    content = await file.read()
    file_key = _store_receipt_file(content=content, filename=file.filename)
    parsed_receipt = parse_spar_receipt(content)

    receipt = Receipt(
        retailer_id=retailer.id,
        store_id=store_id,
        user_id=current_user.id,
        purchase_datetime=parsed_receipt.purchase_datetime,
        total_eur=parsed_receipt.total_eur,
        file_key=file_key,
        status=ReceiptStatus.DRAFT,
        raw_text=parsed_receipt.raw_text,
    )
    session.add(receipt)

    receipt_items: list[ReceiptItem] = []
    matched_products: list[tuple[ParsedReceiptItem, Product]] = []
    for parsed_item in parsed_receipt.items:
        product = _find_matching_product(session, retailer.id, parsed_item)
        if product is not None:
            matched_products.append((parsed_item, product))

        receipt_items.append(
            ReceiptItem(
                receipt_id=receipt.id,
                product_id=product.id if product else None,
                line_number=parsed_item.line_number,
                raw_name=parsed_item.raw_name,
                normalized_raw_name=parsed_item.normalized_raw_name,
                quantity=parsed_item.quantity,
                unit_of_measure=parsed_item.unit_of_measure,
                unit_price_eur=parsed_item.unit_price_eur,
                line_total_eur=parsed_item.line_total_eur,
            ),
        )

    session.add_all(receipt_items)

    session.commit()
    return receipt


@router.get("", response_model=ReceiptsPublic)
def read_receipts(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> ReceiptsPublic:
    count_statement = (
        select(func.count())
        .select_from(Receipt)
        .where(
            Receipt.user_id == current_user.id,
        )
    )
    count = session.exec(count_statement).one()

    statement = (
        select(Receipt)
        .where(Receipt.user_id == current_user.id)
        .order_by(Receipt.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    receipts = session.exec(statement).all()
    return ReceiptsPublic(data=receipts, count=count)


@router.get("/{receipt_id}", response_model=Receipt)
def read_receipt(
    receipt_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Receipt:
    receipt = _get_user_receipt(session, current_user.id, receipt_id)
    return receipt


@router.patch("/{receipt_id}", response_model=Receipt)
def update_receipt(
    receipt_id: uuid.UUID,
    receipt_in: ReceiptUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> Receipt:
    receipt = _get_user_receipt(session, current_user.id, receipt_id)

    if receipt_in.status == ReceiptStatus.COMPLETED:
        items = _get_receipt_items(session, receipt.id)
        incomplete_items = [
            item for item in items if item.product_id is None and not item.is_skipped
        ]
        if incomplete_items:
            raise HTTPException(
                status_code=400,
                detail="All receipt items must be matched or skipped before completion",
            )
        receipt.status = ReceiptStatus.COMPLETED
    elif receipt_in.status == ReceiptStatus.DRAFT:
        receipt.status = ReceiptStatus.DRAFT

    session.add(receipt)
    session.commit()
    session.refresh(receipt)
    return receipt


@router.patch("/{receipt_id}/items/{item_id}", response_model=ReceiptItemReviewPublic)
def update_receipt_item(
    receipt_id: uuid.UUID,
    item_id: uuid.UUID,
    item_in: ReceiptItemUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> ReceiptItem:
    receipt = _get_user_receipt(session, current_user.id, receipt_id)
    item = session.get(ReceiptItem, item_id)
    if item is None or item.receipt_id != receipt.id:
        raise HTTPException(status_code=404, detail="Receipt item not found")
    if receipt.status == ReceiptStatus.COMPLETED:
        raise HTTPException(
            status_code=400, detail="Completed receipts cannot be edited"
        )

    update_data = item_in.model_dump(exclude_unset=True)

    if "product_id" in update_data:
        product_id = update_data["product_id"]
        if product_id is None:
            item.product_id = None
        else:
            product = session.get(Product, product_id)
            if product is None:
                raise HTTPException(status_code=404, detail="Product not found")
            item.product_id = product.id
            item.is_skipped = False

    if "is_skipped" in update_data:
        item.is_skipped = bool(update_data["is_skipped"])
        if item.is_skipped:
            item.product_id = None

    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def _store_receipt_file(content: bytes, filename: str | None) -> str:
    upload_dir = Path(settings.RECEIPT_UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(filename or "receipt.pdf").suffix or ".pdf"
    file_key = f"{uuid.uuid4()}{suffix}"
    (upload_dir / file_key).write_bytes(content)
    return file_key


def _find_matching_product(
    session: SessionDep,
    retailer_id: uuid.UUID,
    parsed_item: ParsedReceiptItem,
) -> Product | None:
    alias_statement = (
        select(Product)
        .join(ProductAlias)
        .where(
            ProductAlias.normalized_alias_name == parsed_item.normalized_raw_name,
            or_(
                ProductAlias.retailer_id == retailer_id,
                ProductAlias.retailer_id.is_(None),
            ),
        )
        .limit(1)
    )
    product = session.exec(alias_statement).first()
    if product is not None:
        return product

    product_statement = select(Product).where(
        func.lower(Product.name) == parsed_item.normalized_raw_name,
    )
    return session.exec(product_statement).first()


def _get_user_receipt(
    session: SessionDep,
    user_id: uuid.UUID,
    receipt_id: uuid.UUID,
) -> Receipt:
    statement = select(Receipt).where(
        Receipt.id == receipt_id,
        Receipt.user_id == user_id,
    )
    receipt = session.exec(statement).first()
    if receipt is None:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt


def _get_receipt_items(session: SessionDep, receipt_id: uuid.UUID) -> list[ReceiptItem]:
    statement = (
        select(ReceiptItem)
        .where(ReceiptItem.receipt_id == receipt_id)
        .order_by(ReceiptItem.line_number)
    )
    return list(session.exec(statement).all())
