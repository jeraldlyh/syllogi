import { cn } from "@/lib/utils";

interface IProps {
  className?: HTMLParagraphElement["className"];
  value: string;
  mono?: boolean;
}
export const Text = ({ className, value, mono }: IProps) => {
  return (
    <p
      className={cn("text-sm font-medium", className, {
        "font-mono text-xs": mono,
        "text-foreground": className && !className.includes("text-"),
      })}
    >
      {value}
    </p>
  );
};
