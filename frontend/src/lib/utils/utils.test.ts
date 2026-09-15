import { describe, expect, it } from "vitest";
import { formatDate, formatTimestamp } from "@/lib/utils/time";
import { parseVideoId } from "@/lib/utils/youtube";

const ID = "dQw4w9WgXcQ";

describe("parseVideoId", () => {
  it.each([
    `https://www.youtube.com/watch?v=${ID}&t=5s`,
    `youtube.com/watch?v=${ID}`,
    `https://youtu.be/${ID}?si=x`,
    `https://www.youtube.com/shorts/${ID}`,
    `https://www.youtube.com/live/${ID}`,
    `https://www.youtube.com/embed/${ID}`,
    ID,
  ])("accepts %s", (input) => expect(parseVideoId(input)).toBe(ID));

  it.each([
    "",
    "hello",
    `https://evil.com/watch?v=${ID}`,
    `https://youtube.com.evil.com/watch?v=${ID}`,
    "https://www.youtube.com/watch?v=short",
  ])("rejects %s", (input) => expect(parseVideoId(input)).toBeNull());
});

describe("time formatting", () => {
  it("formats timestamps", () => {
    expect(formatTimestamp(0)).toBe("0:00");
    expect(formatTimestamp(125.9)).toBe("2:05");
    expect(formatTimestamp(3725)).toBe("1:02:05");
    expect(formatTimestamp(-4)).toBe("0:00");
  });
  it("handles missing or bad dates", () => {
    expect(formatDate(null)).toBeNull();
    expect(formatDate("nope")).toBeNull();
    expect(formatDate("2024-03-05T00:00:00Z")).toContain("2024");
  });
});
