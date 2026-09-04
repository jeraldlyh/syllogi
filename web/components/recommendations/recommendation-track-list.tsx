import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Text } from "@/components/common/text";

interface IProps {
  title: string;
  tracks: string[];
  accent: HTMLParagraphElement["className"];
}

export const TrackList = ({ title, tracks, accent }: IProps) => {
  const renderTracks = (): React.JSX.Element => {
    if (tracks.length === 0) {
      return <Text muted value="None" />;
    }

    const uniqueTracks = Array.from(new Set(tracks));

    return (
      <ScrollArea className="h-32 rounded-md border bg-secondary/50 p-2">
        <ul className="flex flex-col gap-1">
          {uniqueTracks.map((track) => (
            <li key={track} className="border-b last:border-0 py-1">
              <Text mono muted value={track} />
            </li>
          ))}
        </ul>
      </ScrollArea>
    );
  };

  return (
    <div>
      <Text
        disableViewport
        className={cn("mb-2 font-semibold", accent)}
        value={title}
      />
      {renderTracks()}
    </div>
  );
};
