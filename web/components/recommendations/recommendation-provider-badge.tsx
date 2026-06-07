import { cn, capitaliseFirstLetter } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { RecommendationProvider } from "@/hooks/useRecommendationSessions";

export const RecommendationProviderBadge = ({
  provider,
}: {
  provider: RecommendationProvider;
}) => {
  return (
    <Badge
      variant="outline"
      className={cn("text-xs whitespace-nowrap w-fit", {
        "border-orange-500/30 bg-orange-500/10 text-orange-400":
          provider === "lastfm",
      })}
    >
      {provider === "lastfm" ? "Last.fm" : capitaliseFirstLetter(provider)}
    </Badge>
  );
};
