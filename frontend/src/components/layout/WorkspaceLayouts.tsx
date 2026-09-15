import { MessageSquare, ScrollText } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface LayoutSlots {
  player: React.ReactNode;
  details: React.ReactNode;
  transcript: React.ReactNode;
  chat: React.ReactNode;
}

/** Player + details + transcript on the left, chat on the right. */
export function DesktopLayout({ player, details, transcript, chat }: LayoutSlots) {
  return (
    <main className="grid min-h-0 flex-1 gap-4 p-4 lg:grid-cols-[3fr_2fr]">
      <div className="flex min-h-0 flex-col gap-4 overflow-y-auto">
        {player}
        {details}
        <div className="min-h-80 flex-1">{transcript}</div>
      </div>
      <div className="min-h-0">{chat}</div>
    </main>
  );
}

/** Stacked: player first (kept in view), details, then chat/transcript tabs. */
export function MobileLayout({ player, details, transcript, chat }: LayoutSlots) {
  return (
    <main className="flex-1 overflow-y-auto">
      <div className="sticky top-0 z-10 bg-background p-3 pb-2">{player}</div>
      <div className="space-y-3 px-3 pb-3">
        {details}
        <Tabs defaultValue="chat">
          <TabsList className="w-full">
            <TabsTrigger value="chat">
              <MessageSquare aria-hidden /> Chat
            </TabsTrigger>
            <TabsTrigger value="transcript">
              <ScrollText aria-hidden /> Transcript
            </TabsTrigger>
          </TabsList>
          {/* Keep both mounted so switching tabs never interrupts a streaming answer. */}
          <TabsContent value="chat" keepMounted className="h-[60dvh] data-hidden:hidden">
            {chat}
          </TabsContent>
          <TabsContent value="transcript" keepMounted className="h-[60dvh] data-hidden:hidden">
            {transcript}
          </TabsContent>
        </Tabs>
      </div>
    </main>
  );
}
