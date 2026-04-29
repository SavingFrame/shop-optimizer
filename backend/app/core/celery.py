import datetime
import uuid

from celery import Celery
from celery.schedules import crontab
from sqlmodel import Session

from app.core.db import engine
from app.services.openfoodfacts_product_images import OpenFoodFactsProductImageSyncer
from app.services.price_csv_import_job import PriceCsvImportJob, parse_import_date

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
def download_csv(date: datetime.date | str | None = None):
    today = parse_import_date(date)
    job = PriceCsvImportJob()

    for retailer_id in job.supported_retailer_ids():
        download_retailer_csv.delay(
            retailer_id=str(retailer_id),
            date=today.isoformat(),
        )


@celery.task
def download_retailer_csv(retailer_id: str, date: str):
    PriceCsvImportJob().import_retailer(
        retailer_id=uuid.UUID(retailer_id),
        date=parse_import_date(date),
    )


@celery.task
def sync_product_images(limit: int | None = None):
    with Session(engine) as session:
        OpenFoodFactsProductImageSyncer().sync_missing_product_images(
            session=session,
            limit=limit,
        )
