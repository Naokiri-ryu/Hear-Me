from celery.utils.log import get_task_logger

from api.db import SessionLocal
from workers.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(bind=True, name="workers.enrich_playlist", max_retries=3)
def enrich_playlist(self, user_id: int, playlist_id: int, limit: int | None = None) -> dict:
    """Fill missing album/isrc/duration metadata from MusicBrainz (batch, via queue)."""
    from api.clients.musicbrainz_client import MusicBrainzClient, MusicBrainzClientError
    from models.playlist import Playlist
    from models.playlist_track import PlaylistTrack
    from models.track import Track
    from sqlalchemy import select
    from sqlalchemy.exc import OperationalError

    try:
        db = SessionLocal()
        try:
            playlist = db.get(Playlist, playlist_id)
            if playlist is None or playlist.user_id != user_id:
                return {"ok": False, "reason": "not_found", "updated": 0}

            links = db.scalars(
                select(PlaylistTrack)
                .where(PlaylistTrack.playlist_id == playlist_id)
                .order_by(PlaylistTrack.position)
            ).all()
            tracks: list[Track] = []
            for link in links:
                track = db.get(Track, link.track_id)
                if track is not None and track.title:
                    tracks.append(track)
            if limit is not None:
                tracks = tracks[:limit]

            updated = 0
            enriched = 0
            touched: list[tuple[Track, RecordingHitLike]] = []
            with MusicBrainzClient() as client:
                try:
                    for track in tracks:
                        if track.isrc and track.album:
                            continue
                        hit = client.search_recording(track.title, track.artist)
                        if hit is None:
                            continue
                        enriched += 1
                        touched.append((track, hit))
                except MusicBrainzClientError as exc:
                    logger.warning("enrich_playlist aborted mid-way: %s (%d updated)", exc, updated)
                    raise

            for track, hit in touched:
                if not track.album and hit.album is not None:
                    track.album = hit.album
                if not track.isrc and hit.isrc:
                    track.isrc = hit.isrc
                if hit.length_ms is not None and not track.duration_ms:
                    track.duration_ms = hit.length_ms
                updated += 1
            db.commit()
            return {
                "ok": True,
                "playlist_id": playlist_id,
                "searched": len(tracks),
                "enriched": enriched,
                "updated": updated,
            }
        finally:
            db.close()
    except OperationalError as exc:
        logger.warning("enrich_playlist DB retry (countdown 2**%s): %s", self.request.retries, exc)
        raise self.retry(exc=exc, countdown=2**self.request.retries) from exc