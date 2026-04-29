import datetime
import logging
import uuid
from collections.abc import Sequence

from sqlmodel import Session, select

from app.core.db import engine
from app.models.retailer import ReailerEnum
from app.models.store import Store
from app.services.price_csv_importer import (
    BaseRetailerPriceCsvParser,
    KauflandPriceCsvParser,
    PriceCsvImporter,
)
from app.services.price_downloader import (
    BasePriceDownloader,
    KauflandPriceDownloader,
    StorePriceCsvNotFound,
)

logger = logging.getLogger(__name__)

RetailerImport = tuple[uuid.UUID, BasePriceDownloader, BaseRetailerPriceCsvParser]


def parse_import_date(date: datetime.date | str | None) -> datetime.date:
    if date is None:
        return datetime.date.today()
    if isinstance(date, datetime.date):
        return date
    return datetime.date.fromisoformat(date)


class PriceCsvImportJob:
    def supported_retailer_ids(self) -> list[uuid.UUID]:
        return [retailer_id for retailer_id, _, _ in self._retailer_imports()]

    def import_retailer(self, retailer_id: uuid.UUID, date: datetime.date) -> None:
        _, downloader, parser = self._get_retailer_import(retailer_id)
        store_ids = self._get_retailer_store_ids(retailer_id)

        if not store_ids:
            logger.info(
                "No stores found for retailer %s, skipping CSV import.",
                parser.retailer_name,
            )
            return

        try:
            downloader.download_prices_list(date=date)
        except Exception:
            logger.exception(
                "Failed to download price list for retailer %s on %s, skipping retailer.",
                parser.retailer_name,
                date,
            )
            return

        if not downloader.has_price_files:
            logger.info(
                "No price CSV files found for retailer %s on %s, skipping retailer.",
                parser.retailer_name,
                date,
            )
            return

        importer = PriceCsvImporter(
            parser=parser,
            observed_date=date,
        )
        for store_id in store_ids:
            try:
                self._import_store_price_csv(
                    downloader=downloader,
                    importer=importer,
                    store_id=store_id,
                )
            except StorePriceCsvNotFound as exc:
                logger.info(
                    "Skipping price CSV import for retailer %s, store %s, date %s: %s",
                    parser.retailer_name,
                    store_id,
                    date,
                    exc,
                )
            except Exception:
                logger.exception(
                    "Failed to import price CSV for retailer %s, store %s, date %s. Continuing.",
                    parser.retailer_name,
                    store_id,
                    date,
                )

    def _retailer_imports(self) -> Sequence[RetailerImport]:
        return [
            # (ReailerEnum.SPAR.value.id, SparPriceDownloader(), SparPriceCsvParser()),
            # (ReailerEnum.LIDL.value.id, LidlPriceDownloader(), LidlPriceCsvParser()),
            (
                ReailerEnum.KAUFLAND.value.id,
                KauflandPriceDownloader(),
                KauflandPriceCsvParser(),
            ),
        ]

    def _get_retailer_import(self, retailer_id: uuid.UUID) -> RetailerImport:
        for import_config in self._retailer_imports():
            if import_config[0] == retailer_id:
                return import_config
        raise ValueError(f"Unknown retailer id {retailer_id}.")

    def _get_retailer_store_ids(self, retailer_id: uuid.UUID) -> Sequence[uuid.UUID]:
        with Session(engine) as session:
            stores = session.exec(
                select(Store.id).where(Store.retailer_id == retailer_id)
            ).all()
            return stores

    def _import_store_price_csv(
        self,
        downloader: BasePriceDownloader,
        importer: PriceCsvImporter,
        store_id: uuid.UUID,
    ) -> None:
        with Session(engine) as session:
            store = session.get(Store, store_id)
            if store is None:
                logger.warning(
                    "Store %s disappeared before CSV import, skipping.",
                    store_id,
                )
                return

            rows = downloader.download_price_csv_for_store(store=store)
            importer.import_prices(
                session=session,
                rows=rows,
                store=store,
            )
