"""Rule-based playlist grouping (auto-sort by category -> ordered track ids).

Genre source is ARTIST metadata (multi-artist tracks union their artists'
genres; a track may therefore appear in several categories). Release decade is
derived from the album release_date. Spotify audio-features/audio-analysis are
permanently deprecated for new apps and are NEVER used here.
"""

from typing import Callable

from models.track import Track

UNKNOWN_CATEGORY = "Unknown"


def _strip(value: str | None) -> str:
    return (value or "").strip()


def _primary_artist(artist: str | None) -> str:
    parts = [p for p in (artist or "").split(",") if p.strip()]
    return parts[0].strip() if parts else ""


def _sort_tracks(tracks: list[Track]) -> list[int]:
    return [
        t.id
        for t in sorted(tracks, key=lambda t: (_strip(t.title).lower(), t.id))
    ]


def _sort_groups(groups: dict[str, list[int]]) -> dict[str, list[int]]:
    return dict(sorted(groups.items(), key=lambda item: item[0].lower()))


def group_by_genre(tracks: list[Track]) -> dict[str, list[int]]:
    buckets: dict[str, list[Track]] = {}
    for track in tracks:
        genres = [g.strip() for g in (track.genres or []) if g and g.strip()]
        for genre in genres or [UNKNOWN_CATEGORY]:
            buckets.setdefault(genre, []).append(track)
    return _sort_groups({key: _sort_tracks(ts) for key, ts in buckets.items()})


def group_by_artist(tracks: list[Track]) -> dict[str, list[int]]:
    buckets: dict[str, list[Track]] = {}
    for track in tracks:
        key = _primary_artist(track.artist) or UNKNOWN_CATEGORY
        buckets.setdefault(key, []).append(track)
    return _sort_groups({key: _sort_tracks(ts) for key, ts in buckets.items()})


def group_by_album(tracks: list[Track]) -> dict[str, list[int]]:
    buckets: dict[str, list[Track]] = {}
    for track in tracks:
        key = _strip(track.album) or UNKNOWN_CATEGORY
        buckets.setdefault(key, []).append(track)
    return _sort_groups({key: _sort_tracks(ts) for key, ts in buckets.items()})


def _decade_key(year: int | None) -> str:
    if year is None:
        return UNKNOWN_CATEGORY
    return f"{(year // 10) * 10}s"


def group_by_decade(tracks: list[Track]) -> dict[str, list[int]]:
    buckets: dict[str, list[Track]] = {}
    for track in tracks:
        buckets.setdefault(_decade_key(track.release_year), []).append(track)
    return _sort_groups({key: _sort_tracks(ts) for key, ts in buckets.items()})


GROUP_BY_FUNCTIONS: dict[str, Callable[[list[Track]], dict[str, list[int]]]] = {
    "genre": group_by_genre,
    "artist": group_by_artist,
    "album": group_by_album,
    "decade": group_by_decade,
}


def group_tracks(tracks: list[Track], sort_by: str) -> dict[str, list[int]]:
    try:
        return GROUP_BY_FUNCTIONS[sort_by](tracks)
    except KeyError as exc:
        raise ValueError(f"Unsupported sort_by: {sort_by}") from exc