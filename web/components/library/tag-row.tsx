import { TAG_FIELD_LABELS, TagField, TagSource } from "@/hooks/useLibrary";
import { cn } from "@/lib/utils";

const SOURCE_LABELS: Record<TagSource, string> = {
  file: "on disk",
  musicbrainz: "musicbrainz",
  lrclib: "lrclib",
  you: "edited",
};

const SOURCE_STYLES: Record<TagSource, string> = {
  file: "text-muted-foreground/70",
  musicbrainz: "text-sky-400",
  lrclib: "text-rose-400",
  you: "text-amber-400",
};

interface IProps {
  field: TagField;
  frame: string;
  source: TagSource;
  isChanged: boolean;
  isFlashing: boolean;
  children: React.ReactNode;
  hint?: React.ReactNode;
}

export const TagRow = ({
  field,
  frame,
  source,
  isChanged,
  isFlashing,
  children,
  hint,
}: IProps) => {
  const label = TAG_FIELD_LABELS[field];
  const showFrame = frame.toUpperCase() !== label.toUpperCase();

  return (
    <div
      className={cn(
        "border-l-2 py-3 pl-4 pr-0.5 transition-colors duration-500 motion-reduce:transition-none",
        isChanged ? "border-l-primary" : "border-l-muted-foreground/30",
        isFlashing && "bg-primary/5",
      )}
    >
      <div className="flex items-baseline justify-between gap-3 pb-2">
        <div className="flex items-baseline gap-2.5">
          <label
            htmlFor={`tag-${field}`}
            className="text-xs font-medium uppercase tracking-widest"
          >
            {label}
          </label>
          {showFrame && (
            <span className="font-mono text-xs text-muted-foreground/60">
              {frame}
            </span>
          )}
        </div>
        <span
          className={cn(
            "shrink-0 font-mono text-xs uppercase tracking-widest",
            SOURCE_STYLES[source],
          )}
        >
          {SOURCE_LABELS[source]}
        </span>
      </div>
      {children}
      {hint}
    </div>
  );
};
