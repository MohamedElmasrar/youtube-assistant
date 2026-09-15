"use client";

import { AppHeader } from "@/components/layout/AppHeader";
import { EmptyState } from "@/components/layout/EmptyState";
import { DesktopLayout, MobileLayout } from "@/components/layout/WorkspaceLayouts";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { TranscriptPanel } from "@/components/transcript/TranscriptPanel";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { VideoDetails } from "@/components/video/VideoDetails";
import { VideoPlayer } from "@/components/video/VideoPlayer";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { useSelectedVideo } from "@/hooks/useSelectedVideo";
import { useVideo } from "@/hooks/useVideo";

export function Workspace() {
  const [videoId, selectVideo] = useSelectedVideo();
  const video = useVideo(videoId);
  const isDesktop = useMediaQuery("(min-width: 1024px)", true);

  // Ingestion has settled (indexed, or failed in a way the transcript endpoint may still serve).
  const settled = video.isSuccess;
  const problem = video.error
    ? video.error.message
    : video.data?.status === "failed"
      ? (video.data.error?.message ?? "This video could not be prepared.")
      : null;
  const chatNotice = video.isPending
    ? "Preparing the video. The first load can take a moment."
    : problem
      ? "Chat is unavailable for this video."
      : null;

  return (
    <div className="flex h-dvh flex-col">
      <AppHeader onSubmit={selectVideo} loading={video.isFetching} />
      {videoId === null ? (
        <EmptyState />
      ) : (
        <WorkspaceBody
          isDesktop={isDesktop}
          slots={{
            player: <VideoPlayer videoId={videoId} />,
            details: (
              <div className="space-y-3">
                <VideoDetails videoId={videoId} metadata={video.data?.metadata} loading={video.isPending} />
                {problem && (
                  <Alert variant="destructive">
                    <AlertDescription>{problem}</AlertDescription>
                  </Alert>
                )}
              </div>
            ),
            transcript: <TranscriptPanel videoId={videoId} enabled={settled} />,
            chat: <ChatPanel key={videoId} videoId={videoId} unavailableReason={chatNotice} />,
          }}
        />
      )}
    </div>
  );
}

function WorkspaceBody({
  isDesktop,
  slots,
}: {
  isDesktop: boolean;
  slots: React.ComponentProps<typeof DesktopLayout>;
}) {
  return isDesktop ? <DesktopLayout {...slots} /> : <MobileLayout {...slots} />;
}
