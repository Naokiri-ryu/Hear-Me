from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from api.db import get_db
from api.dependencies import get_current_user
from api.schemas.playlist import (
    PlaylistCreate,
    PlaylistGroupOut,
    PlaylistGroupRequest,
    PlaylistOut,
    PlaylistSortRequest,
    PlaylistSummary,
    TaskAccepted,
    playlist_group_to_out,
    playlist_to_out,
    playlist_to_summary,
)
from models.playlist import Playlist
from models.playlist_group import PlaylistGroup
from models.playlist_track import PlaylistTrack
from models.user import User
from workers.celery_app import celery_app

router = APIRouter(prefix="/playlists", tags=["playlists"])


def _get_owned_playlist(db: Session, user_id: int, playlist_id: int) -> Playlist:
    playlist = db.scalar(
        select(Playlist)
        .options(
            selectinload(Playlist.tracks).selectinload(PlaylistTrack.track)
        )
        .where(Playlist.id == playlist_id)
    )
    if playlist is None or playlist.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")
    return playlist


@router.get("", response_model=list[PlaylistSummary])
def list_playlists(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PlaylistSummary]:
    rows = db.execute(
        select(Playlist, func.count(PlaylistTrack.id))
        .outerjoin(PlaylistTrack, PlaylistTrack.playlist_id == Playlist.id)
        .where(Playlist.user_id == current_user.id)
        .group_by(Playlist.id)
        .order_by(Playlist.created_at.desc(), Playlist.id.desc())
    ).all()
    return [playlist_to_summary(playlist, count) for playlist, count in rows]


@router.post("", response_model=PlaylistOut, status_code=status.HTTP_201_CREATED)
def create_playlist(
    payload: PlaylistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Playlist:
    playlist = Playlist(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
    )
    db.add(playlist)
    db.commit()
    db.refresh(playlist)
    return _get_owned_playlist(db, current_user.id, playlist.id)


@router.get("/{playlist_id}", response_model=PlaylistOut)
def get_playlist(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Playlist:
    playlist = _get_owned_playlist(db, current_user.id, playlist_id)
    # ensure deterministic track order
    playlist.tracks.sort(key=lambda link: (link.position, link.track_id))
    return playlist


@router.delete("/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_playlist(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    playlist = db.scalar(select(Playlist).where(Playlist.id == playlist_id))
    if playlist is None or playlist.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")
    db.execute(delete(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist_id))
    db.delete(playlist)
    db.commit()


@router.post("/{playlist_id}/sync", response_model=TaskAccepted, status_code=status.HTTP_202_ACCEPTED)
def sync_playlist(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskAccepted:
    playlist = _get_owned_playlist(db, current_user.id, playlist_id)
    if not playlist.source_platform or not playlist.source_playlist_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Playlist has no remote source; create it via a platform sync first",
        )
    if playlist.source_platform != "spotify":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sync for platform '{playlist.source_platform}' not implemented yet",
        )
    # rule (AGENTS.md): bulk external ops go through the job queue, never sync
    task = celery_app.send_task(
        "workers.fetch_spotify_playlist",
        args=[current_user.id, playlist.source_playlist_id],
    )
    return TaskAccepted(task_id=task.id)


@router.post("/{playlist_id}/sort", response_model=TaskAccepted, status_code=status.HTTP_202_ACCEPTED)
def sort_playlist(
    playlist_id: int,
    payload: PlaylistSortRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskAccepted:
    _get_owned_playlist(db, current_user.id, playlist_id)
    task = celery_app.send_task(
        "workers.sort_playlist",
        args=[current_user.id, playlist_id, payload.strategy],
    )
    return TaskAccepted(task_id=task.id)


@router.post("/{playlist_id}/enrich", response_model=TaskAccepted, status_code=status.HTTP_202_ACCEPTED)
def enrich_playlist(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskAccepted:
    _get_owned_playlist(db, current_user.id, playlist_id)
    task = celery_app.send_task(
        "workers.enrich_playlist",
        args=[current_user.id, playlist_id],
    )
    return TaskAccepted(task_id=task.id)


@router.post("/{playlist_id}/group", response_model=TaskAccepted, status_code=status.HTTP_202_ACCEPTED)
def group_playlist(
    playlist_id: int,
    payload: PlaylistGroupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskAccepted:
    """Queue a rule-based grouping run (genre/artist/album/decade)."""
    _get_owned_playlist(db, current_user.id, playlist_id)
    task = celery_app.send_task(
        "workers.group_playlist",
        args=[current_user.id, playlist_id, payload.sort_by],
    )
    return TaskAccepted(task_id=task.id)


@router.get("/{playlist_id}/groups", response_model=list[PlaylistGroupOut])
def list_playlist_groups(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PlaylistGroupOut]:
    """Latest stored grouping snapshots (for the dashboard), newest first."""
    _get_owned_playlist(db, current_user.id, playlist_id)
    rows = db.scalars(
        select(PlaylistGroup)
        .where(PlaylistGroup.playlist_id == playlist_id)
        .order_by(PlaylistGroup.created_at.desc(), PlaylistGroup.id.desc())
    ).all()
    return [playlist_group_to_out(g) for g in rows]