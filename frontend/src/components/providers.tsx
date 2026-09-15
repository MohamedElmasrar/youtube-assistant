"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { TooltipProvider } from "@/components/ui/tooltip";
import { PlayerProvider } from "@/lib/player/context";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          // Video metadata and transcripts are stable; fetch once per session.
          queries: { staleTime: Infinity, retry: false, refetchOnWindowFocus: false },
        },
      }),
  );
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <PlayerProvider>{children}</PlayerProvider>
      </TooltipProvider>
    </QueryClientProvider>
  );
}
