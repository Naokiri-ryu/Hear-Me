# AGENTS.md

## Project Overview
Music management app: cross-platform playlist transfer (Spotify, Apple Music, YT Music,
SoundCloud) + auto-sort playlist (genre/artist/album/mood) + music discovery + info
lagu/album/artist.

## Repo State
- Scaffold aktif: `/api` (FastAPI: auth register/login JWT, Spotify OAuth handler,
  Spotify client), `/workers` (Celery: `workers.ping`, `workers.fetch_spotify_playlist`
  idempotent, `workers.sort_playlist` reorder, `workers.group_playlist` auto-sort
  grouping), `/models` (SQLAlchemy), `alembic/` (users, playlists, tracks,
  playlist_tracks, platform_credentials, playlist_groups), `tests/` (pytest, semua
  panggilan API eksternal di-mock), `/frontend`.
- Auto-sort playlist rule-based sudah live: `workers.group_playlist` grouping per
  **genre** (union genre semua artist track, dari endpoint `/artists`), **artist**
  (artist pertama), **album**, dan **decade** (dari `release_date` album), snapshot
  disimpan di tabel `playlist_groups` (map kategori -> list track_id) untuk dashboard.
  Endpoint: `POST /playlists/{id}/group` + `GET /playlists/{id}/groups`.
- Token Spotify disimpan ENCRYPTED (Fernet) di `platform_credentials` — jangan pernah
  menaruh plaintext. Refresh token + rotate otomatis ada di `api/clients/spotify_client.py`
  (refresh-before-expiry, rate-limit dari config, retry exponential backoff).
- Client hanya butuh `SPOTIFY_CLIENT_ID/SECRET` (di `.env`) untuk dipakai live; tanpa itu,
  `/auth/spotify/login` balas 503 dan semua tes jalan via mock.
- Python 3.13, sync SQLAlchemy 2.0 + psycopg2. Setup: `python -m venv .venv`, aktifkan,
  `pip install -r requirements-dev.txt`.

## Tech Stack
- **Backend**: Python, FastAPI
- **Job Queue / Worker**: Celery + Redis (untuk sync playlist async, jangan pernah sync
  secara synchronous di HTTP request)
- **Database**: PostgreSQL
- **Cache**: Redis (OAuth token, hasil query API yang sering diulang, rate-limit counter)
- **Frontend**: Next.js (React) — SSR untuk halaman publik (share playlist), SPA untuk
  dashboard user
- **Mobile (nanti)**: React Native/Expo, share logic dengan web

## Architecture
```
Frontend (Next.js) -> Backend API (FastAPI) -> Job Queue (Celery/Redis) -> Worker(s)
                              |                                              |
                              v                                              v
                          PostgreSQL                            External Music APIs
                              |                          (Spotify, Apple Music, YT Music,
                              v                            SoundCloud, MusicBrainz, Last.fm,
                            Redis Cache                    Genius)
```

- Semua request sync/transfer playlist DAN operasi bervolume besar apa pun (batch fetch
  metadata, sync) WAJIB lewat job queue — tidak boleh panggil API eksternal secara
  sinkron di request handler FastAPI (playlist bisa 1000+ lagu -> timeout / kena rate
  limit block).
- Tiap platform musik punya OAuth flow sendiri. Token per user per platform disimpan
  terenkripsi di tabel `platform_credentials`. Refresh token di-handle otomatis di layer
  client, bukan di worker task.
- Worker harus respect rate limit tiap platform (dari config, jangan hardcode) dan
  implement retry dengan exponential backoff.

## Platform Integrations
- **WAJIB baca** `.opencode/skills/platform-api-integration/SKILL.md` (skill
  `platform-api-integration`) sebelum menambah/mengubah/men-debug integrasi platform
  musik apa pun. Pattern baku: OAuth handler -> token refresh -> API client wrapper ->
  worker task.
- **Spotify**: API resmi, paling stabil untuk `/artists`, `/playlists`, search, dll.
  **PENTING — endpoint `/audio-features`, `/audio-analysis`, dan `/recommendations`
  dideprecate PERMANEN untuk app baru sejak 27 Nov 2024 dan return 403. TIDAK ada
  workaround; jangan pernah memanggilnya atau mengasumsikan danceability/energy/
  valence/tempo tersedia.** Genre untuk auto-sort hanya dari endpoint `/artists`
  (artist-level genres); data "mood"/tonal TIDAK tersedia dari Spotify.
- **Apple Music**: MusicKit API, butuh Apple Developer Program (berbayar), auth pakai
  JWT dari private key.
- **YouTube Music**: TIDAK ada API resmi. Kalau dipakai, pakai library unofficial
  (mis. ytmusicapi) dan isolasi errornya — bisa patah sewaktu-waktu, jangan sampai
  menjatuhkan fitur lain. Beri disclaimer ke user.
- **SoundCloud**: API resmi ada tapi butuh approval khusus, tidak dibuka bebas.
- **MusicBrainz**: metadata musik open-source, gratis (info album/artist).
- **Last.fm**: similar artist, tag-based discovery, statistik.
- **Genius**: lirik & anotasi — jangan reproduksi lirik penuh (hak cipta), metadata boleh.

## Conventions
- Struktur folder: `/api` (FastAPI app; auth & clients di subfolder), `/workers` (Celery
  tasks), `/models` (DB models/schema), `/frontend`.
- Penamaan tabel: snake_case, plural (`users`, `playlists`, `tracks`,
  `platform_mappings`). Token OAuth per user per platform: tabel `platform_credentials`,
  disimpan terenkripsi (bukan di tabel `users`).
- Migration DB pakai Alembic, satu migration per perubahan skema, deskriptif.
- Pattern integrasi platform baru: OAuth handler -> token refresh -> API client wrapper
  -> worker task (detail di skill `platform-api-integration`).

## Commands (dari root repo, use venv python)
- `.venv\Scripts\python -m uvicorn api.main:app --reload` — backend API lokal (Windows)
- `.venv\Scripts\python -m celery -A workers.celery_app worker --loglevel=info` — worker
- `.venv\Scripts\python -m alembic upgrade head` — jalankan migration DB (butuh Postgres)
- `.venv\Scripts\python -m alembic upgrade head --sql` — verifikasi migration tanpa DB
- `.venv\Scripts\python -m pytest -q` — test suite (harus hijau di tiap perubahan backend)
- `npm run dev` (di folder `/frontend`) — jalankan frontend (setelah di-scaffold)

## Testing
- Backend: pytest + TestClient, semua panggilan API eksternal di-mock
  (`tests/test_spotify_client.py`, `test_spotify_oauth.py`).
- Worker: task dijalankan eager mode (`task_always_eager`) dengan `SessionLocal`
  di-monkeypunch ke SQLite in-memory (`tests/test_spotify_task.py`).
- DB test pakai SQLite in-memory (StaticPool), bukan Postgres — jangan ubah ini tanpa
  alasan jelas.