"use client";

import { ExternalLink } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { usePlayerController } from "@/lib/player/context";
import { loadYouTubeApi } from "@/lib/player/youtube-api";

// YouTube error codes meaning "cannot be played in an embedded player".
const UNPLAYABLE = new Set([2, 5, 100, 101, 150]);

export function VideoPlayer({ videoId }: { videoId: string }) {
  const controller = usePlayerController();
  const host = useRef<HTMLDivElement>(null);
  const player = useRef<YT.Player | null>(null);
  const videoIdRef = useRef(videoId);
  const [failure, setFailure] = useState<{ videoId: string; message: string } | null>(null);

  // Create the player once. Later video changes reuse it so the iframe never remounts.
  useEffect(() => {
    let cancelled = false;
    const mount = document.createElement("div");
    host.current?.appendChild(mount);

    loadYouTubeApi()
      .then(() => {
        if (cancelled) return;
        player.current = new YT.Player(mount, {
          videoId: videoIdRef.current,
          width: "100%",
          height: "100%",
          playerVars: { rel: 0, playsinline: 1 },
          events: {
            onReady: (event) => controller.attach(event.target),
            onStateChange: (event) => controller.handleStateChange(event.data),
            onError: (event) => {
              if (UNPLAYABLE.has(event.data)) {
                setFailure({
                  videoId: videoIdRef.current,
                  message: "This video cannot be played in an embedded player.",
                });
              }
            },
          },
        });
      })
      .catch((error: Error) =>
        setFailure({ videoId: videoIdRef.current, message: error.message }),
      );

    return () => {
      cancelled = true;
      controller.detach();
      player.current?.destroy();
      player.current = null;
      mount.remove();
    };
  }, [controller]);

  useEffect(() => {
    if (videoIdRef.current === videoId) return;
    videoIdRef.current = videoId;
    player.current?.loadVideoById(videoId);
  }, [videoId]);

  const error = failure?.videoId === videoId ? failure.message : null;

  return (
    <div className="relative aspect-video w-full overflow-hidden rounded-lg border bg-black shadow-sm">
      <div ref={host} className="size-full [&_iframe]:size-full" />
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-background/95 p-4">
          <Alert className="max-w-md">
            <AlertTitle>Playback unavailable</AlertTitle>
            <AlertDescription>
              {error}{" "}
              <a
                className="inline-flex items-center gap-1 underline underline-offset-2"
                href={`https://www.youtube.com/watch?v=${videoId}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                Watch on YouTube <ExternalLink className="size-3" aria-hidden />
              </a>
            </AlertDescription>
          </Alert>
        </div>
      )}
    </div>
  );
}
