"""Drop product alternative name

Revision ID: 0004_drop_alt_name
Revises: 0003_backfill_product_aliases
Create Date: 2026-04-29 00:00:00.000000

"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision = "0004_drop_alt_name"
down_revision = "0003_backfill_product_aliases"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index("ix_product_alternative_name_trgm", table_name="product")
    op.drop_index(op.f("ix_product_alternative_name"), table_name="product")
    op.drop_column("product", "alternative_name")


def downgrade():
    op.add_column(
        "product",
        sa.Column(
            "alternative_name",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=True,
        ),
    )
    op.execute(
        """
        UPDATE product
        SET alternative_name = aliases.alias_name
        FROM (
            SELECT DISTINCT ON (product_id)
                product_id,
                alias_name
            FROM productalias
            WHERE source = 'openfoodfacts'
            ORDER BY product_id, confidence DESC NULLS LAST, last_seen_at DESC NULLS LAST
        ) AS aliases
        WHERE aliases.product_id = product.id
        """
    )
    op.create_index(
        op.f("ix_product_alternative_name"),
        "product",
        ["alternative_name"],
        unique=False,
    )
    op.create_index(
        "ix_product_alternative_name_trgm",
        "product",
        ["alternative_name"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"alternative_name": "gin_trgm_ops"},
    )
