import ReactMarkdown from "react-markdown";
import type { ChatMessageOut } from "@/types";
import { CitationFootnotes } from "./CitationFootnotes";
import { Avatar } from "@/components/ui/avatar";

export function MessageBubble({ message, userLabel }: { message: ChatMessageOut; userLabel: string }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex animate-fade-in justify-end gap-3 px-6 py-3">
        <div className="max-w-xl rounded-2xl rounded-tr-sm bg-primary px-4 py-2.5 text-sm text-primary-foreground">
          {message.content}
        </div>
        <Avatar name={userLabel} className="h-7 w-7 shrink-0 text-xs" />
      </div>
    );
  }

  return (
    <div className="flex animate-fade-in gap-3 px-6 py-3">
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-secondary font-mono text-[10px] font-medium text-secondary-foreground">
        AI
      </div>
      <div className="max-w-2xl rounded-2xl rounded-tl-sm border border-border bg-card px-4 py-3">
        <div className="prose-doc font-serif text-[15px] text-foreground">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
        {message.citations && <CitationFootnotes citations={message.citations} />}
      </div>
    </div>
  );
}
