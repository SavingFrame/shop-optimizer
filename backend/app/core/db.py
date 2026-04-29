from sqlmodel import Session, SQLModel, create_engine, select

from app import crud
from app.core.config import settings
from app.models.price_observation import PriceObservation  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.product_alias import ProductAlias  # noqa: F401
from app.models.retailer import ReailerEnum, Retailer  # noqa: F401
from app.models.store import Store  # noqa: F401
from app.models.user import User, UserCreate

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


# make sure all SQLModel models are imported before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def get_or_create(session: Session, model: type[SQLModel], defaults=None, **params):
    instance = session.exec(select(model).filter_by(**params)).first()
    if instance:
        return instance, False
    else:
        params |= defaults or {}
        instance = model(**params)
        try:
            session.add(instance)
            session.commit()
        except Exception:  # The actual exception depends on the specific database so we catch all exceptions. This is similar to the official documentation: https://docs.sqlalchemy.org/en/latest/orm/session_transaction.html
            session.rollback()
            instance = session.query(model).filter_by(**params).one()
            return instance, False
        else:
            return instance, True


def init_db(session: Session) -> None:
    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        crud.create_user(session=session, user_create=user_in)
    for retailer in ReailerEnum:
        get_or_create(
            session,
            Retailer,
            name=retailer.value.name,
            id=retailer.value.id,
        )
    get_or_create(
        session,
        Store,
        retailer_id=ReailerEnum.SPAR.value.id,
        store_code="8711",
        name="Interspar Supernova",
        address="Kolakova 14",
        prefix="hipermarket_zagreb_kolakova_14__dubrava_8711_interspar_zg_garden_dub._",
    )

    get_or_create(
        session,
        Store,
        retailer_id=ReailerEnum.LIDL.value.id,
        store_code="209",
        name="Lidl Risnjačka 1",
        address="Risnjačka ul. 1, 10000, Zagreb",
        prefix="Supermarket 209_Risnjačka ulica_1_10000_Zagreb_",
    )

    get_or_create(
        session,
        Store,
        retailer_id=ReailerEnum.KAUFLAND.value.id,
        store_code="5930",
        name="Kaufland Jablanska 80",
        address="Jablanska ulica br. 80, Zagreb",
        prefix="Hipermarket_Jablanska_ulica_br_80_Zagreb_5930_",
    )
