import Link from "next/link";
import {
  ArrowUpRight,
  Download,
  Library,
  ListMusic,
  Sparkles,
  TrendingUp,
} from "lucide-react";

const features = [
  {
    icon: ListMusic,
    title: "Playlist Sync",
    body: "Mirror public Spotify and YouTube playlists into your server on a schedule, with a per-run breakdown of what moved.",
    href: "/docs/features/playlist-sync",
  },
  {
    icon: Download,
    title: "Downloads",
    body: "Tracks missing from your library fetch themselves — slskd first, YouTube fallback — then the library rescans.",
    href: "/docs/features/downloads",
  },
  {
    icon: Sparkles,
    title: "Recommendations",
    body: "A fresh daily playlist built from your Last.fm or ListenBrainz history. Solo taste or a blend with the whole house.",
    href: "/docs/features/recommendations",
  },
  {
    icon: TrendingUp,
    title: "Charts",
    body: "Browse globally trending tracks and queue any of them for download without leaving the dashboard.",
    href: "/docs/features/charts",
  },
  {
    icon: Library,
    title: "Library",
    body: "Browse the download shelf, retag files, fill in lyrics, and clear out duplicates and empty folders.",
    href: "/docs/features/library",
  },
];

export function Features() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-16 sm:px-8 lg:py-24">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="font-chip text-xs uppercase tracking-sy-wide text-emerald-600 dark:text-emerald-400">
            What it does
          </p>
          <h2 className="font-display mt-2 text-3xl font-bold tracking-tight sm:text-4xl">
            Five decks, one booth.
          </h2>
        </div>
        <Link
          href="/docs/features"
          className="group inline-flex items-center gap-1.5 text-sm font-medium text-fd-muted-foreground transition hover:text-fd-foreground"
        >
          All features
          <ArrowUpRight className="size-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
        </Link>
      </div>
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((feature) => (
          <Link
            key={feature.href}
            href={feature.href}
            className="group relative overflow-hidden rounded-2xl border border-fd-border bg-fd-card p-6 transition duration-300 hover:-translate-y-1 hover:border-emerald-500/60 hover:shadow-xl"
          >
            <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-fd-border bg-fd-background transition group-hover:border-emerald-500/50">
              <feature.icon className="size-5" />
            </span>
            <h3 className="font-display mt-5 text-xl font-bold">
              {feature.title}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-fd-muted-foreground">
              {feature.body}
            </p>
          </Link>
        ))}
        <Link
          href="/docs/usage/logs"
          className="group relative overflow-hidden rounded-2xl border border-dashed border-fd-border p-6 transition duration-300 hover:-translate-y-1 hover:border-emerald-500/60 hover:shadow-xl"
        >
          <h3 className="font-display mt-5 text-xl font-bold">
            Plus the receipts.
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-fd-muted-foreground">
            Every run leaves a session behind - what was added, removed,
            missing, or downloaded. No black boxes.
          </p>
        </Link>
      </div>
    </section>
  );
}
