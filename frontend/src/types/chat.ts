import { z } from "zod";

/** A citation the backend validated against retrieved transcript chunks. */
export const citationSchema = z.object({
  chunk_id: z.string(),
  video_id: z.string(),
  start_time: z.number(),
  end_time: z.number(),
  text: z.string(),
});

export type Citation = z.infer<typeof citationSchema>;
