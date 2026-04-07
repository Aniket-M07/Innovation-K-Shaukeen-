import { Check, Copy, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import { useState } from "react";
import { submitChatFeedback } from "../../services/api";

function ChatMessage({ role, text, timestamp, isTyping, chatId, source, onFeedbackSubmitted }) {
  const [copied, setCopied] = useState(false);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [feedbackSent, setFeedbackSent] = useState(false);
  const isUser = role === "user";

  const handleCopy = async () => {
    if (isTyping || !text) {
      return;
    }

    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {
      setCopied(false);
    }
  };

  const sendFeedback = async () => {
    if (!chatId || !rating || submittingFeedback || feedbackSent) {
      return;
    }

    setSubmittingFeedback(true);
    try {
      await submitChatFeedback(chatId, rating, comment.trim());
      setFeedbackSent(true);
      if (onFeedbackSubmitted) {
        onFeedbackSubmitted(chatId);
      }
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const sourceLabel = (() => {
    if (source === "web") return "Web";
    if (source === "ai") return "GPT";
    if (source === "documents") return "Docs";
    return null;
  })();

  return (
    <motion.div
      className={`mb-5 flex ${isUser ? "justify-end" : "justify-start"}`}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <div className={`max-w-[86%] sm:max-w-[74%] ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`rounded-2xl px-4 py-3 shadow-sm ${
            isUser
              ? "rounded-br-md gradient-accent text-white"
              : "rounded-bl-md border border-slate-200 bg-white text-slate-800 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
          }`}
        >
          {isTyping ? (
            <div className="flex items-center gap-1.5 py-1">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          ) : (
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{text}</p>
          )}
        </div>

        <div className={`mt-1.5 flex items-center gap-2 text-xs ${isUser ? "justify-end" : "justify-start"}`}>
          {!isUser ? <Sparkles size={12} className="text-cyan-600 dark:text-cyan-400" /> : null}
          <span className="text-slate-500 dark:text-slate-400">{new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
          {!isUser && sourceLabel ? (
            <span className="rounded-full bg-slate-100 px-2 py-1 font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
              {sourceLabel}
            </span>
          ) : null}
          {!isUser && !isTyping ? (
            <button
              type="button"
              onClick={handleCopy}
              className="inline-flex items-center gap-1 rounded-xl px-2 py-1 text-slate-500 transition hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
            >
              {copied ? <Check size={12} /> : <Copy size={12} />} {copied ? "Copied" : "Copy"}
            </button>
          ) : null}
        </div>

        {!isUser && !isTyping ? (
          <div className="mt-2 rounded-2xl border border-slate-200 bg-white/80 p-3 dark:border-slate-700 dark:bg-slate-900/70">
            <p className="mb-2 text-xs font-semibold text-slate-500 dark:text-slate-400">Was this answer helpful?</p>
            <div className="flex flex-wrap items-center gap-2">
              {[1, 2, 3, 4, 5].map((value) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setRating(value)}
                  className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
                    rating === value
                      ? "bg-blue-600 text-white"
                      : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                  }`}
                >
                  {value}
                </button>
              ))}
              <input
                type="text"
                value={comment}
                onChange={(event) => setComment(event.target.value)}
                placeholder="Optional note for improvement"
                className="min-w-44 flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
              />
              <button
                type="button"
                onClick={sendFeedback}
                disabled={!rating || submittingFeedback || feedbackSent}
                className="rounded-xl gradient-accent px-3 py-2 text-xs font-semibold text-white disabled:opacity-60"
              >
                {feedbackSent ? "Saved" : submittingFeedback ? "Saving..." : "Send"}
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </motion.div>
  );
}

export default ChatMessage;