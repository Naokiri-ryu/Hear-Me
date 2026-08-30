import Link from "next/link";

export function WaveformMark() {
  return (
    <span className="inline-flex items-end gap-[3px]" aria-hidden="true">
      <span className="h-2 w-[3px] rounded-full bg-lime" />
      <span className="h-4 w-[3px] rounded-full bg-violet" />
      <span className="h-3 w-[3px] rounded-full bg-fuchsia" />
      <span className="h-5 w-[3px] rounded-full bg-violet" />
      <span className="h-2 w-[3px] rounded-full bg-lime" />
    </span>
  );
}

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-line/70 bg-night/70 backdrop-blur-md">
      <nav className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-5 sm:px-8">
        <Link href="/" className="group flex items-center gap-2.5">
          <WaveformMark />
          <span className="text-lg font-semibold tracking-tight text-ink">
            Hear<span className="text-violet">-</span>Me
          </span>
        </Link>
        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="hidden rounded-full border border-line-2 px-4 py-2 text-sm font-medium text-ink transition-colors hover:border-fuchsia/50 hover:text-white sm:inline-flex"
          >
            Log in
          </Link>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 rounded-full bg-ink px-4 py-2 text-sm font-semibold text-night transition-all hover:bg-white hover:shadow-[0_0_28px_rgba(139,92,246,0.45)]"
          >
            Get started
          </Link>
        </div>
      </nav>
    </header>
  );
}