"""Widen product unit of measure

Revision ID: f2d7a9b6c4e1
Revises: 5d4e9c8b2a17
Create Date: 2026-04-29 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f2d7a9b6c4e1"
down_revision = "5d4e9c8b2a17"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("product") as batch_op:
        batch_op.alter_column(
            "unit_of_measure",
            existing_type=sa.String(length=16),
            type_=sa.String(length=64),
            existing_nullable=True,
        )


def downgrade():
    with op.batch_alter_table("product") as batch_op:
        batch_op.alter_column(
            "unit_of_measure",
            existing_type=sa.String(length=64),
            type_=sa.String(length=16),
            existing_nullable=True,
        )
