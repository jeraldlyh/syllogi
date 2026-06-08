import { Text } from "@/components/common/text";

interface ISummaryItemProps {
  icon: React.ReactNode;
  label: string;
  value: string | number | React.JSX.Element;
  mono?: boolean;
}

export const SummaryItem = ({
  icon,
  label,
  value,
  mono = false,
}: ISummaryItemProps) => {
  return (
    <div className="grid grid-cols-[auto,1fr] gap-x-2 gap-y-1">
      {icon}
      <p className="text-xs text-muted-foreground">{label}</p>
      <div />
      {typeof value === "string" || typeof value === "number" ? (
        <Text className="truncate" value={String(value)} mono={mono} />
      ) : (
        value
      )}
    </div>
  );
};
