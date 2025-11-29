import { useOpenAiGlobal } from "./useOpenaiGlobal";
import { type DisplayMode } from "./types";

/**
 * Hook to access the current display mode from ChatGPT.
 * 
 * @returns The current display mode: "inline", "pip", or "fullscreen"
 * 
 * @example
 * ```tsx
 * import { useDisplayMode } from 'fastapps';
 * 
 * export default function MyWidget() {
 *   const displayMode = useDisplayMode();
 *   
 *   return (
 *     <div className={`mode-${displayMode}`}>
 *       Current mode: {displayMode}
 *     </div>
 *   );
 * }
 * ```
 */
export const useDisplayMode = (): DisplayMode | null => {
  return useOpenAiGlobal("displayMode");
};
