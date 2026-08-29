import { cn } from "@/lib/utils";

const TEXT_VARIANTS = {
  xs: "text-xs",
  sm: "text-sm",
  base: "text-base",
  lg: "text-lg",
} as const;

export type TextVariant = keyof typeof TEXT_VARIANTS;

interface IProps {
  className?: HTMLParagraphElement["className"];
  value: string;
  variant?: TextVariant;
  mono?: boolean;
  noWrap?: boolean;
  muted?: boolean;
  disableViewport?: boolean;
}
export const Text = ({
  className,
  value,
  variant = "xs",
  mono,
  noWrap,
  muted,
  disableViewport,
}: IProps) => {
  return (
    <p
      className={cn(
        TEXT_VARIANTS[variant],
        {
          "font-mono": mono,
          "text-foreground": className && !className.includes("text-"),
          "whitespace-nowrap": noWrap,
          "text-muted-foreground": muted,
          "md:text-sm": variant === "xs" && !disableViewport,
        },
        className,
      )}
    >
      {value}
    </p>
  );
};
