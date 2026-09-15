"use client";

import { CalendarDays, Clock, ExternalLink, Eye, Info } from "lucide-react";
import { useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate, formatTimestamp } from "@/lib/utils/time";
import type { VideoMetadata } from "@/types/video";

interface VideoDetailsProps {
  videoId: string;
  metadata: VideoMetadata | undefined;
  loading: boolean;
}

export function VideoDetails({ videoId, metadata, loading }: VideoDetailsProps) {
  const [expanded, setExpanded] = useState(false);

  if (loading && !metadata) {
    return (
      <div className="space-y-2" aria-busy="true" aria-label="Loading video details">
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-4 w-full" />
      </div>
    );
  }

  if (!metadata?.available) {
    return (
      <Alert>
        <Info aria-hidden />
        <AlertDescription>
          Video details are unavailable. Add a YouTube API key to the backend to show them.
          Chat and transcript still work.{" "}
          <a
            className="inline-flex items-center gap-1 underline underline-offset-2"
            href={`https://www.youtube.com/watch?v=${videoId}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            Open on YouTube <ExternalLink className="size-3" aria-hidden />
          </a>
        </AlertDescription>
      </Alert>
    );
  }

  const published = formatDate(metadata.published_at);
  return (
    <div className="space-y-2">
      <h2 className="text-lg leading-snug font-semibold text-balance">{metadata.title}</h2>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
        {metadata.channel_title && (
          <span className="font-medium text-foreground">{metadata.channel_title}</span>
        )}
        {published && (
          <span className="inline-flex items-center gap-1">
            <CalendarDays className="size-3.5" aria-hidden /> {published}
          </span>
        )}
        {metadata.duration_seconds != null && (
          <span className="inline-flex items-center gap-1">
            <Clock className="size-3.5" aria-hidden /> {formatTimestamp(metadata.duration_seconds)}
          </span>
        )}
        {metadata.view_count != null && (
          <span className="inline-flex items-center gap-1">
            <Eye className="size-3.5" aria-hidden /> {metadata.view_count.toLocaleString()} views
          </span>
        )}
      </div>
      {metadata.description && (
        <div>
          <p
            className={`text-sm whitespace-pre-line text-muted-foreground ${expanded ? "" : "line-clamp-2"}`}
          >
            {metadata.description}
          </p>
          <Button variant="link" size="xs" className="px-0" onClick={() => setExpanded(!expanded)}>
            {expanded ? "Show less" : "Show more"}
          </Button>
        </div>
      )}
    </div>
  );
}
