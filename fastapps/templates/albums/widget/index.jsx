import React from "react";
import { AppsSDKUIProvider } from "@openai/apps-sdk-ui/components/AppsSDKUIProvider";
import { Button } from "@openai/apps-sdk-ui/components/Button";
import { EmptyMessage } from "@openai/apps-sdk-ui/components/EmptyMessage";
import { useWidgetData, useHostContextCompat, useHostActions } from "fastapps";
import useEmblaCarousel from "embla-carousel-react";
import { ArrowLeft, ArrowRight } from "lucide-react";
import FullscreenViewer from "./FullscreenViewer";
import AlbumCard from "./AlbumCard";
import "./index.css";

function AlbumsCarousel({ albums, onSelect }) {
  const normalizedAlbums = Array.isArray(albums)
    ? albums.filter((album) => album && album.cover)
    : [];
  const hasAlbums = normalizedAlbums.length > 0;
  const [emblaRef, emblaApi] = useEmblaCarousel({
    align: "center",
    loop: false,
    containScroll: "trimSnaps",
    slidesToScroll: "auto",
    dragFree: false,
  });
  const [canPrev, setCanPrev] = React.useState(false);
  const [canNext, setCanNext] = React.useState(false);

  React.useEffect(() => {
    if (!emblaApi) return;
    const updateButtons = () => {
      setCanPrev(emblaApi.canScrollPrev());
      setCanNext(emblaApi.canScrollNext());
    };
    updateButtons();
    emblaApi.on("select", updateButtons);
    emblaApi.on("reInit", updateButtons);
    return () => {
      emblaApi.off("select", updateButtons);
      emblaApi.off("reInit", updateButtons);
    };
  }, [emblaApi]);

  if (!hasAlbums) {
    return (
      <div className="antialiased relative w-full py-5">
        <EmptyMessage>
          No albums available. Provide up to 8 entries for best results.
        </EmptyMessage>
      </div>
    );
  }

  return (
    <div className="antialiased relative w-full text-default py-5 select-none min-h-[260px]">
      <div className="overflow-hidden" ref={emblaRef}>
        <div className="flex gap-5 items-stretch">
          {normalizedAlbums.map((album, i) => (
            <div
              key={album.id}
              className={`shrink-0 ${i === 0 ? "ml-6" : ""} ${i === normalizedAlbums.length - 1 ? "mr-6" : ""}`}
            >
              <AlbumCard album={album} onSelect={onSelect} />
            </div>
          ))}
        </div>
      </div>
      {canPrev && (
        <Button
          aria-label="Previous"
          className="absolute left-2 top-1/2 -translate-y-1/2 z-10"
          variant="outline"
          color="secondary"
          size="sm"
          uniform
          pill
          onClick={() => emblaApi && emblaApi.scrollPrev()}
        >
          <ArrowLeft strokeWidth={1.5} className="h-4 w-4" aria-hidden="true" />
        </Button>
      )}
      {canNext && (
        <Button
          aria-label="Next"
          className="absolute right-2 top-1/2 -translate-y-1/2 z-10"
          variant="outline"
          color="secondary"
          size="sm"
          uniform
          pill
          onClick={() => emblaApi && emblaApi.scrollNext()}
        >
          <ArrowRight strokeWidth={1.5} className="h-4 w-4" aria-hidden="true" />
        </Button>
      )}
    </div>
  );
}

function {ClassName}Inner() {
  const data = useWidgetData() || {};
  const albumsFromData = Array.isArray(data.albums) ? data.albums : [];

  const normalizedAlbums = albumsFromData
    .filter((album) => album && album.cover)
    .map((album) => ({
      ...album,
      photos: Array.isArray(album.photos) ? album.photos : [],
    }));

  const limitedAlbums = normalizedAlbums.slice(0, 8);
  const hostContext = useHostContextCompat();
  const isFullscreen = hostContext.displayMode === "fullscreen";
  const [selectedAlbum, setSelectedAlbum] = React.useState(null);
  const maxHeight = hostContext.maxHeight ?? undefined;
  const hostActions = useHostActions();

  React.useEffect(() => {
    if (!selectedAlbum) {
      return;
    }
    const stillExists = limitedAlbums.some((album) => album.id === selectedAlbum.id);
    if (!stillExists) {
      setSelectedAlbum(null);
      // Graceful no-op if not supported
      hostActions.requestDisplayMode("inline");
    }
  }, [hostActions, limitedAlbums, selectedAlbum]);

  const handleSelectAlbum = (album) => {
    if (!album) return;
    setSelectedAlbum(album);
    hostActions.requestDisplayMode("fullscreen");
  };

  const handleBackToAlbums = () => {
    setSelectedAlbum(null);
    hostActions.requestDisplayMode("inline");
  };

  return (
    <div
      className={
        "relative antialiased w-full text-default " +
        (isFullscreen ? "bg-surface" : "bg-transparent")
      }
      style={{
        maxHeight: isFullscreen ? undefined : maxHeight,
        overflow: isFullscreen ? "visible" : "auto",
      }}
    >
      {!isFullscreen && (
        <AlbumsCarousel albums={limitedAlbums} onSelect={handleSelectAlbum} />
      )}

      {isFullscreen && selectedAlbum && (
        <FullscreenViewer album={selectedAlbum} onBack={handleBackToAlbums} />
      )}
    </div>
  );
}

export default function {ClassName}() {
  return (
    <AppsSDKUIProvider>
      <{ClassName}Inner />
    </AppsSDKUIProvider>
  );
}
