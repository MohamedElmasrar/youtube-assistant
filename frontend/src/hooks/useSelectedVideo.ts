"use client";

import { useState, useSyncExternalStore } from "react";
import { readStorage, writeStorage } from "@/lib/storage";

const KEY = "youtube-assistant:last-video";
const subscribe = () => () => {};

/** The selected video ID. Restored from localStorage after a refresh, without hydration mismatch. */
export function useSelectedVideo() {
  const stored = useSyncExternalStore(
    subscribe,
    () => readStorage(KEY),
    () => null,
  );
  const [override, setOverride] = useState<string | null | undefined>(undefined);
  const videoId = override === undefined ? stored : override;

  const select = (id: string | null) => {
    writeStorage(KEY, id);
    setOverride(id);
  };
  return [videoId, select] as const;
}
