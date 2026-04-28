import datetime as dt
import logging
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, ClassVar

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.price_observation import PriceObservation
from app.models.product import Product
from app.models.retailer import ReailerEnum
from app.models.store import Store

logger = logging.getLogger(__name__)

CsvRow = Mapping[str, str | None]


@dataclass(frozen=True)
class NormalizedPriceRow:
    retailer_product_code: str
    source_product_name: str
    barcode: str | None
    brand: str | None
    net_quantity: str | None
    unit_of_measure: str | None
    category: str | None
    retail_price_eur: Decimal | None
    unit_price_eur: Decimal
    special_sale_price_eur: Decimal | None


class BaseRetailerPriceCsvParser:
    retailer_id: ClassVar[uuid.UUID]
    retailer_name: ClassVar[str]
    delimiter: ClassVar[str]
    encoding: ClassVar[str] = "cp1250"
    columns: ClassVar[dict[str, str]]

    def normalize_row(self, row: CsvRow) -> NormalizedPriceRow | None:
        name = self.clean(row.get(self.columns["name"]))
        code = self.clean(row.get(self.columns["code"]))
        unit_price = self.parse_decimal(row.get(self.columns["unit_price"]))
        if not name or not code or unit_price is None:
            return None

        return NormalizedPriceRow(
            retailer_product_code=code,
            source_product_name=name,
            barcode=self.clean(row.get(self.columns["barcode"])),
            brand=self.clean(row.get(self.columns["brand"])),
            net_quantity=self.clean(row.get(self.columns["net_quantity"])),
            unit_of_measure=self.clean(row.get(self.columns["unit_of_measure"])),
            category=self.clean(row.get(self.columns["category"])),
            retail_price_eur=self.parse_decimal(row.get(self.columns["retail_price"])),
            unit_price_eur=unit_price,
            special_sale_price_eur=self.parse_decimal(
                row.get(self.columns["special_sale_price"])
            ),
        )

    @staticmethod
    def parse_decimal(value: Any) -> Decimal | None:
        clean_value = BaseRetailerPriceCsvParser.clean(value)
        if clean_value is None:
            return None
        normalized = (
            clean_value.replace(".", "").replace(",", ".")
            if "," in clean_value
            else clean_value
        )
        try:
            return Decimal(normalized)
        except InvalidOperation:
            return None

    @staticmethod
    def clean(value: Any) -> str | None:
        if value is None:
            return None
        clean_value = str(value).strip()
        return clean_value or None


class LidlPriceCsvParser(BaseRetailerPriceCsvParser):
    retailer_id = ReailerEnum.LIDL.value.id
    retailer_name = ReailerEnum.LIDL.value.name
    delimiter = ","
    columns = {
        "name": "NAZIV",
        "code": "ŠIFRA",
        "brand": "MARKA",
        "net_quantity": "NETO_KOLIČINA",
        "unit_of_measure": "JEDINICA_MJERE",
        "retail_price": "MALOPRODAJNA_CIJENA",
        "unit_price": "CIJENA_ZA_JEDINICU_MJERE",
        "special_sale_price": "MPC_ZA_VRIJEME_POSEBNOG_OBLIKA_PRODAJE",
        "barcode": "BARKOD",
        "category": "KATEGORIJA_PROIZVODA",
    }


class SparPriceCsvParser(BaseRetailerPriceCsvParser):
    retailer_id = ReailerEnum.SPAR.value.id
    retailer_name = ReailerEnum.SPAR.value.name
    delimiter = ";"
    columns = {
        "name": "naziv",
        "code": "šifra",
        "brand": "marka",
        "net_quantity": "neto količina",
        "unit_of_measure": "jedinica mjere",
        "retail_price": "MPC (EUR)",
        "unit_price": "cijena za jedinicu mjere (EUR)",
        "special_sale_price": "MPC za vrijeme posebnog oblika prodaje (EUR)",
        "barcode": "barkod",
        "category": "kategorija proizvoda",
    }


