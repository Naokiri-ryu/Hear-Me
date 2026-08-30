from types import SimpleNamespace

from models.playlist import Playlist
from models.playlist_track import PlaylistTrack
from models.track import Track
from models.user import User

HITS = {
    "Known One": SimpleNamespace(album="Album X", isrc="USABC1234567", length_ms=180000),
    "Known Two": SimpleNamespace(album=None, isrc="USABC7654321", length_ms=200000),
}


class FakeMusicBrainzClient:
    def __init__(self, *args, **kwargs):
        self.searched = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None

    def search_recording(self, title, artist=None):
        self.searched.append(title)
        return HITS[title] if title in HITS else None


def _patch_client(monkeypatch, dbfactory_value):
    import api.clients.musicbrainz_client as mb_module
    from workers.tasks import enrich_playlist as enrich_tasks

    monkeypatch.setattr(mb_module, "MusicBrainzClient", FakeMusicBrainzClient)
    monkeypatch.setattr(enrich_tasks, "SessionLocal", dbfactory_value)


def test_enrich_fills_metadata(db_session, dbfactory, eager, monkeypatch):
    from workers.tasks import enrich_playlist as enrich_tasks

    user = User(email="enrich@example.com", password_hash="x", display_name="Enrich")
    db_session.add(user)
    db_session.commit()

    playlist = Playlist(user_id=user.id, name="Needs Metadata")
    db_session.add(playlist)
    db_session.commit()

    tracks = []
    for title in ("Known One", "Known Two", "Unknown One"):
        track = Track(title=title, artist="Artist", album=None, duration_ms=None, isrc=None)
        db_session.add(track)
        tracks.append(track)
    db_session.flush()
    for pos, track in enumerate(tracks):
        db_session.add(PlaylistTrack(playlist_id=playlist.id, track_id=track.id, position=pos))
    db_session.commit()

    _patch_client(monkeypatch, dbfactory)
    result = enrich_tasks.enrich_playlist(user.id, playlist.id)

    assert result["ok"] is True
    assert result["enriched"] == 2
    assert result["updated"] == 2
    assert result["searched"] == 3

    db_session.expire_all()
    known_one = db_session.query(Track).filter(Track.title == "Known One").one()
    assert known_one.album == "Album X"
    assert known_one.isrc == "USABC1234567"
    assert known_one.duration_ms == 180000

    unknown = db_session.query(Track).filter(Track.title == "Unknown One").one()
    assert unknown.album is None
    assert unknown.isrc is None


def test_enrich_is_idempotent(db_session, dbfactory, eager, monkeypatch):
    from workers.tasks import enrich_playlist as enrich_tasks

    user = User(email="enrich2@example.com", password_hash="x", display_name="Enrich")
    db_session.add(user)
    db_session.commit()

    playlist = Playlist(user_id=user.id, name="N")
    db_session.add(playlist)
    db_session.commit()
    track = Track(title="Known One", artist="Artist", album=None, duration_ms=None, isrc=None)
    db_session.add(track)
    db_session.flush()
    db_session.add(PlaylistTrack(playlist_id=playlist.id, track_id=track.id, position=0))
    db_session.commit()

    _patch_client(monkeypatch, dbfactory)
    first = enrich_tasks.enrich_playlist(user.id, playlist.id)
    second = enrich_tasks.enrich_playlist(user.id, playlist.id)

    # second run: track already enriched, client still searched but nothing to update
    assert first["updated"] == 1
    assert second["searched"] == 1
    assert second["updated"] == 0


def test_enrich_playlist_missing_playlist(db_session, dbfactory, eager, monkeypatch):
    from workers.tasks import enrich_playlist as enrich_tasks

    user = User(email="enrich3@example.com", password_hash="x", display_name="Enrich")
    db_session.add(user)
    db_session.commit()

    _patch_client(monkeypatch, dbfactory)
    result = enrich_tasks.enrich_playlist(user.id, 999999)
    assert result == {"ok": False, "reason": "not_found", "updated": 0}