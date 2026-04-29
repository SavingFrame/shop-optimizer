"""Drop product alias store id

Revision ID: 0009_drop_product_alias_store_id
Revises: 0008_remove_primary_name_aliases
Create Date: 2026-04-29 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0009_drop_product_alias_store_id"
down_revision = "0008_remove_primary_name_aliases"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DROP INDEX IF EXISTS uq_product_alias_source_identity")

    op.execute(
        """
        WITH ranked_aliases AS (
            SELECT
                id,
                first_value(id) OVER (
                    PARTITION BY
                        product_id,
                        retailer_id,
                        normalized_alias_name,
                        retailer_product_code,
                        source
                    ORDER BY last_seen_at DESC, first_seen_at ASC, id
                ) AS keeper_id,
                min(first_seen_at) OVER (
                    PARTITION BY
                        product_id,
                        retailer_id,
                        normalized_alias_name,
                        retailer_product_code,
                        source
                ) AS merged_first_seen_at,
                max(last_seen_at) OVER (
                    PARTITION BY
                        product_id,
                        retailer_id,
                        normalized_alias_name,
                        retailer_product_code,
                        source
                ) AS merged_last_seen_at,
                max(confidence) OVER (
                    PARTITION BY
                        product_id,
                        retailer_id,
                        normalized_alias_name,
                        retailer_product_code,
                        source
                ) AS merged_confidence
            FROM productalias
        )
        UPDATE productalias
        SET
            first_seen_at = ranked_aliases.merged_first_seen_at,
            last_seen_at = ranked_aliases.merged_last_seen_at,
            confidence = ranked_aliases.merged_confidence
        FROM ranked_aliases
        WHERE productalias.id = ranked_aliases.keeper_id
        """
    )
    op.execute(
        """
        WITH ranked_aliases AS (
            SELECT
                id,
                row_number() OVER (
                    PARTITION BY
                        product_id,
                        retailer_id,
                        normalized_alias_name,
                        retailer_product_code,
                        source
                    ORDER BY last_seen_at DESC, first_seen_at ASC, id
                ) AS row_number
            FROM productalias
        )
        DELETE FROM productalias
        USING ranked_aliases
        WHERE productalias.id = ranked_aliases.id
            AND ranked_aliases.row_number > 1
        """
    )

    op.drop_index(op.f("ix_productalias_store_id"), table_name="productalias")
    op.drop_constraint("productalias_store_id_fkey", "productalias", type_="foreignkey")
    op.drop_column("productalias", "store_id")

    op.execute(
        """
        CREATE UNIQUE INDEX uq_product_alias_source_identity
        ON productalias (
            product_id,
            retailer_id,
            normalized_alias_name,
            retailer_product_code,
            source
        ) NULLS NOT DISTINCT
        """
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS uq_product_alias_source_identity")
    op.add_column("productalias", sa.Column("store_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "productalias_store_id_fkey",
        "productalias",
        "store",
        ["store_id"],
        ["id"],
    )
    op.create_index(op.f("ix_productalias_store_id"), "productalias", ["store_id"])
    op.execute(
        """
        CREATE UNIQUE INDEX uq_product_alias_source_identity
        ON productalias (
            product_id,
            retailer_id,
            store_id,
            normalized_alias_name,
            retailer_product_code,
            source
        ) NULLS NOT DISTINCT
        """
    )
