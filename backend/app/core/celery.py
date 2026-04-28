import datetime
import logging

from celery import Celery
from celery.schedules import crontab
from sqlmodel import Session, select

from app.core.db import engine
from app.models.retailer import ReailerEnum
from app.models.store import Store
from app.services.openfoodfacts_product_images import OpenFoodFactsProductImageSyncer
from app.services.price_csv_importer import (
    KauflandPriceCsvParser,
    LidlPriceCsvParser,
    PriceCsvImporter,
    SparPriceCsvParser,
)
from app.services.price_downloader import (
    KauflandPriceDownloader,
    LidlPriceDownloader,
    SparPriceDownloader,
)

logger = logging.getLogger(__name__)

celery = Celery(
    "worker",
    broker="redis://localhost:6379/12",
    backend="redis://localhost:6379/13",  # result backend
)

celery.conf.beat_schedule = {
    "download-csv-daily-at-7am": {
        "task": "app.core.celery.download_csv",
        "schedule": crontab(hour=7, minute=0),
    },
}


@celery.task
def download_csv(date: datetime.date | None = None):
    today = date or datetime.date.today()
    retailer_imports = [
        (ReailerEnum.SPAR.value.id, SparPriceDownloader(), SparPriceCsvParser()),
        (ReailerEnum.LIDL.value.id, LidlPriceDownloader(), LidlPriceCsvParser()),
        (
            ReailerEnum.KAUFLAND.value.id,
            KauflandPriceDownloader(),
            KauflandPriceCsvParser(),
        ),
    ]

    with Session(engine) as session:
        for retailer_id, downloader, parser in retailer_imports:
            stores = session.exec(
                select(Store).where(Store.retailer_id == retailer_id)
            ).all()
            if not stores:
                logger.info(
                    "No stores found for retailer %s, skipping CSV import.",
                    parser.retailer_name,
                )
                continue

            downloader.download_prices_list(date=today)
            importer = PriceCsvImporter(
                parser=parser,
                observed_date=today,
            )
            for store in stores:
                rows = downloader.download_price_csv_for_store(store=store)
                importer.import_prices(
                    session=session,
                    rows=rows,
                    store=store,
                )


@celery.task
def sync_product_images(limit: int | None = None):
    with Session(engine) as session:
        OpenFoodFactsProductImageSyncer().sync_missing_product_images(
            session=session,
            limit=limit,
        )
