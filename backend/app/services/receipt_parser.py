from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class ParsedReceiptItem:
    line_number: int
    raw_name: str
    normalized_raw_name: str
    quantity: Decimal
    unit_of_measure: str | None
    unit_price_eur: Decimal | None
    line_total_eur: Decimal


@dataclass(frozen=True)
class ParsedReceipt:
    purchase_datetime: datetime | None
    total_eur: Decimal | None
    raw_text: str
    items: list[ParsedReceiptItem]


def normalize_receipt_name(value: str) -> str:
    return " ".join(value.strip().lower().split())


def parse_spar_receipt(_content: bytes) -> ParsedReceipt:
    """Temporary SPAR parser stub.

    This is intentionally hardcoded from the current sample receipt so endpoint and
    review flow can be developed before real PDF extraction and parsing exist.
    """
    item_rows = [
        (1, "ŠUNKA KOCKICE 2X75 g", "2", None, "2.59", "5.18"),
        (2, "VREĆICA L RECIKLIRANA", "2", None, "0.19", "0.38"),
        (3, "PILEĆI FILE OP", "0.730", "kg", "12.65", "9.23"),
        (4, "PILEĆI FILE OP", "0.868", "kg", "12.65", "10.98"),
        (5, "Svinjetina mljevena", "0.592", "kg", "4.11", "2.43"),
        (6, "PUREĆE MLJEVENO 500 g", "1", None, "4.39", "4.39"),
        (7, "BIO JAGODA 250 g", "2", None, "1.59", "3.18"),
        (8, "KRASTAVAC SALATAR VH KOM", "2", None, "0.69", "1.38"),
        (9, "KREKER TUC SLANINA 100 g", "2", None, "0.79", "1.58"),
        (10, "MANGO READY TO EAT", "1", None, "2.19", "2.19"),
        (11, "UMAK SW.CHIL.ASIA 700 ml", "1", None, "8.49", "8.49"),
        (12, "IN.JUHA POD.POVRĆE 375 g", "1", None, "1.59", "1.59"),
        (13, "VAFEL FRONDI LIMUN 250 g", "1", None, "1.99", "1.99"),
        (14, "VRH.ZA KUH.DUKAT 3X200 g", "1", None, "3.99", "3.99"),
        (15, "TJ.BARILLA PIPE RI.500 g", "1", None, "1.89", "1.89"),
        (16, "POLI 500 g PERUTNINA", "1", None, "4.49", "4.49"),
        (17, "MLIJ.SV.3,2% Z BREG.1 L", "1", None, "1.49", "1.49"),
        (18, "RIŽA LJEPLJIVA SPAR 1 Kg", "1", None, "3.99", "3.99"),
        (19, "SALATA KRIST. KOM", "1", None, "0.89", "0.89"),
        (20, "VREĆICA VRLO LAGANA PVC", "1", None, "0.01", "0.01"),
        (21, "JOG.FORTIA VIŠNJA 330 g", "1", None, "1.49", "1.49"),
        (22, "JOG.JAG/CR.RIBIZ 330 g", "1", None, "1.49", "1.49"),
        (23, "JAJA ŽITO POD.UZ.M 10/1", "2", None, "2.99", "5.98"),
    ]
    items = [
        ParsedReceiptItem(
            line_number=line_number,
            raw_name=raw_name,
            normalized_raw_name=normalize_receipt_name(raw_name),
            quantity=Decimal(quantity),
            unit_of_measure=unit_of_measure,
            unit_price_eur=Decimal(unit_price_eur) if unit_price_eur else None,
            line_total_eur=Decimal(line_total_eur),
        )
        for (
            line_number,
            raw_name,
            quantity,
            unit_of_measure,
            unit_price_eur,
            line_total_eur,
        ) in item_rows
    ]

    return ParsedReceipt(
        purchase_datetime=datetime(2026, 4, 18, 13, 25),
        total_eur=Decimal("78.70"),
        raw_text="Temporary hardcoded SPAR receipt parser output.",
        items=items,
    )
