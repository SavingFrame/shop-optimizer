"""Add product list item alternatives

Revision ID: 0012_item_alternatives
Revises: 0011_add_product_lists
Create Date: 2026-04-30 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0012_item_alternatives"
down_revision = "0011_add_product_lists"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "productlistitemalternative",
        sa.Column("product_list_item_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["product.id"],
        ),
        sa.ForeignKeyConstraint(
            ["product_list_item_id"],
            ["productlistitem.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "product_list_item_id",
            "product_id",
            name="uq_product_list_item_alternative_product",
        ),
    )
    op.create_index(
        op.f("ix_productlistitemalternative_product_id"),
        "productlistitemalternative",
        ["product_id"],
    )
    op.create_index(
        op.f("ix_productlistitemalternative_product_list_item_id"),
        "productlistitemalternative",
        ["product_list_item_id"],
    )


def downgrade():
    op.drop_index(
        op.f("ix_productlistitemalternative_product_list_item_id"),
        table_name="productlistitemalternative",
    )
    op.drop_index(
        op.f("ix_productlistitemalternative_product_id"),
        table_name="productlistitemalternative",
    )
    op.drop_table("productlistitemalternative")
