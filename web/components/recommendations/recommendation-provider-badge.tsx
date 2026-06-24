import { Badge } from "@/components/ui/badge";
import { RecommendationProvider } from "@/hooks/useRecommendationSessions";
import { cn } from "@/lib/utils";

export const RecommendationProviderBadge = ({
  provider,
}: {
  provider: RecommendationProvider;
}) => {
  return (
    <Badge
      variant="outline"
      className={cn("text-xs whitespace-nowrap w-fit", {
        "border-fuchsia-500/30 bg-fuchsia-500/10 text-fuchsia-400":
          provider === "lastfm",
        "border-sky-500/30 bg-sky-500/10 text-sky-400":
          provider === "listenbrainz",
      })}
    >
      {provider === "lastfm" ? "Last.fm" : "ListenBrainz"}
    </Badge>
  );
};
