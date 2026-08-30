"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, login, saveToken } from "@/lib/api";
import { AUTH_EVENT } from "@/lib/use-auth";

export default function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setPending(true);
    try {
      const token = await login(email, password);
      saveToken(token.access_token);
      window.dispatchEvent(new Event(AUTH_EVENT));
      router.push("/me");
      router.refresh();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Could not reach the server. Is the backend running?");
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5" noValidate>
      <div className="flex flex-col gap-2">
        <label htmlFor="email" className="text-sm font-medium text-ink">
          Email
        </label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          className="h-11 rounded-[10px] border border-border bg-surface-2 px-4 text-sm text-ink placeholder:text-muted outline-none transition-colors focus:border-border-strong"
        />
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="password" className="text-sm font-medium text-ink">
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          className="h-11 rounded-[10px] border border-border bg-surface-2 px-4 text-sm text-ink placeholder:text-muted outline-none transition-colors focus:border-border-strong"
        />
      </div>

      {error ? (
        <p
          role="alert"
          className="rounded-[10px] border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger"
        >
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={pending}
        className="mt-1 inline-flex h-11 items-center justify-center rounded-[10px] bg-accent text-sm font-medium text-canvas transition-colors hover:bg-[#e6b34f] disabled:cursor-not-allowed disabled:opacity-60"
      >
        {pending ? "Signing in…" : "Log in"}
      </button>
    </form>
  );
}