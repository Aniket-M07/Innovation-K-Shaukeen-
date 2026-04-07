import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppLayout from "../components/layout/AppLayout";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import { useToast } from "../components/ui/ToastProvider";
import { User, Mail, LogOut } from "lucide-react";

function ProfilePage() {
  const navigate = useNavigate();
  const { pushToast } = useToast();
  const [user, setUser] = useState(null);

  useEffect(() => {
    const storedUser = localStorage.getItem("sca_user");
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    } else {
      navigate("/login");
    }
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem("sca_token");
    localStorage.removeItem("sca_user");
    pushToast({ title: "Logged out", message: "You have been logged out successfully", type: "success" });
    navigate("/login");
  };

  if (!user) {
    return null;
  }

  return (
    <AppLayout>
      <motion.div
        className="mx-auto max-w-2xl px-4 py-8"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.28 }}
      >
        <div className="mb-8">
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">Profile</h1>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
            Manage your account information and settings
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <Card className="p-6">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl gradient-accent">
              <User size={28} className="text-white" />
            </div>
            <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400">Full Name</h3>
            <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-100">{user.name}</p>
          </Card>

          <Card className="p-6">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-100 dark:bg-amber-900">
              <Mail size={28} className="text-amber-600 dark:text-amber-400" />
            </div>
            <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400">Email Address</h3>
            <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-100">{user.email}</p>
          </Card>

          <Card className="p-6">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-100 dark:bg-emerald-900">
              <span className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                {user.role === "admin" ? "👤" : "🎓"}
              </span>
            </div>
            <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400">Role</h3>
            <p className="mt-1 text-lg font-semibold capitalize text-slate-900 dark:text-slate-100">
              {user.role === "admin" ? "Administrator" : "Student"}
            </p>
          </Card>

          <Card className="p-6">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-100 dark:bg-blue-900">
              <span className="text-2xl">✓</span>
            </div>
            <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400">Account Status</h3>
            <p className="mt-1 text-lg font-semibold text-emerald-600 dark:text-emerald-400">Active</p>
          </Card>
        </div>

        <Card className="mt-8 p-6">
          <h2 className="mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">Account Actions</h2>
          <div className="flex flex-col gap-3">
            <motion.button
              onClick={handleLogout}
              className="flex items-center gap-2 rounded-2xl bg-rose-600 px-4 py-2.5 font-semibold text-white transition hover:bg-rose-700 w-fit"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <LogOut size={18} />
              Logout
            </motion.button>
          </div>
        </Card>
      </motion.div>
    </AppLayout>
  );
}

export default ProfilePage;
