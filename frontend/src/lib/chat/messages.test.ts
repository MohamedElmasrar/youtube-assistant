import type { Message } from "@langchain/langgraph-sdk";
import { describe, expect, it } from "vitest";
import { linkCitations, messageCitations, messageText, toolActivities } from "@/lib/chat/messages";
import { findActiveIndex } from "@/lib/player/context";

const citation = {
  chunk_id: "abc_5",
  video_id: "abc",
  start_time: 120.5,
  end_time: 154.8,
  text: "text",
};

describe("linkCitations", () => {
  it("links validated ids and drops unknown or half-streamed markers", () => {
    const text = "A [[abc_5]] B [[fake_1]] C [[abc_5, fake_2]] D [[abc";
    expect(linkCitations(text, [citation])).toBe(
      "A [cite](#cite:abc_5) B  C [cite](#cite:abc_5) D ",
    );
  });
  it("drops every marker while no citations are validated yet", () => {
    expect(linkCitations("Answer [[abc_5]].", [])).toBe("Answer .");
  });
});

describe("message helpers", () => {
  it("reads text from strings and content blocks", () => {
    expect(messageText({ type: "ai", content: "hi" } as Message)).toBe("hi");
    const blocks = { type: "ai", content: [{ type: "text", text: "a" }, { type: "text", text: "b" }] };
    expect(messageText(blocks as Message)).toBe("ab");
  });
  it("keeps only well-formed citations", () => {
    const message = {
      type: "ai",
      content: "",
      additional_kwargs: { citations: [citation, { chunk_id: 1 }, "junk"] },
    } as unknown as Message;
    expect(messageCitations(message)).toEqual([citation]);
    expect(messageCitations({ type: "ai", content: "" } as Message)).toEqual([]);
  });
  it("reports tool progress", () => {
    const ai = {
      type: "ai",
      id: "m",
      content: "",
      tool_calls: [{ id: "t1", name: "search_video_transcript", args: { query: "attention" } }],
    } as unknown as Message;
    const pending = toolActivities(ai, [ai]);
    expect(pending).toMatchObject([{ label: "Searching transcript", detail: "attention", done: false }]);
    const tool = { type: "tool", tool_call_id: "t1", content: "" } as unknown as Message;
    expect(toolActivities(ai, [ai, tool])[0].done).toBe(true);
  });
});

describe("findActiveIndex", () => {
  const segments = [0, 5, 10].map((start) => ({ start, duration: 5, text: "" }));
  it("finds the segment containing the playback time", () => {
    expect(findActiveIndex(segments, -1)).toBe(-1);
    expect(findActiveIndex(segments, 0)).toBe(0);
    expect(findActiveIndex(segments, 7)).toBe(1);
    expect(findActiveIndex(segments, 99)).toBe(2);
    expect(findActiveIndex([], 3)).toBe(-1);
  });
});
