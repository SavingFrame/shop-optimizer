"""Convert product net quantity to numeric

Revision ID: 2165576649b7
Revises: f044033a6749
Create Date: 2026-06-11 01:32:54.927648

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2165576649b7"
down_revision = "f044033a6749"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "product",
        "net_quantity",
        existing_type=sa.VARCHAR(length=32),
        type_=sa.Numeric(precision=12, scale=5),
        existing_nullable=True,
        postgresql_using="replace(net_quantity, ',', '.')::numeric(12,5)",
    )


def downgrade():
    op.alter_column(
        "product",
        "net_quantity",
        existing_type=sa.Numeric(precision=12, scale=5),
        type_=sa.VARCHAR(length=32),
        existing_nullable=True,
        postgresql_using="net_quantity::text",
    )
