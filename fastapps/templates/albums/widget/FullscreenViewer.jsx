import React from "react";
import { Button } from "@openai/apps-sdk-ui/components/Button";
import { ArrowLeft } from "lucide-react";
import { useMaxHeight } from "fastapps";
import FilmStrip from "./FilmStrip";

export default function FullscreenViewer({ album, onBack }) {
  const maxHeight = useMaxHeight() ?? undefined;
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
    <div
      className="relative w-full h-full bg-white"
      style={{
        maxHeight,
        height: maxHeight,
      }}
    >
      {/* Back button */}
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

      <div className="absolute inset-0 flex flex-row overflow-hidden">
        {/* Film strip */}
        <div className="hidden md:block absolute pointer-events-none z-10 left-0 top-0 bottom-0 w-40">
          <FilmStrip album={{ ...album, photos }} selectedIndex={index} onSelect={setIndex} />
        </div>
        {/* Main photo */}
        <div className="flex-1 min-w-0 px-40 py-10 relative flex items-center justify-center">
          <div className="relative w-full h-full">
            {photo ? (
              <img
                src={photo.url}
                alt={photo.title || album.title || "Photo"}
                className="absolute inset-0 m-auto rounded-3xl shadow-sm border border-black/10 max-w-full max-h-full object-contain"
              />
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
