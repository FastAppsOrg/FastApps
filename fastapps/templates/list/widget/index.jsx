import React from "react";
import { AppsSDKUIProvider } from "@openai/apps-sdk-ui/components/AppsSDKUIProvider";
import { Button } from "@openai/apps-sdk-ui/components/Button";
import { EmptyMessage } from "@openai/apps-sdk-ui/components/EmptyMessage";
import { Image } from "@openai/apps-sdk-ui/components/Image";
import { useWidgetProps } from "fastapps";
import { PlusCircle, Star } from "lucide-react";
import "./index.css";

function {ClassName}Inner() {
  const { title, description, items } = useWidgetProps() || {};
  const normalizedItems = Array.isArray(items) ? items.slice(0, 7) : [];
  const hasItems = normalizedItems.length > 0;

  return (
    <div className="antialiased w-full text-foreground px-4 pb-2 border border-default rounded-3xl overflow-hidden bg-surface shadow-card">
      <div className="max-w-full">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4 border-b border-subtle py-4">
          <div className="flex flex-col gap-1">
            <div className="text-base sm:text-xl font-medium heading-md">
              {title || "List Title"}
            </div>
            <div className="text-sm text-secondary">
              {description || "A list of items"}
            </div>
          </div>
          <div className="sm:ml-auto">
            <Button variant="outline" color="secondary" size="sm" pill>
              Save list
            </Button>
          </div>
        </div>
        <ol className="min-w-full text-sm flex flex-col">
          {normalizedItems.map((item, i) => {
            const rank = i + 1;
            const infoText = item?.info || "–";
            return (
              <li key={item?.id || i} className="px-1 sm:px-2">
                <div className="flex w-full items-center gap-3 py-3">
                  <div className="font-medium text-secondary hidden sm:block w-4 text-right">
                    {rank}
                  </div>
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <Image
                      src={item?.thumbnail || "https://via.placeholder.com/44"}
                      alt={item?.name || `Item ${rank}`}
                      className="h-10 w-10 sm:h-11 sm:w-11 rounded-lg object-cover"
                      loading="lazy"
                    />
                    <div className="min-w-0 flex flex-col">
                      <div className="font-medium text-sm sm:text-base truncate max-w-[40ch]">
                        {item?.name || `Item ${rank}`}
                      </div>
                      <div className="mt-1 flex items-center gap-3 text-secondary text-sm">
                        <div className="flex items-center gap-1">
                          <Star strokeWidth={1.5} className="h-3 w-3" aria-hidden="true" />
                          <span>
                            {typeof item?.rating === "number"
                              ? item.rating.toFixed(1)
                              : item?.rating || "–"}
                          </span>
                        </div>
                        <div className="whitespace-nowrap sm:hidden">{infoText}</div>
                      </div>
                    </div>
                  </div>
                  <div className="hidden sm:block text-sm text-secondary whitespace-nowrap">
                    {infoText}
                  </div>
                  <div className="flex justify-end">
                    <Button
                      variant="outline"
                      color="secondary"
                      size="sm"
                      pill
                      aria-label={`Add ${item?.name || `item ${rank}`} to list`}
                    >
                      <PlusCircle strokeWidth={1.5} className="h-4 w-4" aria-hidden="true" />
                      Add
                    </Button>
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
        {!hasItems && (
          <div className="py-6">
            <EmptyMessage>
              No items available. Provide up to 7 entries for best results.
            </EmptyMessage>
          </div>
        )}
      </div>
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
