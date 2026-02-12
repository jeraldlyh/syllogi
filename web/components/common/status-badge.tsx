import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface IProps {
  status: boolean | undefined;
}
export const StatusBadge = ({ status }: IProps) => {
  const getLabel = (): string => {
    if (status === undefined) return "Loading";

    if (!status) return "Failed";
    return "Success";
  };

  return (
    <Badge
      variant="outline"
      className={cn({
        "border-emerald-500/30 bg-emerald-500/10 text-emerald-400": status,
        "border-amber-500/30 bg-amber-500/10 text-amber-400":
          status === undefined,
        "border-red-500/30 bg-red-500/10 text-red-400": !status,
      })}
    >
      {getLabel()}
    </Badge>
  );
};
