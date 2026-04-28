import abc
import csv
import datetime

import httpx
from pydantic import BaseModel, Field

from app.models.store import Store


class BasePriceDownloader(abc.ABC):
    def __init__(self):
        self._downloaded_prices = None

    @abc.abstractmethod
    def download_prices_list(self, date: datetime.date) -> None: ...

    @abc.abstractmethod
    def download_price_csv_for_store(self, store: Store) -> csv.DictReader: ...


class SparkPriceListItem(BaseModel):
    name: str
    url: str = Field(alias="URL")


class SparkPriceListResponse(BaseModel):
    files: list[SparkPriceListItem]
    count: int


class SparPriceDownloader(BasePriceDownloader):
    def download_prices_list(self, date: datetime.date) -> None:
        with httpx.Client() as client:
            date_str = date.strftime("%Y%m%d")
            response = client.get(
                f"https://www.spar.hr/datoteke_cjenici/Cjenik{date_str}.json",
            )
            response.raise_for_status()
            price_list_response = SparkPriceListResponse.model_validate_json(
                response.text
            )
            self._downloaded_prices = price_list_response.files

    def download_price_csv_for_store(self, store: Store) -> csv.DictReader:
        if not self._downloaded_prices:
            raise ValueError(
                "Price list not downloaded yet. Call download_prices_list first."
            )
        price_list_item = next(
            (
                price_list_item
                for price_list_item in self._downloaded_prices
                if price_list_item.name.startswith(store.prefix)
            ),
            None,
        )
        if not price_list_item:
            raise ValueError(
                f"Price list for store with prefix {store.prefix} not found."
            )
        with httpx.Client() as client:
            response = client.get(price_list_item.url)
            response.raise_for_status()
            # Spar CSV files are Windows-1250 encoded and semicolon-delimited.
            csv_text = response.content.decode("cp1250")
            reader = csv.DictReader(csv_text.splitlines(), delimiter=";")
        return reader
