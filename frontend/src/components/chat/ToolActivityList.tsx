import { Check, Loader2, Search } from "lucide-react";
import type { ToolActivity } from "@/lib/chat/messages";

/** Compact status lines for the tools the agent used (or is using) for an answer. */
export function ToolActivityList({ activities }: { activities: ToolActivity[] }) {
  if (activities.length === 0) return null;
  return (
    <ul className="space-y-1" aria-label="Assistant activity">
      {activities.map((activity) => (
        <li key={activity.id} className="flex items-center gap-1.5 text-xs text-muted-foreground">
          {activity.done ? (
            <Check className="size-3.5 shrink-0" aria-hidden />
          ) : (
            <Loader2 className="size-3.5 shrink-0 animate-spin" aria-hidden />
          )}
          <Search className="size-3.5 shrink-0" aria-hidden />
          <span className="truncate">
            {activity.label}
            {activity.detail && <> · “{activity.detail}”</>}
          </span>
        </li>
      ))}
    </ul>
  );
}
