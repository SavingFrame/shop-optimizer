"""Add product image URL

Revision ID: c9839fae6a1d
Revises: 7d08c2111c74
Create Date: 2026-04-28 13:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c9839fae6a1d"
down_revision = "7d08c2111c74"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("product") as batch_op:
        batch_op.add_column(sa.Column("image_url", sa.String(length=2048), nullable=True))


def downgrade():
    with op.batch_alter_table("product") as batch_op:
        batch_op.drop_column("image_url")
