import { useCallback, useRef, useState } from "react";
import { UploadCloud, Link2, Type, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { uploadDocument, ingestUrl, ingestText } from "@/lib/documents";
import { cn } from "@/lib/utils";

type Mode = "file" | "url" | "text";

export function UploadPanel({ onIngested }: { onIngested: () => void }) {
  const [mode, setMode] = useState<Mode>("file");
  const [isDragging, setIsDragging] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [urlValue, setUrlValue] = useState("");
  const [textTitle, setTextTitle] = useState("");
  const [textContent, setTextContent] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setError(null);
    setIsSubmitting(true);
    try {
      for (const file of Array.from(files)) {
        await uploadDocument(file);
      }
      onIngested();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Upload failed. Please try a different file.");
    } finally {
      setIsSubmitting(false);
    }
  }, [onIngested]);

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlValue.trim()) return;
    setError(null);
    setIsSubmitting(true);
    try {
      await ingestUrl(urlValue.trim());
      setUrlValue("");
      onIngested();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Couldn't fetch that URL.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textTitle.trim() || !textContent.trim()) return;
    setError(null);
    setIsSubmitting(true);
    try {
      await ingestText(textTitle.trim(), textContent.trim());
      setTextTitle("");
      setTextContent("");
      onIngested();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Couldn't save that text.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="flex border-b border-border">
        {[
          { key: "file" as Mode, label: "Upload file", icon: UploadCloud },
          { key: "url" as Mode, label: "From URL", icon: Link2 },
          { key: "text" as Mode, label: "Paste text", icon: Type },
        ].map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setMode(key)}
            className={cn(
              "flex flex-1 items-center justify-center gap-2 border-b-2 py-3 text-sm font-medium transition-colors",
              mode === key
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      <div className="p-5">
        {mode === "file" && (
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
              handleFiles(e.dataTransfer.files);
            }}
            onClick={() => fileInputRef.current?.click()}
            className={cn(
              "flex cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed py-10 text-center transition-colors",
              isDragging ? "border-primary bg-secondary/50" : "border-border hover:border-primary/50"
            )}
          >
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".pdf,.docx,.txt,.csv,.xlsx"
              multiple
              onChange={(e) => handleFiles(e.target.files)}
            />
            {isSubmitting ? (
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            ) : (
              <UploadCloud className="h-8 w-8 text-muted-foreground" />
            )}
            <p className="mt-3 text-sm font-medium text-foreground">
              Drop files here, or click to browse
            </p>
            <p className="mt-1 text-xs text-muted-foreground">PDF, DOCX, TXT, CSV, or XLSX</p>
          </div>
        )}

        {mode === "url" && (
          <form onSubmit={handleUrlSubmit} className="flex gap-2">
            <Input
              placeholder="https://example.com/article"
              value={urlValue}
              onChange={(e) => setUrlValue(e.target.value)}
              type="url"
              required
            />
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Adding…" : "Add"}
            </Button>
          </form>
        )}

        {mode === "text" && (
          <form onSubmit={handleTextSubmit} className="space-y-3">
            <Input
              placeholder="Title for this note"
              value={textTitle}
              onChange={(e) => setTextTitle(e.target.value)}
              required
            />
            <Textarea
              placeholder="Paste your text here…"
              rows={5}
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              required
            />
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving…" : "Save"}
            </Button>
          </form>
        )}

        {error && (
          <p className="mt-3 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
        )}
      </div>
    </div>
  );
}
