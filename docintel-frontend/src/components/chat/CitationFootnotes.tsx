import { useState } from "react";
import { FileText } from "lucide-react";
import type { Citation } from "@/types";
import { cn } from "@/lib/utils";

export function CitationFootnotes({ citations }: { citations: Citation[] }) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  if (citations.length === 0) return null;

  return (
    <div className="mt-3 border-t border-border pt-3">
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="mr-1 text-xs font-medium text-muted-foreground">Sources</span>
        {citations.map((citation, i) => (
          <button
            key={citation.chunk_id}
            onClick={() => setOpenIndex(openIndex === i ? null : i)}
            className={cn(
              "flex h-5 w-5 items-center justify-center rounded-full border font-mono text-[10px] font-medium transition-colors",
              openIndex === i
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-secondary text-secondary-foreground hover:border-primary/50"
            )}
            title={citation.document_title}
          >
            {i + 1}
          </button>
        ))}
      </div>

      {openIndex !== null && (
        <div className="mt-2 animate-fade-in rounded-md border border-border bg-secondary/40 p-3">
          <div className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-foreground">
            <FileText className="h-3 w-3" />
            {citations[openIndex].document_title}
            <span className="ml-auto text-muted-foreground">
              {Math.round(citations[openIndex].score * 100)}% match
            </span>
          </div>
          <p className="font-serif text-sm italic leading-relaxed text-muted-foreground">
            "{citations[openIndex].snippet}"
          </p>
        </div>
      )}
    </div>
  );
}
