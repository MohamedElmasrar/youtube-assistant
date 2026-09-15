"use client";

import { Clock } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { usePlayerController } from "@/lib/player/context";
import { formatTimestamp } from "@/lib/utils/time";
import type { Citation } from "@/types/chat";

const PREVIEW_CHARS = 220;

/** A validated citation. Clicking seeks the player to the cited chunk's start time. */
export function CitationLink({ citation }: { citation: Citation }) {
  const controller = usePlayerController();
  const preview =
    citation.text.length > PREVIEW_CHARS
      ? `${citation.text.slice(0, PREVIEW_CHARS).trimEnd()}…`
      : citation.text;

  return (
    <Tooltip>
      <TooltipTrigger
        type="button"
        onClick={() => controller.seekTo(citation.start_time)}
        aria-label={`Play from ${formatTimestamp(citation.start_time)}`}
        className="mx-0.5 inline-flex items-center gap-1 rounded-md border bg-secondary px-1.5 py-0.5 align-baseline font-mono text-xs text-secondary-foreground tabular-nums transition-colors hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
      >
        <Clock className="size-3" aria-hidden />
        {formatTimestamp(citation.start_time)}
      </TooltipTrigger>
      <TooltipContent className="max-w-sm flex-col items-start gap-1">
        <span className="font-mono">
          {formatTimestamp(citation.start_time)} – {formatTimestamp(citation.end_time)}
        </span>
        <span className="opacity-90">{preview}</span>
      </TooltipContent>
    </Tooltip>
  );
}
