/**
 * Minimal MCP Apps (SEP-1865 draft) postMessage client for UI iframes.
 *
 * The UI (guest) sends JSON-RPC 2.0 messages to its parent host.
 * This client handles ui/initialize handshake and generic request/notification flows.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */

export type JsonRpcId = number;

export type JsonRpcRequest = {
  jsonrpc: "2.0";
  id: JsonRpcId;
  method: string;
  params?: any;
};

export type JsonRpcResponse =
  | {
      jsonrpc: "2.0";
      id: JsonRpcId;
      result: any;
    }
  | {
      jsonrpc: "2.0";
      id: JsonRpcId;
      error: { code: number; message: string; data?: any };
    };

export type JsonRpcNotification = {
  jsonrpc: "2.0";
  method: string;
  params?: any;
};

export type HostContext = {
  toolInfo?: {
    id?: string | number;
    tool?: any;
  };
  theme?: "light" | "dark" | "system";
  displayMode?: "inline" | "fullscreen" | "pip" | "carousel";
  availableDisplayModes?: string[];
  viewport?: {
    width: number;
    height: number;
    maxHeight?: number;
    maxWidth?: number;
  };
  locale?: string;
  timeZone?: string;
  userAgent?: string;
  platform?: "web" | "desktop" | "mobile";
  deviceCapabilities?: { touch?: boolean; hover?: boolean };
  safeAreaInsets?: { top: number; right: number; bottom: number; left: number };
};

export type UiInitializeResult = {
  protocolVersion: string;
  hostCapabilities?: any;
  hostInfo?: { name: string; version: string };
  hostContext?: HostContext;
};

type Pending = {
  resolve: (value: any) => void;
  reject: (error: Error) => void;
};

export class McpAppsClient {
  private static shared = new WeakMap<Window, McpAppsClient>();
  private target: Window;
  private targetOrigin: string;
  private nextId: number;
  private pending: Map<number, Pending>;
  private notificationHandlers: Map<string, ((params: unknown) => void)[]>;
  private latestToolResult: unknown = null;
  private latestToolInput: unknown = null;
  private toolResultListeners: ((result: unknown) => void)[] = [];
  private toolInputListeners: ((params: unknown) => void)[] = [];
  private refCount = 0;

  /**
   * Get a shared client for a target window (singleton per window).
   */
  static getShared(targetWindow?: Window, hostOrigin?: string) {
    const key = targetWindow ?? window.parent;
    const existing = McpAppsClient.shared.get(key);
    if (existing) return existing;
    const created = new McpAppsClient(key, hostOrigin);
    McpAppsClient.shared.set(key, created);
    return created;
  }

  constructor(targetWindow?: Window, hostOrigin?: string) {
    this.target = targetWindow ?? window.parent;
    // Prefer provided origin, else referrer origin, else wildcard (as last resort)
    const referrerOrigin =
      typeof document !== "undefined" && document.referrer
        ? new URL(document.referrer).origin
        : "*";
    this.targetOrigin = hostOrigin ?? referrerOrigin ?? "*";
    this.nextId = 1;
    this.pending = new Map();
    this.notificationHandlers = new Map();
    this.handleMessage = this.handleMessage.bind(this);
  }

  connect() {
    if (this.refCount === 0) {
      window.addEventListener("message", this.handleMessage);
    }
    this.refCount += 1;
  }

  disconnect() {
    this.refCount = Math.max(0, this.refCount - 1);
    if (this.refCount === 0) {
      window.removeEventListener("message", this.handleMessage);
      this.pending.clear();
      this.notificationHandlers.clear();
    }
  }

  async initialize(): Promise<UiInitializeResult> {
    const result = await this.sendRequest("ui/initialize", {
      capabilities: {},
      clientInfo: { name: "fastapps-ui", version: "1.0.0" },
      protocolVersion: "2025-06-18",
    });
    return result as UiInitializeResult;
  }

  async sendRequest(method: string, params?: any): Promise<any> {
    const id = this.nextId++;
    const message: JsonRpcRequest = {
      jsonrpc: "2.0",
      id,
      method,
      params,
    };

    const promise = new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      try {
        this.target.postMessage(message, this.targetOrigin);
      } catch (e: any) {
        this.pending.delete(id);
        reject(e);
      }
    });

    return promise;
  }

  sendNotification(method: string, params?: any) {
    const message: JsonRpcNotification = {
      jsonrpc: "2.0",
      method,
      params,
    };
    this.target.postMessage(message, this.targetOrigin);
  }

  onNotification(method: string, handler: (params: unknown) => void) {
    const handlers = this.notificationHandlers.get(method) ?? [];
    handlers.push(handler);
    this.notificationHandlers.set(method, handlers);
  }

  onToolResult(handler: (result: unknown) => void) {
    this.toolResultListeners.push(handler);
  }

  onToolInput(handler: (params: unknown) => void) {
    this.toolInputListeners.push(handler);
  }

  getLatestToolResult<T = any>(): T | null {
    return this.latestToolResult as T | null;
  }

  getLatestToolInput<T = any>(): T | null {
    return this.latestToolInput as T | null;
  }

  private handleMessage(event: MessageEvent) {
    const data = event.data as JsonRpcResponse | JsonRpcNotification;
    if (!data || data.jsonrpc !== "2.0") {
      return;
    }

    // Response
    if ("id" in data && (data as any).id !== undefined) {
      const pending = this.pending.get((data as any).id);
      if (!pending) return;
      this.pending.delete((data as any).id);

      if ("result" in data) {
        pending.resolve((data as any).result);
      } else if ("error" in data) {
        pending.reject(new Error((data as any).error?.message ?? "Unknown error"));
      }
      return;
    }

    // Notification
    if ("method" in data) {
      const method = (data as any).method as string;
      const handlers = this.notificationHandlers.get(method) ?? [];
      handlers.forEach((fn) => fn((data as any).params));

      // Special-case tool notifications per SEP-1865
      if (method === "ui/notifications/tool-result") {
        this.latestToolResult = (data as any).params ?? null;
        this.toolResultListeners.forEach((fn) => fn(this.latestToolResult));
      } else if (method === "ui/notifications/tool-input") {
        this.latestToolInput = (data as any).params ?? null;
        this.toolInputListeners.forEach((fn) => fn(this.latestToolInput));
      }
    }
  }
}
