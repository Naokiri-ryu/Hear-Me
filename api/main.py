from fastapi import FastAPI

from api.auth import spotify as spotify_oauth
from api.config import settings
from api.routers import auth, connections, health, jobs, playlists

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(spotify_oauth.router)
app.include_router(playlists.router)
app.include_router(connections.router)
app.include_router(jobs.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"app": settings.APP_NAME, "docs": "/docs", "health": "/health"}