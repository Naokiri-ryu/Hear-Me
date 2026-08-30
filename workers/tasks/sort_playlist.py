from celery.utils.log import get_task_logger

from api.db import SessionLocal
from workers.celery_app import celery_app
from workers.sorting import order_tracks

logger = get_task_logger(__name__)


@celery_app.task(bind=True, name="workers.sort_playlist", max_retries=3)
def sort_playlist(self, user_id: int, playlist_id: int, strategy: str) -> dict:
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
                return {"ok": False, "reason": "not_found", "reordered": 0}
            if strategy not in ("title", "artist", "album", "duration"):
                return {"ok": False, "reason": "unsupported_strategy", "reordered": 0}

            links = db.scalars(
                select(PlaylistTrack)
                .where(PlaylistTrack.playlist_id == playlist_id)
                .order_by(PlaylistTrack.position)
            ).all()

            pairs = [(link, db.get(Track, link.track_id)) for link in links]
            pairs = [p for p in pairs if p[1] is not None]

            ordered = order_tracks([track for _, track in pairs], strategy)
            pos_by_track_id = {track.id: i for i, track in enumerate(ordered)}
            reordered = 0
            for link, _ in pairs:
                new_pos = pos_by_track_id[link.track_id]
                if link.position != new_pos:
                    link.position = new_pos
                    reordered += 1
            db.commit()
            return {"ok": True, "playlist_id": playlist_id, "strategy": strategy, "reordered": reordered}
        finally:
            db.close()
    except OperationalError as exc:
        logger.warning("sort_playlist DB retry (countdown 2**%s): %s", self.request.retries, exc)
        raise self.retry(exc=exc, countdown=2**self.request.retries) from exc