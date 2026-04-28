import datetime

from celery import Celery
from celery.schedules import crontab
from sqlmodel import Session, select

from app.core.db import engine
from app.models.retailer import ReailerEnum
from app.models.store import Store
from app.services.price_csv_importer import PriceCsvImporter, SparPriceCsvParser
from app.services.price_downloader import SparPriceDownloader

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
def download_csv():
    downloader = SparPriceDownloader()
    today = datetime.date.today()
    downloader.download_prices_list(date=today)

    importer = PriceCsvImporter(
        parser=SparPriceCsvParser(),
        observed_date=today,
    )
    with Session(engine) as session:
        stores = session.exec(
            select(Store).where(Store.retailer_id == ReailerEnum.SPAR.value.id)
        ).all()
        for store in stores:
            rows = downloader.download_price_csv_for_store(store=store)
            importer.import_prices(
                session=session,
                rows=rows,
                store=store,
            )
