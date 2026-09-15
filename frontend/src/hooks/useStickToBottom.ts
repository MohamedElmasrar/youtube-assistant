"use client";

import { useEffect, useRef } from "react";

const VIEWPORT = '[data-slot="scroll-area-viewport"]';
const THRESHOLD_PX = 80;

/**
 * Keeps a ScrollArea pinned to the bottom while content streams in, unless the user has
 * scrolled up. Attach the returned ref to an element at the end of the scrolled content.
 */
export function useStickToBottom(change: unknown) {
  const anchor = useRef<HTMLDivElement>(null);
  const stuck = useRef(true);

  useEffect(() => {
    const viewport = anchor.current?.closest<HTMLElement>(VIEWPORT);
    if (!viewport) return;
    const onScroll = () => {
      stuck.current =
        viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight < THRESHOLD_PX;
    };
    viewport.addEventListener("scroll", onScroll, { passive: true });
    return () => viewport.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const viewport = anchor.current?.closest<HTMLElement>(VIEWPORT);
    if (viewport && stuck.current) viewport.scrollTop = viewport.scrollHeight;
  }, [change]);

  return anchor;
}
