import time

import httpx

from api.clients.musicbrainz_client import MusicBrainzClient, MusicBrainzClientError

RECORDING_PAYLOAD = {
    "count": 1,
    "recordings": [
        {
            "id": "mb-1",
            "title": "Song One",
            "artist-credit": [{"name": "Artist A"}],
            "releases": [{"title": "Album X"}],
            "length": 180000,
            "isrcs": ["USABC1234567"],
        }
    ],
}


def test_search_recording_parses_fields(monkeypatch):
    resp = httpx.Response(200, json=RECORDING_PAYLOAD)
    monkeypatch.setattr(httpx.Client, "get", lambda self, path, params: resp)
    monkeypatch.setattr(time, "sleep", lambda s: None)

    with MusicBrainzClient(interval=0.0) as client:
        hit = client.search_recording("Song One", "Artist A")

    assert hit is not None
    assert hit.mbid == "mb-1"
    assert hit.title == "Song One"
    assert hit.artist == "Artist A"
    assert hit.album == "Album X"
    assert hit.length_ms == 180000
    assert hit.isrc == "USABC1234567"


def test_search_recording_no_hits(monkeypatch):
    resp = httpx.Response(200, json={"count": 0, "recordings": []})
    monkeypatch.setattr(httpx.Client, "get", lambda self, path, params: resp)
    monkeypatch.setattr(time, "sleep", lambda s: None)

    with MusicBrainzClient(interval=0.0) as client:
        assert client.search_recording("Totally Unknown Song") is None


def test_retries_on_503_then_succeeds(monkeypatch):
    responses = iter(
        [
            httpx.Response(503, text="rate limited"),
            httpx.Response(200, json=RECORDING_PAYLOAD),
        ]
    )
    monkeypatch.setattr(httpx.Client, "get", lambda self, path, params: next(responses))
    monkeypatch.setattr(time, "sleep", lambda s: None)

    with MusicBrainzClient(interval=0.0) as client:
        hit = client.search_recording("Song One")
    assert hit is not None


def test_raises_on_persistent_503(monkeypatch):
    resp = httpx.Response(503, text="rate limited")
    monkeypatch.setattr(httpx.Client, "get", lambda self, path, params: resp)
    monkeypatch.setattr(time, "sleep", lambda s: None)

    with MusicBrainzClient(interval=0.0) as client:
        import pytest

        with pytest.raises(MusicBrainzClientError):
            client.search_recording("Song One")


def test_raises_on_non_200(monkeypatch):
    resp = httpx.Response(403, text="forbidden")
    monkeypatch.setattr(httpx.Client, "get", lambda self, path, params: resp)

    with MusicBrainzClient(interval=0.0) as client:
        import pytest

        with pytest.raises(MusicBrainzClientError):
            client.search_recording("Song One")