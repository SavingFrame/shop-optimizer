"""Add product alias table

Revision ID: 0002_add_product_alias
Revises: 0001_base_schema
Create Date: 2026-04-29 00:00:00.000000

"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_add_product_alias"
down_revision = "0001_base_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "productalias",
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("retailer_id", sa.Uuid(), nullable=True),
        sa.Column(
            "alias_name",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=False,
        ),
        sa.Column(
            "normalized_alias_name",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=False,
        ),
        sa.Column(
            "retailer_product_code",
            sqlmodel.sql.sqltypes.AutoString(length=32),
            nullable=True,
        ),
        sa.Column("barcode", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=True),
        sa.Column("source", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"]),
        sa.ForeignKeyConstraint(["retailer_id"], ["retailer.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "product_id",
            "retailer_id",
            "normalized_alias_name",
            "retailer_product_code",
            "source",
            name="uq_product_alias_source_identity",
        ),
    )
    op.create_index(op.f("ix_productalias_alias_name"), "productalias", ["alias_name"])
    op.create_index(op.f("ix_productalias_barcode"), "productalias", ["barcode"])
    op.create_index(
        op.f("ix_productalias_normalized_alias_name"),
        "productalias",
        ["normalized_alias_name"],
    )
    op.create_index(
        op.f("ix_productalias_product_id"),
        "productalias",
        ["product_id"],
    )
    op.create_index(
        op.f("ix_productalias_retailer_id"),
        "productalias",
        ["retailer_id"],
    )
    op.create_index(
        op.f("ix_productalias_retailer_product_code"),
        "productalias",
        ["retailer_product_code"],
    )
    op.create_index(op.f("ix_productalias_source"), "productalias", ["source"])
    op.create_index(
        "ix_productalias_alias_name_trgm",
        "productalias",
        ["alias_name"],
        postgresql_using="gin",
        postgresql_ops={"alias_name": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_productalias_normalized_alias_name_trgm",
        "productalias",
        ["normalized_alias_name"],
        postgresql_using="gin",
        postgresql_ops={"normalized_alias_name": "gin_trgm_ops"},
    )


def downgrade():
    op.drop_index("ix_productalias_normalized_alias_name_trgm", table_name="productalias")
    op.drop_index("ix_productalias_alias_name_trgm", table_name="productalias")
    op.drop_index(op.f("ix_productalias_source"), table_name="productalias")
    op.drop_index(
        op.f("ix_productalias_retailer_product_code"),
        table_name="productalias",
    )
    op.drop_index(op.f("ix_productalias_retailer_id"), table_name="productalias")
    op.drop_index(op.f("ix_productalias_product_id"), table_name="productalias")
    op.drop_index(
        op.f("ix_productalias_normalized_alias_name"),
        table_name="productalias",
    )
    op.drop_index(op.f("ix_productalias_barcode"), table_name="productalias")
    op.drop_index(op.f("ix_productalias_alias_name"), table_name="productalias")
    op.drop_table("productalias")
