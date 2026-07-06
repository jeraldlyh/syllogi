import { Text } from "@/components/common/text";
import { formatDuration } from "@/lib/utils";
import Image from "next/image";
import { ChartBadge } from "./chart-badge";

interface IProps {
  trackName: string;
  albumName?: string;
  duration: number;
  imageUrl: string;
  isExist: boolean;
  isDownloading: boolean;
  children?: React.ReactNode;
}

export const ChartGridCard = ({
  trackName,
  albumName,
  duration,
  imageUrl,
  isExist,
  isDownloading,
  children,
}: IProps): React.JSX.Element => {
  return (
    <div className="group relative flex flex-col overflow-hidden rounded-lg border border-border bg-card transition-colors hover:border-foreground/20">
      <div className="relative aspect-square overflow-hidden bg-secondary">
        {imageUrl ? (
          <Image
            src={imageUrl}
            alt={trackName}
            fill
            className="object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <Text
              className="text-3xl font-bold"
              muted
              value={trackName.charAt(0).toUpperCase()}
            />
          </div>
        )}
        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent p-2.5">
          <Text className="text-xs" value={formatDuration(duration)} />
        </div>
        <div className="absolute top-2 right-2">
          <ChartBadge isExist={isExist} isDownloading={isDownloading} />
        </div>
      </div>
      <div className="flex flex-1 flex-col gap-1 p-3">
        <Text className="truncate font-semibold" value={trackName} />
        {albumName && (
          <Text className="truncate !text-xs" muted value={albumName} />
        )}
        {children && (
          <div className="mt-auto flex items-center justify-between pt-2">
            {children}
          </div>
        )}
      </div>
    </div>
  );
};
