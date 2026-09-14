import Image from 'next/image';
import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="flex flex-col items-center justify-center flex-1 text-center px-4 gap-6">
      <Image src="/assets/icon.png" alt="syllogi" width={96} height={96} className="rounded-2xl" />
      <div>
        <h1 className="text-3xl font-bold mb-3">syllogi</h1>
        <p className="text-fd-muted-foreground max-w-xl">
          Self-hosted automation that keeps your Jellyfin or Navidrome music library in sync with
          Spotify and YouTube playlists, downloads what is missing, and builds recommendations from
          your listening history.
        </p>
      </div>
      <div className="flex gap-3">
        <Link
          href="/docs"
          className="rounded-lg bg-fd-primary text-fd-primary-foreground px-4 py-2 font-medium"
        >
          Read the docs
        </Link>
        <Link
          href="/docs/quick-start"
          className="rounded-lg border px-4 py-2 font-medium"
        >
          Quick start
        </Link>
      </div>
    </main>
  );
}
