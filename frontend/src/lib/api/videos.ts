import { apiRequest } from "@/lib/api/client";
import {
  transcriptSchema,
  videoResponseSchema,
  type Transcript,
  type VideoResponse,
} from "@/types/video";

/** Validate, fetch and index a video. Idempotent: indexed videos return immediately. */
export function ingestVideo(url: string, signal?: AbortSignal): Promise<VideoResponse> {
  return apiRequest("/api/videos", videoResponseSchema, {
    method: "POST",
    body: JSON.stringify({ url }),
    signal,
  });
}

export function fetchTranscript(videoId: string, signal?: AbortSignal): Promise<Transcript> {
  return apiRequest(
    `/api/videos/${encodeURIComponent(videoId)}/transcript`,
    transcriptSchema,
    { signal },
  );
}
