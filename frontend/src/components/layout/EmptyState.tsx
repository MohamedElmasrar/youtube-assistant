import { MessageSquareText } from "lucide-react";

export function EmptyState() {
  return (
    <div className="flex flex-1 items-center justify-center p-6">
      <div className="max-w-sm space-y-2 text-center">
        <MessageSquareText className="mx-auto size-8 text-muted-foreground" aria-hidden />
        <h2 className="text-base font-medium">Paste a YouTube link to begin</h2>
        <p className="text-sm text-muted-foreground">
          Watch the video, search its transcript, and ask questions. Answers cite the moments in
          the video they come from.
        </p>
      </div>
    </div>
  );
}
