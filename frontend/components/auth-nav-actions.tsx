"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/use-auth";

export default function AuthNavActions() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  function handleLogout() {
    logout();
    router.push("/");
    router.refresh();
  }

  if (loading) {
    return null;
  }

  if (user) {
    return (
      <>
        <Link
          href="/me"
          className="inline-flex max-w-[160px] items-center justify-center overflow-hidden text-ellipsis whitespace-nowrap rounded-[10px] border border-border bg-surface px-4 py-2 text-sm font-medium text-ink transition-colors hover:border-border-strong hover:bg-surface-2"
        >
          {user.display_name ?? user.email}
        </Link>
        <button
          type="button"
          onClick={handleLogout}
          className="inline-flex rounded-[10px] border border-border px-4 py-2 text-sm font-medium text-ink transition-colors hover:border-border-strong hover:text-white"
        >
          Log out
        </button>
      </>
    );
  }

  return (
    <>
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
    </>
  );
}