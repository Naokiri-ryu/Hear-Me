from fastapi import FastAPI

from api.config import settings
from api.routers import health

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

app.include_router(health.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"app": settings.APP_NAME, "docs": "/docs", "health": "/health"}