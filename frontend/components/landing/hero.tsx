import Link from "next/link";

export default function Hero() {
  return (
    <section className="mx-auto w-full max-w-6xl px-5 pb-24 pt-28 sm:px-8 sm:pt-36">
      <div className="max-w-2xl">
        <h1 className="font-display text-balance text-5xl font-light leading-[1.08] tracking-tight text-ink sm:text-6xl lg:text-7xl">
          Every playlist.
          <br />
          Every platform.
          <br />
          One lane.
        </h1>

        <p className="mt-7 max-w-xl text-pretty text-base leading-relaxed text-muted sm:text-lg">
          Move your library between Spotify, Apple Music, YT Music and
          SoundCloud. Let Hear-Me re-arrange playlists by genre, artist, album
          or mood — and discover new tracks along the way.
        </p>

        <div className="mt-11 flex flex-col items-start gap-3 sm:flex-row">
          <Link
            href="/login"
            className="inline-flex items-center justify-center rounded-[10px] bg-accent px-6 py-3 text-sm font-medium text-canvas transition-colors hover:bg-[#e6b34f]"
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
            className="inline-flex items-center justify-center rounded-[10px] border border-border px-6 py-3 text-sm font-medium text-ink transition-colors hover:border-border-strong hover:bg-surface"
          >
            Create an account
          </Link>
        </div>
      </div>
    </section>
  );
}