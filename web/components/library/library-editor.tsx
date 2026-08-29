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
import { Drawer, DrawerContent, DrawerTitle } from "@/components/ui/drawer";
import { Skeleton } from "@/components/ui/skeleton";
import { useLibraryTrack } from "@/hooks/useLibrary";
import { useState } from "react";
import { EditorBody } from "./library-editor-body";

const PLACEHOLDER_ROWS = [0, 1, 2, 3, 4];

const EditorSkeleton = () => (
  <div className="flex flex-col gap-4 px-4 pb-8">
    <Skeleton className="h-8 w-2/3" />
    <Skeleton className="h-4 w-1/2" />
    <div className="flex flex-col gap-3 pt-4">
      {PLACEHOLDER_ROWS.map((row) => (
        <Skeleton key={row} className="h-16 w-full" />
      ))}
    </div>
  </div>
);

interface IProps {
  path: string | null;
  onClose: () => void;
  onSaved: () => void;
}

export const LibraryEditor = ({ path, onClose, onSaved }: IProps) => {
  const { data, isLoading, isError } = useLibraryTrack(path);
  const [isDirty, setIsDirty] = useState(false);
  const [isConfirmingClose, setIsConfirmingClose] = useState(false);

  const close = (): void => {
    setIsDirty(false);
    setIsConfirmingClose(false);
    onClose();
  };

  const renderContent = (): React.JSX.Element => {
    if (isLoading || (!data && !isError)) return <EditorSkeleton />;

    if (isError || !data) {
      return (
        <div className="flex flex-col items-center gap-2 px-4 py-16 text-center">
          <Text
            variant="lg"
            className="font-semibold"
            value="This file could not be read"
          />
          <Text
            variant="sm"
            muted
            value="It may have been moved or renamed since the last scan. Refresh the list to see what is on disk now."
          />
        </div>
      );
    }

    return (
      <EditorBody
        key={data.path}
        detail={data}
        onSaved={onSaved}
        onDirtyChange={setIsDirty}
      />
    );
  };

  return (
    <>
      <Drawer
        open={Boolean(path)}
        onOpenChange={(open) => {
          if (open) return;

          if (isDirty) {
            setIsConfirmingClose(true);
            return;
          }
          close();
        }}
      >
        <DrawerContent>
          <DrawerTitle className="sr-only">
            {path ? `Edit tags for ${path}` : "Edit tags"}
          </DrawerTitle>
          {renderContent()}
        </DrawerContent>
      </Drawer>
      <AlertDialog open={isConfirmingClose} onOpenChange={setIsConfirmingClose}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Discard unsaved changes?</AlertDialogTitle>
            <AlertDialogDescription>
              The tags you changed have not been written to the file. Closing
              now leaves it exactly as it is on disk.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Keep editing</AlertDialogCancel>
            <AlertDialogAction onClick={close}>
              Discard changes
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
