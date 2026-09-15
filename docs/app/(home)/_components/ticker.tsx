const tickerRuns = [
  "overnight drive | 64 tracks | 41s",
  "daily rotation | 50 tracks | 28s",
  "charts pull | 30 tracks | 6 queued",
  "blend friday | 40 tracks | 52s",
  "soul sleepers | 72 tracks | 33s",
  "recent obsession | 25 tracks | 19s",
  "top tracks | 50 tracks | 36s",
  "slow sunday | 30 tracks | 44s",
];

export function Ticker() {
  return (
    <section
      aria-label="Recent sync runs"
      className="relative border-y border-fd-border bg-fd-card"
    >
      <div className="group relative left-1/2 w-screen -translate-x-1/2 overflow-hidden py-3">
        <div className="animate-marquee flex w-max items-center gap-8 pr-8 group-hover:pause-animation">
          {[0, 1].map((copy) => (
            <div
              key={copy}
              aria-hidden={copy === 1}
              className="flex items-center gap-8"
            >
              {tickerRuns.map((run) => (
                <span
                  key={`${copy}-${run}`}
                  className="font-chip flex items-center gap-8 whitespace-nowrap text-xs text-fd-muted-foreground"
                >
                  {run}
                  <span className="text-emerald-600 dark:text-emerald-500">///</span>
                </span>
              ))}
            </div>
          ))}
        </div>
        <div
          aria-hidden
          className="pointer-events-none absolute inset-y-0 left-0 z-10 w-16 bg-linear-to-r from-fd-card to-transparent"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute inset-y-0 right-0 z-10 w-16 bg-linear-to-l from-fd-card to-transparent"
        />
      </div>
    </section>
  );
}
