import { UserPlus } from "lucide-react";
import { motion } from "framer-motion";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import { useToast } from "../components/ui/ToastProvider";
import { registerUser } from "../services/api";

function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    firstName: "",
    lastName: "",
    email: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { pushToast } = useToast();

  const onSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const name = `${form.firstName} ${form.lastName}`.trim();
      const response = await registerUser({
        name,
        email: form.email,
        password: form.password,
        role: "student",
      });

      localStorage.setItem("sca_token", response.token);
      localStorage.setItem("sca_user", JSON.stringify(response.user));
      pushToast({ title: "Account created", message: "Welcome to Smart Campus AI", type: "success" });
      navigate(response.user?.role === "admin" ? "/admin" : "/chat");
    } catch (err) {
      setError(err.message || "Registration failed");
      pushToast({ title: "Registration failed", message: err.message || "Please try again.", type: "error" });
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
      <Card className="w-full max-w-lg p-6 sm:p-8">
        <div className="mb-6 text-center">
          <span className="mx-auto mb-3 inline-flex h-12 w-12 items-center justify-center rounded-2xl gradient-accent text-white">
            <UserPlus size={22} />
          </span>
          <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">Create Account</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Join Smart Campus AI in seconds</p>
        </div>

        <form className="grid grid-cols-1 gap-4 sm:grid-cols-2" onSubmit={onSubmit}>
          <input
            type="text"
            placeholder="First name"
            value={form.firstName}
            onChange={(event) => setForm((prev) => ({ ...prev, firstName: event.target.value }))}
            className="h-11 rounded-2xl border border-slate-200 px-4 text-sm outline-none ring-blue-400/40 transition focus:ring dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
          />
          <input
            type="text"
            placeholder="Last name"
            value={form.lastName}
            onChange={(event) => setForm((prev) => ({ ...prev, lastName: event.target.value }))}
            className="h-11 rounded-2xl border border-slate-200 px-4 text-sm outline-none ring-blue-400/40 transition focus:ring dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
          />
          <input
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
            className="h-11 rounded-2xl border border-slate-200 px-4 text-sm outline-none ring-blue-400/40 transition focus:ring sm:col-span-2 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
          />
          <input
            type="password"
            placeholder="Password"
            value={form.password}
            onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
            className="h-11 rounded-2xl border border-slate-200 px-4 text-sm outline-none ring-blue-400/40 transition focus:ring sm:col-span-2 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
          />
          {error ? <p className="text-sm font-medium text-rose-600 sm:col-span-2">{error}</p> : null}
          <Button className="sm:col-span-2" type="submit" disabled={loading}>
            {loading ? "Creating Account..." : "Create Account"}
          </Button>
        </form>

        <p className="mt-4 text-center text-sm text-slate-600 dark:text-slate-300">
          Already registered? <Link to="/login" className="font-semibold text-blue-600">Login here</Link>
        </p>
      </Card>
    </motion.div>
  );
}

export default RegisterPage;