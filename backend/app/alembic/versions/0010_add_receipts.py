"""Add receipts

Revision ID: 0010_add_receipts
Revises: 0009_drop_product_alias_store_id
Create Date: 2026-04-29 00:00:00.000000

"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision = "0010_add_receipts"
down_revision = "0009_drop_product_alias_store_id"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "receipt",
        sa.Column("retailer_id", sa.Uuid(), nullable=False),
        sa.Column("store_id", sa.Uuid(), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("purchase_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_eur", sa.Numeric(10, 2), nullable=True),
        sa.Column("file_key", sqlmodel.sql.sqltypes.AutoString(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["retailer_id"], ["retailer.id"]),
        sa.ForeignKeyConstraint(["store_id"], ["store.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_receipt_purchase_datetime"),
        "receipt",
        ["purchase_datetime"],
        unique=False,
    )
    op.create_index(op.f("ix_receipt_retailer_id"), "receipt", ["retailer_id"], unique=False)
    op.create_index(op.f("ix_receipt_store_id"), "receipt", ["store_id"], unique=False)
    op.create_index(op.f("ix_receipt_user_id"), "receipt", ["user_id"], unique=False)

    op.create_table(
        "receiptitem",
        sa.Column("receipt_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("price_observation_id", sa.Uuid(), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("raw_name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column(
            "normalized_raw_name",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=False,
        ),
        sa.Column("quantity", sa.Numeric(10, 3), nullable=False),
        sa.Column(
            "unit_of_measure",
            sqlmodel.sql.sqltypes.AutoString(length=64),
            nullable=True,
        ),
        sa.Column("unit_price_eur", sa.Numeric(10, 2), nullable=True),
        sa.Column("line_total_eur", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_skipped", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["price_observation_id"], ["priceobservation.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"]),
        sa.ForeignKeyConstraint(["receipt_id"], ["receipt.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("receipt_id", "line_number", name="uq_receipt_item_line"),
    )
    op.create_index(
        op.f("ix_receiptitem_normalized_raw_name"),
        "receiptitem",
        ["normalized_raw_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_receiptitem_price_observation_id"),
        "receiptitem",
        ["price_observation_id"],
        unique=False,
    )
    op.create_index(op.f("ix_receiptitem_product_id"), "receiptitem", ["product_id"], unique=False)
    op.create_index(op.f("ix_receiptitem_receipt_id"), "receiptitem", ["receipt_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_receiptitem_receipt_id"), table_name="receiptitem")
    op.drop_index(op.f("ix_receiptitem_product_id"), table_name="receiptitem")
    op.drop_index(op.f("ix_receiptitem_price_observation_id"), table_name="receiptitem")
    op.drop_index(op.f("ix_receiptitem_normalized_raw_name"), table_name="receiptitem")
    op.drop_table("receiptitem")
    op.drop_index(op.f("ix_receipt_user_id"), table_name="receipt")
    op.drop_index(op.f("ix_receipt_store_id"), table_name="receipt")
    op.drop_index(op.f("ix_receipt_retailer_id"), table_name="receipt")
    op.drop_index(op.f("ix_receipt_purchase_datetime"), table_name="receipt")
    op.drop_table("receipt")
