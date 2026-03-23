from fastapi import FastAPI

from app.core.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": f"{settings.app_name} is running",
        "version": settings.version,
    }