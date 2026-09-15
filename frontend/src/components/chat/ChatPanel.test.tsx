import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { renderWithProviders } from "@/test/utils";

const conversation = {
  messages: [] as unknown[],
  isLoading: false,
  isRestoring: false,
  error: null as string | null,
  send: vi.fn(),
  stop: vi.fn(),
  startNew: vi.fn(),
};
vi.mock("@/hooks/useVideoConversation", () => ({ useVideoConversation: () => conversation }));

const citation = {
  chunk_id: "abc_5",
  video_id: "abc",
  start_time: 125,
  end_time: 150,
  text: "Attention weighs tokens.",
};

describe("ChatPanel", () => {
  beforeEach(() => {
    Object.assign(conversation, { messages: [], isLoading: false, error: null, isRestoring: false });
  });

  it("sends a question with Enter and clears the box", async () => {
    renderWithProviders(<ChatPanel videoId="abc" unavailableReason={null} />);
    await userEvent.type(screen.getByLabelText("Ask about this video"), "Why?{enter}");
    expect(conversation.send).toHaveBeenCalledWith("Why?");
    expect(screen.getByLabelText("Ask about this video")).toHaveValue("");
  });

  it("offers suggestions that send immediately", async () => {
    renderWithProviders(<ChatPanel videoId="abc" unavailableReason={null} />);
    await userEvent.click(screen.getByRole("button", { name: "Summarize this video" }));
    expect(conversation.send).toHaveBeenCalledWith("Summarize this video");
  });

  it("renders a streaming answer and tool activity", () => {
    conversation.isLoading = true;
    conversation.messages = [
      { type: "human", id: "1", content: "Where is attention explained?" },
      {
        type: "ai",
        id: "2",
        content: "",
        tool_calls: [{ id: "t", name: "search_video_transcript", args: { query: "attention" } }],
      },
      { type: "ai", id: "3", content: "It is explained near the start [[abc" },
    ];
    renderWithProviders(<ChatPanel videoId="abc" unavailableReason={null} />);
    expect(screen.getByText("Where is attention explained?")).toBeInTheDocument();
    expect(screen.getByText(/Searching transcript/)).toBeInTheDocument();
    expect(screen.getByText(/It is explained near the start/)).toBeInTheDocument();
    expect(screen.queryByText(/\[\[/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Stop response" })).toBeInTheDocument();
  });

  it("shows validated citations as links that seek the player", async () => {
    conversation.messages = [
      { type: "human", id: "1", content: "q" },
      {
        type: "ai",
        id: "2",
        content: "Attention weighs tokens [[abc_5]] and also [[abc_99]].",
        additional_kwargs: { citations: [citation] },
      },
    ];
    const { seekTo } = renderWithProviders(<ChatPanel videoId="abc" unavailableReason={null} />);
    const link = screen.getByRole("button", { name: "Play from 2:05" });
    await userEvent.click(link);
    expect(seekTo).toHaveBeenCalledWith(125);
    expect(screen.queryByText(/abc_99/)).not.toBeInTheDocument();
  });

  it("disables input and explains when chat is unavailable", () => {
    renderWithProviders(<ChatPanel videoId="abc" unavailableReason="Chat is unavailable for this video." />);
    expect(screen.getByLabelText("Ask about this video")).toBeDisabled();
    expect(screen.getByText("Chat is unavailable for this video.")).toBeInTheDocument();
  });

  it("shows run errors and lets the user start over", async () => {
    conversation.error = "Run failed";
    conversation.messages = [{ type: "human", id: "1", content: "q" }];
    renderWithProviders(<ChatPanel videoId="abc" unavailableReason={null} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Run failed");
    await userEvent.click(screen.getByRole("button", { name: /new conversation/i }));
    expect(conversation.startNew).toHaveBeenCalled();
  });
});
