import React from "react";
import { Image } from "@openai/apps-sdk-ui/components/Image";

export default function FilmStrip({ album, selectedIndex, onSelect }) {
  if (!album?.photos?.length) {
    return null;
  }

  return (
    <div className="h-full w-full overflow-auto flex flex-col items-center justify-center p-5 space-y-5">
      {album.photos.map((photo, idx) => (
        <button
          key={photo.id}
          type="button"
          onClick={() => onSelect?.(idx)}
          className={
            "block w-full p-[1px] pointer-events-auto rounded-xl cursor-pointer border transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-default " +
            (idx === selectedIndex
              ? "border-strong bg-primary-soft-alpha"
              : "border-default hover:border-strong")
          }
          aria-pressed={idx === selectedIndex}
          aria-label={`View ${photo.title || `photo ${idx + 1}`}`}
        >
          <div className="aspect-[5/3] rounded-lg overflow-hidden w-full">
            <Image
              src={photo.url}
              alt={photo.title || `Photo ${idx + 1}`}
              className="h-full w-full object-cover"
              loading="lazy"
            />
          </div>
        </button>
      ))}
    </div>
  );
}
