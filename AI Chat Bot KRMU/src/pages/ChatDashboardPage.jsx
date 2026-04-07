import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import AppLayout from "../components/layout/AppLayout";
import ChatSidebar from "../components/chat/ChatSidebar";
import ChatMessage from "../components/chat/ChatMessage";
import ChatInput from "../components/chat/ChatInput";
import Modal from "../components/ui/Modal";
import Skeleton from "../components/ui/Skeleton";
import EmptyState from "../components/ui/EmptyState";
import { useToast } from "../components/ui/ToastProvider";
import { starterMessages } from "../data/mockData";
import { fetchChatHistory, sendChatQuery } from "../services/api";

function ChatDashboardPage() {
  const [messages, setMessages] = useState(starterMessages);
  const [isTyping, setIsTyping] = useState(false);
  const [showHistory, setShowHistory] = useState(true);
  const [newChatModal, setNewChatModal] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [error, setError] = useState("");
  const { pushToast } = useToast();

  useEffect(() => {
    const loadHistory = async () => {
      setLoadingHistory(true);
      setError("");

      try {
        const response = await fetchChatHistory(50);
        const rows = response.data || [];
        const restored = [];

        for (const row of rows.slice().reverse()) {
          restored.push({
            id: `${row.id}-u`,
            role: "user",
            text: row.user_message,
            timestamp: row.created_at,
          });
          restored.push({
            id: `${row.id}-a`,
            role: "assistant",
            text: row.ai_response,
            timestamp: row.created_at,
            chatId: row.id,
            source: row.source || row.metadata?.source || "documents",
          });
        }

        setMessages(restored.length ? restored : starterMessages);
      } catch (err) {
        setError(err.message || "Failed to load chat history");
        pushToast({ title: "History unavailable", message: err.message || "Could not load chat history", type: "error" });
      } finally {
        setLoadingHistory(false);
      }
    };

    loadHistory();
  }, []);

  const historyItems = useMemo(() => {
    return messages
      .filter((message) => message.role === "user")
      .map((message) => message.text)
      .slice(-12)
      .reverse();
  }, [messages]);

  const handleSend = async (text) => {
    setError("");
    const userMessage = { id: Date.now(), role: "user", text, timestamp: new Date() };
    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    try {
      const response = await sendChatQuery(text);
      const data = response.data;
      const assistantMessage = {
        id: `${data.id}-a`,
        role: "assistant",
        text: data.ai_response,
        timestamp: data.created_at || new Date(),
        chatId: data.id,
        source: data.metadata?.source || "documents",
      };
      setMessages((prev) => [...prev, assistantMessage]);
      pushToast({ title: "Response received", message: "Smart Campus AI replied successfully", type: "success", timeout: 1800 });
    } catch (err) {
      setError(err.message || "Failed to get AI response");
      pushToast({ title: "Query failed", message: err.message || "Please try again.", type: "error" });
      const assistantMessage = {
        id: Date.now() + 1,
        role: "assistant",
        text: "I am having trouble reaching the server right now. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const resetChat = () => {
    setMessages(starterMessages);
    setNewChatModal(false);
  };

  return (
    <AppLayout>
      <motion.div
        className="h-[calc(100vh-7.4rem)] min-h-140"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.28 }}
      >
        <div className="mb-3 flex items-center justify-between">
          <h1 className="text-xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">Chat Dashboard</h1>
          <button
            type="button"
            onClick={() => setShowHistory((prev) => !prev)}
            className="inline-flex items-center gap-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 lg:hidden dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
          >
            {showHistory ? <PanelLeftClose size={16} /> : <PanelLeftOpen size={16} />} History
          </button>
        </div>

        <div className="grid h-[calc(100%-2.25rem)] gap-4 lg:grid-cols-[18rem_1fr]">
          <div className={`${showHistory ? "block" : "hidden"} lg:block`}>
            <ChatSidebar items={historyItems} onNewChat={() => setNewChatModal(true)} />
          </div>

          <section className="glass-card flex h-full flex-col p-3 sm:p-4">
            {loadingHistory ? (
              <div className="mb-3 space-y-2">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-16 w-[75%]" />
                <Skeleton className="ml-auto h-16 w-[62%]" />
              </div>
            ) : null}
            {error ? <p className="mb-2 text-sm font-medium text-rose-600">{error}</p> : null}
            <div className="mb-2 flex-1 overflow-y-auto pr-1">
              {!loadingHistory && messages.length === 0 ? (
                <EmptyState
                  title="No messages yet"
                  description="Start a conversation to see smart responses with citations here."
                />
              ) : null}

              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  role={message.role}
                  text={message.text}
                  timestamp={message.timestamp}
                  chatId={message.chatId}
                  source={message.source}
                />
              ))}

              {isTyping ? <ChatMessage role="assistant" isTyping timestamp={new Date()} /> : null}
            </div>

            <ChatInput onSend={handleSend} disabled={isTyping || loadingHistory} isTyping={isTyping} />
          </section>
        </div>
      </motion.div>

      <Modal open={newChatModal} title="Start New Conversation" onClose={() => setNewChatModal(false)}>
        <p className="text-sm text-slate-600 dark:text-slate-300">This will clear the current chat window and begin a fresh conversation.</p>
        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={() => setNewChatModal(false)}
            className="rounded-2xl bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={resetChat}
            className="rounded-2xl gradient-accent px-4 py-2 text-sm font-semibold text-white"
          >
            Start New Chat
          </button>
        </div>
      </Modal>
    </AppLayout>
  );
}

export default ChatDashboardPage;