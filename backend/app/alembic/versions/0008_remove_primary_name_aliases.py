"""Remove primary name aliases

Revision ID: 0008_remove_primary_name_aliases
Revises: 0007_select_primary_names
Create Date: 2026-04-29 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0008_remove_primary_name_aliases"
down_revision = "0007_select_primary_names"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DELETE FROM productalias WHERE source = 'primary_name'")


def downgrade():
    pass
