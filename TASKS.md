# TASKS.md — Sesi Otonom OpenCode

Log backlog untuk sesi kerja mandiri (~1 jam). Update status tiap item selesai,
supaya tetap bisa dilacak setelah sesi chat dengan OpenCode berakhir.

## Urutan prioritas

1. [ ] **Perbaiki SECRET_KEY / TOKEN_ENCRYPTION_KEY**
   - Pisahkan SECRET_KEY (JWT signing) dan TOKEN_ENCRYPTION_KEY (Fernet di
     api/security.py) — jangan derive dari key yang sama
   - Tambahkan field ENV di api/config.py (development/production)
   - Validasi startup: kalau ENV=production dan salah satu key masih default
     ("change-me") atau di bawah 32 byte → app harus gagal start, bukan warning
   - Update .env.example dengan instruksi generate utk masing-masing key
   - Update test terkait supaya tidak lagi trigger InsecureKeyLengthWarning
   - Update AGENTS.md gotchas: catat kedua key terpisah dan wajib >=32 byte di prod

2. [ ] **Auth shell (indikator login + /me)**
   - Backlog dari sesi sebelumnya, belum dikerjakan

3. [ ] **Dashboard frontend**
   - Tampilkan playlist Spotify user (dari endpoint yang sudah ada)
   - Tampilkan hasil grouping dari GET /playlists/{id}/groups
   - Ikuti skill design-system ("Midnight Editorial")

## Kalau backlog di atas selesai sebelum waktu habis

Lanjutkan sesuai arah AGENTS.md → section "Competitive Positioning": prioritaskan
fitur yang memperdalam auto-sort/dashboard (diferensiator utama Hear-Me) sebelum
menambah platform baru (Apple Music/YT Music). Pecah kerjaan jadi unit kecil yang
masing-masing bisa di-commit utuh — jangan mulai sesuatu yang tidak mungkin selesai
rapi sebelum waktu habis.

## Diketahui / batasan environment

- Redis tidak jalan di lokal — endpoint yang dispatch Celery task (/sync, /sort,
  /enrich, /group) akan 500 tanpa Redis service aktif. Ini bukan bug, sudah dari awal.
