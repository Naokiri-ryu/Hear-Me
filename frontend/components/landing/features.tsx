const FEATURES = [
  {
    title: "Transfer playlists",
    description:
      "Move playlists between Spotify, Apple Music, YT Music and SoundCloud. Heavy sync runs as background jobs — your library never stalls.",
    icon: (
      <svg
        className="h-6 w-6"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M8 3 4 7l4 4" />
        <path d="M4 7h16" />
        <path d="m16 21 4-4-4-4" />
        <path d="M20 17H4" />
      </svg>
    ),
  },
  {
    title: "Auto-sort your library",
    description:
      "Re-arrange playlists by genre, artist, album or mood in a single tap — a messy list becomes a curated set.",
    icon: (
      <svg
        className="h-6 w-6"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="m3 6 3-3 3 3" />
        <path d="M6 3v11" />
        <path d="m15 18 3 3 3-3" />
        <path d="M18 21V10" />
        <path d="M3 14h8" />
        <path d="M13 6h8" />
      </svg>
    ),
  },
  {
    title: "Discover more",
    description:
      "Find new tracks and dig into deep info about songs, albums and artists — all in one place.",
    icon: (
      <svg
        className="h-6 w-6"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <circle cx="12" cy="12" r="9" />
        <path d="M16 3.5c-1 2.5-1.5 5-1.5 8.5s.5 6 1.5 8.5" />
        <path d="M8 3.5c1 2.5 1.5 5 1.5 8.5S9 18 8 20.5" />
        <path d="M3.5 16c2.5-1 5-1.5 8.5-1.5s6 .5 8.5 1.5" />
        <path d="M3.5 8c2.5 1 5 1.5 8.5 1.5s6-.5 8.5-1.5" />
      </svg>
    ),
  },
];

export default function Features() {
  return (
    <section className="relative border-t border-line/60 bg-night-2">
      <div className="mx-auto w-full max-w-6xl px-5 py-20 sm:px-8 sm:py-24">
        <div className="mx-auto max-w-xl text-center">
          <h2 className="text-3xl font-bold tracking-tight text-ink sm:text-4xl">
            One home for your whole library
          </h2>
          <p className="mt-3 text-pretty text-muted">
            Stop juggling apps. Hear-Me brings your playlists together, then
            takes care of the organizing.
          </p>
        </div>

        <div className="mt-14 grid gap-4 sm:grid-cols-3 sm:gap-5">
          {FEATURES.map((feature) => (
            <article
              key={feature.title}
              className="group relative overflow-hidden rounded-2xl border border-line bg-surface p-6 transition-all hover:border-line-2 hover:bg-surface-2"
            >
              <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-violet/10 blur-2xl transition-opacity opacity-0 group-hover:opacity-100" />
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl border border-line-2 bg-surface-2 text-violet">
                {feature.icon}
              </div>
              <h3 className="mt-5 text-lg font-semibold text-ink">
                {feature.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">
                {feature.description}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}