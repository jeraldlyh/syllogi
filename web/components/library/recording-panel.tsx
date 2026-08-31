import { Text } from "@/components/common/text";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RecordingMatch, useRecordingMatches } from "@/hooks/useLibrary";
import { cn, formatClock } from "@/lib/utils";
import { ExternalLink, Link2 } from "lucide-react";
import { useState } from "react";
import { PanelMessage, SourcePanel } from "./source-panel";

const MAX_GENRES = 4;

interface IProps {
  initialQuery: string;
  linkedId: string;
  onApply: (match: RecordingMatch) => void;
}

export const RecordingPanel = ({ initialQuery, linkedId, onApply }: IProps) => {
  const [query, setQuery] = useState(initialQuery);
  const { data, isLoading, isError } = useRecordingMatches(query || null);

  const renderResults = (): React.JSX.Element => {
    if (isLoading) {
      return <PanelMessage value="Searching MusicBrainz..." />;
    }

    if (isError) {
      return (
        <PanelMessage value="MusicBrainz did not respond. Search again in a moment." />
      );
    }

    if (!data || data.length === 0) {
      return (
        <PanelMessage value="No recordings match that search. Try the artist and title on their own." />
      );
    }

    return (
      <ul className="flex flex-col gap-2">
        {data.map((match) => {
          const isLinked = Boolean(linkedId) && match.id === linkedId;

          return (
            <li
              key={match.id}
              className={cn(
                "rounded-md border p-3 transition-colors",
                isLinked
                  ? "border-primary/40 bg-primary/5"
                  : "border-border hover:border-muted-foreground/30",
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">
                    {match.title}
                    {match.disambiguation && (
                      <span className="text-muted-foreground">
                        {" "}
                        ({match.disambiguation})
                      </span>
                    )}
                  </p>
                  <Text
                    muted
                    className="truncate"
                    value={[match.artist_name, match.album_name]
                      .filter(Boolean)
                      .join(" — ")}
                  />
                </div>
                {isLinked && (
                  <Badge
                    variant="outline"
                    className="shrink-0 gap-1 border-primary/30 bg-primary/10 text-xs uppercase tracking-wider text-primary"
                  >
                    <Link2 className="h-3 w-3" />
                    Linked
                  </Badge>
                )}
              </div>
              <Text
                mono
                muted
                className="mt-1.5"
                value={[match.year, formatClock(match.duration)]
                  .filter(Boolean)
                  .join(" | ")}
              />
              {match.genres.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {match.genres.slice(0, MAX_GENRES).map((genre) => (
                    <Badge
                      key={genre}
                      variant="secondary"
                      className="text-xs font-normal"
                    >
                      {genre}
                    </Badge>
                  ))}
                </div>
              )}
              <div className="mt-2.5 flex items-center gap-1">
                <Button
                  type="button"
                  size="sm"
                  variant={isLinked ? "secondary" : "default"}
                  className="h-7 text-xs"
                  onClick={() => onApply(match)}
                >
                  {isLinked ? "Apply again" : "Use this recording"}
                </Button>
                <Button
                  asChild
                  size="icon"
                  variant="ghost"
                  className="h-7 w-7 text-muted-foreground hover:text-foreground"
                >
                  <a
                    href={match.url}
                    target="_blank"
                    rel="noreferrer"
                    aria-label={`Open ${match.title} on MusicBrainz`}
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                </Button>
              </div>
            </li>
          );
        })}
      </ul>
    );
  };

  return (
    <SourcePanel
      eyebrow="Recording"
      origin="musicbrainz"
      originClassName="text-sky-400"
      placeholder="Search artist and title"
      initialQuery={initialQuery}
      onSearch={setQuery}
    >
      {renderResults()}
    </SourcePanel>
  );
};
