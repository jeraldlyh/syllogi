import { Badge } from "@/components/ui/badge";
import { LibraryFormat } from "@/hooks/useLibrary";
import { cn } from "@/lib/utils";

const FORMAT_CLASSES: Record<LibraryFormat, string> = {
  flac: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
  mp3: "border-sky-500/30 bg-sky-500/10 text-sky-400",
  opus: "border-violet-500/30 bg-violet-500/10 text-violet-400",
};

export const TrackFormatBadge = ({
  format,
  className,
}: {
  format: LibraryFormat;
  className?: string;
}) => (
  <Badge
    variant="outline"
    className={cn(
      "font-mono uppercase tracking-wider",
      FORMAT_CLASSES[format],
      className,
    )}
  >
    {format}
  </Badge>
);
