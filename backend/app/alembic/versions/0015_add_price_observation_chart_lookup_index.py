"""Add price observation chart lookup index

Revision ID: 0015_price_chart_lookup_idx
Revises: 0014_alt_similarity_score
Create Date: 2026-04-30 00:00:00.000000

"""

from alembic import context, op

# revision identifiers, used by Alembic.
revision = "0015_price_chart_lookup_idx"
down_revision = "0014_alt_similarity_score"
branch_labels = None
depends_on = None

INDEX_NAME = "ix_priceobservation_product_retailer_date_price_not_null"


def upgrade():
    with context.get_context().autocommit_block():
        op.execute(
            f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {INDEX_NAME} "
            "ON priceobservation (product_id, retailer_id, observed_date) "
            "INCLUDE (price_eur, is_special_sale) "
            "WHERE price_eur IS NOT NULL",
        )


def downgrade():
    with context.get_context().autocommit_block():
        op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {INDEX_NAME}")
