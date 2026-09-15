import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Workspace } from "@/components/layout/Workspace";
import { ApiError } from "@/lib/api/client";
import { renderWithProviders } from "@/test/utils";

const ingestVideo = vi.fn();
const fetchTranscript = vi.fn();
vi.mock("@/lib/api/videos", () => ({
  ingestVideo: (...args: unknown[]) => ingestVideo(...args),
  fetchTranscript: (...args: unknown[]) => fetchTranscript(...args),
}));
// The YouTube iframe cannot run in jsdom.
vi.mock("@/components/video/VideoPlayer", () => ({
  VideoPlayer: ({ videoId }: { videoId: string }) => <div data-testid="player">{videoId}</div>,
}));
vi.mock("@/hooks/useVideoConversation", () => ({
  useVideoConversation: (videoId: string) => ({
    messages: [], isLoading: false, isRestoring: false, error: null,
    send: vi.fn(), stop: vi.fn(), startNew: vi.fn(), videoId,
  }),
}));

const metadata = (id: string, title: string) => ({
  video_id: id, available: true, title, channel_title: "Channel", description: "About it",
  published_at: "2024-01-02T00:00:00Z", duration_seconds: 125,
});
const ready = (id: string, title: string) => ({
  video_id: id, status: "ready", cached: false, language: "en", chunk_count: 3, metadata: metadata(id, title),
});
const transcript = (id: string, text: string) => ({
  video_id: id, language: "en", is_generated: false, segments: [{ start: 3, duration: 2, text }],
});

async function load(url: string) {
  const input = screen.getByLabelText("YouTube video URL");
  await userEvent.clear(input);
  await userEvent.type(input, `${url}{enter}`);
}

describe("Workspace", () => {
  beforeEach(() => {
    ingestVideo.mockImplementation(async (id: string) => ready(id, `Title ${id}`));
    fetchTranscript.mockImplementation(async (id: string) => transcript(id, `line of ${id}`));
  });

  it("starts empty, then shows player, details, transcript and chat", async () => {
    renderWithProviders(<Workspace />);
    expect(screen.getByText("Paste a YouTube link to begin")).toBeInTheDocument();
    await load("https://youtu.be/aaaaaaaaaaa");
    expect(screen.getByTestId("player")).toHaveTextContent("aaaaaaaaaaa");
    expect(await screen.findByText("Title aaaaaaaaaaa")).toBeInTheDocument();
    expect(await screen.findByText("line of aaaaaaaaaaa")).toBeInTheDocument();
    expect(screen.getByLabelText("Ask about this video")).toBeEnabled();
    expect(ingestVideo).toHaveBeenCalledWith("aaaaaaaaaaa", expect.anything());
  });

  it("switches videos without showing stale data", async () => {
    renderWithProviders(<Workspace />);
    await load("aaaaaaaaaaa");
    await screen.findByText("line of aaaaaaaaaaa");
    await load("bbbbbbbbbbb");
    expect(screen.getByTestId("player")).toHaveTextContent("bbbbbbbbbbb");
    expect(await screen.findByText("line of bbbbbbbbbbb")).toBeInTheDocument();
    expect(screen.queryByText("line of aaaaaaaaaaa")).not.toBeInTheDocument();
    expect(screen.getByText("Title bbbbbbbbbbb")).toBeInTheDocument();
  });

  it("restores the last video after a refresh", async () => {
    localStorage.setItem("youtube-assistant:last-video", "ccccccccccc");
    renderWithProviders(<Workspace />);
    expect(await screen.findByText("Title ccccccccccc")).toBeInTheDocument();
  });

  it("falls back gracefully when metadata is unavailable", async () => {
    ingestVideo.mockImplementation(async (id: string) => ({
      ...ready(id, ""), metadata: { video_id: id, available: false },
    }));
    renderWithProviders(<Workspace />);
    await load("aaaaaaaaaaa");
    expect(await screen.findByText(/Video details are unavailable/)).toBeInTheDocument();
    expect(await screen.findByText("line of aaaaaaaaaaa")).toBeInTheDocument();
    expect(screen.getByLabelText("Ask about this video")).toBeEnabled();
  });

  it("disables chat and explains when the video has no transcript", async () => {
    ingestVideo.mockImplementation(async (id: string) => ({
      ...ready(id, "T"), status: "failed", chunk_count: 0,
      error: { code: "transcript_unavailable", message: "No captions are available for this video.", stage: "fetch_transcript" },
    }));
    fetchTranscript.mockRejectedValue(new ApiError("No captions are available for this video.", "transcript_unavailable", 404));
    renderWithProviders(<Workspace />);
    await load("aaaaaaaaaaa");
    await waitFor(() => expect(screen.getByLabelText("Ask about this video")).toBeDisabled());
    expect(screen.getAllByText("No captions are available for this video.").length).toBeGreaterThan(0);
    expect(screen.getByTestId("player")).toBeInTheDocument();
  });

  it("shows a backend connection error", async () => {
    ingestVideo.mockRejectedValue(new ApiError("Cannot reach the backend. Is `langgraph dev` running?", "network_error", 0));
    renderWithProviders(<Workspace />);
    await load("aaaaaaaaaaa");
    expect(await screen.findByText(/Cannot reach the backend/)).toBeInTheDocument();
  });
});
