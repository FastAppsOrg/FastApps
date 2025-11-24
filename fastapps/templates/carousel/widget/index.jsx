import React from "react";
import { AppsSDKUIProvider } from "@openai/apps-sdk-ui/components/AppsSDKUIProvider";
import { Button } from "@openai/apps-sdk-ui/components/Button";
import { EmptyMessage } from "@openai/apps-sdk-ui/components/EmptyMessage";
import { useWidgetProps } from "fastapps";
import useEmblaCarousel from "embla-carousel-react";
import { ArrowLeft, ArrowRight } from "lucide-react";
import Card from "./Card";
import "./index.css";

function {ClassName}Inner() {
  const { cards } = useWidgetProps() || {};

  const normalizedCards = Array.isArray(cards) ? cards : [];
  const limitedCards = normalizedCards.slice(0, 8);
  const hasCards = limitedCards.length > 0;

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

  if (!hasCards) {
    return (
      <div className="antialiased relative w-full py-5">
        <EmptyMessage>
          No items to display. Provide up to 8 entries for best results.
        </EmptyMessage>
      </div>
    );
  }

  return (
    <div className="antialiased relative w-full py-5">
      <div className="overflow-hidden" ref={emblaRef}>
        <div className="flex gap-4 items-stretch">
          {limitedCards.map((card, i) => (
            <div
              key={card.id}
              className={`shrink-0 ${i === 0 ? "ml-5" : ""} ${i === limitedCards.length - 1 ? "mr-5" : ""}`}
            >
              <Card card={card} />
            </div>
          ))}
        </div>
      </div>
      {canPrev && (
        <Button
          aria-label="Previous carousel item"
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
          aria-label="Next carousel item"
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

export default function {ClassName}() {
  return (
    <AppsSDKUIProvider>
      <{ClassName}Inner />
    </AppsSDKUIProvider>
  );
}
