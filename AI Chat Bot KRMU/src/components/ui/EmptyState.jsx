import { Inbox } from "lucide-react";

function EmptyState({ title, description, icon: Icon = Inbox, className = "" }) {
  return (
    <div className={`flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300/80 px-4 py-8 text-center dark:border-slate-700 ${className}`}>
      <span className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
        <Icon size={18} />
      </span>
      <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{title}</p>
      <p className="mt-1 max-w-sm text-xs text-slate-500 dark:text-slate-400">{description}</p>
    </div>
  );
}

export default EmptyState;