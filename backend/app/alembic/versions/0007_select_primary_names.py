"""Select primary product names

Revision ID: 0007_select_primary_names
Revises: 0006_rename_primary_alias_source
Create Date: 2026-04-29 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0007_select_primary_names"
down_revision = "0006_rename_primary_alias_source"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        WITH ranked_aliases AS (
            SELECT
                productalias.product_id,
                left(
                    btrim(
                        regexp_replace(
                            regexp_replace(
                                regexp_replace(productalias.alias_name, '(_OC|_C)$', ''),
                                '( PET| LIM)$',
                                ''
                            ),
                            '\\s+',
                            ' ',
                            'g'
                        )
                    ),
                    255
                ) AS primary_name,
                row_number() OVER (
                    PARTITION BY productalias.product_id
                    ORDER BY
                        CASE retailer.name
                            WHEN 'Kaufland' THEN 1
                            WHEN 'Spar' THEN 2
                            WHEN 'Lidl' THEN 3
                            ELSE 99
                        END,
                        productalias.last_seen_at DESC,
                        productalias.alias_name
                ) AS row_number
            FROM productalias
            JOIN retailer ON retailer.id = productalias.retailer_id
            WHERE productalias.source = 'price_csv'
        )
        UPDATE product
        SET name = ranked_aliases.primary_name
        FROM ranked_aliases
        WHERE ranked_aliases.product_id = product.id
            AND ranked_aliases.row_number = 1
            AND ranked_aliases.primary_name <> ''
        """
    )


def downgrade():
    pass
