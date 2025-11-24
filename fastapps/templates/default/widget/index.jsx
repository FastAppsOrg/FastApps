import React from "react";
import { AppsSDKUIProvider } from "@openai/apps-sdk-ui/components/AppsSDKUIProvider";
import { Badge } from "@openai/apps-sdk-ui/components/Badge";
import { useWidgetProps } from "fastapps";

function {ClassName}Inner() {
  const { message } = useWidgetProps() || {};

  return (
    <div className="w-full rounded-3xl border border-default bg-surface shadow-card p-6 sm:p-8 text-left">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-secondary text-sm">FastApps Widget</p>
          <h1 className="mt-1 heading-lg">{message || "Welcome to FastApps"}</h1>
        </div>
        <Badge color="info">Template</Badge>
      </div>
      <p className="mt-4 text-secondary text-sm leading-relaxed">
        Edit <code>server/tools</code> for logic and <code>widgets/{`{identifier}`}</code> for UI. Apps
        SDK UI is prewired—swap this content with your own.
      </p>
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
