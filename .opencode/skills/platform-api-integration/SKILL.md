---
name: platform-api-integration
description: Use this skill whenever adding, modifying, or debugging an integration with an external music platform API (Spotify, Apple Music, YT Music, SoundCloud, MusicBrainz, Last.fm, Genius) in this project — including OAuth flows, token refresh, API client wrappers, and worker tasks that call these platforms.
---

# Platform API Integration Pattern

Setiap integrasi platform musik baru di project ini WAJIB mengikuti struktur yang sama,
supaya konsisten dan gampang di-maintain.

## Alur wajib: OAuth -> Token Refresh -> API Client -> Worker Task

### 1. OAuth handler
- Lokasi: `/api/auth/<platform>.py`
- Simpan `access_token`, `refresh_token`, `expires_at` per user per platform di tabel
  `platform_credentials` (bukan di tabel `users` langsung).
- Token disimpan terenkripsi (jangan plaintext di DB).

### 2. Token refresh
- Cek `expires_at` sebelum tiap panggilan API. Kalau sudah/hampir expired, refresh
  dulu SEBELUM memanggil endpoint utama — jangan retry-after-fail sebagai strategi utama.
- Refresh logic ditaruh di layer client (`/api/clients/<platform>_client.py`), bukan
  diulang-ulang di tiap worker task.

### 3. API client wrapper
- Satu file per platform: `/api/clients/<platform>_client.py`.
- Wrapper bertanggung jawab atas: auth header, rate-limit handling (baca dari config,
  jangan hardcode), retry dengan exponential backoff, parsing response ke schema
  internal (jangan expose raw response platform ke layer atas).
- Kalau platform tidak resmi/unofficial (YT Music, SoundCloud) — isolasi errornya:
  jangan biarkan exception dari client ini menjatuhkan proses lain. Tangkap dan log
  dengan jelas bahwa ini unofficial API yang rawan berubah.

### 4. Worker task
- Semua pemanggilan client di atas untuk operasi bervolume besar (fetch/sync
  playlist) HARUS lewat Celery task, tidak boleh dipanggil langsung dari route FastAPI.
- Task harus idempotent (aman dijalankan ulang kalau retry).

## Checklist sebelum menganggap integrasi platform baru "selesai"
- [ ] Token disimpan terenkripsi, bukan plaintext
- [ ] Ada refresh-token flow otomatis, teruji untuk kasus token expired
- [ ] Rate limit platform ada di config, bukan hardcoded
- [ ] Client wrapper punya retry + backoff
- [ ] Kalau unofficial API: error diisolasi, tidak menjatuhkan fitur lain
- [ ] Response dari platform di-parse ke schema internal (tidak expose raw response)
- [ ] Ada test dengan mock API (tidak hit API asli di test suite)

## Status API per platform (update kalau berubah)
- Spotify: resmi, stabil untuk `/artists`, `/playlists`, search, dll. **Endpoints
  `/audio-features`, `/audio-analysis`, dan `/recommendations` DIPRECAT PERMANEN untuk
  app baru sejak 27 Nov 2024 dan return 403. Tidak ada workaround — jangan pernah
  memanggilnya, jangan pernah mengasumsikan data danceability/energy/valence/tempo
  tersedia, dan jangan rebuild fitur yang bergantung pada data itu.** Satu-satunya
  sumber genre yang sah adalah `/artists` (artist-level genres); data mood/tonal
  TIDAK tersedia dari Spotify.
- Apple Music: resmi (MusicKit), butuh Apple Developer Program + JWT dari private key.
- YT Music: TIDAK resmi (mis. ytmusicapi) — rawan patah, isolasi errornya.
- SoundCloud: resmi tapi butuh approval khusus, akses terbatas.
- MusicBrainz / Last.fm / Genius: dipakai untuk metadata/discovery/lirik, bukan untuk
  transfer playlist.
