import pytest
from sqlalchemy import select
from types import SimpleNamespace

from models.playlist import Playlist
from models.playlist_group import PlaylistGroup
from models.playlist_track import PlaylistTrack
from models.track import Track
from models.user import User
from workers.grouping import (
    group_by_album,
    group_by_artist,
    group_by_decade,
    group_by_genre,
    group_tracks,
)


def _mk(id, title, artist=None, album=None, genres=None, release_year=None):
    return Track(
        id=id,
        title=title,
        artist=artist,
        album=album,
        genres=genres,
        release_year=release_year,
    )


def test_group_by_genre_multi_category():
    tracks = [
        _mk(1, "A", genres=["rock", "indie"]),
        _mk(2, "B", genres=["rock"]),
        _mk(3, "Z", genres=None),
    ]
    assert group_by_genre(tracks) == {
        "indie": [1],
        "rock": [1, 2],
        "Unknown": [3],
    }


def test_group_by_artist_uses_primary():
    tracks = [
        _mk(1, "Z", artist="Aya, Bob"),
        _mk(2, "A", artist="Aya"),
        _mk(3, "M", artist=None),
    ]
    assert group_by_artist(tracks) == {
        "Aya": [2, 1],  # ordered by title within the category
        "Unknown": [3],
    }


def test_group_by_album_case_insensitive_order_of_categories():
    tracks = [
        _mk(1, "S", album="Beta"),
        _mk(2, "S", album="alpha"),
        _mk(3, "S", album=None),
    ]
    assert group_by_album(tracks) == {
        "alpha": [2],
        "Beta": [1],
        "Unknown": [3],
    }


def test_group_by_decade():
    tracks = [
        _mk(1, "S", release_year=2023),
        _mk(2, "S", release_year=1998),
        _mk(3, "S", release_year=None),
    ]
    assert group_by_decade(tracks) == {
        "1990s": [2],
        "2020s": [1],
        "Unknown": [3],
    }


def test_group_by_decade_boundary():
    assert group_by_decade([_mk(1, "S", release_year=1970)]) == {"1970s": [1]}


def test_unsupported_sort_by_raises():
    with pytest.raises(ValueError):
        group_tracks([_mk(1, "S")], "mood")


def _seed_groups_playlist(db_session, dbfactory=None):
    user = User(email="grp@example.com", password_hash="x", display_name="Grp")
    db_session.add(user)
    db_session.commit()
    playlist = Playlist(user_id=user.id, name="Groups")
    db_session.add(playlist)
    db_session.commit()
    rows = [
        ("Alpha Rock", "Aya", "Album X", ["rock", "indie"], 2023),
        ("Beta Rock", "Aya", "Album X", ["rock"], 2023),
        ("Zed Jazz", "Ben", "Album Y", ["jazz"], 2001),
        ("No Genre", "Cal", "Album Z", None, None),
    ]
    for pos, (title, artist, album, genres, year) in enumerate(rows):
        track = Track(title=title, artist=artist, album=album, genres=genres, release_year=year)
        db_session.add(track)
        db_session.flush()
        db_session.add(
            PlaylistTrack(playlist_id=playlist.id, track_id=track.id, position=pos)
        )
    db_session.commit()
    return user.id, playlist.id


def _title_map(db_session, playlist_id):
    links = db_session.scalars(
        select(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist_id)
    ).all()
    return {
        link.track_id: db_session.get(Track, link.track_id).title for link in links
    }


def test_group_playlist_task_stores_snapshot(db_session, dbfactory, eager, monkeypatch):
    from workers.tasks import group_playlist as group_tasks

    user_id, playlist_id = _seed_groups_playlist(db_session)
    monkeypatch.setattr(group_tasks, "SessionLocal", dbfactory)

    result = group_tasks.group_playlist(user_id, playlist_id, "genre")
    assert result["ok"] is True
    assert result["sort_by"] == "genre"
    assert result["track_count"] == 4
    assert result["group_count"] == 4
    by_id = _title_map(db_session, playlist_id)
    assert [by_id[i] for i in result["groups"]["rock"]] == ["Alpha Rock", "Beta Rock"]
    assert [by_id[i] for i in result["groups"]["indie"]] == ["Alpha Rock"]
    assert result["groups"]["Unknown"]  # no-genre track

    with dbfactory() as session:
        stored = session.scalar(
            select(PlaylistGroup).where(PlaylistGroup.playlist_id == playlist_id)
        )
        assert stored is not None
        assert stored.sort_by == "genre"
        assert stored.track_count == 4
        assert stored.groups == result["groups"]


