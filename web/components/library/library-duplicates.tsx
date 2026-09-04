import { Text } from "@/components/common/text";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DuplicateGroup,
  deleteLibraryTracks,
  useDuplicateTracks,
} from "@/hooks/useLibrary";
import { CopyCheck, CopyX, Loader2, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { LibraryDuplicateRow } from "./library-duplicate-row";
import { cn } from "@/lib/utils";

const PLACEHOLDER_ROWS = [0, 1, 2, 3, 4];

interface IProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDeleted: () => void;
}

export const LibraryDuplicates = ({
  open,
  onOpenChange,
  onDeleted,
}: IProps) => {
  const { data, isLoading, isError, refresh } = useDuplicateTracks(open);

  const [selected, setSelected] = useState<string[]>([]);
  const [isConfirming, setIsConfirming] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [kept, setKept] = useState<string[]>([]);
  const [hasFailed, setHasFailed] = useState(false);

  const groups = useMemo<DuplicateGroup[]>(() => data ?? [], [data]);
  const duplicates = useMemo(
    () =>
      groups.flatMap((group) => {
        const bestCopy = group.tracks.reduce((best, track) => {
          if (track.size !== best.size) {
            return track.size > best.size ? track : best;
          }

          return track.filled_fields.length > best.filled_fields.length
            ? track
            : best;
        });

        return group.tracks
          .filter((track) => track.path !== bestCopy.path)
          .map((track) => track.path);
      }),
    [groups],
  );

  const handleToggle = (path: string): void =>
    setSelected((previous) =>
      previous.includes(path)
        ? previous.filter((selectedPath) => selectedPath !== path)
        : [...previous, path],
    );

  const handleReset = (): void => {
    setSelected([]);
    setKept([]);
    setHasFailed(false);
  };

  const handleDelete = async (): Promise<void> => {
    setIsConfirming(false);
    setIsDeleting(true);
    setHasFailed(false);

    try {
      const result = await deleteLibraryTracks(selected);

      setSelected([]);
      setKept(result.kept);
      await refresh();
      onDeleted();

      if (result.kept.length === 0) onOpenChange(false);
    } catch {
      setHasFailed(true);
    } finally {
      setIsDeleting(false);
    }
  };

  const renderContent = (): React.JSX.Element => {
    if (isLoading && !data) {
      return (
        <div className="flex flex-col gap-2">
          {PLACEHOLDER_ROWS.map((row) => (
            <Skeleton key={row} className="h-6 w-full" />
          ))}
        </div>
      );
    }

    if (isError) {
      return (
        <div className="flex flex-col items-center gap-2 py-5 text-center">
          <CopyX className="h-8 w-8 text-red-400/40" />
          <Text
            variant="sm"
            className="italic text-red-400"
            value="Could not read the duplicate list"
          />
        </div>
      );
    }

    if (groups.length === 0) {
      return (
        <div className="flex flex-col items-center gap-2 py-5 text-center">
          <CopyCheck className="h-8 w-8 text-muted-foreground/40" />
          <Text variant="sm" muted value="Every track has a single copy" />
        </div>
      );
    }

    return (
      <div className="flex max-h-[50vh] flex-col gap-4 overflow-y-auto">
        {groups.map((group) => {
          const remaining = group.tracks.filter(
            (track) => !selected.includes(track.path),
          );

          return (
            <div key={group.tracks[0].path}>
              <div className="flex items-baseline justify-between pb-1">
                <div className="flex flex-col gap-y-0.5">
                  <Text
                    variant="sm"
                    className="truncate font-medium"
                    value={group.title}
                  />
                  <Text
                    disableViewport
                    muted
                    className="truncate"
                    value={group.artist || "No artist"}
                  />
                </div>
                <Text
                  disableViewport
                  muted
                  value={`${group.tracks.length} copies`}
                />
              </div>
              <ul className="rounded-md border border-border">
                {group.tracks.map((track) => (
                  <LibraryDuplicateRow
                    key={track.path}
                    track={track}
                    isSelected={selected.includes(track.path)}
                    isOnlyCopyLeft={
                      remaining.length === 1 && remaining[0].path === track.path
                    }
                    onToggle={() => handleToggle(track.path)}
                  />
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <>
      <Dialog
        open={open}
        onOpenChange={(next) => {
          if (!next) handleReset();

          onOpenChange(next);
        }}
      >
        <DialogContent
          className={cn({
            "md:max-w-2xl": groups.length > 0,
          })}
        >
          <DialogHeader>
            <DialogTitle>Duplicated tracks</DialogTitle>
            <DialogDescription>
              Tick the copies to delete. Every track keeps at least one file.
            </DialogDescription>
          </DialogHeader>
          {renderContent()}
          {hasFailed && (
            <Text
              variant="sm"
              className="text-red-400"
              value="Could not delete the selected files. Try again in a moment."
            />
          )}
          {kept.length > 0 && (
            <Text
              variant="sm"
              className="text-amber-400"
              value={`${kept.length} file${kept.length === 1 ? "" : "s"} could not be deleted. Check if the library directory is writable.`}
            />
          )}
          {groups.length > 0 && (
            <DialogFooter className="md:justify-between">
              <Button
                variant="outline"
                onClick={() =>
                  setSelected(selected.length > 0 ? [] : duplicates)
                }
                disabled={isDeleting}
              >
                {selected.length > 0 ? "Clear selection" : "Keep the best copy"}
              </Button>
              <Button
                variant="destructive"
                onClick={() => setIsConfirming(true)}
                disabled={selected.length === 0 || isDeleting}
              >
                {isDeleting ? <Loader2 className="animate-spin" /> : <Trash2 />}
                Delete
              </Button>
            </DialogFooter>
          )}
        </DialogContent>
      </Dialog>
      <AlertDialog open={isConfirming} onOpenChange={setIsConfirming}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Delete {selected.length} file{selected.length === 1 ? "" : "s"}?
            </AlertDialogTitle>
            <AlertDialogDescription>
              This removes them from disk for good. The copies left unticked are
              kept.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Keep them</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete}>
              Delete them
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
