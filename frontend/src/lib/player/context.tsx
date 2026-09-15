"use client";

import { createContext, useContext, useState, useSyncExternalStore } from "react";
import { PlayerController } from "@/lib/player/controller";
import type { TranscriptSegment } from "@/types/video";

const PlayerContext = createContext<PlayerController | null>(null);

export function PlayerProvider({ children }: { children: React.ReactNode }) {
  const [controller] = useState(() => new PlayerController());
  return <PlayerContext.Provider value={controller}>{children}</PlayerContext.Provider>;
}

export function usePlayerController(): PlayerController {
  const controller = useContext(PlayerContext);
  if (!controller) throw new Error("usePlayerController must be used inside PlayerProvider");
  return controller;
}

/** Index of the segment containing the playback position, or -1. Re-renders only on change. */
export function useActiveSegmentIndex(segments: TranscriptSegment[]): number {
  const controller = usePlayerController();
  return useSyncExternalStore(
    controller.subscribe,
    () => findActiveIndex(segments, controller.getTime()),
    () => -1,
  );
}

export function findActiveIndex(segments: TranscriptSegment[], time: number): number {
  let low = 0;
  let high = segments.length - 1;
  let found = -1;
  while (low <= high) {
    const mid = (low + high) >> 1;
    if (segments[mid].start <= time) {
      found = mid;
      low = mid + 1;
    } else high = mid - 1;
  }
  return found;
}
