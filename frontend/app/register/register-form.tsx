"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, register } from "@/lib/api";

export default function RegisterForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setPending(true);
    try {
      await register({
        email,
        password,
        ...(displayName.trim().length > 0
          ? { display_name: displayName.trim() }
          : {}),
      });
      router.push("/login");
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
        <label htmlFor="display-name" className="text-sm font-medium text-ink">
          Display name{" "}
          <span className="font-normal text-muted">(optional)</span>
        </label>
        <input
          id="display-name"
          name="display_name"
          type="text"
          autoComplete="nickname"
          maxLength={120}
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          placeholder="How should we call you?"
          className="h-11 rounded-[10px] border border-border bg-surface-2 px-4 text-sm text-ink placeholder:text-muted outline-none transition-colors focus:border-border-strong"
        />
      </div>

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
          autoComplete="new-password"
          required
          minLength={8}
          maxLength={128}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="At least 8 characters"
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
        {pending ? "Creating account…" : "Create account"}
      </button>
    </form>
  );
}