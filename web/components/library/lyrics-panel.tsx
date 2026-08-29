import { Text } from "@/components/common/text";
import { Button } from "@/components/ui/button";
import { LyricsCandidate, useLyricsCandidates } from "@/hooks/useLibrary";
import { formatClock } from "@/lib/utils";
import { useState } from "react";
import { PanelMessage, SourcePanel } from "./source-panel";

const PREVIEW_LINES = 2;

interface IProps {
  initialQuery: string;
  onApply: (lyrics: string) => void;
}

export const LyricsPanel = ({ initialQuery, onApply }: IProps) => {
  const [query, setQuery] = useState(initialQuery);
  const { data, isLoading, isError } = useLyricsCandidates(query || null);

  const renderMeta = (candidate: LyricsCandidate): string => {
    const body = candidate.synced_lyrics
      ? "synced"
      : candidate.plain_lyrics
        ? "plain"
        : "";

    return [
      formatClock(candidate.duration),
      body,
      candidate.instrumental ? "instrumental" : "",
    ]
      .filter(Boolean)
      .join(" · ");
  };

  const renderPreview = (candidate: LyricsCandidate): string => {
    const body = candidate.synced_lyrics || candidate.plain_lyrics;

    return body.split("\n").slice(0, PREVIEW_LINES).join(" / ");
  };

  const renderResults = (): React.JSX.Element => {
    if (isLoading) {
      return <PanelMessage value="Searching LRCLIB..." />;
    }

    if (isError) {
      return (
        <PanelMessage value="LRCLIB did not respond. Search again in a moment." />
      );
    }

    if (!data || data.length === 0) {
      return (
        <PanelMessage value="No lyrics match that search. LRCLIB matches best on the exact title." />
      );
    }

    return (
      <ul className="flex flex-col gap-2">
        {data.map((candidate) => (
          <li
            key={candidate.id}
            className="rounded-md border border-border p-3 transition-colors hover:border-muted-foreground/30"
          >
            <Text
              variant="sm"
              className="truncate font-medium"
              value={candidate.track_name}
            />
            <Text
              muted
              className="truncate"
              value={[candidate.artist_name, candidate.album_name]
                .filter(Boolean)
                .join(" — ")}
            />
            <Text mono muted className="mt-1.5" value={renderMeta(candidate)} />
            {!candidate.instrumental && (
              <Text
                mono
                className="mt-2 line-clamp-2 leading-relaxed text-muted-foreground/70"
                value={renderPreview(candidate)}
              />
            )}
            <div className="mt-2.5 flex flex-wrap items-center gap-1">
              {candidate.synced_lyrics && (
                <Button
                  type="button"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={() => onApply(candidate.synced_lyrics)}
                >
                  Use synced
                </Button>
              )}
              {candidate.plain_lyrics && (
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  className="h-7 text-xs"
                  onClick={() => onApply(candidate.plain_lyrics)}
                >
                  Use plain
                </Button>
              )}
              {candidate.instrumental && (
                <span className="text-xs text-muted-foreground">
                  Marked instrumental, no lyrics to copy.
                </span>
              )}
            </div>
          </li>
        ))}
      </ul>
    );
  };

  return (
    <SourcePanel
      eyebrow="Lyrics"
      origin="lrclib"
      originClassName="text-rose-400"
      placeholder="Search artist and title"
      initialQuery={initialQuery}
      onSearch={setQuery}
    >
      {renderResults()}
    </SourcePanel>
  );
};
