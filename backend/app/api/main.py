from fastapi import APIRouter

from app.api.routes import dashboard, login, private, products, receipts, users, utils
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(products.router)
api_router.include_router(receipts.router)
api_router.include_router(dashboard.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
