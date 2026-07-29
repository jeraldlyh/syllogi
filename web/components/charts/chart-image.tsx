import { Text } from "@/components/common/text";

interface IProps {
  imageUrl?: string | null;
  alt: string;
  children?: React.ReactNode;
}

export const ChartImage = ({ imageUrl, alt, children }: IProps) => {
  return (
    <div className="relative min-w-56 min-h-56 aspect-square overflow-hidden bg-secondary">
      {imageUrl ? (
        <img
          src={imageUrl}
          alt={alt}
          loading="lazy"
          decoding="async"
          className="absolute h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
        />
      ) : (
        <div className="flex h-full items-center justify-center">
          <Text
            className="text-3xl font-bold"
            muted
            value={alt.charAt(0).toUpperCase()}
          />
        </div>
      )}
      {children}
    </div>
  );
};
