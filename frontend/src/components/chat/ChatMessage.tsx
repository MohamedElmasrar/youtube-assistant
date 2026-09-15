import type { Message } from "@langchain/langgraph-sdk";
import { AssistantContent } from "@/components/chat/AssistantContent";
import { ToolActivityList } from "@/components/chat/ToolActivityList";
import { messageCitations, messageText, toolActivities } from "@/lib/chat/messages";

interface ChatMessageProps {
  message: Message;
  allMessages: Message[];
}

export function ChatMessage({ message, allMessages }: ChatMessageProps) {
  const text = messageText(message);

  if (message.type === "human") {
    return (
      <div className="flex justify-end">
        <p className="max-w-[85%] rounded-2xl rounded-br-sm bg-primary px-3.5 py-2 text-sm whitespace-pre-wrap text-primary-foreground">
          {text}
        </p>
      </div>
    );
  }

  if (message.type !== "ai") return null;
  const activities = toolActivities(message, allMessages);
  if (!text && activities.length === 0) return null;

  return (
    <div className="max-w-[95%] space-y-2">
      <ToolActivityList activities={activities} />
      {text && <AssistantContent text={text} citations={messageCitations(message)} />}
    </div>
  );
}
