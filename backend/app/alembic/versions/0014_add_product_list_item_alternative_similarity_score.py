"""Add product list item alternative similarity score

Revision ID: 0014_alt_similarity_score
Revises: 0013_lower_trigram_indexes
Create Date: 2026-04-30 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0014_alt_similarity_score"
down_revision = "0013_lower_trigram_indexes"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "productlistitemalternative",
        sa.Column("similarity_score", sa.Numeric(6, 4), nullable=True),
    )


def downgrade():
    op.drop_column("productlistitemalternative", "similarity_score")
