/**
 * FastApps React Hooks - React hooks for building ChatGPT widgets
 * 
 * @packageDocumentation
 */

export { useOpenAiGlobal } from './hooks/useOpenaiGlobal';
export { useWidgetProps } from './hooks/useWidgetProps';
export { useWidgetState } from './hooks/useWidgetState';
export { useDisplayMode } from './hooks/useDisplayMode';
export { useMaxHeight } from './hooks/useMaxHeight';
export { useMcpAppsHostContext } from './hooks/useMcpAppsHostContext';
export { useMcpAppsToolResult } from './hooks/useMcpAppsToolResult';
export { useMcpAppsToolInput } from './hooks/useMcpAppsToolInput';
export { useWidgetData } from './hooks/useWidgetData';
export { useHostContextCompat } from './hooks/useHostContextCompat';
export { useHostActions } from './hooks/useHostActions';
export { McpAppsClient } from './mcp/appsClient';

export type {
  OpenAiGlobals,
  UnknownObject,
  Theme,
  SafeArea,
  SafeAreaInsets,
  DeviceType,
  UserAgent,
  DisplayMode,
  CallToolResponse,
} from './hooks/types';

export type { HostContext, UiInitializeResult } from './mcp/appsClient';
