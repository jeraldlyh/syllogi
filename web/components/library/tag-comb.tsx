import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { TAG_FIELD_LABELS, TAG_FIELDS, TagField } from "@/hooks/useLibrary";
import { cn } from "@/lib/utils";

interface IProps {
  filled: TagField[];
  className?: string;
}

export const TagComb = ({ filled, className }: IProps) => {
  const present = new Set(filled);
  const missing = TAG_FIELDS.filter((field) => !present.has(field));
  const label =
    missing.length === 0
      ? "All 7 tags present"
      : `${filled.length} of 7 tags present. Missing ${missing
          .map((field) => TAG_FIELD_LABELS[field].toLowerCase())
          .join(", ")}`;

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          role="img"
          aria-label={label}
          className={cn("inline-flex items-end gap-0.5", className)}
        >
          {TAG_FIELDS.map((field) => (
            <span
              key={field}
              className={cn(
                "w-0.5 rounded-full transition-[height,background-color] duration-300 motion-reduce:transition-none",
                present.has(field)
                  ? "h-4 bg-primary"
                  : "h-2 bg-muted-foreground/25",
              )}
            />
          ))}
        </span>
      </TooltipTrigger>
      <TooltipContent side="left" className="font-mono text-xs">
        {label}
      </TooltipContent>
    </Tooltip>
  );
};