def test_group_playlist_task_idempotent(db_session, dbfactory, eager, monkeypatch):
    from workers.tasks import group_playlist as group_tasks

    user_id, playlist_id = _seed_groups_playlist(db_session)
    monkeypatch.setattr(group_tasks, "SessionLocal", dbfactory)

    group_tasks.group_playlist(user_id, playlist_id, "decade")
    group_tasks.group_playlist(user_id, playlist_id, "decade")

    with dbfactory() as session:
        rows = session.scalars(
            select(PlaylistGroup).where(PlaylistGroup.playlist_id == playlist_id)
        ).all()
        assert len(rows) == 1  # re-run replaces, never duplicates


def test_group_playlist_task_decade_buckets(db_session, dbfactory, eager, monkeypatch):
    from workers.tasks import group_playlist as group_tasks

    user_id, playlist_id = _seed_groups_playlist(db_session)
    monkeypatch.setattr(group_tasks, "SessionLocal", dbfactory)

    result = group_tasks.group_playlist(user_id, playlist_id, "decade")
    assert set(result["groups"]) == {"2020s", "2000s", "Unknown"}
    assert result["track_count"] == 4
    by_id = _title_map(db_session, playlist_id)
    assert [by_id[i] for i in result["groups"]["2000s"]] == ["Zed Jazz"]


def test_group_playlist_task_not_found(db_session, dbfactory, eager, monkeypatch):
    from workers.tasks import group_playlist as group_tasks

    user_id, playlist_id = _seed_groups_playlist(db_session)
    monkeypatch.setattr(group_tasks, "SessionLocal", dbfactory)

    result = group_tasks.group_playlist(user_id, 999999, "genre")
    assert result == {
        "ok": False,
        "reason": "not_found",
        "sort_by": "genre",
        "groups": {},
    }


def test_group_playlist_task_unsupported_strategy(db_session, dbfactory, eager, monkeypatch):
    from workers.tasks import group_playlist as group_tasks

    user_id, playlist_id = _seed_groups_playlist(db_session)
    monkeypatch.setattr(group_tasks, "SessionLocal", dbfactory)

    result = group_tasks.group_playlist(user_id, playlist_id, "mood")
    assert result["ok"] is False
    assert result["reason"] == "unsupported_strategy"


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_group_dispatch_queues_task(client, token, db_session, monkeypatch):
    resp = client.post("/playlists", headers=_auth_headers(token), json={"name": "Groupable"})
    assert resp.status_code == 201, resp.text
    playlist_id = resp.json()["id"]
    user_id = client.get("/auth/me", headers=_auth_headers(token)).json()["id"]
    captured = {}

    import api.routers.playlists as playlists_mod

    def fake_send_task(name, args=None, **kwargs):
        captured["name"] = name
        captured["args"] = args
        return SimpleNamespace(id="task-g1")

    monkeypatch.setattr(playlists_mod.celery_app, "send_task", fake_send_task)

    resp = client.post(
        f"/playlists/{playlist_id}/group",
        headers=_auth_headers(token),
        json={"sort_by": "genre"},
    )
    assert resp.status_code == 202, resp.text
    assert captured["name"] == "workers.group_playlist"
    assert captured["args"] == [user_id, playlist_id, "genre"]
    assert resp.json()["task_id"] == "task-g1"

    resp = client.post(
        f"/playlists/{playlist_id}/group",
        headers=_auth_headers(token),
        json={"sort_by": "mood"},
    )
    assert resp.status_code == 422


def test_list_playlist_groups(client, token, db_session):
    resp = client.post("/playlists", headers=_auth_headers(token), json={"name": "Shown"})
    assert resp.status_code == 201, resp.text
    playlist_id = resp.json()["id"]

    db_session.add(
        PlaylistGroup(
            playlist_id=playlist_id,
            sort_by="genre",
            groups={"rock": [1, 2], "jazz": [3]},
            track_count=3,
        )
    )
    db_session.commit()

    resp = client.get(f"/playlists/{playlist_id}/groups", headers=_auth_headers(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body) == 1
    assert body[0]["sort_by"] == "genre"
    assert body[0]["groups"] == {"rock": [1, 2], "jazz": [3]}
    assert body[0]["track_count"] == 3
    assert body[0]["group_count"] == 2
    assert body[0]["created_at"] is not None


def test_list_playlist_groups_requires_owner(client, token, db_session):
    db_session.add(Playlist(name="Secret", user_id=99999))
    db_session.commit()
    secret = db_session.scalar(select(Playlist).where(Playlist.name == "Secret"))
    resp = client.get(f"/playlists/{secret.id}/groups", headers=_auth_headers(token))
    assert resp.status_code == 404