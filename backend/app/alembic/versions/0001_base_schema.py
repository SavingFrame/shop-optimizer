"""Base schema

Revision ID: 0001_base_schema
Revises:
Create Date: 2026-04-29 00:00:00.000000

"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_base_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "user",
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("full_name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("hashed_password", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)

    op.create_table(
        "product",
        sa.Column("barcode", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=True),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column(
            "alternative_name",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=True,
        ),
        sa.Column("brand", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True),
        sa.Column(
            "net_quantity",
            sqlmodel.sql.sqltypes.AutoString(length=32),
            nullable=True,
        ),
        sa.Column(
            "unit_of_measure",
            sqlmodel.sql.sqltypes.AutoString(length=64),
            nullable=True,
        ),
        sa.Column("category", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True),
        sa.Column("image_url", sqlmodel.sql.sqltypes.AutoString(length=2048), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_product_barcode"), "product", ["barcode"], unique=True)
    op.create_index(op.f("ix_product_name"), "product", ["name"], unique=False)
    op.create_index(
        op.f("ix_product_alternative_name"),
        "product",
        ["alternative_name"],
        unique=False,
    )
    op.create_index(op.f("ix_product_brand"), "product", ["brand"], unique=False)
    op.create_index(op.f("ix_product_category"), "product", ["category"], unique=False)
    op.create_index(
        "ix_product_name_trgm",
        "product",
        ["name"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_product_alternative_name_trgm",
        "product",
        ["alternative_name"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"alternative_name": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_product_brand_trgm",
        "product",
        ["brand"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"brand": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_product_category_trgm",
        "product",
        ["category"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"category": "gin_trgm_ops"},
    )

    op.create_table(
        "retailer",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_retailer_name"), "retailer", ["name"], unique=True)

    op.create_table(
        "store",
        sa.Column("retailer_id", sa.Uuid(), nullable=False),
        sa.Column(
            "store_code",
            sqlmodel.sql.sqltypes.AutoString(length=64),
            nullable=False,
        ),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("address", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("prefix", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["retailer_id"], ["retailer.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("retailer_id", "store_code", name="uq_store_retailer_code"),
    )
    op.create_index(op.f("ix_store_retailer_id"), "store", ["retailer_id"], unique=False)
    op.create_index(op.f("ix_store_store_code"), "store", ["store_code"], unique=False)

    op.create_table(
        "priceobservation",
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("retailer_id", sa.Uuid(), nullable=False),
        sa.Column("store_id", sa.Uuid(), nullable=False),
        sa.Column("observed_date", sa.Date(), nullable=False),
        sa.Column(
            "retailer_product_code",
            sqlmodel.sql.sqltypes.AutoString(length=32),
            nullable=False,
        ),
        sa.Column(
            "source_product_name",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=False,
        ),
        sa.Column("price_eur", sa.Numeric(10, 2), nullable=True),
        sa.Column("unit_price_eur", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_special_sale", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "source_file_name",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=True,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"]),
        sa.ForeignKeyConstraint(["retailer_id"], ["retailer.id"]),
        sa.ForeignKeyConstraint(["store_id"], ["store.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "retailer_id",
            "store_id",
            "observed_date",
            "retailer_product_code",
            "product_id",
            name="uq_price_observation_retailer_store_date_code_product",
        ),
    )
    op.create_index(
        op.f("ix_priceobservation_observed_date"),
        "priceobservation",
        ["observed_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_priceobservation_product_id"),
        "priceobservation",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_priceobservation_retailer_id"),
        "priceobservation",
        ["retailer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_priceobservation_retailer_product_code"),
        "priceobservation",
        ["retailer_product_code"],
        unique=False,
    )
    op.create_index(
        op.f("ix_priceobservation_store_id"),
        "priceobservation",
        ["store_id"],
        unique=False,
    )
    op.create_index(
        "ix_priceobservation_observed_date_product_retailer_store",
        "priceobservation",
        ["observed_date", "product_id", "retailer_id", "store_id"],
        unique=False,
    )
    op.create_index(
        "ix_priceobservation_product_price",
        "priceobservation",
        ["product_id", "price_eur"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_priceobservation_product_price", table_name="priceobservation")
    op.drop_index(
        "ix_priceobservation_observed_date_product_retailer_store",
        table_name="priceobservation",
    )
    op.drop_index(op.f("ix_priceobservation_store_id"), table_name="priceobservation")
    op.drop_index(
        op.f("ix_priceobservation_retailer_product_code"),
        table_name="priceobservation",
    )
    op.drop_index(op.f("ix_priceobservation_retailer_id"), table_name="priceobservation")
    op.drop_index(op.f("ix_priceobservation_product_id"), table_name="priceobservation")
    op.drop_index(op.f("ix_priceobservation_observed_date"), table_name="priceobservation")
    op.drop_table("priceobservation")
    op.drop_index(op.f("ix_store_store_code"), table_name="store")
    op.drop_index(op.f("ix_store_retailer_id"), table_name="store")
    op.drop_table("store")
    op.drop_index(op.f("ix_retailer_name"), table_name="retailer")
    op.drop_table("retailer")
    op.drop_index("ix_product_category_trgm", table_name="product")
    op.drop_index("ix_product_brand_trgm", table_name="product")
    op.drop_index("ix_product_alternative_name_trgm", table_name="product")
    op.drop_index("ix_product_name_trgm", table_name="product")
    op.drop_index(op.f("ix_product_category"), table_name="product")
    op.drop_index(op.f("ix_product_brand"), table_name="product")
    op.drop_index(op.f("ix_product_alternative_name"), table_name="product")
    op.drop_index(op.f("ix_product_name"), table_name="product")
    op.drop_index(op.f("ix_product_barcode"), table_name="product")
    op.drop_table("product")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
