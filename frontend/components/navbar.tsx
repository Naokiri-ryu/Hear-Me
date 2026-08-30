import Link from "next/link";

export function WaveformMark() {
  return (
    <span className="inline-flex items-end gap-[3px]" aria-hidden="true">
      <span className="h-2 w-[3px] bg-ink opacity-40" />
      <span className="h-4 w-[3px] bg-ink opacity-70" />
      <span className="h-3 w-[3px] bg-ink opacity-55" />
      <span className="h-5 w-[3px] bg-ink" />
      <span className="h-2 w-[3px] bg-ink opacity-40" />
    </span>
  );
}

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-border bg-canvas/85 backdrop-blur-md">
      <nav className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-5 sm:px-8">
        <Link href="/" className="flex items-center gap-3">
          <WaveformMark />
          <span className="text-base font-medium tracking-tight text-ink">
            Hear-Me
          </span>
        </Link>
        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="hidden rounded-[10px] border border-border px-4 py-2 text-sm font-medium text-ink transition-colors hover:border-border-strong hover:text-white sm:inline-flex"
          >
            Log in
          </Link>
          <Link
            href="/register"
            className="inline-flex rounded-[10px] border border-border bg-surface px-4 py-2 text-sm font-medium text-ink transition-colors hover:border-border-strong hover:bg-surface-2"
          >
            Get started
          </Link>
        </div>
      </nav>
    </header>
  );
}