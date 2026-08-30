from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.playlist_track import PlaylistTrack


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    artist: Mapped[str] = mapped_column(String(500), nullable=True)
    album: Mapped[str] = mapped_column(String(500), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    isrc: Mapped[str] = mapped_column(String(12), nullable=True, index=True)
    # Artist-level genres (union across the track's artists). Source: Spotify
    # /artists endpoint. NOTE: audio-features/audio-analysis are PERMANENTLY
    # deprecated for new apps (403 since 2024-11-27) — genres come from artist
    # metadata, never from audio features.
    genres: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    # Release year parsed from the album release_date (e.g. "2024-05-20" -> 2024).
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    playlist_links: Mapped[list["PlaylistTrack"]] = relationship(back_populates="track")