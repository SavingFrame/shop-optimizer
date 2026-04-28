from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class ProductSearchBase(DeclarativeBase):
    pass


class ProductSearchIndex(ProductSearchBase):
    """SQLAlchemy mapping for the SQLite FTS5 product search virtual table.

    The table is created by Alembic with CREATE VIRTUAL TABLE, not by metadata.
    Keep this model on separate metadata so SQLModel autogeneration does not try
    to create product_fts as a normal table.
    """

    __tablename__ = "product_fts"

    rowid: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String)
    brand: Mapped[str | None] = mapped_column(String)
    category: Mapped[str | None] = mapped_column(String)
