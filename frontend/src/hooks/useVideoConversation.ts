"use client";

import type { Message } from "@langchain/langgraph-sdk";
import { useStream } from "@langchain/langgraph-sdk/react";
import { useState } from "react";
import { ASSISTANT_ID, API_URL } from "@/lib/config";
import { readJson, writeStorage } from "@/lib/storage";

interface ConversationState extends Record<string, unknown> {
  messages: Message[];
  video_id?: string;
}

const THREADS_KEY = "youtube-assistant:threads";

type ThreadMap = Record<string, string>;

function saveThread(videoId: string, threadId: string | null) {
  const threads = readJson<ThreadMap>(THREADS_KEY, {});
  if (threadId) threads[videoId] = threadId;
  else delete threads[videoId];
  writeStorage(THREADS_KEY, JSON.stringify(threads));
}

function isNotFound(error: unknown): boolean {
  return typeof error === "object" && error !== null && "status" in error && error.status === 404;
}

export function errorMessage(error: unknown): string {
  if (error instanceof Error && error.message) return error.message;
  if (typeof error === "string") return error;
  if (typeof error === "object" && error !== null && "message" in error) {
    return String((error as { message: unknown }).message);
  }
  return "Something went wrong. Please try again.";
}

/**
 * One LangGraph thread per video. The thread ID is remembered in localStorage so the
 * conversation is restored after a refresh; the Agent Server owns the actual history.
 * Mount with `key={videoId}` so state resets when the video changes.
 */
export function useVideoConversation(videoId: string) {
  const [threadId, setThreadId] = useState<string | null>(
    () => readJson<ThreadMap>(THREADS_KEY, {})[videoId] ?? null,
  );

  const stream = useStream<ConversationState>({
    apiUrl: API_URL,
    assistantId: ASSISTANT_ID,
    threadId,
    onThreadId: (id) => {
      saveThread(videoId, id);
      setThreadId(id);
    },
    onError: (error) => {
      // A remembered thread that no longer exists on the server: start fresh next time.
      if (isNotFound(error)) {
        saveThread(videoId, null);
        setThreadId(null);
      }
    },
  });

  const send = (text: string) => {
    const content = text.trim();
    if (!content || stream.isLoading) return;
    void stream.submit(
      { messages: [{ type: "human", content }] },
      {
        // The trusted video binding. The backend pins the thread to this video.
        context: { video_id: videoId },
        optimisticValues: (previous) => ({
          ...previous,
          messages: [
            ...(previous.messages ?? []),
            { type: "human", content, id: crypto.randomUUID() },
          ],
        }),
      },
    );
  };

  const startNew = () => {
    void stream.stop();
    saveThread(videoId, null);
    setThreadId(null);
  };

  return {
    messages: stream.messages,
    isLoading: stream.isLoading,
    isRestoring: stream.isThreadLoading,
    error: stream.error ? errorMessage(stream.error) : null,
    send,
    stop: () => void stream.stop(),
    startNew,
  };
}
