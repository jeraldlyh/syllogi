import { cn } from "@/lib/utils";

interface IProps {
  className?: HTMLParagraphElement["className"];
  value: string;
  mono?: boolean;
  noWrap?: boolean;
  muted?: boolean;
}
export const Text = ({ className, value, mono, noWrap, muted }: IProps) => {
  return (
    <p
      className={cn(
        "text-xs md:text-sm font-medium",
        {
          "font-mono": mono,
          "text-foreground": className && !className.includes("text-"),
          "text-nowrap": noWrap,
          "text-muted-foreground": muted,
        },
        className,
      )}
    >
      {value}
    </p>
  );
};
