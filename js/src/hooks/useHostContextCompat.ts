import { useMemo } from "react";
import { useOpenAiGlobal } from "./useOpenaiGlobal";
import { useMcpAppsHostContext } from "./useMcpAppsHostContext";

/**
 * Merge OpenAI globals and MCP Apps hostContext into a single object.
 * OpenAI values take precedence if present.
 */
export function useHostContextCompat() {
  const openaiTheme = useOpenAiGlobal("theme");
  const openaiDisplayMode = useOpenAiGlobal("displayMode");
  const openaiMaxHeight = useOpenAiGlobal("maxHeight");
  const openaiSafeArea = useOpenAiGlobal("safeArea");
  const openaiLocale = useOpenAiGlobal("locale");
  const openaiUserAgent = useOpenAiGlobal("userAgent");

  const { hostContext } = useMcpAppsHostContext();
  const protocolHint =
    typeof window !== "undefined"
      ? (window as any).__FASTAPPS_PROTOCOL
      : undefined;

  return useMemo(
    () => ({
      theme:
        protocolHint === "openai-apps"
          ? openaiTheme ?? null
          : protocolHint === "mcp-apps"
            ? hostContext?.theme ?? null
            : openaiTheme ?? hostContext?.theme ?? null,
      displayMode:
        protocolHint === "openai-apps"
          ? openaiDisplayMode ?? null
          : protocolHint === "mcp-apps"
            ? hostContext?.displayMode ?? null
            : openaiDisplayMode ?? hostContext?.displayMode ?? null,
      maxHeight:
        protocolHint === "openai-apps"
          ? openaiMaxHeight ?? null
          : protocolHint === "mcp-apps"
            ? hostContext?.viewport?.maxHeight ?? null
            : openaiMaxHeight ?? hostContext?.viewport?.maxHeight ?? null,
      safeArea:
        protocolHint === "openai-apps"
          ? openaiSafeArea ?? null
          : protocolHint === "mcp-apps"
            ? hostContext?.safeAreaInsets ?? null
            : openaiSafeArea ?? hostContext?.safeAreaInsets ?? null,
      locale:
        protocolHint === "openai-apps"
          ? openaiLocale ?? null
          : protocolHint === "mcp-apps"
            ? hostContext?.locale ?? null
            : openaiLocale ?? hostContext?.locale ?? null,
      userAgent:
        protocolHint === "openai-apps"
          ? openaiUserAgent ?? null
          : protocolHint === "mcp-apps"
            ? hostContext?.userAgent ?? null
            : openaiUserAgent ?? hostContext?.userAgent ?? null,
      // raw accessors
      _openai: {
        theme: openaiTheme,
        displayMode: openaiDisplayMode,
        maxHeight: openaiMaxHeight,
        safeArea: openaiSafeArea,
        locale: openaiLocale,
        userAgent: openaiUserAgent,
      },
      _mcp: hostContext,
    }),
    [
      openaiTheme,
      openaiDisplayMode,
      openaiMaxHeight,
      openaiSafeArea,
      openaiLocale,
      openaiUserAgent,
      hostContext,
      protocolHint,
    ]
  );
}
