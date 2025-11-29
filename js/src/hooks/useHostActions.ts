import { useCallback } from "react";
import { McpAppsClient } from "../mcp/appsClient";
import { useEffect, useMemo } from "react";

/**
 * Host actions compatible with both OpenAI Apps and MCP Apps.
 *
 * - openLink: OpenAI openExternal or MCP ui/open-link
 * - sendMessage: OpenAI sendFollowUpMessage or MCP ui/message
 * - callTool: OpenAI callTool or MCP tools/call
 * - requestDisplayMode: OpenAI requestDisplayMode (no MCP equivalent yet)
 */
export function useHostActions(targetWindow?: Window) {
  const protocolHint =
    typeof window !== "undefined"
      ? (window as any).__FASTAPPS_PROTOCOL
      : undefined;
  const client = useMemo(
    () => McpAppsClient.getShared(targetWindow),
    [targetWindow]
  );

  useEffect(() => {
    client.connect();
    client.initialize().catch((e) => {
      console.warn("MCP Apps initialize failed", e);
    });
    return () => {
      client.disconnect();
    };
  }, [client]);

  const openLink = useCallback(
    async (href: string) => {
      if (protocolHint !== "mcp-apps" && window?.openai?.openExternal) {
        return window.openai.openExternal({ href });
      }
      return client.sendRequest("ui/open-link", { url: href });
    },
    [client, protocolHint]
  );

  const sendMessage = useCallback(
    async (text: string) => {
      if (protocolHint !== "mcp-apps" && window?.openai?.sendFollowUpMessage) {
        return window.openai.sendFollowUpMessage({ prompt: text });
      }
      return client.sendRequest("ui/message", {
        role: "user",
        content: { type: "text", text },
      });
    },
    [client, protocolHint]
  );

  const callTool = useCallback(
    async (name: string, args: Record<string, unknown>) => {
      if (protocolHint !== "mcp-apps" && window?.openai?.callTool) {
        return window.openai.callTool(name, args);
      }
      return client.sendRequest("tools/call", { name, arguments: args });
    },
    [client, protocolHint]
  );

  const requestDisplayMode = useCallback(
    async (mode: "inline" | "fullscreen" | "pip") => {
      if (protocolHint !== "mcp-apps" && window?.openai?.requestDisplayMode) {
        return window.openai.requestDisplayMode({ mode });
      }
      // No MCP Apps equivalent defined yet; return a resolved promise.
      return Promise.resolve({ mode });
    },
    [protocolHint]
  );

  return {
    openLink,
    sendMessage,
    callTool,
    requestDisplayMode,
  };
}
