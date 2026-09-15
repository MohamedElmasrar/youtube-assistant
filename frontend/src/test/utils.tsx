import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import { vi } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { PlayerProvider } from "@/lib/player/context";
import { PlayerController } from "@/lib/player/controller";

/** Renders with the app's providers; `seekTo` is spied so tests can assert player seeks. */
export function renderWithProviders(ui: React.ReactElement) {
  const seekTo = vi.spyOn(PlayerController.prototype, "seekTo").mockImplementation(() => {});
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={client}>
        <TooltipProvider>
          <PlayerProvider>{children}</PlayerProvider>
        </TooltipProvider>
      </QueryClientProvider>
    );
  }
  return { ...render(ui, { wrapper: Wrapper }), seekTo };
}
