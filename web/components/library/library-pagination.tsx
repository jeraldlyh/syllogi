import { Text } from "@/components/common/text";
import { LIBRARY_PAGE_SIZE } from "@/hooks/useLibrary";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "../ui/button";

export const LibraryPagination = ({
  page,
  shown,
  matched,
  onChange,
}: {
  page: number;
  shown: number;
  matched: number;
  onChange: (page: number) => void;
}) => {
  const first = page * LIBRARY_PAGE_SIZE + 1;
  const last = page * LIBRARY_PAGE_SIZE + shown;
  const pageCount = Math.max(1, Math.ceil(matched / LIBRARY_PAGE_SIZE));

  return (
    <nav
      aria-label="pages"
      className="grid grid-cols-1 place-items-center md:flex md:flex-wrap items-center md:justify-between gap-3 mt-3"
    >
      <Text mono muted value={`${first}–${last} of ${matched} files`} />
      {pageCount > 1 && (
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="gap-1"
            disabled={page === 0}
            onClick={() => onChange(page - 1)}
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </Button>
          <Text mono muted value={`${page + 1} / ${pageCount}`} />
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="gap-1"
            disabled={page >= pageCount - 1}
            onClick={() => onChange(page + 1)}
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </nav>
  );
};
