from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from models.playlist import Playlist
from models.playlist_group import PlaylistGroup
from models.playlist_track import PlaylistTrack

SortStrategy = Literal["title", "artist", "album", "duration"]
SortBy = Literal["genre", "artist", "album", "decade"]


class TrackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    artist: str | None
    album: str | None
    duration_ms: int | None
    isrc: str | None


class PlaylistTrackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    position: int
    track: TrackOut


class PlaylistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class PlaylistSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    source_platform: str | None
    source_playlist_id: str | None
    track_count: int


class PlaylistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    source_platform: str | None
    source_playlist_id: str | None
    created_at: datetime
    updated_at: datetime
    tracks: list[PlaylistTrackOut]


class PlaylistSortRequest(BaseModel):
    strategy: SortStrategy


class PlaylistGroupRequest(BaseModel):
    sort_by: SortBy


class PlaylistGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    playlist_id: int
    sort_by: str
    groups: dict[str, list[int]]
    track_count: int
    group_count: int
    created_at: datetime


class TaskAccepted(BaseModel):
    task_id: str
    status: str = "queued"


def playlist_to_summary(playlist: Playlist, track_count: int = 0) -> PlaylistSummary:
    return PlaylistSummary(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        source_platform=playlist.source_platform,
        source_playlist_id=playlist.source_playlist_id,
        track_count=track_count,
    )


def playlist_to_out(playlist: Playlist) -> PlaylistOut:
    return PlaylistOut.model_validate(playlist)


def playlist_group_to_out(group: PlaylistGroup) -> PlaylistGroupOut:
    return PlaylistGroupOut(
        id=group.id,
        playlist_id=group.playlist_id,
        sort_by=group.sort_by,
        groups=group.groups or {},
        track_count=group.track_count,
        group_count=len(group.groups or {}),
        created_at=group.created_at,
    )