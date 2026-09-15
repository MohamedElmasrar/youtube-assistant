"use client";

import { LocateFixed, Search } from "lucide-react";
import { useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import { TranscriptSegmentRow } from "@/components/transcript/TranscriptSegmentRow";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { useTranscript } from "@/hooks/useVideo";
import { useActiveSegmentIndex } from "@/lib/player/context";

const VIEWPORT = '[data-slot="scroll-area-viewport"]';

function TranscriptSkeleton() {
  return (
    <div className="space-y-3 p-3" aria-busy="true" aria-label="Loading transcript">
      {Array.from({ length: 8 }, (_, i) => (
        <Skeleton key={i} className="h-4 w-full" />
      ))}
    </div>
  );
}

export function TranscriptPanel({ videoId, enabled }: { videoId: string; enabled: boolean }) {
  const { data, error, isLoading } = useTranscript(videoId, enabled);
  const segments = useMemo(() => data?.segments ?? [], [data]);
  const activeIndex = useActiveSegmentIndex(segments);
  const [search, setSearch] = useState("");
  const [follow, setFollow] = useState(true);
  const list = useRef<HTMLUListElement>(null);

  const query = useDeferredValue(search.trim().toLowerCase());
  const visible = useMemo(
    () =>
      segments
        .map((segment, index) => ({ segment, index }))
        .filter(({ segment }) => !query || segment.text.toLowerCase().includes(query)),
    [segments, query],
  );

  // Keep the playing line in view without scrolling the rest of the page.
  useEffect(() => {
    if (!follow || query || activeIndex < 0) return;
    const row = list.current?.querySelector<HTMLElement>(`[data-index="${activeIndex}"]`);
    const viewport = row?.closest<HTMLElement>(VIEWPORT);
    if (!row || !viewport) return;
    const rowBox = row.getBoundingClientRect();
    const viewBox = viewport.getBoundingClientRect();
    if (rowBox.top < viewBox.top || rowBox.bottom > viewBox.bottom) {
      viewport.scrollTo({
        top: viewport.scrollTop + rowBox.top - viewBox.top - viewport.clientHeight / 3,
        behavior: "smooth",
      });
    }
  }, [activeIndex, follow, query]);

  return (
    <section aria-label="Transcript" className="flex h-full min-h-0 flex-col rounded-lg border bg-card">
      <header className="flex items-center gap-2 border-b p-2">
        <div className="relative flex-1">
          <Search
            className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden
          />
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search transcript"
            aria-label="Search transcript"
            className="pl-8"
            disabled={segments.length === 0}
          />
        </div>
        {data && (
          <Badge variant="secondary" title={data.is_generated ? "Auto-generated captions" : "Captions"}>
            {data.language}
            {data.is_generated ? " · auto" : ""}
          </Badge>
        )}
        <Button
          variant={follow ? "secondary" : "ghost"}
          size="icon"
          aria-pressed={follow}
          aria-label="Follow playback"
          title="Follow playback"
          onClick={() => setFollow(!follow)}
        >
          <LocateFixed aria-hidden />
        </Button>
      </header>

      <div className="min-h-0 flex-1">
        {isLoading ? (
          <TranscriptSkeleton />
        ) : error ? (
          <div className="p-3">
            <Alert variant="destructive">
              <AlertDescription>{error.message}</AlertDescription>
            </Alert>
          </div>
        ) : !enabled ? (
          <TranscriptSkeleton />
        ) : visible.length === 0 ? (
          <p className="p-4 text-sm text-muted-foreground">
            {query ? "No matching lines." : "This video has no transcript."}
          </p>
        ) : (
          <ScrollArea className="h-full">
            <ul ref={list} className="p-1.5">
              {visible.map(({ segment, index }) => (
                <TranscriptSegmentRow
                  key={index}
                  segment={segment}
                  index={index}
                  active={index === activeIndex}
                  query={query}
                />
              ))}
            </ul>
          </ScrollArea>
        )}
      </div>
    </section>
  );
}
