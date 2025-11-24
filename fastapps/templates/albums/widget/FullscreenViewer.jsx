import React from "react";
import { Button } from "@openai/apps-sdk-ui/components/Button";
import { Image } from "@openai/apps-sdk-ui/components/Image";
import { ArrowLeft } from "lucide-react";
import FilmStrip from "./FilmStrip";

export default function FullscreenViewer({ album, onBack }) {
  const [index, setIndex] = React.useState(0);
  const photos = Array.isArray(album?.photos) ? album.photos : [];

  React.useEffect(() => {
    setIndex(0);
  }, [album?.id]);

  React.useEffect(() => {
    if (index > photos.length - 1) {
      setIndex(0);
    }
  }, [index, photos.length]);

  if (!album) {
    return null;
  }

  const photo = photos[index];

  return (
    <div className="relative w-full bg-surface">
      {onBack && (
        <Button
          aria-label="Back to albums"
          className="absolute left-4 top-4 z-20 shadow-lg"
          variant="outline"
          color="secondary"
          size="md"
          uniform
          pill
          onClick={onBack}
        >
          <ArrowLeft strokeWidth={1.5} className="h-4 w-4" aria-hidden="true" />
        </Button>
      )}

      <div className="flex flex-col md:flex-row items-stretch gap-6 md:gap-10 px-4 sm:px-6 md:px-10 py-8 md:py-12">
        <div className="hidden md:flex w-40 shrink-0">
          <FilmStrip
            album={{ ...album, photos }}
            selectedIndex={index}
            onSelect={setIndex}
          />
        </div>

        <div className="flex-1 min-w-0 flex items-center justify-center">
          {photo ? (
            <Image
              src={photo.url}
              alt={photo.title || album.title || "Photo"}
              className="w-full max-h-[70vh] rounded-3xl shadow-sm border border-default object-contain"
            />
          ) : null}
        </div>
      </div>
    </div>
  );
}
