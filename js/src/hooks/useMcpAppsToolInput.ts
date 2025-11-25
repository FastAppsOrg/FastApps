import { useEffect, useMemo, useState } from "react";
import { McpAppsClient } from "../mcp/appsClient";

/**
 * Subscribe to MCP Apps tool-input notifications.
 * Returns the latest params of `ui/notifications/tool-input`.
 */
export function useMcpAppsToolInput(targetWindow?: Window) {
  const client = useMemo(() => new McpAppsClient(targetWindow), [targetWindow]);
  const [toolInput, setToolInput] = useState<any>(() => client.getLatestToolInput());

  useEffect(() => {
    client.connect();
    client.initialize().catch(() => {
      /* ignore init errors for now */
    });

    const handleInput = (params: any) => {
      setToolInput(params);
    };

    client.onToolInput(handleInput);

    const latest = client.getLatestToolInput();
    if (latest) {
      setToolInput(latest);
    }

    return () => {
      client.disconnect();
    };
  }, [client]);

  return toolInput;
}
