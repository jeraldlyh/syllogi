import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  AudioTags,
  LibraryTrackDetail,
  RecordingMatch,
  TagField,
  TagSource,
} from "@/hooks/useLibrary";
import { api } from "@/lib/api";
import { formatClock, formatSize, removeFileExtension } from "@/lib/utils";
import { ExternalLink, Loader2, Save, Undo2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { LyricsPanel } from "./lyrics-panel";
import { RecordingPanel } from "./recording-panel";
import { TagRow } from "./tag-row";

interface Draft {
  title: string;
  artist: string;
  album: string;
  date: string;
  genresText: string;
  lyrics: string;
  musicbrainz_id: string;
}

const EDITABLE_FIELDS: TagField[] = [
  "title",
  "artist",
  "album",
  "date",
  "genres",
  "musicbrainz_id",
  "lyrics",
];

const TEXT_FIELDS: {
  field: TagField;
  key: keyof Draft;
  placeholder: string;
  className?: string;
}[] = [
  { field: "title", key: "title", placeholder: "Untitled" },
  { field: "artist", key: "artist", placeholder: "Unknown artist" },
  { field: "album", key: "album", placeholder: "No album" },
  {
    field: "date",
    key: "date",
    placeholder: "2020 or 2020-03-20",
    className: "font-mono",
  },
  {
    field: "genres",
    key: "genresText",
    placeholder: "Separate genres with commas",
  },
  {
    field: "musicbrainz_id",
    key: "musicbrainz_id",
    placeholder: "Pick a recording, or paste an MBID",
    className: "font-mono text-xs",
  },
];

const LRC_LINE_PREFIX = "[";
const FLASH_MS = 1000;

const defaultSources = (): Record<TagField, TagSource> =>
  EDITABLE_FIELDS.reduce(
    (accumulator, field) => ({ ...accumulator, [field]: "file" }),
    {} as Record<TagField, TagSource>,
  );

const toDraft = (tags: AudioTags): Draft => ({
  title: tags.title,
  artist: tags.artist,
  album: tags.album,
  date: tags.date,
  genresText: tags.genres.join(", "),
  lyrics: tags.lyrics,
  musicbrainz_id: tags.musicbrainz_id,
});

interface IProps {
  detail: LibraryTrackDetail;
  onSaved: () => void;
  onDirtyChange: (isDirty: boolean) => void;
}

export const EditorBody = ({ detail, onSaved, onDirtyChange }: IProps) => {
  const [draft, setDraft] = useState<Draft>(() => toDraft(detail.tags));
  const [baseline, setBaseline] = useState<Draft>(() => toDraft(detail.tags));
  const [sources, setSources] = useState(defaultSources);
  const [flashing, setFlashing] = useState<TagField[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const flashTimer = useRef<NodeJS.Timeout | undefined>(undefined);

  const isChanged = (key: keyof Draft): boolean => draft[key] !== baseline[key];
  const isDirty = EDITABLE_FIELDS.some((field) =>
    field === "genres"
      ? isChanged("genresText")
      : isChanged(field as keyof Draft),
  );
  const searchQuery = [draft.artist, draft.title].filter(Boolean).join(" ");

  useEffect(() => {
    return () => {
      if (flashTimer.current) clearTimeout(flashTimer.current);
    };
  }, []);

  useEffect(() => {
    onDirtyChange(isDirty);
  }, [isDirty, onDirtyChange]);

  const flash = (fields: TagField[]): void => {
    if (flashTimer.current) clearTimeout(flashTimer.current);

    setFlashing(fields);
    flashTimer.current = setTimeout(() => setFlashing([]), FLASH_MS);
  };

  const setField = (key: keyof Draft, value: string, field: TagField): void => {
    setDraft((previous) => ({ ...previous, [key]: value }));
    setSources((previous) => ({
      ...previous,
      [field]: value === baseline[key] ? "file" : "you",
    }));
  };

  const applyRecording = (match: RecordingMatch): void => {
    const applied: TagField[] = [
      "title",
      "artist",
      "album",
      "date",
      "musicbrainz_id",
    ];

    setDraft((previous) => ({
      ...previous,
      title: match.title || previous.title,
      artist: match.artist_name || previous.artist,
      album: match.album_name || previous.album,
      date: match.release_date || match.year || previous.date,
      genresText: match.genres.length
        ? match.genres.join(", ")
        : previous.genresText,
      musicbrainz_id: match.id,
    }));

    if (match.genres.length) applied.push("genres");

    setSources((previous) => ({
      ...previous,
      ...applied.reduce(
        (accumulator, field) => ({ ...accumulator, [field]: "musicbrainz" }),
        {},
      ),
    }));
    flash(applied);
    toast.success("Recording applied", {
      description:
        "Review the fields, then save changes to write them to disk.",
    });
  };

  const applyLyrics = (lyrics: string): void => {
    setDraft((previous) => ({ ...previous, lyrics }));
    setSources((previous) => ({ ...previous, lyrics: "lrclib" }));
    flash(["lyrics"]);
    toast.success("Lyrics applied", {
      description: "Save changes to write them to the file.",
    });
  };

  const discard = (): void => {
    setDraft(baseline);
    setSources(defaultSources);
    flash([]);
  };

  const save = async (): Promise<void> => {
    setIsSaving(true);

    const response = await api<LibraryTrackDetail>({
      method: "PUT",
      service: "library",
      path: "track",
      body: {
        path: detail.path,
        title: draft.title,
        artist: draft.artist,
        album: draft.album,
        date: draft.date,
        genres: draft.genresText
          .split(",")
          .map((genre) => genre.trim())
          .filter(Boolean),
        lyrics: draft.lyrics,
        musicbrainz_id: draft.musicbrainz_id,
      },
    });

    setIsSaving(false);

    if (response.statusCode !== 200 || !response.data) {
      toast.error("Could not save tags", {
        description: response.error?.message || detail.filename,
      });
      return;
    }

    const saved = toDraft(response.data.tags);

    setDraft(saved);
    setBaseline(saved);
    setSources(defaultSources);
    onSaved();
    toast.success("Tags saved", {
      description: `${detail.filename} rewritten on disk.`,
    });
  };

  const summariseLyrics = (lyrics: string): string => {
    const lines = lyrics.split("\n");
    const written = lines.filter((line) => line.trim()).length;

    if (written === 0) return "No lyrics on this file";

    const isSynced = lines.some((line) =>
      line.trim().startsWith(LRC_LINE_PREFIX),
    );

    return `${written} lines | ${isSynced ? "synced" : "plain"}`;
  };

  return (
    <div className="flex flex-col">
      <header className="flex flex-col gap-3 border-b border-border px-4 pb-4 pt-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h2 className="truncate text-xl font-semibold tracking-tight">
            {draft.title || removeFileExtension(detail.filename)}
          </h2>
          <p className="mt-1 truncate font-mono text-xs text-muted-foreground">
            {detail.path}
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            <Badge
              variant="outline"
              className="border-border font-mono text-xs uppercase tracking-wider"
            >
              {detail.format}
            </Badge>
            <span className="font-mono text-xs text-muted-foreground">
              {formatClock(detail.duration)} | {formatSize(detail.size)}
            </span>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {isDirty && (
            <span className="font-mono text-xs uppercase tracking-widest text-amber-400">
              Unsaved
            </span>
          )}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="gap-1.5"
            disabled={!isDirty || isSaving}
            onClick={discard}
          >
            <Undo2 className="h-3.5 w-3.5" />
            Discard
          </Button>
          <Button
            type="button"
            size="sm"
            className="gap-1.5"
            disabled={!isDirty || isSaving}
            onClick={save}
          >
            {isSaving ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Save className="h-3.5 w-3.5" />
            )}
            Save changes
          </Button>
        </div>
      </header>
      <div className="flex flex-col gap-5 px-4 pb-8 pt-4 lg:grid lg:h-editor lg:grid-cols-2 lg:gap-6">
        <div className="min-h-0 lg:overflow-y-auto lg:pr-2">
          {TEXT_FIELDS.map(({ field, key, placeholder, className }) => (
            <TagRow
              key={field}
              field={field}
              frame={detail.frames[field]}
              source={sources[field]}
              isChanged={isChanged(key)}
              isFlashing={flashing.includes(field)}
              hint={
                field === "musicbrainz_id" && draft.musicbrainz_id ? (
                  <a
                    href={`https://musicbrainz.org/recording/${draft.musicbrainz_id}`}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-2 inline-flex items-center gap-1 text-xs text-sky-400 underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  >
                    Open on MusicBrainz
                    <ExternalLink className="h-3 w-3" />
                  </a>
                ) : undefined
              }
            >
              <Input
                id={`tag-${field}`}
                value={draft[key]}
                onChange={(event) => setField(key, event.target.value, field)}
                placeholder={placeholder}
                className={className}
              />
            </TagRow>
          ))}
          <TagRow
            field="lyrics"
            frame={detail.frames.lyrics}
            source={sources.lyrics}
            isChanged={isChanged("lyrics")}
            isFlashing={flashing.includes("lyrics")}
            hint={
              <p className="mt-2 font-mono text-xs text-muted-foreground">
                {summariseLyrics(draft.lyrics)}
              </p>
            }
          >
            <Textarea
              id="tag-lyrics"
              value={draft.lyrics}
              onChange={(event) =>
                setField("lyrics", event.target.value, "lyrics")
              }
              placeholder="Paste lyrics, or take a match from LRCLIB"
              className="min-h-48 resize-y font-mono text-xs leading-relaxed"
            />
          </TagRow>
        </div>
        <div className="flex min-h-0 w-full flex-col gap-4">
          <div className="flex min-h-0 flex-col lg:flex-1">
            <RecordingPanel
              initialQuery={searchQuery}
              linkedId={draft.musicbrainz_id}
              onApply={applyRecording}
            />
          </div>
          <div className="flex min-h-0 flex-col lg:flex-1">
            <LyricsPanel initialQuery={searchQuery} onApply={applyLyrics} />
          </div>
        </div>
      </div>
    </div>
  );
};
