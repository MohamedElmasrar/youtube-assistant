import { MonitorPlay } from "lucide-react";
import { VideoUrlInput } from "@/components/video/VideoUrlInput";

interface AppHeaderProps {
  onSubmit: (videoId: string) => void;
  loading: boolean;
}

export function AppHeader({ onSubmit, loading }: AppHeaderProps) {
  return (
    <header className="flex flex-wrap items-start gap-x-6 gap-y-2 border-b bg-background px-4 py-3">
      <div className="flex h-8 items-center gap-2">
        <MonitorPlay className="size-5 text-muted-foreground" aria-hidden />
        <h1 className="text-sm font-semibold">YouTube Assistant</h1>
      </div>
      <VideoUrlInput onSubmit={onSubmit} loading={loading} />
    </header>
  );
}
