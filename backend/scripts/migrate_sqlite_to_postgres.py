from __future__ import annotations

import argparse
import logging
import sqlite3
import uuid
from collections.abc import Callable, Iterable, Sequence
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg
from psycopg import Connection

from app.core.config import settings

Transform = Callable[[Any], Any]
logger = logging.getLogger(__name__)


def uuid_from_sqlite(value: Any) -> uuid.UUID | None:
    if value is None:
        return None
    return uuid.UUID(str(value))


def str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def bool_from_sqlite(value: Any) -> bool:
    return bool(value)


def date_from_sqlite(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return date.fromisoformat(str(value))


def datetime_from_sqlite(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value)
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    return datetime.fromisoformat(text)


def decimal_from_sqlite(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


TABLES: tuple[tuple[str, tuple[str, ...], tuple[Transform, ...]], ...] = (
    (
        "user",
        (
            "email",
            "is_active",
            "is_superuser",
            "full_name",
            "id",
            "hashed_password",
            "created_at",
        ),
        (
            str_or_none,
            bool_from_sqlite,
            bool_from_sqlite,
            str_or_none,
            uuid_from_sqlite,
            str_or_none,
            datetime_from_sqlite,
        ),
    ),
    (
        "retailer",
        ("name", "id"),
        (str_or_none, uuid_from_sqlite),
    ),
    (
        "product",
        (
            "barcode",
            "name",
            "brand",
            "net_quantity",
            "unit_of_measure",
            "category",
            "image_url",
            "id",
        ),
        (
            str_or_none,
            str_or_none,
            str_or_none,
            str_or_none,
            str_or_none,
            str_or_none,
            str_or_none,
            uuid_from_sqlite,
        ),
    ),
    (
        "store",
        ("retailer_id", "store_code", "name", "address", "prefix", "id"),
        (
            uuid_from_sqlite,
            str_or_none,
            str_or_none,
            str_or_none,
            str_or_none,
            uuid_from_sqlite,
        ),
    ),
    (
        "priceobservation",
        (
            "product_id",
            "retailer_id",
            "store_id",
            "observed_date",
            "retailer_product_code",
            "source_product_name",
            "price_eur",
            "unit_price_eur",
            "is_special_sale",
            "source_file_name",
            "id",
        ),
        (
            uuid_from_sqlite,
            uuid_from_sqlite,
            uuid_from_sqlite,
            date_from_sqlite,
            str_or_none,
            str_or_none,
            decimal_from_sqlite,
            decimal_from_sqlite,
            bool_from_sqlite,
            str_or_none,
            uuid_from_sqlite,
        ),
    ),
)


def quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def ensure_sqlite_tables(sqlite_connection: sqlite3.Connection) -> None:
    existing_tables = {
        row[0]
        for row in sqlite_connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    missing_tables = [table for table, _, _ in TABLES if table not in existing_tables]
    if missing_tables:
        raise RuntimeError(f"Missing SQLite tables: {', '.join(missing_tables)}")


def truncate_postgres(postgres_connection: Connection) -> None:
    tables = ["productalias", *(table for table, _, _ in reversed(TABLES))]
    table_list = ", ".join(quote_identifier(table) for table in tables)
    with postgres_connection.cursor() as cursor:
        cursor.execute(f"TRUNCATE {table_list} RESTART IDENTITY CASCADE")


def iter_sqlite_rows(
    sqlite_connection: sqlite3.Connection,
    table: str,
    columns: Sequence[str],
    transforms: Sequence[Transform],
    batch_size: int,
) -> Iterable[list[tuple[Any, ...]]]:
    column_list = ", ".join(quote_identifier(column) for column in columns)
    cursor = sqlite_connection.execute(
        f"SELECT {column_list} FROM {quote_identifier(table)}"
    )
    while rows := cursor.fetchmany(batch_size):
        yield [
            tuple(transform(value) for transform, value in zip(transforms, row, strict=True))
            for row in rows
        ]


def copy_table(
    sqlite_connection: sqlite3.Connection,
    postgres_connection: Connection,
    table: str,
    columns: Sequence[str],
    transforms: Sequence[Transform],
    batch_size: int,
) -> int:
    column_list = ", ".join(quote_identifier(column) for column in columns)
    copy_sql = f"COPY {quote_identifier(table)} ({column_list}) FROM STDIN"
    copied = 0
    with postgres_connection.cursor() as cursor:
        with cursor.copy(copy_sql) as copy:
            for rows in iter_sqlite_rows(
                sqlite_connection,
                table,
                columns,
                transforms,
                batch_size,
            ):
                for row in rows:
                    copy.write_row(row)
                copied += len(rows)
    return copied


def backfill_product_aliases(
    sqlite_connection: sqlite3.Connection,
    postgres_connection: Connection,
) -> None:
    with postgres_connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TEMP TABLE legacy_product_alternative_name (
                product_id uuid,
                alias_name text
            ) ON COMMIT DROP
            """
        )
        rows = sqlite_connection.execute(
            """
            SELECT id, alternative_name
            FROM product
            WHERE alternative_name IS NOT NULL AND trim(alternative_name) <> ''
            """
        ).fetchall()
        with cursor.copy(
            "COPY legacy_product_alternative_name (product_id, alias_name) FROM STDIN"
        ) as copy:
            for row in rows:
                copy.write_row(
                    (
                        uuid_from_sqlite(row["id"]),
                        str_or_none(row["alternative_name"]),
                    )
                )
        cursor.execute(
            """
            INSERT INTO productalias (
                id,
                product_id,
                alias_name,
                normalized_alias_name,
                source,
                confidence,
                first_seen_at,
                last_seen_at
            )
            SELECT
                gen_random_uuid(),
                product_id,
                alias_name,
                lower(regexp_replace(btrim(alias_name), '\\s+', ' ', 'g')),
                'openfoodfacts',
                0.8000,
                now(),
                now()
            FROM legacy_product_alternative_name
            ON CONFLICT DO NOTHING
            """
        )
        cursor.execute(
            """
            WITH grouped_aliases AS (
                SELECT
                    priceobservation.product_id,
                    priceobservation.retailer_id,
                    priceobservation.source_product_name AS alias_name,
                    lower(
                        regexp_replace(
                            btrim(priceobservation.source_product_name),
                            '\\s+',
                            ' ',
                            'g'
                        )
                    ) AS normalized_alias_name,
                    priceobservation.retailer_product_code,
                    min(priceobservation.observed_date)::timestamp with time zone
                        AS first_seen_at,
                    max(priceobservation.observed_date)::timestamp with time zone
                        AS last_seen_at
                FROM priceobservation
                WHERE btrim(priceobservation.source_product_name) <> ''
                GROUP BY
                    priceobservation.product_id,
                    priceobservation.retailer_id,
                    priceobservation.source_product_name,
                    priceobservation.retailer_product_code
            )
            INSERT INTO productalias (
                id,
                product_id,
                retailer_id,
                alias_name,
                normalized_alias_name,
                retailer_product_code,
                source,
                confidence,
                first_seen_at,
                last_seen_at
            )
            SELECT
                gen_random_uuid(),
                product_id,
                retailer_id,
                alias_name,
                normalized_alias_name,
                retailer_product_code,
                'price_csv',
                0.9500,
                first_seen_at,
                last_seen_at
            FROM grouped_aliases
            ON CONFLICT DO NOTHING
            """
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy data from the legacy SQLite database to Postgres.",
    )
    parser.add_argument(
        "--sqlite-path",
        type=Path,
        default=Path("app.db"),
        help="Path to the SQLite database. Defaults to backend/app.db when run from backend/.",
    )
    parser.add_argument(
        "--postgres-url",
        default=str(settings.SQLALCHEMY_DATABASE_URI),
        help="Postgres SQLAlchemy URL. Defaults to settings.SQLALCHEMY_DATABASE_URI.",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Truncate target tables before copying data.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50_000,
        help="Rows fetched from SQLite per batch.",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = parse_args()
    sqlite_path = args.sqlite_path
    if not sqlite_path.exists():
        raise FileNotFoundError(sqlite_path)

    sqlite_connection = sqlite3.connect(sqlite_path)
    sqlite_connection.row_factory = sqlite3.Row

    postgres_url = args.postgres_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(postgres_url) as postgres_connection:
        try:
            ensure_sqlite_tables(sqlite_connection)
            if args.truncate:
                truncate_postgres(postgres_connection)

            for table, columns, transforms in TABLES:
                copied = copy_table(
                    sqlite_connection,
                    postgres_connection,
                    table,
                    columns,
                    transforms,
                    args.batch_size,
                )
                logger.info("%s: copied %s rows", table, copied)

            backfill_product_aliases(sqlite_connection, postgres_connection)
            logger.info("productalias: backfilled aliases")
        except Exception:
            postgres_connection.rollback()
            raise
        else:
            postgres_connection.commit()
    sqlite_connection.close()


if __name__ == "__main__":
    main()
