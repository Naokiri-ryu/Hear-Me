from celery.utils.log import get_task_logger

from api.db import SessionLocal
from models.playlist_group import PlaylistGroup
from workers.celery_app import celery_app
from workers.grouping import GROUP_BY_FUNCTIONS, group_tracks

logger = get_task_logger(__name__)


@celery_app.task(bind=True, name="workers.group_playlist", max_retries=3)
def group_playlist(self, user_id: int, playlist_id: int, sort_by: str) -> dict:
    """Group a playlist's tracks into categories (genre/artist/album/decade).

    Pure local computation over stored track metadata (no external API calls),
    idempotent: re-running replaces the stored snapshot for (playlist, sort_by).
    """
    from models.playlist import Playlist
    from models.playlist_track import PlaylistTrack
    from models.track import Track
    from sqlalchemy import delete, select
    from sqlalchemy.exc import OperationalError

    try:
        db = SessionLocal()
        try:
            playlist = db.get(Playlist, playlist_id)
            if playlist is None or playlist.user_id != user_id:
                return {"ok": False, "reason": "not_found", "sort_by": sort_by, "groups": {}}
            if sort_by not in GROUP_BY_FUNCTIONS:
                return {"ok": False, "reason": "unsupported_strategy", "sort_by": sort_by, "groups": {}}

            links = db.scalars(
                select(PlaylistTrack)
                .where(PlaylistTrack.playlist_id == playlist_id)
                .order_by(PlaylistTrack.position, PlaylistTrack.track_id)
            ).all()
            tracks = [db.get(Track, link.track_id) for link in links]
            tracks = [t for t in tracks if t is not None]

            groups = group_tracks(tracks, sort_by)

            db.execute(
                delete(PlaylistGroup).where(
                    PlaylistGroup.playlist_id == playlist_id,
                    PlaylistGroup.sort_by == sort_by,
                )
            )
            db.add(
                PlaylistGroup(
                    playlist_id=playlist_id,
                    sort_by=sort_by,
                    groups=groups,
                    track_count=len(tracks),
                )
            )
            db.commit()
            return {
                "ok": True,
                "playlist_id": playlist_id,
                "sort_by": sort_by,
                "track_count": len(tracks),
                "group_count": len(groups),
                "groups": groups,
            }
        finally:
            db.close()
    except OperationalError as exc:
        logger.warning("group_playlist DB retry (countdown 2**%s): %s", self.request.retries, exc)
        raise self.retry(exc=exc, countdown=2**self.request.retries) from exc