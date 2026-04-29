"""Tighten product alias schema

Revision ID: 0005_tighten_product_alias
Revises: 0004_drop_alt_name
Create Date: 2026-04-29 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0005_tighten_product_alias"
down_revision = "0004_drop_alt_name"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index(op.f("ix_productalias_barcode"), table_name="productalias")
    op.drop_column("productalias", "barcode")

    op.execute("UPDATE productalias SET confidence = 1.0000 WHERE confidence IS NULL")
    op.execute("UPDATE productalias SET first_seen_at = now() WHERE first_seen_at IS NULL")
    op.execute("UPDATE productalias SET last_seen_at = first_seen_at WHERE last_seen_at IS NULL")

    op.alter_column(
        "productalias",
        "confidence",
        existing_type=sa.Numeric(5, 4),
        nullable=False,
        server_default="1.0000",
    )
    op.alter_column(
        "productalias",
        "first_seen_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )
    op.alter_column(
        "productalias",
        "last_seen_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )


def downgrade():
    op.add_column(
        "productalias",
        sa.Column("barcode", sa.String(length=32), nullable=True),
    )
    op.execute(
        """
        UPDATE productalias
        SET barcode = product.barcode
        FROM product
        WHERE product.id = productalias.product_id
        """
    )
    op.create_index(op.f("ix_productalias_barcode"), "productalias", ["barcode"])

    op.alter_column(
        "productalias",
        "last_seen_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
        server_default=None,
    )
    op.alter_column(
        "productalias",
        "first_seen_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
        server_default=None,
    )
    op.alter_column(
        "productalias",
        "confidence",
        existing_type=sa.Numeric(5, 4),
        nullable=True,
        server_default=None,
    )
