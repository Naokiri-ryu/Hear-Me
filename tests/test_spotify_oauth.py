from datetime import datetime, timezone

from sqlalchemy import select

from api.clients.spotify_client import _utc_aware
from api.config import settings
from api.security import create_access_token, decrypt_token
from models.platform_credential import PlatformCredential


def test_spotify_login_requires_app_credentials(client, user, monkeypatch):
    monkeypatch.setattr(settings, "SPOTIFY_CLIENT_ID", "")
    monkeypatch.setattr(settings, "SPOTIFY_CLIENT_SECRET", "")
    headers = {"Authorization": f"Bearer {create_access_token(user.id)}"}
    resp = client.get("/auth/spotify/login", headers=headers)
    assert resp.status_code == 503


def test_spotify_login_and_callback(client, user, db_session, monkeypatch):
    monkeypatch.setattr(settings, "SPOTIFY_CLIENT_ID", "client-id")
    monkeypatch.setattr(settings, "SPOTIFY_CLIENT_SECRET", "client-secret")

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "access_token": "oauth-access",
                "refresh_token": "oauth-refresh",
                "expires_in": 3600,
                "scope": "playlist-read-private",
            }

    monkeypatch.setattr("api.auth.spotify.httpx.post", lambda *a, **k: FakeResponse())

    token = create_access_token(user.id)
    resp = client.get("/auth/spotify/callback", params={"code": "auth-code", "state": token})
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"status": "connected", "platform": "spotify"}

    cred = db_session.scalar(
        select(PlatformCredential).where(
            PlatformCredential.user_id == user.id,
            PlatformCredential.platform == "spotify",
        )
    )
    assert cred is not None
    assert decrypt_token(cred.access_token) == "oauth-access"
    assert decrypt_token(cred.refresh_token) == "oauth-refresh"
    assert _utc_aware(cred.expires_at) > datetime.now(timezone.utc)


def test_spotify_callback_rejects_bad_state(client, user, monkeypatch):
    resp = client.get("/auth/spotify/callback", params={"code": "x", "state": "not-a-jwt"})
    assert resp.status_code == 400