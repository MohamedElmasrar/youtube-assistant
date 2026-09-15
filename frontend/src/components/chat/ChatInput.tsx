"use client";

import { ArrowUp, Square } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface ChatInputProps {
  onSend: (text: string) => void;
  onStop: () => void;
  isLoading: boolean;
  disabled: boolean;
}

export function ChatInput({ onSend, onStop, isLoading, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");

  const submit = () => {
    if (disabled || isLoading || !value.trim()) return;
    onSend(value);
    setValue("");
  };

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
      className="flex items-end gap-2 border-t p-3"
    >
      <Textarea
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
            event.preventDefault();
            submit();
          }
        }}
        placeholder="Ask about this video"
        aria-label="Ask about this video"
        rows={1}
        disabled={disabled}
        className="max-h-32 min-h-9 resize-none"
      />
      {isLoading ? (
        <Button type="button" size="icon" variant="outline" onClick={onStop} aria-label="Stop response">
          <Square aria-hidden />
        </Button>
      ) : (
        <Button type="submit" size="icon" disabled={disabled || !value.trim()} aria-label="Send message">
          <ArrowUp aria-hidden />
        </Button>
      )}
    </form>
  );
}
