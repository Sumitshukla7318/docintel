import { FileText, FileSpreadsheet, Globe, StickyNote, Trash2, Loader2, CheckCircle2, XCircle, Clock } from "lucide-react";
import type { DocumentOut } from "@/types";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const ICONS: Record<string, typeof FileText> = {
  file_pdf: FileText,
  file_docx: FileText,
  file_txt: FileText,
  file_csv: FileSpreadsheet,
  file_xlsx: FileSpreadsheet,
  url: Globe,
  raw_text: StickyNote,
};

const STATUS_CONFIG: Record<string, { label: string; variant: "default" | "secondary" | "success" | "destructive"; icon: typeof Clock }> = {
  pending: { label: "Queued", variant: "secondary", icon: Clock },
  processing: { label: "Processing", variant: "secondary", icon: Loader2 },
  completed: { label: "Ready", variant: "success", icon: CheckCircle2 },
  failed: { label: "Failed", variant: "destructive", icon: XCircle },
};

function formatBytes(bytes: number | null): string {
  if (!bytes) return "—";
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(0)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}

export function DocumentRow({ doc, onDelete }: { doc: DocumentOut; onDelete: (id: string) => void }) {
  const Icon = ICONS[doc.source_type] || FileText;
  const status = STATUS_CONFIG[doc.status];
  const StatusIcon = status.icon;

  return (
    <div className="group flex items-center gap-4 border-b border-border px-5 py-3.5 last:border-b-0 hover:bg-secondary/30">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-secondary text-secondary-foreground">
        <Icon className="h-4 w-4" />
      </div>

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-foreground">{doc.title}</p>
        <p className="text-xs text-muted-foreground">
          {formatBytes(doc.file_size_bytes)}
          {doc.num_chunks ? ` · ${doc.num_chunks} chunks` : ""}
        </p>
        {doc.status === "failed" && doc.error_message && (
          <p className="mt-1 text-xs text-destructive">{doc.error_message}</p>
        )}
      </div>

      <Badge variant={status.variant} className="gap-1">
        <StatusIcon className={cn("h-3 w-3", doc.status === "processing" && "animate-spin")} />
        {status.label}
      </Badge>

      <button
        onClick={() => onDelete(doc.id)}
        className="rounded-md p-1.5 text-muted-foreground opacity-0 transition-opacity hover:bg-destructive/10 hover:text-destructive group-hover:opacity-100"
        title="Delete document"
      >
        <Trash2 className="h-4 w-4" />
      </button>
    </div>
  );
}
