"""Add product lists

Revision ID: 0011_add_product_lists
Revises: 0010_add_receipts
Create Date: 2026-04-29 00:00:00.000000

"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision = "0011_add_product_lists"
down_revision = "0010_add_receipts"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "productlist",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column(
            "description",
            sqlmodel.sql.sqltypes.AutoString(length=1024),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_product_list_user_name"),
    )
    op.create_index(op.f("ix_productlist_user_id"), "productlist", ["user_id"])

    op.create_table(
        "productlistitem",
        sa.Column("product_list_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Numeric(10, 3), nullable=False),
        sa.Column("note", sqlmodel.sql.sqltypes.AutoString(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"]),
        sa.ForeignKeyConstraint(["product_list_id"], ["productlist.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "product_list_id",
            "product_id",
            name="uq_product_list_item_product",
        ),
    )
    op.create_index(
        op.f("ix_productlistitem_product_id"),
        "productlistitem",
        ["product_id"],
    )
    op.create_index(
        op.f("ix_productlistitem_product_list_id"),
        "productlistitem",
        ["product_list_id"],
    )


def downgrade():
    op.drop_index(
        op.f("ix_productlistitem_product_list_id"),
        table_name="productlistitem",
    )
    op.drop_index(op.f("ix_productlistitem_product_id"), table_name="productlistitem")
    op.drop_table("productlistitem")
    op.drop_index(op.f("ix_productlist_user_id"), table_name="productlist")
    op.drop_table("productlist")
