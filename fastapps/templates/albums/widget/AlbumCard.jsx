import React from "react";
import { Button } from "@openai/apps-sdk-ui/components/Button";
import { Image } from "@openai/apps-sdk-ui/components/Image";

function AlbumCard({ album, onSelect }) {
  if (!album) return null;

  const photoCount = Array.isArray(album.photos) ? album.photos.length : 0;
  const photoSummary = photoCount > 0 ? `${photoCount} photos` : "View album";
  const title = album.title || "Album";

  return (
    <Button
      type="button"
      variant="ghost"
      color="secondary"
      className="group relative cursor-pointer flex-shrink-0 w-[272px] bg-transparent text-left rounded-3xl p-0 focus-visible:ring-2 focus-visible:ring-default flex-col items-start"
      style={{ height: "auto" }}
      onClick={() => onSelect?.(album)}
      aria-label={`Open ${title}`}
      block
    >
      <div className="w-full overflow-hidden rounded-2xl shadow-card bg-surface">
        <div className="aspect-[4/3] w-full overflow-hidden">
          <Image
            src={album.cover}
            alt={title}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        </div>
      </div>
      <div className="pt-3 px-1.5 w-full">
        <div className="text-base font-medium truncate text-foreground">
          {title}
        </div>
        <div className="text-sm text-secondary mt-0.5">{photoSummary}</div>
      </div>
    </Button>
  );
}

export default AlbumCard;
