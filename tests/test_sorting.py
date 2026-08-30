from models.playlist import Playlist
from models.playlist_track import PlaylistTrack
from models.track import Track
from models.user import User
from workers.sorting import order_tracks


def _mk(id, title, artist=None, album=None, duration_ms=None):
    return Track(id=id, title=title, artist=artist, album=album, duration_ms=duration_ms)


def test_order_by_title_case_insensitive():
    tracks = [
        _mk(1, "zeta"),
        _mk(2, "Alpha"),
        _mk(3, "beta", artist="Rock"),
    ]
    assert [t.id for t in order_tracks(tracks, "title")] == [2, 3, 1]


def test_order_by_artist_then_title():
    tracks = [
        _mk(1, "Song B", artist="Zed"),
        _mk(2, "Song A", artist="Zed"),
        _mk(3, "Song C", artist="Aya"),
    ]
    assert [t.id for t in order_tracks(tracks, "artist")] == [3, 2, 1]


def test_order_by_duration_missing_goes_first():
    tracks = [
        _mk(1, "Long", duration_ms=99999),
        _mk(2, "Short", duration_ms=1),
        _mk(3, "Unknown", duration_ms=None),
    ]
    assert [t.id for t in order_tracks(tracks, "duration")] == [3, 2, 1]


def test_order_by_album():
    tracks = [
        _mk(1, "T", album="Beta"),
        _mk(2, "T", album="Alpha"),
    ]
    assert [t.id for t in order_tracks(tracks, "album")] == [2, 1]


def test_unsupported_strategy_raises():
    import pytest

    with pytest.raises(ValueError):
        order_tracks([_mk(1, "x")], "mood")


def _seed(playlist_id, positions, session):
    for pos, (title, artist) in positions:
        track = Track(title=title, artist=artist, album="A", duration_ms=42)
        session.add(track)
        session.flush()
        session.add(PlaylistTrack(playlist_id=playlist_id, track_id=track.id, position=pos))
    session.commit()


def test_sort_playlist_task_reorders_positions(db_session, dbfactory, eager, monkeypatch):
    from workers.tasks import sort_playlist as sort_tasks

    user = User(email="sort@example.com", password_hash="x", display_name="Sort")
    db_session.add(user)
    db_session.commit()
    user_id = user.id
    playlist = Playlist(user_id=user_id, name="Sort Me")
    db_session.add(playlist)
    db_session.commit()

    _seed(playlist.id, [(0, ("Z Last", "Zed")), (1, ("A First", "Aya"))], db_session)

    monkeypatch.setattr(sort_tasks, "SessionLocal", dbfactory)
    result = sort_tasks.sort_playlist(user_id, playlist.id, "artist")
    assert result["ok"] is True
    assert result["strategy"] == "artist"
    assert result["reordered"] == 2

    db_session.expire_all()
    links = db_session.query(PlaylistTrack).filter(PlaylistTrack.playlist_id == playlist.id).all()
    by_title = {}
    for link in links:
        track = db_session.get(Track, link.track_id)
        by_title[track.title] = link.position
    assert by_title["A First"] < by_title["Z Last"]


def test_sort_playlist_task_unsupported_strategy(db_session, dbfactory, eager, monkeypatch):
    from workers.tasks import sort_playlist as sort_tasks

    user = User(email="sort2@example.com", password_hash="x", display_name="Sort")
    db_session.add(user)
    db_session.commit()
    playlist = Playlist(user_id=user.id, name="No Sort")
    db_session.add(playlist)
    db_session.commit()

    monkeypatch.setattr(sort_tasks, "SessionLocal", dbfactory)
    result = sort_tasks.sort_playlist(user.id, playlist.id, "bogus")
    assert result == {"ok": False, "reason": "unsupported_strategy", "reordered": 0}


def test_sort_playlist_task_missing_playlist(db_session, dbfactory, eager, monkeypatch):
    from workers.tasks import sort_playlist as sort_tasks

    user = User(email="sort3@example.com", password_hash="x", display_name="Sort")
    db_session.add(user)
    db_session.commit()

    monkeypatch.setattr(sort_tasks, "SessionLocal", dbfactory)
    result = sort_tasks.sort_playlist(user.id, 999999, "title")
    assert result["ok"] is False
    assert result["reason"] == "not_found"