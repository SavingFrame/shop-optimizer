"""Add product FTS search

Revision ID: 36b8f0a7c3d1
Revises: c9839fae6a1d
Create Date: 2026-04-28 14:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "36b8f0a7c3d1"
down_revision = "c9839fae6a1d"
branch_labels = None
depends_on = None


CREATE_PRODUCT_FTS = """
CREATE VIRTUAL TABLE product_fts USING fts5(
    name,
    brand,
    category,
    tokenize='unicode61 remove_diacritics 2',
    prefix='2 3 4'
)
"""

CREATE_PRODUCT_FTS_INSERT_TRIGGER = """
CREATE TRIGGER product_fts_ai AFTER INSERT ON product BEGIN
    INSERT INTO product_fts (
        rowid,
        name,
        brand,
        category
    )
    VALUES (
        new.rowid,
        new.name,
        new.brand,
        new.category
    );
END
"""

CREATE_PRODUCT_FTS_UPDATE_TRIGGER = """
CREATE TRIGGER product_fts_au AFTER UPDATE ON product BEGIN
    DELETE FROM product_fts WHERE rowid = old.rowid;

    INSERT INTO product_fts (
        rowid,
        name,
        brand,
        category
    )
    VALUES (
        new.rowid,
        new.name,
        new.brand,
        new.category
    );
END
"""

CREATE_PRODUCT_FTS_DELETE_TRIGGER = """
CREATE TRIGGER product_fts_ad AFTER DELETE ON product BEGIN
    DELETE FROM product_fts WHERE rowid = old.rowid;
END
"""

BACKFILL_PRODUCT_FTS = """
INSERT INTO product_fts (
    rowid,
    name,
    brand,
    category
)
SELECT
    rowid,
    name,
    brand,
    category
FROM product
"""


def upgrade():
    op.execute(CREATE_PRODUCT_FTS)
    op.execute(CREATE_PRODUCT_FTS_INSERT_TRIGGER)
    op.execute(CREATE_PRODUCT_FTS_UPDATE_TRIGGER)
    op.execute(CREATE_PRODUCT_FTS_DELETE_TRIGGER)
    op.execute(BACKFILL_PRODUCT_FTS)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS product_fts_ad")
    op.execute("DROP TRIGGER IF EXISTS product_fts_au")
    op.execute("DROP TRIGGER IF EXISTS product_fts_ai")
    op.execute("DROP TABLE IF EXISTS product_fts")
