import datetime

from celery import Celery
from celery.schedules import crontab
from sqlmodel import Session, select

from app.core.db import engine
from app.models.store import Store
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

    with Session(engine) as session:
        stores = session.exec(select(Store)).all()
        for store in stores:
            csv_reader = downloader.download_prices_for_store(store=store)
            print(
                f"Downloaded prices for store {store.name} from {store.retailer.name}:"
            )
            print(csv_reader.fieldnames)
