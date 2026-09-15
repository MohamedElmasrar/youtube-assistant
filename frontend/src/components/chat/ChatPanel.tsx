"use client";

import { Loader2, MessageSquarePlus } from "lucide-react";
import { ChatInput } from "@/components/chat/ChatInput";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useStickToBottom } from "@/hooks/useStickToBottom";
import { useVideoConversation } from "@/hooks/useVideoConversation";
import { messageText } from "@/lib/chat/messages";

const SUGGESTIONS = ["Summarize this video", "What are the main topics?"];

interface ChatPanelProps {
  videoId: string;
  /** Why chat is unavailable (e.g. no transcript), or null when ready. */
  unavailableReason: string | null;
}

/** Mount with `key={videoId}` so each video gets its own conversation state. */
export function ChatPanel({ videoId, unavailableReason }: ChatPanelProps) {
  const chat = useVideoConversation(videoId);
  const { messages, isLoading } = chat;
  const last = messages.at(-1);
  const anchor = useStickToBottom(`${messages.length}:${last ? messageText(last).length : 0}`);
  const disabled = unavailableReason !== null || chat.isRestoring;
  const waiting = isLoading && (!last || last.type !== "ai" || messageText(last) === "");

  return (
    <section aria-label="Chat" className="flex h-full min-h-0 flex-col rounded-lg border bg-card">
      <header className="flex items-center justify-between border-b px-3 py-2">
        <h2 className="text-sm font-medium">Ask about this video</h2>
        <Button
          variant="ghost"
          size="sm"
          onClick={chat.startNew}
          disabled={messages.length === 0 && !isLoading}
        >
          <MessageSquarePlus aria-hidden />
          New conversation
        </Button>
      </header>

      <ScrollArea className="min-h-0 flex-1">
        <div className="space-y-4 p-3" aria-live="polite">
          {chat.isRestoring && (
            <p className="text-sm text-muted-foreground">Restoring conversation…</p>
          )}
          {messages.length === 0 && !chat.isRestoring && (
            <div className="space-y-3 py-6 text-center">
              <p className="text-sm text-muted-foreground">
                {unavailableReason ?? "Answers come from the transcript, with timestamps you can click."}
              </p>
              {!unavailableReason && (
                <div className="flex flex-wrap justify-center gap-2">
                  {SUGGESTIONS.map((suggestion) => (
                    <Button key={suggestion} variant="outline" size="sm" onClick={() => chat.send(suggestion)}>
                      {suggestion}
                    </Button>
                  ))}
                </div>
              )}
            </div>
          )}
          {messages.map((message, index) => (
            <ChatMessage key={message.id ?? index} message={message} allMessages={messages} />
          ))}
          {waiting && (
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" aria-hidden /> Thinking…
            </p>
          )}
          {chat.error && (
            <Alert variant="destructive" role="alert">
              <AlertDescription>{chat.error}</AlertDescription>
            </Alert>
          )}
          <div ref={anchor} />
        </div>
      </ScrollArea>

      <ChatInput onSend={chat.send} onStop={chat.stop} isLoading={isLoading} disabled={disabled} />
    </section>
  );
}
