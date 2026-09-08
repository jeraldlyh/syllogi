import { Text } from "@/components/common/text";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useLogs } from "@/hooks/useLogs";
import { cn } from "@/lib/utils";
import { ScrollText } from "lucide-react";
import { useEffect, useRef, useState } from "react";

const LEVELS = ["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"];

const LEVEL_COLOURS: Record<string, string> = {
  DEBUG: "text-muted-foreground",
  INFO: "text-sky-400",
  WARNING: "text-amber-400",
  ERROR: "text-red-400",
  CRITICAL: "text-red-400",
};

export const Logs = () => {
  const { data, isError, isLoading } = useLogs();
  const [level, setLevel] = useState<string>("ALL");
  const [search, setSearch] = useState<string>("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState<number>();

  useEffect(() => {
    const update = (): void => {
      const top = scrollRef.current?.getBoundingClientRect().top ?? 0;

      setHeight(window.innerHeight - top - 48);
    };

    update();
    window.addEventListener("resize", update);

    return () => window.removeEventListener("resize", update);
  }, []);

  const renderContent = (): React.JSX.Element => {
    if (isLoading) {
      return (
        <div className="flex h-full items-center justify-center">
          <Text className="text-muted-foreground italic" value="Loading..." />
        </div>
      );
    }

    if (isError) {
      return (
        <div className="flex h-full items-center justify-center">
          <Text
            className="text-muted-foreground italic text-red-400"
            value="Failed to load logs"
          />
        </div>
      );
    }

    const query = search.trim().toLowerCase();
    const logs = (data ?? [])
      .filter((log) => level === "ALL" || log.level === level)
      .filter(
        (log) =>
          !query ||
          log.message.toLowerCase().includes(query) ||
          log.module.toLowerCase().includes(query),
      )
      .reverse();

    if (logs.length === 0) {
      return (
        <div className="flex h-full flex-col items-center justify-center gap-2">
          <ScrollText className="h-8 w-8 text-muted-foreground/40" />
          <Text variant="sm" muted className="italic" value="No logs to show" />
        </div>
      );
    }

    return (
      <>
        {logs.map((log, index) => (
          <div
            key={`${log.timestamp}-${index}`}
            className="flex gap-3 border-b border-border/50 px-3 py-1.5 last:border-b-0"
          >
            <Text
              muted
              mono
              noWrap
              disableViewport
              value={new Date(log.timestamp).toLocaleTimeString()}
            />
            <Text
              mono
              noWrap
              disableViewport
              className={cn("w-16", LEVEL_COLOURS[log.level])}
              value={log.level}
            />
            <Text
              muted
              mono
              noWrap
              disableViewport
              className="hidden w-32 truncate sm:block"
              value={log.module}
            />
            <p className="font-mono text-xs whitespace-pre-wrap break-all">
              {log.message}
            </p>
          </div>
        ))}
      </>
    );
  };

  return (
    <Card>
      <CardHeader className="flex flex-col gap-3 pb-3 sm:flex-row sm:items-center sm:justify-between">
        <CardTitle className="text-base font-medium text-foreground">
          Logs
        </CardTitle>
        <div className="flex items-center gap-2">
          <Input
            placeholder="Search logs..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            className="h-9 w-full sm:w-56"
          />
          <Select value={level} onValueChange={setLevel}>
            <SelectTrigger className="h-9 w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {LEVELS.map((value) => (
                <SelectItem key={value} value={value}>
                  {value}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        <div
          ref={scrollRef}
          style={height ? { height } : undefined}
          className="h-[32rem] overflow-auto rounded-md border border-border"
        >
          {renderContent()}
        </div>
      </CardContent>
    </Card>
  );
};
