import { useState } from "react";
import type { KeyboardEvent } from "react";
import { SendHorizontal } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

export function ChatComposer({
  onSend,
  disabled,
}: {
  onSend: (message: string) => void;
  disabled: boolean;
}) {
  const [value, setValue] = useState("");

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-border bg-card p-4">
      <div className="mx-auto flex max-w-2xl items-end gap-2">
        <Textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your documents…"
          rows={1}
          className="max-h-40 min-h-[42px]"
          disabled={disabled}
        />
        <Button size="icon" onClick={handleSubmit} disabled={disabled || !value.trim()}>
          <SendHorizontal className="h-4 w-4" />
        </Button>
      </div>
      <p className="mx-auto mt-2 max-w-2xl text-center text-xs text-muted-foreground">
        Answers are grounded only in your uploaded documents.
      </p>
    </div>
  );
}
