from __future__ import annotations

import time
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from api.config import settings

API_USER_AGENT = "HearMe/0.1 (metadata enrichment; contact: hearme-app@example.com)"


@dataclass
class RecordingHit:
    mbid: str
    title: str
    artist: str | None
    album: str | None
    length_ms: int | None
    isrc: str | None


class MusicBrainzClientError(Exception):
    pass


class MusicBrainzClient:
    """Official open metadata service (https://musicbrainz.org/doc/MusicBrainz_API).

    Etiquette enforced: mandatory User-Agent, >=1 request/second, backoff on 503.
    """

    def __init__(self, base_url: str | None = None, interval: float | None = None) -> None:
        self.base_url = base_url or settings.MUSICBRAINZ_API_BASE
        self.interval = interval or settings.MUSICBRAINZ_REQUEST_INTERVAL_SECONDS
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"User-Agent": API_USER_AGENT, "Accept": "application/json"},
            timeout=httpx.Timeout(15.0),
        )
        self._last_request_at = 0.0
        self._max_retries = 3

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "MusicBrainzClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        wait = self.interval - elapsed
        if wait > 0:
            time.sleep(wait)
        self._last_request_at = time.monotonic()

    def _get(self, path: str, params: dict) -> dict:
        for attempt in range(self._max_retries + 1):
            self._throttle()
            try:
                resp = self._client.get(path, params=params)
            except httpx.HTTPError as exc:
                if attempt < self._max_retries:
                    time.sleep(2**attempt)
                    continue
                raise MusicBrainzClientError(str(exc)) from exc
            if resp.status_code == 503 and attempt < self._max_retries:
                time.sleep(2**attempt)
                continue
            if resp.status_code != 200:
                raise MusicBrainzClientError(f"MusicBrainz returned {resp.status_code}")
            try:
                return resp.json()
            except ValueError as exc:
                raise MusicBrainzClientError("MusicBrainz returned non-JSON payload") from exc
        raise MusicBrainzClientError("MusicBrainz unavailable after retries")

    def search_recording(self, title: str, artist: str | None = None) -> RecordingHit | None:
        query_parts = [f'recording:"{title}"']
        if artist:
            query_parts.append(f'AND artist:"{artist}"')
        query = " ".join(query_parts)
        data = self._get("/recording", {"query": query, "fmt": "json", "limit": 3})
        recordings = data.get("recordings") or []
        if not recordings:
            return None
        best = recordings[0]
        artist_credit = best.get("artist-credit") or []
        artist_name: str | None = None
        for credit in artist_credit:
            artist_name = credit.get("name") or artist_name
        releases = best.get("releases") or []
        album_name: str | None = releases[0].get("title") if releases else None
        isrcs = best.get("isrcs") or []
        return RecordingHit(
            mbid=best.get("id"),
            title=best.get("title"),
            artist=artist_name,
            album=album_name,
            length_ms=best.get("length"),
            isrc=(isrcs[0] if isrcs else None),
        )