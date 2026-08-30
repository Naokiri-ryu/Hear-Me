from types import SimpleNamespace

from sqlalchemy import select

from models.playlist import Playlist
from models.playlist_track import PlaylistTrack
from models.track import Track


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _seed_tracks(db_session, titles):
    tracks = []
    for title in titles:
        track = Track(
            title=title,
            artist=f"Artist {title[-1]}",
            album=f"Album {title[-1]}",
            duration_ms=1000,
        )
        db_session.add(track)
        tracks.append(track)
    db_session.commit()
    return tracks


def _make_remote_playlist(client, db_session, token, name="Road Trip"):
    resp = client.post("/playlists", headers=_auth_headers(token), json={"name": name})
    assert resp.status_code == 201, resp.text
    playlist_id = resp.json()["id"]
    playlist = db_session.get(Playlist, playlist_id)
    playlist.source_platform = "spotify"
    playlist.source_playlist_id = "spot-remote-1"
    db_session.commit()
    return playlist_id


def test_create_list_detail_delete(client, token, db_session):
    resp = client.post("/playlists", headers=_auth_headers(token), json={"name": "Chill"})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    playlist_id = body["id"]
    assert body["name"] == "Chill"
    assert body["tracks"] == []

    tracks = _seed_tracks(db_session, ["A", "B", "C"])
    for pos, track in ((2, tracks[0]), (0, tracks[1]), (1, tracks[2])):
        db_session.add(PlaylistTrack(playlist_id=playlist_id, track_id=track.id, position=pos))
    db_session.commit()

    resp = client.get("/playlists", headers=_auth_headers(token))
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["track_count"] == 3

    resp = client.get(f"/playlists/{playlist_id}", headers=_auth_headers(token))
    assert resp.status_code == 200
    tracks_out = resp.json()["tracks"]
    assert [t["track"]["title"] for t in tracks_out] == ["B", "C", "A"]

    resp = client.delete(f"/playlists/{playlist_id}", headers=_auth_headers(token))
    assert resp.status_code == 204
    assert client.get(f"/playlists/{playlist_id}", headers=_auth_headers(token)).status_code == 404


def test_playlist_requires_auth(client):
    assert client.get("/playlists").status_code == 401
    assert client.post("/playlists", json={"name": "X"}).status_code == 401


def test_playlist_ownership(client, token, db_session):
    created = client.post("/playlists", headers=_auth_headers(token), json={"name": "Mine"})
    assert created.status_code == 201
    mine = created.json()["id"]

    other_user_id = 99999
    db_session.add(Playlist(name="Secret", user_id=other_user_id))
    db_session.commit()
    secret = db_session.scalar(select(Playlist).where(Playlist.name == "Secret"))

    resp = client.get(f"/playlists/{secret.id}", headers=_auth_headers(token))
    assert resp.status_code == 404
    resp = client.delete(f"/playlists/{secret.id}", headers=_auth_headers(token))
    assert resp.status_code == 404
    resp = client.get(f"/playlists/{mine}", headers=_auth_headers(token))
    assert resp.status_code == 200


def test_sync_dispatch_queues_celery_task(client, token, db_session, monkeypatch):
    playlist_id = _make_remote_playlist(client, db_session, token)
    captured = {}

    import api.routers.playlists as playlists_mod

    def fake_send_task(name, args=None, **kwargs):
        captured["name"] = name
        captured["args"] = args
        return SimpleNamespace(id="task-1")

    monkeypatch.setattr(playlists_mod.celery_app, "send_task", fake_send_task)

    resp = client.post(f"/playlists/{playlist_id}/sync", headers=_auth_headers(token))
    assert resp.status_code == 202, resp.text
    assert resp.json()["task_id"] == "task-1"
    assert captured["name"] == "workers.fetch_spotify_playlist"


def test_sync_requires_remote_source(client, token, db_session):
    resp = client.post("/playlists", headers=_auth_headers(token), json={"name": "Local"})
    playlist_id = resp.json()["id"]
    resp = client.post(f"/playlists/{playlist_id}/sync", headers=_auth_headers(token))
    assert resp.status_code == 400
    assert "no remote source" in resp.json()["detail"].lower()


def test_sort_dispatch(client, token, db_session, monkeypatch):
    playlist_id = _make_remote_playlist(client, db_session, token, name="Sortable")
    user_id = client.get("/auth/me", headers=_auth_headers(token)).json()["id"]
    captured = {}

    import api.routers.playlists as playlists_mod

    def fake_send_task(name, args=None, **kwargs):
        captured["name"] = name
        captured["args"] = args
        return SimpleNamespace(id="task-2")

    monkeypatch.setattr(playlists_mod.celery_app, "send_task", fake_send_task)

    resp = client.post(
        f"/playlists/{playlist_id}/sort",
        headers=_auth_headers(token),
        json={"strategy": "artist"},
    )
    assert resp.status_code == 202, resp.text
    assert captured["name"] == "workers.sort_playlist"
    assert captured["args"] == [user_id, playlist_id, "artist"]
    assert resp.json()["task_id"] == "task-2"

    resp = client.post(
        f"/playlists/{playlist_id}/sort",
        headers=_auth_headers(token),
        json={"strategy": "mood"},
    )
    assert resp.status_code == 422


def test_enrich_dispatch(client, token, db_session, monkeypatch):
    playlist_id = _make_remote_playlist(client, db_session, token, name="Enrichable")
    captured = {}

    import api.routers.playlists as playlists_mod

    def fake_send_task(name, args=None, **kwargs):
        captured["name"] = name
        captured["args"] = args
        return SimpleNamespace(id="task-3")

    monkeypatch.setattr(playlists_mod.celery_app, "send_task", fake_send_task)

    resp = client.post(f"/playlists/{playlist_id}/enrich", headers=_auth_headers(token))
    assert resp.status_code == 202, resp.text
    assert captured["name"] == "workers.enrich_playlist"
    assert resp.json()["task_id"] == "task-3"