from datetime import datetime, timedelta, timezone

from api.security import encrypt_token
from models.platform_credential import PlatformCredential
from models.user import User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_connections_empty(client, token):
    resp = client.get("/connections", headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["platforms"][0] == {
        "platform": "spotify",
        "connected": False,
        "expires_at": None,
    }


def test_connections_reflect_credential(client, token, db_session):
    me = db_session.query(User).filter(User.email == "u@example.com").one()
    db_session.add(
        PlatformCredential(
            user_id=me.id,
            platform="spotify",
            access_token=encrypt_token("a"),
            refresh_token=encrypt_token("r"),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
    )
    db_session.commit()

    resp = client.get("/connections", headers=_auth_headers(token))
    spotify = resp.json()["platforms"][0]
    assert spotify["platform"] == "spotify"
    assert spotify["connected"] is True
    assert spotify["expires_at"] is not None


def test_connections_require_auth(client):
    assert client.get("/connections").status_code == 401


def test_disconnect_clears_credential(client, token, db_session):
    me = db_session.query(User).filter(User.email == "u@example.com").one()
    db_session.add(
        PlatformCredential(
            user_id=me.id,
            platform="spotify",
            access_token=encrypt_token("a"),
            refresh_token=encrypt_token("r"),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
    )
    db_session.commit()

    resp = client.delete("/connections/spotify", headers=_auth_headers(token))
    assert resp.status_code == 204

    gone = db_session.query(PlatformCredential).filter(PlatformCredential.user_id == me.id).count()
    assert gone == 0

    resp = client.get("/connections", headers=_auth_headers(token))
    assert resp.json()["platforms"][0]["connected"] is False


def test_disconnect_unsupported_platform(client, token):
    resp = client.delete("/connections/youtube", headers=_auth_headers(token))
    assert resp.status_code == 400