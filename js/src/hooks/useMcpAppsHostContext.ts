import { useEffect, useMemo, useState } from "react";
import { HostContext, McpAppsClient } from "../mcp/appsClient";

/**
 * Hook to initialize MCP Apps client and expose hostContext.
 *
 * Usage:
 * const { client, hostContext, initialized, error } = useMcpAppsHostContext();
 */
export function useMcpAppsHostContext(targetWindow?: Window) {
  const client = useMemo(
    () => McpAppsClient.getShared(targetWindow),
    [targetWindow]
  );
  const [hostContext, setHostContext] = useState<HostContext | undefined>();
  const [initialized, setInitialized] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    client.connect();

    client
      .initialize()
      .then((res) => {
        setHostContext(res.hostContext);
        setInitialized(true);
      })
      .catch((e) => {
        setError(e);
      });

    return () => {
      client.disconnect();
    };
  }, [client]);

  return { client, hostContext, initialized, error };
}
