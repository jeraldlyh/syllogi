import { Text } from "@/components/common/text";
import { cn } from "@/lib/utils";
import { useState } from "react";

interface IProps {
  imageUrl?: string | null;
  alt: string;
  className?: string;
  textClassName?: string;
  children?: React.ReactNode;
}

export const ChartImage = ({
  imageUrl,
  alt,
  className,
  textClassName,
  children,
}: IProps) => {
  const [failedUrl, setFailedUrl] = useState<string | null>(null);
  const showImage = !!imageUrl && failedUrl !== imageUrl;

  return (
    <div
      className={cn(
        "relative aspect-square overflow-hidden bg-secondary",
        className,
      )}
    >
      {showImage ? (
        <img
          src={imageUrl}
          alt={alt}
          loading="lazy"
          decoding="async"
          onError={() => setFailedUrl(imageUrl ?? null)}
          className="absolute h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
        />
      ) : (
        <div className="flex h-full items-center justify-center">
          <Text
            className={cn("text-3xl font-bold", textClassName)}
            muted
            value={alt.charAt(0).toUpperCase()}
          />
        </div>
      )}
      {children}
    </div>
  );
};