class PriceCsvImporter:
    def __init__(
        self,
        parser: BaseRetailerPriceCsvParser,
        observed_date: dt.date,
    ) -> None:
        self.parser = parser
        self.observed_date = observed_date

    def import_prices(
        self,
        session: Session,
        rows: Iterable[CsvRow],
        store: Store,
    ) -> None:
        if self.parser.retailer_id != store.retailer_id:
            raise ValueError(
                f"CSV parser {self.parser.retailer_name} does not match store retailer."
            )

        imported = 0
        skipped = 0
        products_created = 0
        observations_created = 0
        observations_updated = 0

        for raw_row in rows:
            normalized = self.parser.normalize_row(raw_row)
            if normalized is None:
                skipped += 1
                continue

            product, product_created = self._get_or_create_product(session, normalized)
            observation, observation_created = self._upsert_observation(
                session=session,
                store=store,
                normalized=normalized,
                product=product,
            )
            session.add(observation)

            imported += 1
            products_created += int(product_created)
            observations_created += int(observation_created)
            observations_updated += int(not observation_created)

        session.commit()
        logger.info(
            "Imported price CSV for store %s using %s parser: imported=%s, skipped=%s, products_created=%s, observations_created=%s, observations_updated=%s",
            store.name,
            self.parser.retailer_name,
            imported,
            skipped,
            products_created,
            observations_created,
            observations_updated,
        )

    def _get_or_create_product(
        self,
        session: Session,
        row: NormalizedPriceRow,
    ) -> tuple[Product, bool]:
        product = None
        if row.barcode:
            product = session.exec(
                select(Product).where(Product.barcode == row.barcode)
            ).first()
        if product is None:
            product = Product(
                barcode=row.barcode,
                name=row.source_product_name,
                brand=row.brand,
                net_quantity=row.net_quantity,
                unit_of_measure=row.unit_of_measure,
                category=row.category,
            )
            session.add(product)
            try:
                session.flush()
            except IntegrityError:
                session.rollback()
                if not row.barcode:
                    raise
                product = session.exec(
                    select(Product).where(Product.barcode == row.barcode)
                ).one()
                return product, False
            return product, True

        changed = False
        for field_name, value in {
            "brand": row.brand,
            "net_quantity": row.net_quantity,
            "unit_of_measure": row.unit_of_measure,
            "category": row.category,
        }.items():
            if getattr(product, field_name) is None and value is not None:
                setattr(product, field_name, value)
                changed = True
        if changed:
            session.add(product)
        return product, False

    def _upsert_observation(
        self,
        session: Session,
        store: Store,
        normalized: NormalizedPriceRow,
        product: Product,
    ) -> tuple[PriceObservation, bool]:
        statement = select(PriceObservation).where(
            PriceObservation.retailer_id == store.retailer_id,
            PriceObservation.store_id == store.id,
            PriceObservation.observed_date == self.observed_date,
            PriceObservation.retailer_product_code
            == normalized.retailer_product_code,
            PriceObservation.product_id == product.id,
        )
        observation = session.exec(statement).first()
        if observation is None:
            return (
                PriceObservation(
                    product_id=product.id,
                    retailer_id=store.retailer_id,
                    store_id=store.id,
                    observed_date=self.observed_date,
                    retailer_product_code=normalized.retailer_product_code,
                    source_product_name=normalized.source_product_name,
                    retail_price_eur=normalized.retail_price_eur,
                    unit_price_eur=normalized.unit_price_eur,
                    special_sale_price_eur=normalized.special_sale_price_eur,
                    source_file_name=None,
                ),
                True,
            )

        observation.product_id = product.id
        observation.source_product_name = normalized.source_product_name
        observation.retail_price_eur = normalized.retail_price_eur
        observation.unit_price_eur = normalized.unit_price_eur
        observation.special_sale_price_eur = normalized.special_sale_price_eur
        observation.source_file_name = None
        return observation, False
