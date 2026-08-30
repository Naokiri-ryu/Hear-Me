import type { Metadata } from "next";
import Link from "next/link";
import { WaveformMark } from "@/components/navbar";
import LoginForm from "./login-form";

export const metadata: Metadata = {
  title: "Log in",
};

export default function LoginPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-canvas px-5 py-16">
      <div className="w-full max-w-sm">
        <Link
          href="/"
          className="mb-10 flex items-center justify-center gap-3"
        >
          <WaveformMark />
          <span className="text-base font-medium tracking-tight text-ink">
            Hear-Me
          </span>
        </Link>

        <div className="rounded-[10px] border border-border bg-surface p-8">
          <h1 className="text-2xl font-medium tracking-tight text-ink">
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
              className="font-medium text-ink underline decoration-border-strong underline-offset-4 transition-colors hover:text-white"
            >
              Create one
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}