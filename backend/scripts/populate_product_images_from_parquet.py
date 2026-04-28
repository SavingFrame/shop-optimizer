#!/usr/bin/env python3
"""Populate product.image_url from an Open Food Facts Parquet export.

Run from the repository root:

    uvx --with duckdb python backend/scripts/populate_product_images_from_parquet.py \
        ./food.parquet --db ./backend/app.db

By default, only products with a missing image_url are updated and a SQLite backup
is created next to the database before writing.
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import time
from pathlib import Path
from typing import Any

import duckdb

OPENFOODFACTS_IMAGE_BASE_URL = "https://images.openfoodfacts.org/images/products"


LANGUAGE_PRIORITY = {
    "hr": 0,
    "en": 1,
    "cs": 2,
    "fr": 3,
    "de": 4,
    "es": 5,
    "it": 6,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Populate product.image_url from an Open Food Facts Parquet file."
    )
    parser.add_argument("parquet", type=Path, help="Path to Open Food Facts parquet file")
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("backend/app.db"),
        help="Path to SQLite database. Default: backend/app.db",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Update products even when image_url is already populated.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute matches but do not update the database.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a SQLite backup before updating.",
    )
    return parser.parse_args()


def openfoodfacts_product_path(code: str) -> str:
    code = code.strip()
    if len(code) <= 3:
        return code
    groups = [code[index : index + 3] for index in range(0, len(code) - 4, 3)]
    groups.append(code[len(code) - 4 :])
    return "/".join(groups)


def image_language(key: str) -> str:
    parts = key.rsplit("_", 1)
    return parts[1] if len(parts) == 2 else ""


def image_sort_key(image: dict[str, Any]) -> tuple[int, int, int, str]:
    key = str(image.get("key") or "")
    sizes = image.get("sizes") or {}
    language = image_language(key)
    has_400 = int(bool(sizes.get("400")))
    has_full = int(bool(sizes.get("full")))
    return (
        LANGUAGE_PRIORITY.get(language, 99),
        -has_400,
        -has_full,
        key,
    )


def select_image_url(code: str, images: list[dict[str, Any]] | None) -> str | None:
    if not images:
        return None

    front_images = [
        image
        for image in images
        if str(image.get("key") or "").startswith("front_") and image.get("rev")
    ]
    if not front_images:
        return None

    selected = sorted(front_images, key=image_sort_key)[0]
    key = selected["key"]
    rev = selected["rev"]
    product_path = openfoodfacts_product_path(code)
    return f"{OPENFOODFACTS_IMAGE_BASE_URL}/{product_path}/{key}.{rev}.400.jpg"


def load_products_missing_images(
    sqlite_connection: sqlite3.Connection,
    overwrite: bool,
) -> dict[str, str]:
    where_clause = "barcode IS NOT NULL"
    if not overwrite:
        where_clause += " AND (image_url IS NULL OR image_url = '')"

    rows = sqlite_connection.execute(
        f"SELECT id, barcode FROM product WHERE {where_clause}"
    ).fetchall()
    return {str(barcode): str(product_id) for product_id, barcode in rows if barcode}


def find_image_urls(
    parquet_path: Path,
    products_by_barcode: dict[str, str],
) -> dict[str, str]:
    if not products_by_barcode:
        return {}

    duckdb_connection = duckdb.connect()
    duckdb_connection.execute("CREATE TEMP TABLE target_barcodes(barcode VARCHAR)")
    duckdb_connection.executemany(
        "INSERT INTO target_barcodes VALUES (?)",
        [(barcode,) for barcode in products_by_barcode],
    )

    rows = duckdb_connection.execute(
        """
        SELECT parquet.code, parquet.images
        FROM read_parquet(?) AS parquet
        INNER JOIN target_barcodes AS target
            ON parquet.code = target.barcode
        WHERE parquet.images IS NOT NULL
        """,
        [str(parquet_path)],
    ).fetchall()

    image_urls: dict[str, str] = {}
    for code, images in rows:
        image_url = select_image_url(code, images)
        if image_url:
            image_urls[products_by_barcode[code]] = image_url

    return image_urls


def create_backup(db_path: Path) -> Path:
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = db_path.with_suffix(f".before-product-images-{timestamp}.db")
    shutil.copy2(db_path, backup_path)
    return backup_path


def main() -> None:
    args = parse_args()
    parquet_path = args.parquet.resolve()
    db_path = args.db.resolve()

    if not parquet_path.exists():
        raise SystemExit(f"Parquet file does not exist: {parquet_path}")
    if not db_path.exists():
        raise SystemExit(f"SQLite database does not exist: {db_path}")

    sqlite_connection = sqlite3.connect(db_path)
    products_by_barcode = load_products_missing_images(
        sqlite_connection=sqlite_connection,
        overwrite=args.overwrite,
    )
    print(f"Products considered: {len(products_by_barcode)}")

    image_urls = find_image_urls(
        parquet_path=parquet_path,
        products_by_barcode=products_by_barcode,
    )
    print(f"Matching image URLs found: {len(image_urls)}")

    for product_id, image_url in list(image_urls.items())[:10]:
        print(f"  {product_id}: {image_url}")

    if args.dry_run:
        print("Dry run complete. No database rows were updated.")
        return

    if image_urls and not args.no_backup:
        backup_path = create_backup(db_path)
        print(f"Backup created: {backup_path}")

    updated = 0
    for product_id, image_url in image_urls.items():
        cursor = sqlite_connection.execute(
            "UPDATE product SET image_url = ? WHERE id = ?",
            (image_url, product_id),
        )
        updated += cursor.rowcount

    sqlite_connection.commit()
    sqlite_connection.close()
    print(f"Rows updated: {updated}")


if __name__ == "__main__":
    main()
