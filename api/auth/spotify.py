from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.config import settings
from api.db import get_db
from api.dependencies import get_current_user
from api.security import create_access_token, decode_access_token, encrypt_token
from models.platform_credential import PlatformCredential
from models.user import User

router = APIRouter(prefix="/auth/spotify", tags=["spotify"])

SPOTIFY_SCOPES = (
    "user-read-private "
    "playlist-read-private "
    "playlist-modify-public "
    "playlist-modify-private"
)
_STATE_TTL = timedelta(minutes=10)


def _token_url() -> str:
    return f"{settings.SPOTIFY_ACCOUNTS_BASE}/api/token"


def _authorize_url(user_id: int) -> str:
    state = create_access_token(str(user_id), expires_delta=_STATE_TTL)
    params = {
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "scope": SPOTIFY_SCOPES,
        "state": state,
    }
    return f"{settings.SPOTIFY_ACCOUNTS_BASE}/authorize?{urlencode(params)}"


@router.get("/login")
def spotify_login(current_user: User = Depends(get_current_user)) -> dict[str, str]:
    if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Spotify app credentials not configured (SPOTIFY_CLIENT_ID/SECRET)",
        )
    return {"authorize_url": _authorize_url(current_user.id)}


@router.get("/callback")
def spotify_callback(code: str, state: str, db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        payload = decode_access_token(state)
        user_id = int(payload["sub"])
    except (ValueError, KeyError, jwt.PyJWTError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown user")

    resp = httpx.post(
        _token_url(),
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "client_secret": settings.SPOTIFY_CLIENT_SECRET,
        },
        timeout=30,
    )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Spotify token exchange failed",
        )

    body = resp.json()
    credential = db.scalar(
        select(PlatformCredential).where(
            PlatformCredential.user_id == user_id,
            PlatformCredential.platform == "spotify",
        )
    )
    if credential is None:
        credential = PlatformCredential(user_id=user_id, platform="spotify")
        db.add(credential)

    now = datetime.now(timezone.utc)
    credential.access_token = encrypt_token(body["access_token"])
    if body.get("refresh_token"):
        credential.refresh_token = encrypt_token(body["refresh_token"])
    credential.expires_at = now + timedelta(seconds=body.get("expires_in", 3600))
    credential.scope = body.get("scope")
    db.commit()

    return {"status": "connected", "platform": "spotify"}