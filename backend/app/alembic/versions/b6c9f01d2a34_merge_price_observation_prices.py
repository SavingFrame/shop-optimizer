"""Merge price observation prices

Revision ID: b6c9f01d2a34
Revises: 36b8f0a7c3d1
Create Date: 2026-04-29 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b6c9f01d2a34"
down_revision = "36b8f0a7c3d1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("priceobservation") as batch_op:
        batch_op.add_column(sa.Column("price_eur", sa.Numeric(10, 2), nullable=True))
        batch_op.add_column(
            sa.Column(
                "is_special_sale",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )

    op.execute(
        """
        UPDATE priceobservation
        SET
            price_eur = COALESCE(special_sale_price_eur, retail_price_eur),
            is_special_sale = CASE
                WHEN special_sale_price_eur IS NOT NULL THEN 1
                ELSE 0
            END
        """
    )

    with op.batch_alter_table("priceobservation") as batch_op:
        batch_op.drop_column("special_sale_price_eur")
        batch_op.drop_column("retail_price_eur")


def downgrade():
    with op.batch_alter_table("priceobservation") as batch_op:
        batch_op.add_column(
            sa.Column("retail_price_eur", sa.Numeric(10, 2), nullable=True)
        )
        batch_op.add_column(
            sa.Column("special_sale_price_eur", sa.Numeric(10, 2), nullable=True)
        )

    op.execute(
        """
        UPDATE priceobservation
        SET
            retail_price_eur = CASE
                WHEN is_special_sale = 0 THEN price_eur
                ELSE NULL
            END,
            special_sale_price_eur = CASE
                WHEN is_special_sale = 1 THEN price_eur
                ELSE NULL
            END
        """
    )

    with op.batch_alter_table("priceobservation") as batch_op:
        batch_op.drop_column("is_special_sale")
        batch_op.drop_column("price_eur")
