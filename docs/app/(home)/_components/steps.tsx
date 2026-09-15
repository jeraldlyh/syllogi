import Link from "next/link";
import { ArrowRight, Clock, Play, Server } from "lucide-react";

const steps = [
  {
    icon: Server,
    title: "Point at your server",
    body: "Jellyfin or Navidrome - one key or login, plus a folder your server already scans.",
    href: "/docs/configuration",
    link: "Configuration",
  },
  {
    icon: Clock,
    title: "Add a playlist + schedule",
    body: "Paste a playlist ID, pick a preset or write your own five-field cron.",
    href: "/docs/concepts/schedules",
    link: "Schedules",
  },
  {
    icon: Play,
    title: "Press play",
    body: "Missing tracks download, tags fill in, and every run leaves a session behind.",
    href: "/docs/features/playlist-sync",
    link: "Playlist sync",
  },
];

export function Steps() {
  return (
    <section className="border-y border-fd-border bg-fd-card/40">
      <div className="mx-auto max-w-6xl px-4 py-16 lg:py-20">
        <p className="font-chip text-xs uppercase tracking-sy-wide text-amber-600 dark:text-amber-400">
          How it runs
        </p>
        <h2 className="font-display mt-2 text-3xl font-bold tracking-tight sm:text-4xl">
          Three steps to autopilot.
        </h2>
        <div className="mt-10 grid gap-8 md:grid-cols-3">
          {steps.map((step) => (
            <div key={step.href} className="relative flex flex-col">
              <span className="flex size-10 items-center justify-center rounded-xl border border-fd-border bg-fd-background">
                <step.icon className="size-5" />
              </span>
              <h3 className="font-display mt-4 text-lg font-bold">
                {step.title}
              </h3>
              <p className="mt-1.5 text-sm leading-relaxed text-fd-muted-foreground">
                {step.body}
              </p>
              <p className="mt-auto">
                <Link
                  href={step.href}
                  className="group inline-flex items-center gap-1 text-sm font-medium text-amber-700 hover:text-amber-600 dark:text-amber-400 dark:hover:text-amber-300"
                >
                  {step.link}
                  <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-0.5" />
                </Link>
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
