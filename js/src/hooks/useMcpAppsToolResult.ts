import { useEffect, useMemo, useState } from "react";
import { McpAppsClient } from "../mcp/appsClient";

/**
 * Subscribe to MCP Apps tool-result notifications.
 * Returns the latest params of `ui/notifications/tool-result`.
 */
export function useMcpAppsToolResult(targetWindow?: Window) {
  const client = useMemo(
    () => McpAppsClient.getShared(targetWindow),
    [targetWindow]
  );
  const [result, setResult] = useState<any>(() => client.getLatestToolResult());

  useEffect(() => {
    client.connect();
    // Initialize handshake so host starts sending notifications
    client.initialize().catch((e) => {
      console.warn("MCP Apps initialize failed", e);
    });

    const handleResult = (params: any) => {
      setResult(params);
    };

    client.onToolResult(handleResult);

    // Prime state if host already sent one before handler
    const latest = client.getLatestToolResult();
    if (latest) {
      setResult(latest);
    }

    return () => {
      client.disconnect();
    };
  }, [client]);

  return result ?? null;
}
