import type { Metadata } from "next";
import Link from "next/link";
import { WaveformMark } from "@/components/navbar";
import LoginForm from "./login-form";

export const metadata: Metadata = {
  title: "Log in",
};

export default function LoginPage() {
  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-night px-5 py-16">
      <div className="bg-glow absolute inset-0" />
      <div className="bg-grid absolute inset-0 [mask-image:radial-gradient(60%_50%_at_50%_30%,black,transparent)]" />

      <div className="relative w-full max-w-sm">
        <Link
          href="/"
          className="mb-10 flex items-center justify-center gap-2.5"
        >
          <WaveformMark />
          <span className="text-xl font-semibold tracking-tight text-ink">
            Hear<span className="text-violet">-</span>Me
          </span>
        </Link>

        <div className="rounded-2xl border border-line bg-surface p-7 shadow-[0_24px_80px_-24px_rgba(0,0,0,0.8)] sm:p-8">
          <h1 className="text-2xl font-bold tracking-tight text-ink">
            Welcome back
          </h1>
          <p className="mt-1.5 text-sm text-muted">
            Log in to manage your library.
          </p>

          <div className="mt-7">
            <LoginForm />
          </div>

          <p className="mt-6 text-center text-sm text-muted">
            Don&apos;t have an account?{" "}
            <Link
              href="/register"
              className="font-medium text-violet transition-colors hover:text-fuchsia"
            >
              Create one
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}