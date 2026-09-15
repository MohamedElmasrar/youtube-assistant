"use client";

import { memo } from "react";
import { usePlayerController } from "@/lib/player/context";
import { cn } from "@/lib/utils";
import { formatTimestamp } from "@/lib/utils/time";
import type { TranscriptSegment } from "@/types/video";

interface TranscriptSegmentRowProps {
  segment: TranscriptSegment;
  index: number;
  active: boolean;
  query: string;
}

function Highlighted({ text, query }: { text: string; query: string }) {
  if (!query) return <>{text}</>;
  const lower = text.toLowerCase();
  const parts: React.ReactNode[] = [];
  let cursor = 0;
  let hit = lower.indexOf(query, cursor);
  while (hit !== -1) {
    parts.push(text.slice(cursor, hit));
    parts.push(
      <mark key={hit} className="rounded-sm bg-yellow-200 px-0.5 text-foreground dark:bg-yellow-500/40">
        {text.slice(hit, hit + query.length)}
      </mark>,
    );
    cursor = hit + query.length;
    hit = lower.indexOf(query, cursor);
  }
  parts.push(text.slice(cursor));
  return <>{parts}</>;
}

export const TranscriptSegmentRow = memo(function TranscriptSegmentRow({
  segment,
  index,
  active,
  query,
}: TranscriptSegmentRowProps) {
  const controller = usePlayerController();
  return (
    <li data-index={index}>
      <button
        type="button"
        onClick={() => controller.seekTo(segment.start)}
        aria-current={active ? "true" : undefined}
        className={cn(
          "flex w-full gap-3 rounded-md px-2 py-1.5 text-left text-sm transition-colors",
          "hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
          active && "bg-accent",
        )}
      >
        <span className="w-12 shrink-0 pt-px font-mono text-xs text-primary tabular-nums">
          {formatTimestamp(segment.start)}
        </span>
        <span className="min-w-0 flex-1">
          <Highlighted text={segment.text} query={query} />
        </span>
      </button>
    </li>
  );
});
