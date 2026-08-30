import Link from "next/link";
import Navbar from "@/components/navbar";
import Hero from "@/components/landing/hero";
import Features from "@/components/landing/features";

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-night">
      <Navbar />
      <main className="flex-1">
        <Hero />
        <Features />
      </main>
      <footer className="border-t border-line/60">
        <div className="mx-auto flex w-full max-w-6xl flex-col items-center justify-between gap-3 px-5 py-8 text-sm text-faint sm:flex-row sm:px-8">
          <p>© {new Date().getFullYear()} Hear-Me</p>
          <nav className="flex items-center gap-6">
            <Link href="/login" className="transition-colors hover:text-ink">
              Log in
            </Link>
            <Link href="/register" className="transition-colors hover:text-ink">
              Create account
            </Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}