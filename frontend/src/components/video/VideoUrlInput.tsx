"use client";

import { Loader2, Play } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { parseVideoId } from "@/lib/utils/youtube";

interface VideoUrlInputProps {
  onSubmit: (videoId: string) => void;
  loading: boolean;
}

export function VideoUrlInput({ onSubmit, loading }: VideoUrlInputProps) {
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const videoId = parseVideoId(value);
    if (!videoId) {
      setError("Enter a valid YouTube video URL.");
      return;
    }
    setError(null);
    onSubmit(videoId);
  };

  return (
    <form onSubmit={handleSubmit} className="flex w-full max-w-xl items-start gap-2" noValidate>
      <div className="flex-1">
        <Input
          type="url"
          inputMode="url"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder="Paste a YouTube link"
          aria-label="YouTube video URL"
          aria-invalid={error !== null}
          aria-describedby={error ? "video-url-error" : undefined}
        />
        {error && (
          <p id="video-url-error" role="alert" className="mt-1 text-xs text-destructive">
            {error}
          </p>
        )}
      </div>
      <Button type="submit" disabled={loading || value.trim() === ""}>
        {loading ? <Loader2 className="animate-spin" aria-hidden /> : <Play aria-hidden />}
        Load
      </Button>
    </form>
  );
}
