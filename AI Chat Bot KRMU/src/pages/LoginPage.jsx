import { GraduationCap } from "lucide-react";
import { motion } from "framer-motion";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import { useToast } from "../components/ui/ToastProvider";
import { loginUser } from "../services/api";

function LoginPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { pushToast } = useToast();

  const onSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await loginUser({ email: form.email, password: form.password });
      localStorage.setItem("sca_token", response.token);
      localStorage.setItem("sca_user", JSON.stringify(response.user));
      pushToast({ title: "Login successful", message: `Welcome ${response.user?.name || "back"}`, type: "success" });
      navigate(response.user?.role === "admin" ? "/admin" : "/chat");
    } catch (err) {
      setError(err.message || "Login failed");
      pushToast({ title: "Login failed", message: err.message || "Please try again.", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      className="flex min-h-screen items-center justify-center px-4 py-8"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28 }}
    >
      <Card className="w-full max-w-md p-6 sm:p-8">
        <div className="mb-6 text-center">
          <span className="mx-auto mb-3 inline-flex h-12 w-12 items-center justify-center rounded-2xl gradient-accent text-white">
            <GraduationCap size={22} />
          </span>
          <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">Welcome Back</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Login to Smart Campus AI</p>
        </div>

        <form className="space-y-4" onSubmit={onSubmit}>
          <input
            type="email"
            placeholder="Email address"
            value={form.email}
            onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
            className="h-11 w-full rounded-2xl border border-slate-200 px-4 text-sm outline-none ring-blue-400/40 transition focus:ring dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
          />
          <input
            type="password"
            placeholder="Password"
            value={form.password}
            onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
            className="h-11 w-full rounded-2xl border border-slate-200 px-4 text-sm outline-none ring-blue-400/40 transition focus:ring dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
          />
          {error ? <p className="text-sm font-medium text-rose-600">{error}</p> : null}
          <Button className="w-full" type="submit" disabled={loading}>
            {loading ? "Signing In..." : "Sign In"}
          </Button>
        </form>

        <p className="mt-4 text-center text-sm text-slate-600 dark:text-slate-300">
          New user? <Link to="/register" className="font-semibold text-blue-600">Create account</Link>
        </p>
      </Card>
    </motion.div>
  );
}

export default LoginPage;