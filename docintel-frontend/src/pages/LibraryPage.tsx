import { useCallback, useEffect, useRef, useState } from "react";
import { BookOpen } from "lucide-react";
import type { DocumentOut } from "@/types";
import { listDocuments, deleteDocument } from "@/lib/documents";
import { UploadPanel } from "@/components/documents/UploadPanel";
import { DocumentRow } from "@/components/documents/DocumentRow";
import { Skeleton } from "@/components/ui/skeleton";

const POLL_INTERVAL_MS = 3000;

export default function LibraryPage() {
  const [documents, setDocuments] = useState<DocumentOut[] | null>(null);
  const pollRef = useRef<number | null>(null);

  const refresh = useCallback(async () => {
    const docs = await listDocuments();
    setDocuments(docs);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Poll while any document is still pending/processing so status updates live.
  useEffect(() => {
    const hasInFlight = documents?.some((d) => d.status === "pending" || d.status === "processing");
    if (hasInFlight) {
      pollRef.current = window.setTimeout(refresh, POLL_INTERVAL_MS);
    }
    return () => {
      if (pollRef.current) window.clearTimeout(pollRef.current);
    };
  }, [documents, refresh]);

  const handleDelete = async (id: string) => {
    setDocuments((prev) => prev?.filter((d) => d.id !== id) ?? null);
    await deleteDocument(id);
  };

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-3xl px-6 py-10">
        <div className="mb-8">
          <h1 className="font-serif text-3xl font-semibold text-foreground">Library</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Add sources here, then ask questions about them in the Assistant.
          </p>
        </div>

        <UploadPanel onIngested={refresh} />

        <div className="mt-8">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-medium text-muted-foreground">
            <BookOpen className="h-4 w-4" />
            {documents ? `${documents.length} source${documents.length === 1 ? "" : "s"}` : "Loading…"}
          </h2>

          {documents === null && (
            <div className="space-y-2">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          )}

          {documents?.length === 0 && (
            <div className="rounded-lg border border-dashed border-border py-12 text-center text-sm text-muted-foreground">
              No sources yet — add your first document above.
            </div>
          )}

          {documents && documents.length > 0 && (
            <div className="rounded-lg border border-border bg-card">
              {documents.map((doc) => (
                <DocumentRow key={doc.id} doc={doc} onDelete={handleDelete} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
