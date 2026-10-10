import { Plus, MessageCircle, X } from "lucide-react";
import type { ChatSessionOut } from "@/types";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export function ChatSidebar({
  sessions,
  activeSessionId,
  onSelect,
  onNew,
  isOpen,
  onClose,
}: {
  sessions: ChatSessionOut[];
  activeSessionId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  isOpen: boolean;
  onClose: () => void;
}) {
  return (
    <>
      {isOpen && (
        <div className="fixed inset-0 z-30 bg-black/40 lg:hidden" onClick={onClose} aria-hidden="true" />
      )}

      <div
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-72 shrink-0 transform flex-col border-r border-border bg-card transition-transform duration-200 lg:relative lg:z-auto lg:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex items-center gap-2 p-3">
          <Button onClick={onNew} variant="outline" className="flex-1 justify-start gap-2">
            <Plus className="h-4 w-4" />
            New conversation
          </Button>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-secondary lg:hidden"
            aria-label="Close conversations"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 space-y-0.5 overflow-y-auto px-2 pb-3">
          {sessions.length === 0 && (
            <p className="px-3 py-6 text-center text-xs text-muted-foreground">
              Your conversations will appear here.
            </p>
          )}
          {sessions.map((session) => (
            <button
              key={session.id}
              onClick={() => onSelect(session.id)}
              className={cn(
                "flex w-full items-start gap-2 rounded-md px-3 py-2.5 text-left text-sm transition-colors",
                activeSessionId === session.id
                  ? "bg-secondary text-secondary-foreground"
                  : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
              )}
            >
              <MessageCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <span className="truncate">{session.title}</span>
            </button>
          ))}
        </div>
      </div>
    </>
  );
}
