from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.playlist import Playlist


class PlaylistGroup(Base):
    """Snapshot of a rule-based grouping run (category -> ordered track ids).

    One row per (playlist_id, sort_by) — re-running replaces the snapshot.
    Stored so the dashboard can render the grouping without recomputing.
    """

    __tablename__ = "playlist_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    playlist_id: Mapped[int] = mapped_column(ForeignKey("playlists.id"), index=True)
    sort_by: Mapped[str] = mapped_column(String(50))
    # map: category key -> list of track ids (in display order within category)
    groups: Mapped[dict] = mapped_column(JSON)
    track_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    playlist: Mapped["Playlist"] = relationship(back_populates="groups")