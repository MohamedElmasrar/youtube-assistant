import type { Message } from "@langchain/langgraph-sdk";
import { citationSchema, type Citation } from "@/types/chat";

/** Plain text of a message, whether its content is a string or a list of content blocks. */
export function messageText(message: Message): string {
  if (typeof message.content === "string") return message.content;
  return message.content
    .map((block) => (block.type === "text" ? block.text : ""))
    .join("");
}

/** Citations the backend validated against retrieved chunks. Unknown shapes are ignored. */
export function messageCitations(message: Message): Citation[] {
  const raw = (message as { additional_kwargs?: { citations?: unknown } }).additional_kwargs
    ?.citations;
  if (!Array.isArray(raw)) return [];
  return raw.flatMap((item) => {
    const parsed = citationSchema.safeParse(item);
    return parsed.success ? [parsed.data] : [];
  });
}

// Models sometimes nest or merge brackets: [[a_1]], [[a_1, a_2]], [[a_1], [a_2]], [a_1].
// A marker is a bracketed run made only of chunk-ID-shaped tokens and separators.
const ID = "[A-Za-z0-9_-]*_\\d+";
const MARKER = new RegExp(
  `\\[+\\s*${ID}(?:[\\s,;\\[\\]]+${ID})*\\s*\\]+|\\[\\[[^\\[\\]]*\\]\\]`,
  "g",
);
const TOKEN = /[A-Za-z0-9_-]+/g;
const PARTIAL_MARKER = /\[[\s\[\],;A-Za-z0-9_-]*$/;

/**
 * Turn `[[chunk_id]]` markers into markdown links `[cite](#cite:chunk_id)` for validated
 * citations and drop everything else (unknown ids, half-streamed markers).
 */
export function linkCitations(text: string, citations: Citation[]): string {
  const known = new Set(citations.map((c) => c.chunk_id));
  return text
    .replace(MARKER, (marker) =>
      (marker.match(TOKEN) ?? [])
        .filter((id) => known.has(id))
        .map((id) => `[cite](#cite:${id})`)
        .join(" "),
    )
    .replace(PARTIAL_MARKER, "");
}

export const CITE_PREFIX = "#cite:";

const TOOL_LABELS: Record<string, string> = {
  search_video_transcript: "Searching transcript",
  get_video_transcript: "Reading transcript",
  get_video_info: "Reading video details",
};

export interface ToolActivity {
  id: string;
  label: string;
  detail: string | null;
  done: boolean;
}

/** Tool calls an assistant message made, and whether their results have arrived. */
export function toolActivities(message: Message, allMessages: Message[]): ToolActivity[] {
  if (message.type !== "ai") return [];
  return (message.tool_calls ?? []).map((call, i) => {
    const query = (call.args as { query?: unknown })?.query;
    return {
      id: call.id ?? `${message.id}-${i}`,
      label: TOOL_LABELS[call.name] ?? call.name,
      detail: typeof query === "string" ? query : null,
      done: allMessages.some((m) => m.type === "tool" && m.tool_call_id === call.id),
    };
  });
}
