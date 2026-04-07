import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, MessageSquareText, User } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";

function SidebarNav({ mobileOpen, onClose }) {
  const location = useLocation();
  const [user, setUser] = useState(null);

  useEffect(() => {
    const storedUser = localStorage.getItem("sca_user");
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const navItems = [
    { label: "Chat Dashboard", icon: MessageSquareText, path: "/chat" },
    ...(user?.role === "admin" ? [{ label: "Admin Dashboard", icon: LayoutDashboard, path: "/admin" }] : []),
    { label: "Profile", icon: User, path: "/profile" },
  ];

  return (
    <>
      <aside className="hidden w-64 shrink-0 lg:block">
        <div className="sticky top-20 px-3">
          <nav className="glass-card p-3">
            {navItems.map((item) => {
              const active = location.pathname === item.path;
              const Icon = item.icon;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`mb-2 flex items-center gap-2 rounded-2xl px-3 py-2.5 text-sm font-semibold transition last:mb-0 ${
                    active
                      ? "gradient-accent text-white shadow-lg shadow-blue-500/20"
                      : "text-slate-700 hover:bg-slate-100"
                  }`}
                >
                  <Icon size={16} />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </aside>

      <AnimatePresence>
        {mobileOpen ? (
          <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true">
            <motion.button
              type="button"
              className="absolute inset-0 bg-slate-900/40"
              onClick={onClose}
              aria-label="Close navigation"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            />
            <motion.div
              className="absolute left-0 top-0 h-full w-72 bg-white p-4 shadow-2xl dark:bg-slate-900"
              initial={{ x: -24, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -24, opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <p className="mb-3 text-sm font-bold text-slate-900 dark:text-slate-100">Navigation</p>
              {navItems.map((item) => {
                const active = location.pathname === item.path;
                const Icon = item.icon;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={onClose}
                    className={`mb-2 flex items-center gap-2 rounded-2xl px-3 py-2.5 text-sm font-semibold transition ${
                      active
                        ? "gradient-accent text-white"
                        : "text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
                    }`}
                  >
                    <Icon size={16} />
                    {item.label}
                  </Link>
                );
              })}
            </motion.div>
          </div>
        ) : null}
      </AnimatePresence>
    </>
  );
}

export default SidebarNav;