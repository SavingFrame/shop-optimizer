from app.models.retailer import ReailerEnum
from app.models.store import Store
from app.services.price_downloader import KauflandPriceDownloader


def make_kaufland_store() -> Store:
    return Store(
        retailer_id=ReailerEnum.KAUFLAND.value.id,
        store_code="5930",
        name="Kaufland Jablanska 80",
        prefix="Hipermarket_Jablanska_ulica_br_80_Zagreb_5930_",
    )


def test_kaufland_store_match_allows_spaces_around_date_in_label():
    label = "Hipermarket_Jablanska_ulica_br_80_Zagreb_5930_ 13032026 _7-30.csv"

    assert KauflandPriceDownloader._matches_store(label, make_kaufland_store())


def test_kaufland_store_match_falls_back_to_store_code():
    label = "Hipermarket_Jablanska_ulica_br_80_Zagreb_5930_13032026_7-30.csv"
    store = make_kaufland_store()
    store.prefix = ""

    assert KauflandPriceDownloader._matches_store(label, store)
