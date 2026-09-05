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
import { deleteEmptyFolders, useEmptyFolders } from "@/hooks/useLibrary";
import { FolderCheck, FolderX, Loader2, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

const PLACEHOLDER_ROWS = [0, 1, 2, 3, 4];

interface IProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDeleted: () => void;
}

export const LibraryEmptyFolders = ({
  open,
  onOpenChange,
  onDeleted,
}: IProps) => {
  const { data, isLoading, isError, refresh } = useEmptyFolders(open);
  const [isConfirming, setIsConfirming] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [kept, setKept] = useState<string[]>([]);
  const [hasFailed, setHasFailed] = useState(false);
  const folders = data ?? [];

  const handleDelete = async (): Promise<void> => {
    setIsConfirming(false);
    setIsDeleting(true);
    setHasFailed(false);

    try {
      const result = await deleteEmptyFolders();

      setKept(result.kept);
      await refresh();
      onDeleted();

      if (result.deleted.length > 0) {
        toast.success(
          `${result.deleted.length} folder${result.deleted.length === 1 ? "" : "s"} deleted`,
          {
            description:
              result.kept.length > 0
                ? `${result.kept.length} folder${result.kept.length === 1 ? "" : "s"} could not be deleted.`
                : "The library no longer holds empty folders.",
          },
        );
      }

      if (result.kept.length === 0) onOpenChange(false);
    } catch {
      setHasFailed(true);
      toast.error("Could not delete the empty folders", {
        description: "Unable to reach the server right now.",
      });
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
          <FolderX className="h-8 w-8 text-red-400/40" />
          <Text
            variant="sm"
            className="italic text-red-400"
            value="Could not read the empty folder list"
          />
        </div>
      );
    }

    if (folders.length === 0) {
      return (
        <div className="flex flex-col items-center gap-2 py-5 text-center">
          <FolderCheck className="h-8 w-8 text-muted-foreground/40" />
          <Text variant="sm" muted value="Every folder holds audio" />
        </div>
      );
    }

    return (
      <ul className="max-h-[50vh] overflow-y-auto rounded-md border border-border">
        {folders.map((folder) => (
          <li
            key={folder.path}
            className="border-b border-border px-3 py-2 font-mono text-xs last:border-b-0"
          >
            <Text variant="xs" muted disableViewport value={folder.path} />
          </li>
        ))}
      </ul>
    );
  };

  return (
    <>
      <Dialog
        open={open}
        onOpenChange={(next) => {
          if (!next) {
            setKept([]);
            setHasFailed(false);
          }

          onOpenChange(next);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Empty folders</DialogTitle>
            <DialogDescription>
              These folders hold no audio anywhere beneath them.
            </DialogDescription>
          </DialogHeader>
          {renderContent()}
          {hasFailed && (
            <Text
              variant="sm"
              className="text-red-400"
              value="Could not delete the empty folders. Try again in a moment."
            />
          )}
          {kept.length > 0 && (
            <Text
              variant="sm"
              className="text-amber-400"
              value={`${kept.length} folder${kept.length === 1 ? "" : "s"} could not be deleted. There might be new audio files since the last scan.`}
            />
          )}
          <DialogFooter>
            <Button
              variant="destructive"
              onClick={() => setIsConfirming(true)}
              disabled={folders.length === 0 || isDeleting}
            >
              {isDeleting ? <Loader2 className="animate-spin" /> : <Trash2 />}
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <AlertDialog open={isConfirming} onOpenChange={setIsConfirming}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Delete {folders.length} folder{folders.length === 1 ? "" : "s"}?
            </AlertDialogTitle>
            <AlertDialogDescription>
              This removes them from disk for good. Any folder that has gained
              audio since the last scan will be left alone.
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
