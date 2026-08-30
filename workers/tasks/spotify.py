from sqlalchemy import delete, select

from api.clients.spotify_client import SpotifyClient, SpotifyClientError
from api.db import SessionLocal
from models.playlist import Playlist
from models.playlist_track import PlaylistTrack
from models.platform_credential import PlatformCredential
from models.track import Track
from workers.celery_app import celery_app

_PLATFORM = "spotify"


def _find_track(db, entry: dict) -> Track | None:
    if entry.get("isrc"):
        track = db.scalar(select(Track).where(Track.isrc == entry["isrc"]))
        if track is not None:
            return track
    return db.scalar(
        select(Track).where(
            Track.title == entry["title"],
            Track.artist == entry["artist"],
        )
    )


@celery_app.task(name="workers.fetch_spotify_playlist", bind=True, max_retries=2)
def fetch_spotify_playlist(
    self,
    user_id: int,
    spotify_playlist_id: str,
) -> dict:
    db = SessionLocal()
    credential = db.scalar(
        select(PlatformCredential).where(
            PlatformCredential.user_id == user_id,
            PlatformCredential.platform == _PLATFORM,
        )
    )
    if credential is None:
        db.close()
        raise SpotifyClientError("no Spotify credential for user")

    try:
        data = SpotifyClient(credential, db).get_playlist(spotify_playlist_id)

        playlist = db.scalar(
            select(Playlist).where(
                Playlist.user_id == user_id,
                Playlist.source_platform == _PLATFORM,
                Playlist.source_playlist_id == spotify_playlist_id,
            )
        )
        if playlist is None:
            playlist = Playlist(
                user_id=user_id,
                source_platform=_PLATFORM,
                source_playlist_id=spotify_playlist_id,
            )
            db.add(playlist)
        playlist.name = data["name"] or "Untitled"
        playlist.description = data.get("description")
        db.flush()

        db.execute(
            delete(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist.id)
        )
        for position, entry in enumerate(data["tracks"]):
            track = _find_track(db, entry)
            if track is None:
                track = Track(
                    title=entry["title"] or "Unknown",
                    artist=entry.get("artist"),
                    album=entry.get("album"),
                    duration_ms=entry.get("duration_ms"),
                    isrc=entry.get("isrc"),
                )
                db.add(track)
                db.flush()
            db.add(PlaylistTrack(playlist_id=playlist.id, track_id=track.id, position=position))

        db.commit()
        return {
            "user_id": user_id,
            "playlist_id": playlist.id,
            "name": data["name"],
            "tracks": len(data["tracks"]),
        }
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=2**self.request.retries) from exc
    finally:
        db.close()