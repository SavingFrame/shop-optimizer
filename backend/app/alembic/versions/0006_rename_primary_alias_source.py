"""Rename primary alias source

Revision ID: 0006_rename_primary_alias_source
Revises: 0005_tighten_product_alias
Create Date: 2026-04-29 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0006_rename_primary_alias_source"
down_revision = "0005_tighten_product_alias"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE productalias SET source = 'primary_name' WHERE source = 'canonical'")


def downgrade():
    op.execute("UPDATE productalias SET source = 'canonical' WHERE source = 'primary_name'")
