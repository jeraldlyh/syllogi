import { cn, convertSnakeCaseToTitleCase } from "@/lib/utils";
import { Badge } from "../ui/badge";
import { RecommendationStrategy } from "@/hooks/useRecommendationSessions";

export const RecommendationStrategyBadge = ({
  strategy,
}: {
  strategy: RecommendationStrategy;
}) => {
  return (
    <Badge
      variant="outline"
      className={cn("text-xs whitespace-nowrap w-fit", {
        "border-blue-500/30 text-blue-400": strategy === "recent_tracks",
        "border-purple-500/30 text-purple-400": strategy === "top_tracks",
        "border-yellow-500/30 text-yellow-400": strategy === "blend",
      })}
    >
      {convertSnakeCaseToTitleCase(strategy)}
    </Badge>
  );
};
