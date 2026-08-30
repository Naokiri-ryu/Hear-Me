import type { Metadata } from "next";
import Link from "next/link";
import { WaveformMark } from "@/components/navbar";
import RegisterForm from "./register-form";

export const metadata: Metadata = {
  title: "Create account",
};

export default function RegisterPage() {
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
            Join Hear-Me
          </h1>
          <p className="mt-1.5 text-sm text-muted">
            Bring your playlists into one place.
          </p>

          <div className="mt-7">
            <RegisterForm />
          </div>

          <p className="mt-6 text-center text-sm text-muted">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-medium text-ink underline decoration-border-strong underline-offset-4 transition-colors hover:text-white"
            >
              Log in
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}