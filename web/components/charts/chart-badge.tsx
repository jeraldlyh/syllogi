import { cn } from "@/lib/utils";
import { Badge } from "../ui/badge";

export const ChartBadge = ({
  isExist,
  isDownloading,
}: {
  isExist: boolean;
  isDownloading: boolean;
}): React.JSX.Element | undefined => {
  const style = "w-fit text-xs text-nowrap font-medium px-1.5 py-0";

  if (isDownloading) {
    return (
      <Badge
        variant="outline"
        className={cn(
          style,
          "border-amber-500/30 bg-amber-500/10 text-amber-400",
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
          "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
        )}
      >
        In Library
      </Badge>
    );
  }
};
