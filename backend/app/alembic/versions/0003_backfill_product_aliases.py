"""Backfill product aliases

Revision ID: 0003_backfill_product_aliases
Revises: 0002_add_product_alias
Create Date: 2026-04-29 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_backfill_product_aliases"
down_revision = "0002_add_product_alias"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.drop_constraint(
        "uq_product_alias_source_identity",
        "productalias",
        type_="unique",
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_product_alias_source_identity
        ON productalias (
            product_id,
            retailer_id,
            normalized_alias_name,
            retailer_product_code,
            source
        ) NULLS NOT DISTINCT
        """
    )

    op.execute(
        """
        INSERT INTO productalias (
            id,
            product_id,
            retailer_id,
            alias_name,
            normalized_alias_name,
            retailer_product_code,
            barcode,
            source,
            confidence,
            first_seen_at,
            last_seen_at
        )
        SELECT
            gen_random_uuid(),
            product.id,
            NULL,
            product.alternative_name,
            lower(regexp_replace(btrim(product.alternative_name), '\\s+', ' ', 'g')),
            NULL,
            product.barcode,
            'openfoodfacts',
            0.8000,
            now(),
            now()
        FROM product
        WHERE product.alternative_name IS NOT NULL
            AND btrim(product.alternative_name) <> ''
        ON CONFLICT DO NOTHING
        """
    )

    op.execute(
        """
        WITH grouped_aliases AS (
            SELECT
                priceobservation.product_id,
                priceobservation.retailer_id,
                priceobservation.source_product_name AS alias_name,
                lower(
                    regexp_replace(
                        btrim(priceobservation.source_product_name),
                        '\\s+',
                        ' ',
                        'g'
                    )
                ) AS normalized_alias_name,
                priceobservation.retailer_product_code,
                product.barcode,
                min(priceobservation.observed_date)::timestamp with time zone AS first_seen_at,
                max(priceobservation.observed_date)::timestamp with time zone AS last_seen_at
            FROM priceobservation
            JOIN product ON product.id = priceobservation.product_id
            WHERE btrim(priceobservation.source_product_name) <> ''
            GROUP BY
                priceobservation.product_id,
                priceobservation.retailer_id,
                priceobservation.source_product_name,
                priceobservation.retailer_product_code,
                product.barcode
        )
        INSERT INTO productalias (
            id,
            product_id,
            retailer_id,
            alias_name,
            normalized_alias_name,
            retailer_product_code,
            barcode,
            source,
            confidence,
            first_seen_at,
            last_seen_at
        )
        SELECT
            gen_random_uuid(),
            grouped_aliases.product_id,
            grouped_aliases.retailer_id,
            grouped_aliases.alias_name,
            grouped_aliases.normalized_alias_name,
            grouped_aliases.retailer_product_code,
            grouped_aliases.barcode,
            'price_csv',
            0.9500,
            grouped_aliases.first_seen_at,
            grouped_aliases.last_seen_at
        FROM grouped_aliases
        ON CONFLICT DO NOTHING
        """
    )


def downgrade():
    op.execute("DELETE FROM productalias WHERE source IN ('openfoodfacts', 'price_csv')")
    op.execute("DROP INDEX uq_product_alias_source_identity")
    op.create_unique_constraint(
        "uq_product_alias_source_identity",
        "productalias",
        [
            "product_id",
            "retailer_id",
            "normalized_alias_name",
            "retailer_product_code",
            "source",
        ],
    )
