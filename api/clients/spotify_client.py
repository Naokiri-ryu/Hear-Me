import time
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from api.config import settings
from api.security import decrypt_token, encrypt_token
from models.platform_credential import PlatformCredential

_REFRESH_TOLERANCE_SECONDS = 60
_MAX_RETRIES = 3
_TIMEOUT_SECONDS = 30
_PAGE_LIMIT = 50
_MAX_PAGES = 50
_ARTISTS_PER_REQUEST = 50


class SpotifyClientError(Exception):
    pass


def _utc_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class SpotifyClient:
    def __init__(self, credential: PlatformCredential, db: Session) -> None:
        self._cred = credential
        self._db = db
        self._token: str | None = None
        # rate-limit throttle per config, not hardcoded
        self._min_interval = 60.0 / max(settings.SPOTIFY_MAX_REQUESTS_PER_MINUTE, 1)
        self._last_request_at = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)

    def _request_token(self, payload: dict) -> dict:
        resp = httpx.post(
            f"{settings.SPOTIFY_ACCOUNTS_BASE}/api/token",
            data={
                "client_id": settings.SPOTIFY_CLIENT_ID,
                "client_secret": settings.SPOTIFY_CLIENT_SECRET,
                **payload,
            },
            timeout=_TIMEOUT_SECONDS,
        )
        if resp.status_code != 200:
            raise SpotifyClientError(f"token request failed: HTTP {resp.status_code}")
        return resp.json()

    def _refresh(self) -> str:
        if not self._cred.refresh_token:
            raise SpotifyClientError("access token expired and no refresh token stored")
        body = self._request_token(
            {
                "grant_type": "refresh_token",
                "refresh_token": decrypt_token(self._cred.refresh_token),
            }
        )
        new_access = body["access_token"]
        new_refresh = body.get("refresh_token") or decrypt_token(self._cred.refresh_token)
        now = datetime.now(timezone.utc)
        self._cred.access_token = encrypt_token(new_access)
        self._cred.refresh_token = encrypt_token(new_refresh)
        self._cred.expires_at = now + timedelta(seconds=body.get("expires_in", 3600))
        self._db.commit()
        return new_access

    def _get_access_token(self) -> str:
        now = datetime.now(timezone.utc)
        expires_at = _utc_aware(self._cred.expires_at) if self._cred.expires_at else None
        if (
            self._token
            and expires_at
            and expires_at > now + timedelta(seconds=_REFRESH_TOLERANCE_SECONDS)
        ):
            return self._token
        if expires_at and expires_at > now + timedelta(seconds=_REFRESH_TOLERANCE_SECONDS):
            self._token = decrypt_token(self._cred.access_token)
            return self._token
        # stale or absent -> refresh BEFORE calling main endpoint (skill rule)
        self._token = self._refresh()
        return self._token

    def _request(self, method: str, path: str, params: dict | None = None) -> dict:
        attempts = 0
        while True:
            attempts += 1
            self._throttle()
            token = self._get_access_token()
            resp = httpx.request(
                method,
                f"{settings.SPOTIFY_API_BASE}{path}",
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                timeout=_TIMEOUT_SECONDS,
            )
            self._last_request_at = time.monotonic()

            if resp.status_code == 401 and attempts == 1:
                self._token = self._refresh()
                continue
            if resp.status_code in (429, 500, 502, 503) and attempts <= _MAX_RETRIES:
                retry_after = resp.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else min(2**attempts, 8)
                time.sleep(delay)
                continue
            if resp.status_code != 200:
                raise SpotifyClientError(f"Spotify API error: HTTP {resp.status_code}: {resp.text[:200]}")
            return resp.json()

    def get_playlist(self, playlist_id: str) -> dict:
        items: list[dict] = []
        offset = 0
        while offset // _PAGE_LIMIT < _MAX_PAGES:
            page = self._request(
                "GET",
                f"/playlists/{playlist_id}",
                {"limit": _PAGE_LIMIT, "offset": offset, "market": "from_token"},
            )
            if offset == 0:
                meta = {
                    "id": page.get("id"),
                    "name": page.get("name"),
                    "description": page.get("description"),
                    "owner": (page.get("owner") or {}).get("display_name"),
                }
            tracks = page.get("tracks", {})
            for entry in tracks.get("items", []):
                track = entry.get("track")
                if track is None:
                    continue  # unavailable episode/track
                artists = track.get("artists", [])
                artist_names = ", ".join(a.get("name", "") for a in artists)
                items.append(
                    {
                        "track_id": track.get("id"),
                        "title": track.get("name"),
                        "artist": artist_names,
                        # genre metadata comes from artist data -> /artists
                        "artist_ids": [a.get("id") for a in artists if a.get("id")],
                        "album": (track.get("album") or {}).get("name"),
                        "release_date": (track.get("album") or {}).get("release_date"),
                        "duration_ms": track.get("duration_ms"),
                        "isrc": (track.get("external_ids") or {}).get("isrc"),
                    }
                )
            offset += _PAGE_LIMIT
            if len(tracks.get("items", [])) < _PAGE_LIMIT:
                break
        return {**meta, "tracks": items}

    def get_artists(self, artist_ids: list[str]) -> dict[str, list[str]]:
        """Map artist id -> list of genre strings (rule-based genre auto-sort).

        Uses the /artists endpoint (max 50 ids per request). Artist genres are the
        ONLY supported genre source: /audio-features & /audio-analysis are
        permanently deprecated for new apps (403), never call them.
        """
        genres_by_artist: dict[str, list[str]] = {}
        unique_ids = list(dict.fromkeys(i for i in artist_ids if i))
        for i in range(0, len(unique_ids), _ARTISTS_PER_REQUEST):
            chunk = unique_ids[i : i + _ARTISTS_PER_REQUEST]
            resp = self._request("GET", "/artists", {"ids": ",".join(chunk)})
            for artist in resp.get("artists", []):
                if artist is None:
                    continue
                genres = [g for g in artist.get("genres", []) if g]
                genres_by_artist[artist.get("id")] = genres
        return genres_by_artist