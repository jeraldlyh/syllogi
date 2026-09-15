import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

export function Footer() {
  return (
    <footer className="relative overflow-hidden border-t border-fd-border bg-fd-card/40">
      <div className="mx-auto max-w-6xl px-6 py-8 sm:px-8">
        <div className="grid gap-10 md:grid-cols-4">
          <nav aria-label="Docs">
            <p className="font-chip text-xs uppercase tracking-sy-wide text-fd-muted-foreground">
              Docs
            </p>
            <ul className="mt-4 space-y-2.5 text-sm">
              <li>
                <Link
                  href="/docs/quick-start"
                  className="transition hover:text-emerald-600 dark:hover:text-emerald-400"
                >
                  Quick start
                </Link>
              </li>
              <li>
                <Link
                  href="/docs/features/playlist-sync"
                  className="transition hover:text-emerald-600 dark:hover:text-emerald-400"
                >
                  Playlist sync
                </Link>
              </li>
              <li>
                <Link
                  href="/docs/features/recommendations"
                  className="transition hover:text-emerald-600 dark:hover:text-emerald-400"
                >
                  Recommendations
                </Link>
              </li>
              <li>
                <Link
                  href="/docs/features/library"
                  className="transition hover:text-emerald-600 dark:hover:text-emerald-400"
                >
                  Library
                </Link>
              </li>
            </ul>
          </nav>
          <nav aria-label="Guides">
            <p className="font-chip text-xs uppercase tracking-sy-wide text-fd-muted-foreground">
              Guides
            </p>
            <ul className="mt-4 space-y-2.5 text-sm">
              <li>
                <Link
                  href="/docs/concepts/schedules"
                  className="transition hover:text-emerald-600 dark:hover:text-emerald-400"
                >
                  Schedules
                </Link>
              </li>
              <li>
                <Link
                  href="/docs/concepts/matching"
                  className="transition hover:text-emerald-600 dark:hover:text-emerald-400"
                >
                  Track matching
                </Link>
              </li>
              <li>
                <Link
                  href="/docs/usage/users-auth"
                  className="transition hover:text-emerald-600 dark:hover:text-emerald-400"
                >
                  Users &amp; auth
                </Link>
              </li>
              <li>
                <Link
                  href="/docs/troubleshooting"
                  className="transition hover:text-emerald-600 dark:hover:text-emerald-400"
                >
                  Troubleshooting
                </Link>
              </li>
            </ul>
          </nav>
          <nav aria-label="Project">
            <p className="font-chip text-xs uppercase tracking-sy-wide text-fd-muted-foreground">
              Project
            </p>
            <ul className="mt-4 space-y-2.5 text-sm">
              <li>
                <a
                  href="https://github.com/jeraldlyh/syllogi"
                  className="group inline-flex items-center gap-1 transition hover:text-emerald-600 dark:hover:text-emerald-400"
                >
                  GitHub
                  <ArrowUpRight className="size-3.5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                </a>
              </li>
              <li>
                <Link
                  href="/docs/configuration"
                  className="transition hover:text-emerald-600 dark:hover:text-emerald-400"
                >
                  Configuration
                </Link>
              </li>
              <li>
                <Link
                  href="/docs/configuration/authentik"
                  className="transition hover:text-emerald-600 dark:hover:text-emerald-400"
                >
                  Authentik SSO
                </Link>
              </li>
              <li>
                <Link
                  href="/docs/usage/logs"
                  className="transition hover:text-emerald-600 dark:hover:text-emerald-400"
                >
                  Logs
                </Link>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </footer>
  );
}
