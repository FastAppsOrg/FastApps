import { useMemo } from "react";
import { useWidgetProps } from "./useWidgetProps";
import { useMcpAppsToolResult } from "./useMcpAppsToolResult";
import type { UnknownObject } from "./types";

type Options<T> = {
  /**
    * Optional fallback if neither OpenAI toolOutput nor MCP Apps tool-result
    * is available yet.
    */
  defaultValue?: T | (() => T);
};

/**
 * Protocol-agnostic widget data hook.
 *
 * - If window.openai.toolOutput exists (OpenAI Apps), return it.
 * - Otherwise, subscribe to MCP Apps ui/notifications/tool-result and return structuredContent.
 */
export function useWidgetData<T extends UnknownObject = UnknownObject>(
  options?: Options<T>
): T | null {
  // OpenAI Apps path
  const openaiProps = useWidgetProps<T>();

  // MCP Apps path
  const mcpResult = useMcpAppsToolResult();
  const mcpData = mcpResult?.structuredContent ?? null;

  // Choose OpenAI first if available, else MCP, else default
  return useMemo(() => {
    if (openaiProps != null) return openaiProps;
    if (mcpData != null) return mcpData as T;

    const { defaultValue } = options ?? {};
    if (defaultValue !== undefined) {
      return typeof defaultValue === "function"
        ? (defaultValue as () => T)()
        : defaultValue;
    }
    return null;
  }, [openaiProps, mcpData, options]);
}
