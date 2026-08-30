"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/navbar";
import { useAuth } from "@/lib/use-auth";
import {
  getPlaylistGroups,
  getPlaylists,
  runGrouping,
  type GroupBy,
  type PlaylistGroup,
  type PlaylistSummary,
} from "@/lib/api";

const SORT_OPTIONS: { value: GroupBy; label: string }[] = [
  { value: "genre", label: "Genre" },
  { value: "artist", label: "Artist" },
  { value: "album", label: "Album" },
  { value: "decade", label: "Decade" },
];

function formatPlatform(platform: string | null): string {
  if (!platform) return "Manual";
  return platform.charAt(0).toUpperCase() + platform.slice(1);
}

function snapshotLabel(sortBy: string): string {
  const op = SORT_OPTIONS.find((o) => o.value === sortBy);
  return op ? op.label : sortBy.charAt(0).toUpperCase() + sortBy.slice(1);
}

function PlaylistCard({ playlist }: { playlist: PlaylistSummary }) {
  const [expanded, setExpanded] = useState(false);
  const [snapshots, setSnapshots] = useState<PlaylistGroup[] | null>(null);
  const [loadingGroups, setLoadingGroups] = useState(false);
  const [sortBy, setSortBy] = useState<GroupBy>("genre");
  const [running, setRunning] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  async function loadGroups() {
    if (snapshots === null) {
      setLoadingGroups(true);
      try {
        const groups = await getPlaylistGroups(playlist.id);
        setSnapshots(groups);
      } catch (error) {
        setNotice(error instanceof Error ? error.message : "Failed to load groups");
      } finally {
        setLoadingGroups(false);
      }
    }
  }

  async function toggle() {
    if (!expanded) {
      setExpanded(true);
      await loadGroups();
    } else {
      setExpanded(false);
    }
  }

  async function reload() {
    setSnapshots(null);
    await loadGroups();
  }

  async function handleRun() {
    setRunning(true);
    setRunError(null);
    setNotice(null);
    try {
      const result = await runGrouping(playlist.id, sortBy);
      setNotice(`Sort queued (task ${result.task_id}). Reload after it finishes.`);
    } catch (error) {
      setRunError(
        error instanceof Error
          ? error.message
          : "Couldn&apos;t start the sort. Check that the worker is running.",
      );
    } finally {
      setRunning(false);
    }
  }

  const selectedSnapshot = snapshots?.[0] ?? null;
  const activeTab = selectedSnapshot?.sort_by ?? (sortBy as string);
  const snapshotTabs = Array.from(
    new Set((snapshots ?? []).map((s) => s.sort_by)),
  );
  const maxCount = selectedSnapshot
    ? Math.max(
        1,
        ...Object.values(selectedSnapshot.groups).map((ids) => ids.length),
      )
    : 0;

  return (
    <article className="rounded-[10px] border border-border bg-surface p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h2 className="font-display text-xl font-light tracking-tight text-ink">
            {playlist.name}
          </h2>
          {playlist.description ? (
            <p className="mt-1 line-clamp-2 text-sm text-muted">
              {playlist.description}
            </p>
          ) : null}
          <p className="mt-2 text-xs uppercase tracking-[0.14em] text-muted">
            {playlist.track_count} tracks · {formatPlatform(playlist.source_platform)}
          </p>
        </div>
        <button
          type="button"
          onClick={toggle}
          className="inline-flex shrink-0 items-center rounded-[10px] border border-border px-3.5 py-2 text-sm font-medium text-ink transition-colors hover:border-border-strong hover:bg-surface-2"
        >
          {expanded ? "Collapse" : "View groups"}
        </button>
      </div>

      {expanded ? (
        <div className="mt-5 border-t border-border pt-5">
          {loadingGroups ? (
            <p className="text-sm text-muted">Loading groups…</p>
          ) : snapshots && snapshots.length === 0 ? (
            <div className="rounded-[10px] border border-border bg-surface-2 p-4">
              <p className="text-sm text-ink">No auto-sort snapshot yet.</p>
              <p className="mt-1 text-sm text-muted">
                Run a sort to group this playlist by genre, artist, album or
                decade.
              </p>
            </div>
          ) : selectedSnapshot ? (
            <div>
              <div className="flex flex-wrap items-center gap-1.5">
                {snapshotTabs.map((tab) => (
                  <span
                    key={tab}
                    className={`rounded-full px-3 py-1 text-xs font-medium ${
                      tab === activeTab
                        ? "bg-surface-2 text-ink"
                        : "text-muted"
                    }`}
                  >
                    {snapshotLabel(tab)}
                  </span>
                ))}
                <span className="ml-auto text-xs text-muted">
                  {selectedSnapshot.track_count} tracks ·{" "}
                  {selectedSnapshot.group_count} groups
                </span>
              </div>
              <ul className="mt-4 space-y-2">
                {Object.entries(selectedSnapshot.groups).map(
                  ([category, trackIds]) => (
                    <li key={category}>
                      <div className="flex items-center justify-between gap-3">
                        <span className="truncate text-sm text-ink">
                          {category}
                        </span>
                        <span className="shrink-0 text-xs text-muted">
                          {trackIds.length} tracks
                        </span>
                      </div>
                      <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-border">
                        <div
                          className="h-full rounded-full bg-border-strong"
                          style={{
                            width: `${(trackIds.length / maxCount) * 100}%`,
                          }}
                        />
                      </div>
                    </li>
                  ),
                )}
              </ul>
            </div>
          ) : (
            <p className="text-sm text-muted">Couldn&apos;t load groups.</p>
          )}

          <div className="mt-5 flex flex-wrap items-center gap-2">
            <select
              value={sortBy}
              onChange={(event) => setSortBy(event.target.value as GroupBy)}
              disabled={running}
              className="h-10 rounded-[10px] border border-border bg-surface-2 px-3 text-sm text-ink transition-colors focus:border-border-strong focus:outline-none"
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  By {option.label}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={handleRun}
              disabled={running}
              className="inline-flex h-10 items-center rounded-[10px] bg-accent px-4 text-sm font-medium text-canvas transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {running ? "Queuing…" : "Run auto-sort"}
            </button>
            <button
              type="button"
              onClick={reload}
              className="inline-flex h-10 items-center rounded-[10px] border border-border px-4 text-sm font-medium text-ink transition-colors hover:border-border-strong hover:bg-surface-2"
            >
              Reload
            </button>
          </div>

          {notice ? <p className="mt-3 text-sm text-muted">{notice}</p> : null}
          {runError ? (
            <p className="mt-3 text-sm text-danger">{runError}</p>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [playlists, setPlaylists] = useState<PlaylistSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  const loadPlaylists = useCallback(async () => {
    setError(null);
    try {
      setPlaylists(await getPlaylists());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load playlists");
    }
  }, []);

  useEffect(() => {
    if (user) {
      const timer = window.setTimeout(() => void loadPlaylists(), 0);
      return () => window.clearTimeout(timer);
    }
  }, [user, loadPlaylists]);

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
      <main className="mx-auto w-full max-w-6xl flex-1 px-5 pb-24 pt-14 sm:px-8 sm:pt-20">
        <header className="max-w-2xl">
          <p className="text-sm text-muted">Dashboard</p>
          <h1 className="mt-1 font-display text-4xl font-light tracking-tight text-ink sm:text-5xl">
            Your playlists
          </h1>
          <p className="mt-3 text-base leading-relaxed text-muted">
            Browse your library and auto-sort a playlist into genre, artist,
            album or decade groups.
          </p>
        </header>

        <section className="mt-10 sm:mt-14">
          {playlists === null && !error ? (
            <p className="text-sm text-muted">Loading playlists…</p>
          ) : error ? (
            <div className="rounded-[10px] border border-border bg-surface p-5">
              <p className="text-sm text-ink">{error}</p>
              <button
                type="button"
                onClick={loadPlaylists}
                className="mt-3 inline-flex h-10 items-center rounded-[10px] border border-border px-4 text-sm font-medium text-ink transition-colors hover:border-border-strong hover:bg-surface-2"
              >
                Try again
              </button>
            </div>
          ) : playlists && playlists.length === 0 ? (
            <div className="rounded-[10px] border border-border bg-surface p-8 text-center">
              <p className="font-display text-2xl font-light tracking-tight text-ink">
                No playlists yet
              </p>
              <p className="mx-auto mt-2 max-w-md text-sm text-muted">
                Import a playlist from Spotify to see it here, then run an
                auto-sort to split it into groups..
              </p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {(playlists ?? []).map((playlist) => (
                <PlaylistCard key={playlist.id} playlist={playlist} />
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}