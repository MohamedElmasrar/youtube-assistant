import { z } from "zod";

export const videoMetadataSchema = z.object({
  video_id: z.string(),
  available: z.boolean(),
  title: z.string().nullish(),
  description: z.string().nullish(),
  channel_title: z.string().nullish(),
  thumbnail_url: z.string().nullish(),
  published_at: z.string().nullish(),
  duration_seconds: z.number().nullish(),
  view_count: z.number().nullish(),
  embeddable: z.boolean().nullish(),
});

export const videoResponseSchema = z.object({
  video_id: z.string(),
  status: z.enum(["ready", "failed"]),
  cached: z.boolean(),
  language: z.string().nullish(),
  chunk_count: z.number(),
  metadata: videoMetadataSchema,
  error: z
    .object({
      code: z.string(),
      message: z.string(),
      stage: z.string().nullish(),
    })
    .nullish(),
});

export const transcriptSegmentSchema = z.object({
  start: z.number(),
  duration: z.number(),
  text: z.string(),
});

export const transcriptSchema = z.object({
  video_id: z.string(),
  language: z.string(),
  is_generated: z.boolean(),
  segments: z.array(transcriptSegmentSchema),
});

export type VideoMetadata = z.infer<typeof videoMetadataSchema>;
export type VideoResponse = z.infer<typeof videoResponseSchema>;
export type TranscriptSegment = z.infer<typeof transcriptSegmentSchema>;
export type Transcript = z.infer<typeof transcriptSchema>;
