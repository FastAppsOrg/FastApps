import { useOpenAiGlobal } from "./useOpenaiGlobal";

/**
 * Hook to get widget props from ChatGPT tool output.
 * 
 * @param defaultState - Optional default state to use when toolOutput is not available
 * @returns The tool output data passed from the MCP server
 * 
 * @example
 * ```tsx
 * import { useWidgetProps } from 'fastapps';
 * 
 * export default function MyWidget() {
 *   const { message, count } = useWidgetProps();
 *   return <div>{message} - {count}</div>;
 * }
 * ```
 */
export function useWidgetProps<T extends Record<string, unknown>>(
  defaultState?: T | (() => T)
): T {
  const props = useOpenAiGlobal("toolOutput") as T;

  const fallback =
    typeof defaultState === "function"
      ? (defaultState as () => T | null)()
      : defaultState ?? null;

  return props ?? fallback;
}
