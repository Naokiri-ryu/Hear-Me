"""auto-sort grouping: track genre/release_year + playlist_groups

Revision ID: 0002_playlist_grouping
Revises: 0001_initial
Create Date: 2026-08-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_playlist_grouping"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # genre/release metadata used by rule-based auto-sort (genre/decade).
    # NOTE: stored from ARTIST metadata + album release_date — audio-features
    # are permanently deprecated for new Spotify apps (403, do not use).
    op.add_column("tracks", sa.Column("genres", sa.JSON(), nullable=True))
    op.add_column("tracks", sa.Column("release_year", sa.Integer(), nullable=True))
    op.create_index("ix_tracks_release_year", "tracks", ["release_year"])

    op.create_table(
        "playlist_groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("playlist_id", sa.Integer(), nullable=False),
        sa.Column("sort_by", sa.String(length=50), nullable=False),
        sa.Column("groups", sa.JSON(), nullable=False),
        sa.Column("track_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["playlist_id"], ["playlists.id"], name="fk_playlist_groups_playlist_id_playlists"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_playlist_groups"),
    )
    op.create_index("ix_playlist_groups_playlist_id", "playlist_groups", ["playlist_id"])


def downgrade() -> None:
    op.drop_index("ix_playlist_groups_playlist_id", table_name="playlist_groups")
    op.drop_table("playlist_groups")
    op.drop_index("ix_tracks_release_year", table_name="tracks")
    op.drop_column("tracks", "release_year")
    op.drop_column("tracks", "genres")