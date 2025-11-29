import { useOpenAiGlobal } from "./useOpenaiGlobal";

/**
 * Hook to access the maximum height constraint from ChatGPT.
 * 
 * @returns The maximum height in pixels
 * 
 * @example
 * ```tsx
 * import { useMaxHeight } from 'fastapps';
 * 
 * export default function MyWidget() {
 *   const maxHeight = useMaxHeight();
 *   
 *   return (
 *     <div style={{ maxHeight: `${maxHeight}px`, overflow: 'auto' }}>
 *       Content that respects the max height
 *     </div>
 *   );
 * }
 * ```
 */
export const useMaxHeight = (): number | null => {
  return useOpenAiGlobal("maxHeight");
};
