# AGENTS.md

## Project Overview
Music management app: cross-platform playlist transfer (Spotify, Apple Music, YT Music,
SoundCloud) + auto-sort playlist (genre/artist/album/mood) + music discovery + info
lagu/album/artist.

## Repo State
- Scaffold dasar sudah ada: `/api` (FastAPI), `/workers` (Celery), `/models` (SQLAlchemy),
  `alembic/` (migration awal: users, playlists, tracks, playlist_tracks,
  platform_credentials), `/frontend` (placeholder saja).
- Belum ada implementasi platform API / OAuth / Celery task konkret — itu step berikutnya.
- Python 3.13, sync SQLAlchemy 2.0 + psycopg2. Run via venv: `python -m venv .venv`,
  aktifkan, lalu `pip install -r requirements.txt`.

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
- **Spotify**: API resmi, paling stabil. Audio features endpoint
  (danceability/energy/valence) sempat dideprecate untuk app baru — cek ketersediaan
  sebelum dipakai untuk fitur auto-sort.
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
- `npm run dev` (di folder `/frontend`) — jalankan frontend (setelah di-scaffold)

## Testing
- Backend: pytest, mock semua panggilan API eksternal (jangan hit API asli di test)
- Worker: test task Celery secara eager mode
- Frontend: (isi sesuai testing framework yang dipilih nanti — belum ditentukan)