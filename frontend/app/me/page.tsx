"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/navbar";
import { useAuth } from "@/lib/use-auth";

export default function MePage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  function handleLogout() {
    logout();
    router.push("/");
    router.refresh();
  }

  if (loading || !user) {
    return (
      <div className="flex min-h-screen flex-col bg-canvas">
        <Navbar />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <Navbar />
      <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col justify-center px-5 pb-24 pt-16 sm:px-8">
        <div className="rounded-[10px] border border-border bg-surface p-8">
          <p className="text-sm text-muted">Signed in as</p>
          <h1 className="font-display text-3xl font-light tracking-tight text-ink">
            {user.display_name ?? "Hear-Me user"}
          </h1>
          <p className="mt-1.5 text-sm text-muted">{user.email}</p>

          <dl className="mt-6 grid grid-cols-2 gap-6 border-t border-border pt-6 text-sm">
            <div>
              <dt className="text-muted">User id</dt>
              <dd className="mt-0.5 text-ink">{user.id}</dd>
            </div>
            <div>
              <dt className="text-muted">Status</dt>
              <dd className="mt-0.5 text-ink">
                {user.is_active ? "Active" : "Disabled"}
              </dd>
            </div>
          </dl>

          <button
            type="button"
            onClick={handleLogout}
            className="mt-8 inline-flex h-11 items-center justify-center rounded-[10px] border border-border px-5 text-sm font-medium text-ink transition-colors hover:border-border-strong hover:bg-surface-2"
          >
            Log out
          </button>
        </div>
      </main>
    </div>
  );
}