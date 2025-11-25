import { useCallback } from "react";
import { McpAppsClient } from "../mcp/appsClient";

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
  const clientRef = useCallback(() => new McpAppsClient(targetWindow), [targetWindow]);

  const ensureMcpClient = useCallback(() => {
    const client = clientRef();
    client.connect();
    client.initialize().catch(() => {
      /* ignore init errors */
    });
    return client;
  }, [clientRef]);

  const openLink = useCallback(
    async (href: string) => {
      if (protocolHint !== "mcp-apps" && window?.openai?.openExternal) {
        return window.openai.openExternal({ href });
      }
      const client = ensureMcpClient();
      return client.sendRequest("ui/open-link", { url: href });
    },
    [ensureMcpClient]
  );

  const sendMessage = useCallback(
    async (text: string) => {
      if (protocolHint !== "mcp-apps" && window?.openai?.sendFollowUpMessage) {
        return window.openai.sendFollowUpMessage({ prompt: text });
      }
      const client = ensureMcpClient();
      return client.sendRequest("ui/message", {
        role: "user",
        content: { type: "text", text },
      });
    },
    [ensureMcpClient]
  );

  const callTool = useCallback(
    async (name: string, args: Record<string, unknown>) => {
      if (protocolHint !== "mcp-apps" && window?.openai?.callTool) {
        return window.openai.callTool(name, args);
      }
      const client = ensureMcpClient();
      return client.sendRequest("tools/call", { name, arguments: args });
    },
    [ensureMcpClient]
  );

  const requestDisplayMode = useCallback(
    async (mode: "inline" | "fullscreen" | "pip") => {
      if (protocolHint !== "mcp-apps" && window?.openai?.requestDisplayMode) {
        return window.openai.requestDisplayMode({ mode });
      }
      // No MCP Apps equivalent defined yet; return a resolved promise.
      return Promise.resolve({ mode });
    },
    []
  );

  return {
    openLink,
    sendMessage,
    callTool,
    requestDisplayMode,
  };
}
