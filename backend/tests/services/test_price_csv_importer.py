import datetime as dt
from decimal import Decimal

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.price_observation import PriceObservation
from app.models.product import Product
from app.models.retailer import ReailerEnum, Retailer
from app.models.store import Store
from app.services.price_csv_importer import LidlPriceCsvParser, PriceCsvImporter


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def make_store(session: Session, store_code: str) -> Store:
    retailer = Retailer(
        id=ReailerEnum.LIDL.value.id,
        name=ReailerEnum.LIDL.value.name,
    )
    session.merge(retailer)
    store = Store(
        retailer_id=ReailerEnum.LIDL.value.id,
        store_code=store_code,
        name=f"Lidl {store_code}",
    )
    session.add(store)
    session.commit()
    session.refresh(store)
    return store


def make_lidl_row(
    *,
    code: str = "0082225",
    name: str = "Krastavac",
    price: str = "1.29",
) -> dict[str, str]:
    return {
        "NAZIV": name,
        "ŠIFRA": code,
        "MARKA": "",
        "NETO_KOLIČINA": "1",
        "JEDINICA_MJERE": "1kg",
        "MALOPRODAJNA_CIJENA": price,
        "CIJENA_ZA_JEDINICU_MJERE": price,
        "MPC_ZA_VRIJEME_POSEBNOG_OBLIKA_PRODAJE": "",
        "BARKOD": "",
        "KATEGORIJA_PROIZVODA": "Hrana",
    }


def test_no_barcode_product_is_reused_by_retailer_product_code_across_stores():
    session = make_session()
    store_a = make_store(session, "209")
    store_b = make_store(session, "269")
    importer = PriceCsvImporter(
        parser=LidlPriceCsvParser(),
        observed_date=dt.date(2026, 4, 29),
    )

    importer.import_prices(session, [make_lidl_row()], store_a)
    importer.import_prices(session, [make_lidl_row(price="1.39")], store_b)

    products = session.exec(select(Product)).all()
    observations = session.exec(select(PriceObservation)).all()

    assert len(products) == 1
    assert products[0].barcode is None
    assert products[0].name == "Krastavac"
    assert len(observations) == 2
    assert {observation.product_id for observation in observations} == {products[0].id}


def test_no_barcode_product_reimport_updates_existing_observation():
    session = make_session()
    store = make_store(session, "209")
    importer = PriceCsvImporter(
        parser=LidlPriceCsvParser(),
        observed_date=dt.date(2026, 4, 29),
    )

    importer.import_prices(session, [make_lidl_row(price="1.29")], store)
    importer.import_prices(session, [make_lidl_row(price="1.49")], store)

    products = session.exec(select(Product)).all()
    observations = session.exec(select(PriceObservation)).all()

    assert len(products) == 1
    assert len(observations) == 1
    assert observations[0].product_id == products[0].id
    assert observations[0].price_eur == Decimal("1.49")
