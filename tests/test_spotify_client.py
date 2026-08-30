from datetime import datetime, timedelta, timezone

import pytest

from api.clients.spotify_client import SpotifyClient, SpotifyClientError, _utc_aware
from api.security import encrypt_token
from models.platform_credential import PlatformCredential


def _make_credential(db_session, *, access="stale-access", refresh="refresh-tok", expires_at=None):
    cred = PlatformCredential(
        user_id=1,
        platform="spotify",
        access_token=encrypt_token(access),
        refresh_token=encrypt_token(refresh),
        expires_at=expires_at,
    )
    db_session.add(cred)
    db_session.commit()
    db_session.refresh(cred)
    return cred


def test_refresh_before_expired(db_session, monkeypatch):
    class FakeResponse:
        status_code = 200

        def json(self):
            return {"access_token": "fresh-access", "expires_in": 3600}

    monkeypatch.setattr(
        "api.clients.spotify_client.httpx.post",
        lambda *a, **k: FakeResponse(),
    )
    cred = _make_credential(
        db_session,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    client = SpotifyClient(cred, db_session)
    token = client._get_access_token()
    assert token == "fresh-access"
    db_session.refresh(cred)
    assert _utc_aware(cred.expires_at) > datetime.now(timezone.utc)


def test_refresh_raises_without_refresh_token(db_session):
    cred = _make_credential(db_session, refresh="owner", expires_at=None)
    client = SpotifyClient(cred, db_session)
    with pytest.raises(SpotifyClientError):
        client._get_access_token()


def test_get_playlist_parses_internal_schema(monkeypatch):
    page = {
        "id": "pl1",
        "name": "My Playlist",
        "description": "desc",
        "owner": {"display_name": "Tester"},
        "tracks": {
            "items": [
                {
                    "track": {
                        "id": "t1",
                        "name": "Song One",
                        "artists": [{"name": "Artist A"}, {"name": "Artist B"}],
                        "album": {"name": "Album X"},
                        "duration_ms": 180000,
                        "external_ids": {"isrc": "USABC1234567"},
                    }
                },
                {"track": None},
            ]
        },
    }

    class FakeClient(SpotifyClient):
        def __init__(self):
            super().__init__(object(), object())

        def _request(self, method, path, params=None):
            return page

    client = FakeClient()
    data = client.get_playlist("pl1")
    assert data["id"] == "pl1"
    assert data["tracks"] == [
        {
            "track_id": "t1",
            "title": "Song One",
            "artist": "Artist A, Artist B",
            "album": "Album X",
            "duration_ms": 180000,
            "isrc": "USABC1234567",
        }
    ]