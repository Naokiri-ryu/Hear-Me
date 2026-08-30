import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Hear-Me — Music, everywhere.",
    template: "%s — Hear-Me",
  },
  description:
    "Transfer playlists across Spotify, Apple Music, YT Music and SoundCloud; auto-sort by genre, artist, album or mood; and discover new music.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full">{children}</body>
    </html>
  );
}