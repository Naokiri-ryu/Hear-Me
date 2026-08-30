from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from api.db import get_db
from api.dependencies import get_current_user
from models.platform_credential import PlatformCredential
from models.user import User

router = APIRouter(prefix="/connections", tags=["connections"])

PLATFORMS = ("spotify",)


class ConnectionOut(BaseModel):
    platform: str
    connected: bool
    expires_at: datetime | None


class ConnectionsOut(BaseModel):
    platforms: list[ConnectionOut]


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@router.get("", response_model=ConnectionsOut)
def list_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConnectionsOut:
    creds = db.scalars(
        select(PlatformCredential).where(PlatformCredential.user_id == current_user.id)
    ).all()
    by_platform = {c.platform: c for c in creds}
    now = datetime.now(timezone.utc)
    items = []
    for platform in PLATFORMS:
        cred = by_platform.get(platform)
        connected = False
        expires_at = None
        if cred is not None:
            expires = _as_utc(cred.expires_at) if cred.expires_at is not None else None
            connected = expires is None or expires > now
            expires_at = expires
        items.append(ConnectionOut(platform=platform, connected=connected, expires_at=expires_at))
    return ConnectionsOut(platforms=items)


@router.delete("/{platform}", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_platform(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    if platform not in PLATFORMS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported platform: {platform}")
    db.execute(
        delete(PlatformCredential).where(
            PlatformCredential.user_id == current_user.id,
            PlatformCredential.platform == platform,
        )
    )
    db.commit()