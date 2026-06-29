import { cn } from "@/lib/utils";
import { Badge } from "../ui/badge";

export const ChartBadge = ({
  isExist,
  isDownloading,
}: {
  isExist: boolean;
  isDownloading: boolean;
}): React.JSX.Element | undefined => {
  const style = "text-xs whitespace-nowrap px-1.5 py-0 w-fit";

  if (isDownloading) {
    return (
      <Badge
        variant="outline"
        className={cn(
          style,
          "border-amber-500/50 bg-amber-500/80 text-amber-100",
        )}
      >
        Downloading
      </Badge>
    );
  }

  if (isExist) {
    return (
      <Badge
        variant="outline"
        className={cn(
          style,
          "border-emerald-500/50 bg-emerald-500/80 text-emerald-100",
        )}
      >
        In Library
      </Badge>
    );
  }
};
