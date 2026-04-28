"""Update price observation unique constraint

Revision ID: 7d08c2111c74
Revises: e1c71ea8a68c
Create Date: 2026-04-28 12:30:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "7d08c2111c74"
down_revision = "e1c71ea8a68c"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("priceobservation") as batch_op:
        batch_op.drop_constraint(
            "uq_price_observation_retailer_store_date_code",
            type_="unique",
        )
        batch_op.create_unique_constraint(
            "uq_price_observation_retailer_store_date_code_product",
            [
                "retailer_id",
                "store_id",
                "observed_date",
                "retailer_product_code",
                "product_id",
            ],
        )


def downgrade():
    with op.batch_alter_table("priceobservation") as batch_op:
        batch_op.drop_constraint(
            "uq_price_observation_retailer_store_date_code_product",
            type_="unique",
        )
        batch_op.create_unique_constraint(
            "uq_price_observation_retailer_store_date_code",
            [
                "retailer_id",
                "store_id",
                "observed_date",
                "retailer_product_code",
            ],
        )
