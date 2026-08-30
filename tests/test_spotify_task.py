from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from api.security import encrypt_token
from models.playlist import Playlist
from models.playlist_track import PlaylistTrack
from models.platform_credential import PlatformCredential
from models.track import Track
from models.user import User

FAKE_PLAYLIST = {
    "id": "spotify-pl-1",
    "name": "Road Trip",
    "description": "for driving",
    "owner": "Tester",
    "tracks": [
        {
            "track_id": "st1",
            "title": "Song One",
            "artist": "Artist A, Artist B",
            "artist_ids": ["a1", "a2"],
            "album": "Album X",
            "release_date": "2024-05-20",
            "duration_ms": 180000,
            "isrc": "USABC1234567",
        },
        {
            "track_id": "st2",
            "title": "Song Two",
            "artist": "Artist C",
            "artist_ids": ["a3"],
            "album": "Album Y",
            "release_date": "1998-01-31",
            "duration_ms": 200000,
            "isrc": None,
        },
    ],
}

FAKE_ARTIST_GENRES = {"a1": ["rock", "indie"], "a2": ["synth-pop"], "a3": ["jazz"]}


def _seed_user_and_credential(task_factory):
    with task_factory() as session:
        user = User(
            email="task@example.com",
            password_hash="ignored-in-test",
            display_name="Tasker",
        )
        session.add(user)
        session.flush()
        cred = PlatformCredential(
            user_id=user.id,
            platform="spotify",
            access_token=encrypt_token("valid-access"),
            refresh_token=encrypt_token("refresh"),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        session.add(cred)
        session.commit()
        return user.id


def test_fetch_spotify_playlist_idempotent(db_session, dbfactory, eager, monkeypatch):
    from api.clients import spotify_client as client_module
    from workers.tasks import spotify as spotify_tasks

    user_id = _seed_user_and_credential(dbfactory)
    monkeypatch.setattr(spotify_tasks, "SessionLocal", dbfactory)
    monkeypatch.setattr(client_module.SpotifyClient, "get_playlist", lambda self, pid: FAKE_PLAYLIST)
    monkeypatch.setattr(
        client_module.SpotifyClient,
        "get_artists",
        lambda self, ids: FAKE_ARTIST_GENRES,
    )

    first = spotify_tasks.fetch_spotify_playlist(user_id, "spotify-pl-1")
    assert first["tracks"] == 2

    second = spotify_tasks.fetch_spotify_playlist(user_id, "spotify-pl-1")
    assert second["tracks"] == 2

    with dbfactory() as session:
        playlist = session.scalar(
            select(Playlist).where(Playlist.source_playlist_id == "spotify-pl-1")
        )
        assert playlist is not None
        assert playlist.name == "Road Trip"

        tracks = session.scalars(select(Track)).all()
        assert len(tracks) == 2
        by_title = {t.title: t for t in tracks}
        # genre = union across the track's artists (multi-artist, multi-genre)
        assert set(by_title["Song One"].genres) == {"rock", "indie", "synth-pop"}
        assert by_title["Song Two"].genres == ["jazz"]
        assert by_title["Song One"].release_year == 2024
        assert by_title["Song Two"].release_year == 1998

        links = session.scalars(
            select(PlaylistTrack)
            .where(PlaylistTrack.playlist_id == playlist.id)
            .order_by(PlaylistTrack.position)
        ).all()
        assert [link.position for link in links] == [0, 1]

    # idempotent: re-running does not duplicate rows
    with dbfactory() as session:
        assert len(session.scalars(select(Track)).all()) == 2
        assert len(
            session.scalars(select(Playlist).where(Playlist.user_id == user_id)).all()
        ) == 1


def test_fetch_spotify_playlist_missing_credential(dbfactory, eager, monkeypatch):
    import pytest

    from api.clients.spotify_client import SpotifyClientError
    from workers.tasks import spotify as spotify_tasks

    with dbfactory() as session:
        user = User(email="no-cred@example.com", password_hash="x", display_name="NoCred")
        session.add(user)
        session.commit()
        user_id = user.id

    monkeypatch.setattr(spotify_tasks, "SessionLocal", dbfactory)
    with pytest.raises(SpotifyClientError):
        spotify_tasks.fetch_spotify_playlist(user_id, "spotify-pl-1")