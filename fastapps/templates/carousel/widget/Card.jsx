import React from "react";
import { Button } from "@openai/apps-sdk-ui/components/Button";
import { Image } from "@openai/apps-sdk-ui/components/Image";
import { Star } from "lucide-react";

export default function Card({ card }) {
  if (!card) return null;
  return (
    <div className="min-w-[220px] select-none max-w-[220px] w-[65vw] sm:w-[220px] self-stretch flex flex-col">
      <div className="w-full">
        <Image
          src={card.thumbnail}
          alt={card.name || card.description || "Carousel card"}
          className="w-full aspect-square rounded-2xl object-cover shadow-sm"
        />
      </div>
      <div className="mt-3 flex flex-col flex-1">
        <div className="text-base font-medium truncate line-clamp-1 text-default">
          {card.name}
        </div>
        <div className="text-xs mt-1 flex items-center gap-1 text-secondary">
          <Star className="h-3 w-3" aria-hidden="true" />
          {card.rating?.toFixed ? card.rating.toFixed(1) : card.rating}
          {card.price ? <span>· {card.price}</span> : null}
        </div>
        {card.description ? (
          <div className="text-sm mt-2 flex-auto text-secondary">
            {card.description}
          </div>
        ) : null}
        <div className="mt-5">
          <Button variant="soft" color="secondary" size="sm" pill>
            Learn more
          </Button>
        </div>
      </div>
    </div>
  );
}
