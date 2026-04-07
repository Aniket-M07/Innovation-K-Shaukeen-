import { Mic, SendHorizonal } from "lucide-react";
import { useState } from "react";

function ChatInput({ onSend, disabled, isTyping = false }) {
  const [value, setValue] = useState("");

  const send = () => {
    const content = value.trim();
    if (!content || disabled) {
      return;
    }
    onSend(content);
    setValue("");
  };

  return (
    <div className="sticky bottom-2 z-20 mt-4 rounded-2xl border border-slate-200 bg-white/95 p-2 shadow-lg shadow-slate-900/5 backdrop-blur dark:border-slate-700 dark:bg-slate-950/80">
      {isTyping ? (
        <div className="mb-2 flex items-center gap-2 rounded-xl bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
          AI is typing...
        </div>
      ) : null}
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              send();
            }
          }}
          placeholder="Ask Smart Campus AI anything..."
          className="h-11 flex-1 rounded-2xl border border-transparent bg-slate-50 px-4 text-sm text-slate-900 outline-none ring-blue-400/40 transition focus:ring dark:bg-slate-900 dark:text-slate-100"
        />
        <button
          type="button"
          className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-600 transition hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
          aria-label="Voice input"
        >
          <Mic size={18} />
        </button>
        <button
          type="button"
          onClick={send}
          disabled={disabled}
          className="gradient-accent inline-flex h-11 w-11 items-center justify-center rounded-2xl text-white shadow-lg shadow-blue-500/30 transition hover:brightness-110 disabled:opacity-60"
          aria-label="Send message"
        >
          <SendHorizonal size={18} />
        </button>
      </div>
    </div>
  );
}

export default ChatInput;