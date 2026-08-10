import { Text } from "@/components/common/text";
import { ChartImage } from "./chart-image";

interface IProps {
  name: string;
  imageUrl: string | null;
  onClick: () => void;
}

export const ChartSearchArtistCard = ({
  name,
  imageUrl,
  onClick,
}: IProps): React.JSX.Element => {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group relative flex flex-col overflow-hidden rounded-lg border border-border bg-card text-left transition-colors hover:border-foreground/20"
    >
      <ChartImage imageUrl={imageUrl} alt={name} />
      <div className="flex flex-1 flex-col gap-1 p-3">
        <Text className="truncate font-semibold" value={name} />
        <Text className="text-xs text-muted-foreground" value="Artist" />
      </div>
    </button>
  );
};
