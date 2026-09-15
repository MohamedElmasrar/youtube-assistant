"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchTranscript, ingestVideo } from "@/lib/api/videos";

/**
 * Prepares a video (metadata + transcript + index). The POST is idempotent, so it is safe to
 * run as a cached query; React Query aborts it if the user switches videos meanwhile.
 */
export function useVideo(videoId: string | null) {
  return useQuery({
    queryKey: ["video", videoId],
    queryFn: ({ signal }) => ingestVideo(videoId as string, signal),
    enabled: videoId !== null,
  });
}

export function useTranscript(videoId: string | null, enabled: boolean) {
  return useQuery({
    queryKey: ["transcript", videoId],
    queryFn: ({ signal }) => fetchTranscript(videoId as string, signal),
    enabled: videoId !== null && enabled,
  });
}
