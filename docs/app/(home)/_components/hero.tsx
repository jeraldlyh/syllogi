import Image from "next/image";
import Link from "next/link";
import { ArrowRight, ArrowUpRight, Play } from "lucide-react";

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-sy-hero-glow"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-sy-dots bg-size-sy-dots text-fd-foreground/10 opacity-35"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 bottom-0 h-40 bg-linear-to-b from-transparent to-fd-background"
      />
      <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-6 pb-16 pt-14 sm:px-8 sm:pt-20 lg:grid-cols-2 lg:pb-24">
        <div>
          <p className="animate-rise inline-flex items-center gap-2 rounded-full border border-fd-border bg-fd-card px-3 py-1.5 text-xs font-mono">
            <span className="animate-blink inline-block h-2 w-2 rounded-full bg-red-500" />
            ON AIR | SELF-HOSTED MUSIC AUTOMATION
          </p>
          <h1
            className="font-display animate-rise mt-5 text-5xl font-extrabold leading-none tracking-tight text-balance sm:text-6xl lg:text-7xl"
            style={{ animationDelay: "90ms" }}
          >
            Your library,
            <br />
            on
            <span className="text-emerald-600 dark:text-emerald-400">
              &nbsp;autopilot.
            </span>
          </h1>
          <p
            className="animate-rise my-5 max-w-xl text-base text-fd-muted-foreground"
            style={{ animationDelay: "180ms" }}
          >
            Keep your Jellyfin or Navidrome library in sync with Spotify and
            YouTube playlists - downloading what&apos;s missing and building
            recommendations from your listening history.
          </p>
          <div
            className="animate-rise flex flex-wrap items-center gap-3"
            style={{ animationDelay: "270ms" }}
          >
            <Link
              href="/docs"
              className="group inline-flex items-center gap-2 rounded-xl bg-fd-primary px-5 py-2.5 text-sm font-medium text-fd-primary-foreground transition hover:opacity-90"
            >
              Read the docs
              <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <Link
              href="/docs/quick-start"
              className="inline-flex items-center gap-2 rounded-xl border border-fd-border bg-fd-card px-5 py-2.5 text-sm font-medium transition hover:border-emerald-500/60"
            >
              <Play className="size-4" />
              Quick start
            </Link>
            <a
              href="https://github.com/jeraldlyh/syllogi"
              className="inline-flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium text-fd-muted-foreground transition hover:text-fd-foreground"
            >
              <ArrowUpRight className="size-4" />
              GitHub
            </a>
          </div>
          <div
            className="animate-rise mt-10 flex items-center gap-4"
            style={{ animationDelay: "360ms" }}
          >
            <div aria-hidden className="flex h-8 flex-1 items-end gap-0.75">
              {Array.from({ length: 32 }).map((_, i) => (
                <span
                  key={i}
                  className={`origin-bottom animate-eq  w-full rounded-sm ${i % 5 === 0 ? "bg-fd-foreground/25" : "bg-emerald-500/90"}`}
                  style={{
                    height: "100%",
                    animationDelay: `${((i * 137) % 1100) / 1000}s`,
                    animationDuration: `${0.9 + ((i * 37) % 60) / 100}s`,
                  }}
                />
              ))}
            </div>
          </div>
        </div>
        <div
          className="animate-rise relative mx-auto w-64 sm:w-80 lg:w-92"
          style={{ animationDelay: "200ms" }}
        >
          <div
            aria-hidden
            className="absolute -inset-10 rounded-full bg-emerald-500/15 blur-3xl"
          />
          <div className="animate-spin-slow pause-on-hover relative aspect-square rounded-full bg-sy-grooves shadow-2xl ring-1 ring-black/70">
            <div
              aria-hidden
              className="absolute inset-0 rounded-full bg-sy-shine"
            />
            <div className="absolute inset-1/3 flex flex-col items-center justify-center gap-1.5 rounded-full shadow-inner">
              <Image
                src="/assets/icon.png"
                alt=""
                width={96}
                height={96}
                className="rounded-full"
              />
            </div>
            <div className="absolute left-1/2 top-1/2 size-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-stone-950 ring-2 ring-emerald-100" />
          </div>
          <div className="absolute -right-3 top-8 hidden sm:block lg:-right-8">
            <p className="font-chip inline-flex items-center gap-2 whitespace-nowrap rounded-full border border-fd-border bg-fd-card px-3.5 py-1.5 text-xs text-fd-muted-foreground shadow-lg font-medium">
              <span className="animate-blink inline-block size-1.5 rounded-full bg-blue-500" />
              SYNCING
            </p>
          </div>
          <div className="absolute -left-3 bottom-14 hidden sm:block lg:-left-10">
            <p className="font-chip inline-flex items-center gap-2 whitespace-nowrap rounded-full border border-fd-border bg-fd-card px-3.5 py-1.5 text-xs text-fd-muted-foreground shadow-lg font-medium">
              <span className="animate-blink inline-block size-1.5 rounded-full bg-amber-500" />
              DOWNLOADING
            </p>
          </div>
          <div className="absolute -bottom-5 left-1/2 -translate-x-1/2">
            <p className="font-chip inline-flex items-center gap-2 whitespace-nowrap rounded-full border border-fd-border bg-fd-card px-3.5 py-1.5 text-xs text-fd-muted-foreground shadow-lg font-medium">
              <span className="animate-blink inline-block size-1.5 rounded-full bg-emerald-500" />
              RECOMMENDING
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
