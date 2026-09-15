import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useVideoConversation } from "@/hooks/useVideoConversation";

interface StreamOptions {
  threadId: string | null;
  onThreadId: (id: string) => void;
  onError: (error: unknown) => void;
}

const submit = vi.fn();
const stop = vi.fn();
let options: StreamOptions;
let streamState: Record<string, unknown>;

vi.mock("@langchain/langgraph-sdk/react", () => ({
  useStream: (opts: StreamOptions) => {
    options = opts;
    return { submit, stop, messages: [], isLoading: false, isThreadLoading: false, error: null, ...streamState };
  },
}));

const THREADS = "youtube-assistant:threads";

describe("useVideoConversation", () => {
  beforeEach(() => {
    streamState = {};
  });

  it("starts without a thread and remembers the one the server creates", () => {
    const { result } = renderHook(() => useVideoConversation("vid"));
    expect(options.threadId).toBeNull();
    act(() => options.onThreadId("thread-1"));
    expect(JSON.parse(localStorage.getItem(THREADS)!)).toEqual({ vid: "thread-1" });
    expect(options.threadId).toBe("thread-1");
    expect(result.current.messages).toEqual([]);
  });

  it("reuses the stored thread for the same video, and keeps videos separate", () => {
    localStorage.setItem(THREADS, JSON.stringify({ vid: "thread-1", other: "thread-2" }));
    renderHook(() => useVideoConversation("vid"));
    expect(options.threadId).toBe("thread-1");
    renderHook(() => useVideoConversation("other"));
    expect(options.threadId).toBe("thread-2");
    renderHook(() => useVideoConversation("brand-new"));
    expect(options.threadId).toBeNull();
  });

  it("submits the human message with the trusted video context", () => {
    const { result } = renderHook(() => useVideoConversation("vid"));
    act(() => result.current.send("  What is attention? "));
    const [input, submitOptions] = submit.mock.calls[0];
    expect(input).toEqual({ messages: [{ type: "human", content: "What is attention?" }] });
    expect(submitOptions.context).toEqual({ video_id: "vid" });
    const optimistic = submitOptions.optimisticValues({ messages: [] });
    expect(optimistic.messages).toHaveLength(1);
  });

  it("ignores empty input and duplicate submissions while a run is active", () => {
    const { result, rerender } = renderHook(() => useVideoConversation("vid"));
    act(() => result.current.send("   "));
    streamState = { isLoading: true };
    rerender();
    act(() => result.current.send("again"));
    expect(submit).not.toHaveBeenCalled();
  });

  it("starts a new conversation by stopping the run and forgetting the thread", () => {
    localStorage.setItem(THREADS, JSON.stringify({ vid: "thread-1", other: "t2" }));
    const { result } = renderHook(() => useVideoConversation("vid"));
    act(() => result.current.startNew());
    expect(stop).toHaveBeenCalled();
    expect(options.threadId).toBeNull();
    expect(JSON.parse(localStorage.getItem(THREADS)!)).toEqual({ other: "t2" });
  });

  it("drops a remembered thread that the server no longer has", () => {
    localStorage.setItem(THREADS, JSON.stringify({ vid: "gone" }));
    renderHook(() => useVideoConversation("vid"));
    act(() => options.onError({ status: 404 }));
    expect(options.threadId).toBeNull();
    expect(localStorage.getItem(THREADS)).toBe("{}");
  });

  it("surfaces stream errors as readable text", () => {
    streamState = { error: new Error("Run failed") };
    const { result } = renderHook(() => useVideoConversation("vid"));
    expect(result.current.error).toBe("Run failed");
  });
});
