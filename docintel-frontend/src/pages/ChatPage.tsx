import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { BookOpen, Loader2, PanelLeft } from "lucide-react";
import type { ChatSessionOut, ChatMessageOut } from "@/types";
import { listSessions, getSessionDetail, sendQuery } from "@/lib/chat";
import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ChatComposer } from "@/components/chat/ChatComposer";
import { useAuth } from "@/context/AuthContext";

export default function ChatPage() {
  const { sessionId } = useParams<{ sessionId?: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [sessions, setSessions] = useState<ChatSessionOut[]>([]);
  const [messages, setMessages] = useState<ChatMessageOut[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [isLoadingSession, setIsLoadingSession] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const refreshSessions = useCallback(async () => {
    const data = await listSessions();
    setSessions(data);
  }, []);

  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  useEffect(() => {
    if (!sessionId) {
      setMessages([]);
      return;
    }
    setIsLoadingSession(true);
    getSessionDetail(sessionId)
      .then((detail) => setMessages(detail.messages))
      .finally(() => setIsLoadingSession(false));
  }, [sessionId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleSend = async (content: string) => {
    const optimisticUserMessage: ChatMessageOut = {
      id: `temp-${Date.now()}`,
      role: "user",
      content,
      citations: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUserMessage]);
    setIsSending(true);

    try {
      const response = await sendQuery({ message: content, session_id: sessionId });

      if (!sessionId) {
        // First message in a brand-new conversation — adopt the session the backend created.
        navigate(`/chat/${response.session_id}`, { replace: true });
        refreshSessions();
      }

      const assistantMessage: ChatMessageOut = {
        id: response.message_id,
        role: "assistant",
        content: response.answer,
        citations: response.citations,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: ChatMessageOut = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: err?.response?.data?.detail || "Something went wrong answering that. Please try again.",
        citations: null,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="flex h-full">
      <ChatSidebar
        sessions={sessions}
        activeSessionId={sessionId ?? null}
        onSelect={(id) => {
          navigate(`/chat/${id}`);
          setIsSidebarOpen(false);
        }}
        onNew={() => {
          navigate("/chat");
          setIsSidebarOpen(false);
        }}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      <div className="flex flex-1 flex-col">
        <div className="flex items-center gap-2 border-b border-border px-4 py-2.5 lg:hidden">
          <button
            onClick={() => setIsSidebarOpen(true)}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-secondary"
            aria-label="Show conversations"
          >
            <PanelLeft className="h-4 w-4" />
          </button>
          <span className="text-sm font-medium text-foreground">Conversations</span>
        </div>

        <div ref={scrollRef} className="flex-1 overflow-y-auto py-4">
          {!sessionId && messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center px-6 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-secondary">
                <BookOpen className="h-6 w-6 text-secondary-foreground" />
              </div>
              <h2 className="mt-4 font-serif text-xl font-semibold text-foreground">
                Ask anything about your library
              </h2>
              <p className="mt-1 max-w-sm text-sm text-muted-foreground">
                Every answer is grounded in your uploaded documents and cited back to its source.
              </p>
            </div>
          )}

          {isLoadingSession && (
            <div className="flex justify-center py-10">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          )}

          {!isLoadingSession &&
            messages.map((message) => (
              <MessageBubble key={message.id} message={message} userLabel={user?.full_name || user?.email || "You"} />
            ))}

          {isSending && (
            <div className="flex gap-3 px-6 py-3">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-secondary font-mono text-[10px] font-medium text-secondary-foreground">
                AI
              </div>
              <div className="flex items-center gap-1 rounded-2xl rounded-tl-sm border border-border bg-card px-4 py-3">
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground" />
              </div>
            </div>
          )}
        </div>

        <ChatComposer onSend={handleSend} disabled={isSending} />
      </div>
    </div>
  );
}
