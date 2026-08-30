import Link from "next/link";

export default function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div className="bg-grid absolute inset-0 [mask-image:radial-gradient(70%_60%_at_50%_0%,black,transparent)]" />
      <div className="bg-glow absolute inset-0" />

      <div className="relative mx-auto flex w-full max-w-6xl flex-col items-center px-5 pb-28 pt-24 text-center sm:px-8 sm:pt-32">
        <span className="mb-8 inline-flex items-center gap-2 rounded-full border border-line-2 bg-surface px-4 py-1.5 text-xs font-medium uppercase tracking-[0.18em] text-muted">
          <span className="h-1.5 w-1.5 rounded-full bg-lime" />
          Playlist sync · Auto-sort · Discovery
        </span>

        <h1 className="text-gradient max-w-3xl text-balance text-5xl font-bold leading-[1.05] tracking-tight sm:text-6xl lg:text-7xl">
          Every playlist.
          <br />
          Every platform.
          <br />
          One lane.
        </h1>

        <p className="mt-6 max-w-xl text-pretty text-base leading-relaxed text-muted sm:text-lg">
          Move your library between Spotify, Apple Music, YT Music and
          SoundCloud. Let Hear-Me re-arrange playlists by genre, artist, album
          or mood — and discover new tracks along the way.
        </p>

        <div className="mt-10 flex flex-col items-center gap-3 sm:flex-row">
          <Link
            href="/login"
            className="inline-flex w-full items-center justify-center rounded-full bg-gradient-to-r from-violet to-fuchsia px-7 py-3.5 text-sm font-semibold text-white shadow-[0_0_36px_rgba(139,92,246,0.5)] transition-all hover:shadow-[0_0_52px_rgba(232,121,249,0.65)] sm:w-auto"
          >
            Log in to your library
            <svg
              className="ml-2 h-4 w-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M5 12h14" />
              <path d="m13 6 6 6-6 6" />
            </svg>
          </Link>
          <Link
            href="/register"
            className="inline-flex w-full items-center justify-center rounded-full border border-line-2 bg-surface px-7 py-3.5 text-sm font-semibold text-ink transition-colors hover:border-fuchsia/50 hover:bg-surface-2 sm:w-auto"
          >
            Create an account
          </Link>
        </div>
      </div>
    </section>
  );
}