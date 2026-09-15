import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { VideoUrlInput } from "@/components/video/VideoUrlInput";

describe("VideoUrlInput", () => {
  it("submits the extracted video id", async () => {
    const onSubmit = vi.fn();
    render(<VideoUrlInput onSubmit={onSubmit} loading={false} />);
    await userEvent.type(
      screen.getByLabelText("YouTube video URL"),
      "https://youtu.be/dQw4w9WgXcQ{enter}",
    );
    expect(onSubmit).toHaveBeenCalledWith("dQw4w9WgXcQ");
  });

  it("shows an error for invalid input and does not submit", async () => {
    const onSubmit = vi.fn();
    render(<VideoUrlInput onSubmit={onSubmit} loading={false} />);
    await userEvent.type(screen.getByLabelText("YouTube video URL"), "not a video{enter}");
    expect(screen.getByRole("alert")).toHaveTextContent("valid YouTube");
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("disables loading while a video is being prepared", () => {
    render(<VideoUrlInput onSubmit={() => {}} loading />);
    expect(screen.getByRole("button", { name: /load/i })).toBeDisabled();
  });
});
