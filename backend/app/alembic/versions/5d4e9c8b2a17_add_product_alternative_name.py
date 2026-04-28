"""Add product alternative name

Revision ID: 5d4e9c8b2a17
Revises: b6c9f01d2a34
Create Date: 2026-04-29 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5d4e9c8b2a17"
down_revision = "b6c9f01d2a34"
branch_labels = None
depends_on = None


CREATE_PRODUCT_FTS = """
CREATE VIRTUAL TABLE product_fts USING fts5(
    name,
    alternative_name,
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
        alternative_name,
        brand,
        category
    )
    VALUES (
        new.rowid,
        new.name,
        new.alternative_name,
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
        alternative_name,
        brand,
        category
    )
    VALUES (
        new.rowid,
        new.name,
        new.alternative_name,
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
    alternative_name,
    brand,
    category
)
SELECT
    rowid,
    name,
    alternative_name,
    brand,
    category
FROM product
"""

CREATE_OLD_PRODUCT_FTS = """
CREATE VIRTUAL TABLE product_fts USING fts5(
    name,
    brand,
    category,
    tokenize='unicode61 remove_diacritics 2',
    prefix='2 3 4'
)
"""

CREATE_OLD_PRODUCT_FTS_INSERT_TRIGGER = """
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

CREATE_OLD_PRODUCT_FTS_UPDATE_TRIGGER = """
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

BACKFILL_OLD_PRODUCT_FTS = """
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


def drop_product_fts():
    op.execute("DROP TRIGGER IF EXISTS product_fts_ad")
    op.execute("DROP TRIGGER IF EXISTS product_fts_au")
    op.execute("DROP TRIGGER IF EXISTS product_fts_ai")
    op.execute("DROP TABLE IF EXISTS product_fts")


def upgrade():
    drop_product_fts()
    with op.batch_alter_table("product") as batch_op:
        batch_op.add_column(sa.Column("alternative_name", sa.String(length=255), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_product_alternative_name"),
            ["alternative_name"],
            unique=False,
        )

    op.execute(CREATE_PRODUCT_FTS)
    op.execute(CREATE_PRODUCT_FTS_INSERT_TRIGGER)
    op.execute(CREATE_PRODUCT_FTS_UPDATE_TRIGGER)
    op.execute(CREATE_PRODUCT_FTS_DELETE_TRIGGER)
    op.execute(BACKFILL_PRODUCT_FTS)


def downgrade():
    drop_product_fts()
    with op.batch_alter_table("product") as batch_op:
        batch_op.drop_index(batch_op.f("ix_product_alternative_name"))
        batch_op.drop_column("alternative_name")

    op.execute(CREATE_OLD_PRODUCT_FTS)
    op.execute(CREATE_OLD_PRODUCT_FTS_INSERT_TRIGGER)
    op.execute(CREATE_OLD_PRODUCT_FTS_UPDATE_TRIGGER)
    op.execute(CREATE_PRODUCT_FTS_DELETE_TRIGGER)
    op.execute(BACKFILL_OLD_PRODUCT_FTS)
