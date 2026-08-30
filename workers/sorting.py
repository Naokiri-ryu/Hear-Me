from typing import Callable

from models.track import Track


def _fallback(value: str | None) -> str:
    return (value or "").strip().lower()


def sort_by_title(track: Track) -> tuple:
    return (_fallback(track.title), track.id)


def sort_by_artist(track: Track) -> tuple:
    return (_fallback(track.artist), _fallback(track.title), track.id)


def sort_by_album(track: Track) -> tuple:
    return (_fallback(track.album), _fallback(track.artist), _fallback(track.title), track.id)


def sort_by_duration(track: Track) -> tuple:
    return (track.duration_ms if track.duration_ms is not None else -1, _fallback(track.title), track.id)


STRATEGY_KEYS: dict[str, Callable[[Track], tuple]] = {
    "title": sort_by_title,
    "artist": sort_by_artist,
    "album": sort_by_album,
    "duration": sort_by_duration,
}


def strategy_key(strategy: str) -> Callable[[Track], tuple]:
    try:
        return STRATEGY_KEYS[strategy]
    except KeyError as exc:  # pragma: no cover - guarded by schema Literal
        raise ValueError(f"Unsupported sort strategy: {strategy}") from exc


def order_tracks(tracks: list[Track], strategy: str) -> list[Track]:
    key = strategy_key(strategy)
    return sorted(tracks, key=key)