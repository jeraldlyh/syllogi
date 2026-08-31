import { Text } from "@/components/common/text";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { Search } from "lucide-react";
import { useState } from "react";

interface IProps {
  eyebrow: string;
  origin: string;
  originClassName: string;
  placeholder: string;
  initialQuery: string;
  onSearch: (query: string) => void;
  children: React.ReactNode;
}

export const SourcePanel = ({
  eyebrow,
  origin,
  originClassName,
  placeholder,
  initialQuery,
  onSearch,
  children,
}: IProps) => {
  const [term, setTerm] = useState(initialQuery);

  return (
    <section className="flex h-full min-h-0 flex-col rounded-md border border-border bg-card">
      <header className="flex items-center justify-between gap-2 border-b border-border px-3 py-2.5">
        <h3 className="font-mono text-xs uppercase tracking-widest text-foreground">
          {eyebrow}
        </h3>
        <span
          className={cn(
            "font-mono text-xs uppercase tracking-widest",
            originClassName,
          )}
        >
          {origin}
        </span>
      </header>
      <form
        className="flex gap-2 border-b border-border p-3"
        onSubmit={(event) => {
          event.preventDefault();
          onSearch(term.trim());
        }}
      >
        <Input
          value={term}
          onChange={(event) => setTerm(event.target.value)}
          placeholder={placeholder}
          aria-label={placeholder}
          className="h-8 text-sm"
        />
        <Button
          type="submit"
          size="sm"
          variant="secondary"
          className="h-8 gap-1.5"
        >
          <Search className="h-3.5 w-3.5" />
          Search
        </Button>
      </form>
      <div className="max-h-72 min-h-0 flex-1 overflow-y-auto p-3 lg:max-h-none">
        {children}
      </div>
    </section>
  );
};

export const PanelMessage = ({ value }: { value: string }) => (
  <Text variant="sm" muted className="px-1 py-6 text-center" value={value} />
);
