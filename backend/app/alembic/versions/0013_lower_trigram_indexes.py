"""Use lower-expression trigram indexes

Revision ID: 0013_lower_trigram_indexes
Revises: 0012_item_alternatives
Create Date: 2026-04-30 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0013_lower_trigram_indexes"
down_revision = "0012_item_alternatives"
branch_labels = None
depends_on = None


LOWER_TRIGRAM_INDEXES = (
    (
        "ix_product_lower_name_trgm",
        "product",
        "lower(name)",
    ),
    (
        "ix_product_lower_brand_trgm",
        "product",
        "lower(brand)",
    ),
    (
        "ix_product_lower_category_trgm",
        "product",
        "lower(category)",
    ),
    (
        "ix_productalias_lower_alias_name_trgm",
        "productalias",
        "lower(alias_name)",
    ),
    (
        "ix_productalias_lower_normalized_alias_name_trgm",
        "productalias",
        "lower(normalized_alias_name)",
    ),
)

RAW_TRIGRAM_INDEXES = (
    ("ix_product_name_trgm", "product", "name"),
    ("ix_product_brand_trgm", "product", "brand"),
    ("ix_product_category_trgm", "product", "category"),
    ("ix_productalias_alias_name_trgm", "productalias", "alias_name"),
    (
        "ix_productalias_normalized_alias_name_trgm",
        "productalias",
        "normalized_alias_name",
    ),
)


def upgrade():
    for index_name, table_name, _column_name in RAW_TRIGRAM_INDEXES:
        op.drop_index(index_name, table_name=table_name)

    for index_name, table_name, expression in LOWER_TRIGRAM_INDEXES:
        op.execute(
            f"CREATE INDEX {index_name} "
            f"ON {table_name} USING gin (({expression}) gin_trgm_ops)",
        )


def downgrade():
    for index_name, table_name, _expression in LOWER_TRIGRAM_INDEXES:
        op.drop_index(index_name, table_name=table_name)

    for index_name, table_name, column_name in RAW_TRIGRAM_INDEXES:
        op.execute(
            f"CREATE INDEX {index_name} "
            f"ON {table_name} USING gin ({column_name} gin_trgm_ops)",
        )
