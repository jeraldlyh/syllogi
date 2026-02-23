import { Badge } from "@/components/ui/badge";
import { SyncSession } from "@/hooks/useSyncSessions";
import { cn } from "@/lib/utils";

interface IProps {
  status: SyncSession["status"];
}
export const StatusBadge = ({ status }: IProps) => {
  const formatLabel = (): string => {
    switch (status) {
      case "pending":
        return "Pending";
      case "in_progress":
        return "In Progress";
      case "completed":
        return "Completed";
      case "failed":
        return "Failed";
      default:
        return "Unknown";
    }
  };

  return (
    <Badge
      variant="outline"
      className={cn({
        "border-emerald-500/30 bg-emerald-500/10 text-emerald-400":
          status === "completed",
        "border-amber-500/30 bg-amber-500/10 text-amber-400":
          status === "in_progress",
        "border-red-500/30 bg-red-500/10 text-red-400": status === "failed",
        "border-muted/30 bg-muted/10 text-muted-foreground":
          status === "pending",
      })}
    >
      {formatLabel()}
    </Badge>
  );
};
