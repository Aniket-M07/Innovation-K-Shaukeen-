import { Clock3, Plus } from "lucide-react";
import { motion } from "framer-motion";
import Button from "../ui/Button";
import Card from "../ui/Card";
import EmptyState from "../ui/EmptyState";

function ChatSidebar({ items, onNewChat }) {
  return (
    <Card className="h-full p-3">
      <Button className="mb-3 w-full" onClick={onNewChat}>
        <Plus size={16} className="mr-1" /> New Chat
      </Button>
      <p className="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Chat History</p>
      <div className="space-y-2">
        {items.length === 0 ? (
          <EmptyState
            title="No conversations yet"
            description="Your recent questions will appear here after you send your first message."
            className="py-6"
          />
        ) : (
          items.map((item, index) => (
            <motion.button
              key={`${item}-${index}`}
              type="button"
              className="flex w-full items-center gap-2 rounded-2xl px-3 py-2 text-left text-sm text-slate-700 transition hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2, delay: index * 0.02 }}
            >
              <Clock3 size={14} className="shrink-0 text-slate-400 dark:text-slate-500" />
              <span className="truncate">{item}</span>
            </motion.button>
          ))
        )}
      </div>
    </Card>
  );
}

export default ChatSidebar;