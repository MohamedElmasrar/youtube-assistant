import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { TranscriptPanel } from "@/components/transcript/TranscriptPanel";
import { renderWithProviders } from "@/test/utils";

const useTranscript = vi.fn();
vi.mock("@/hooks/useVideo", () => ({ useTranscript: (...args: unknown[]) => useTranscript(...args) }));

const transcript = {
  video_id: "abc",
  language: "en",
  is_generated: true,
  segments: [
    { start: 0, duration: 4, text: "Welcome to the talk" },
    { start: 65, duration: 4, text: "Attention is all you need" },
    { start: 3725, duration: 4, text: "Thanks for watching" },
  ],
};

describe("TranscriptPanel", () => {
  beforeEach(() => useTranscript.mockReturnValue({ data: transcript, error: null, isLoading: false }));

  it("renders timestamped segments", () => {
    renderWithProviders(<TranscriptPanel videoId="abc" enabled />);
    expect(screen.getByText("1:05")).toBeInTheDocument();
    expect(screen.getByText("1:02:05")).toBeInTheDocument();
    expect(screen.getByText("en · auto")).toBeInTheDocument();
  });

  it("filters by search text", async () => {
    renderWithProviders(<TranscriptPanel videoId="abc" enabled />);
    await userEvent.type(screen.getByLabelText("Search transcript"), "attention");
    const items = await screen.findAllByRole("listitem");
    expect(items).toHaveLength(1);
    expect(within(items[0]).getByText("Attention")).toBeInTheDocument();
  });

  it("seeks the player when a line is clicked", async () => {
    const { seekTo } = renderWithProviders(<TranscriptPanel videoId="abc" enabled />);
    await userEvent.click(screen.getByRole("button", { name: /Attention is all/ }));
    expect(seekTo).toHaveBeenCalledWith(65);
  });

  it("shows loading and error states", () => {
    useTranscript.mockReturnValue({ data: undefined, error: null, isLoading: true });
    const { rerender } = renderWithProviders(<TranscriptPanel videoId="abc" enabled />);
    expect(screen.getByLabelText("Loading transcript")).toBeInTheDocument();
    useTranscript.mockReturnValue({ data: undefined, error: new Error("No captions"), isLoading: false });
    rerender(<TranscriptPanel videoId="abc" enabled />);
    expect(screen.getByText("No captions")).toBeInTheDocument();
  });
});
