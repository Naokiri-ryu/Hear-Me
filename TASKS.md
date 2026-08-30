# TASKS.md — Sesi Otonom OpenCode

Log backlog untuk sesi kerja mandiri (~1 jam). Update status tiap item selesai,
supaya tetap bisa dilacak setelah sesi chat dengan OpenCode berakhir.

## Urutan prioritas

1. [x] **Perbaiki SECRET_KEY / TOKEN_ENCRYPTION_KEY**
   - Selesai di commit 5d5f22b: TOKEN_ENCRYPTION_KEY terpisah di api/config.py,
     api/security.py pakai _fernet_key(source) dari TOKEN_ENCRYPTION_KEY, ENV gate
     production (placeholder/<32 byte → gagal start), .env.example, 5 test baru
     (roundtrip, produksi), AGENTS.md gotchas. 70 passed. .env lokal sudah ada
     TOKEN_ENCRYPTION_KEY acak.

2. [x] **Auth shell (indikator login + /me)**
   - Selesai di commit 9ad4bd4: lib/api.ts (clearToken/decodeToken/getMe),
     lib/use-auth.ts (useAuth + AUTH_EVENT), components/auth-nav-actions.tsx,
     app/me/page.tsx route-guard, login-form redirect /me. live: /, /login,
     /register, /me semua 200, login proxy 200.

3. [x] **Dashboard frontend**
   - Selesai: route /dashboard (client, auth-guard), daftar playlist dari
     GET /api/playlists via frontend/lib/api.ts (getPlaylists, getPlaylistGroups,
     runGrouping; request() kini auto-attach Bearer + handle 204), kartu expandable
     menampilkan snapshot grouping (tab per sort_by, chip kategori + count + bar
     netral), kontrol Run auto-sort dengan error handling (Redis down → pesan).
     Link Dashboard di navbar saat login. Desain ikuti design-system (a11y, satu
     accent, serif hanya headline, 10px radius). Lint & build bersih, /dashboard
     live 200. Playlist demo id=2 "Discover Weekly (demo)" dibuat utk verifikasi.

## Kalau backlog di atas selesai sebelum waktu habis

Lanjutkan sesuai arah AGENTS.md → section "Competitive Positioning": prioritaskan
fitur yang memperdalam auto-sort/dashboard (diferensiator utama Hear-Me) sebelum
menambah platform baru (Apple Music/YT Music). Pecah kerjaan jadi unit kecil yang
masing-masing bisa di-commit utuh — jangan mulai sesuatu yang tidak mungkin selesai
rapi sebelum waktu habis.

## Diketahui / batasan environment

- Redis tidak jalan di lokal — endpoint yang dispatch Celery task (/sync, /sort,
  /enrich, /group) akan 500 tanpa Redis service aktif. Ini bukan bug, sudah dari awal.
