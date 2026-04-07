import { Activity, FileUp, MessageSquareMore, UsersRound, UserPlus } from "lucide-react";
import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import AppLayout from "../components/layout/AppLayout";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";
import Skeleton from "../components/ui/Skeleton";
import EmptyState from "../components/ui/EmptyState";
import { useToast } from "../components/ui/ToastProvider";
import {
  deleteAdminDocument,
  fetchAdminAnalytics,
  fetchAdminDocuments,
  uploadAdminDocument,
  createAdminUser,
} from "../services/api";

function statusChip(status) {
  if (status === "Resolved") {
    return "bg-emerald-100 text-emerald-700";
  }
  if (status === "Pending") {
    return "bg-amber-100 text-amber-700";
  }
  return "bg-rose-100 text-rose-700";
}

function AdminDashboardPage() {
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showCreateAdminModal, setShowCreateAdminModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [creatingAdmin, setCreatingAdmin] = useState(false);
  const [error, setError] = useState("");
  const [documents, setDocuments] = useState([]);
  const [loadingData, setLoadingData] = useState(true);
  const [adminForm, setAdminForm] = useState({
    name: "",
    email: "",
    password: "",
  });
  const [analytics, setAnalytics] = useState({
    totalUsers: 0,
    totalChats: 0,
    totalDocuments: 0,
    totalFeedback: 0,
  });
  const { pushToast } = useToast();

  const cards = useMemo(
    () => [
      { label: "Total Users", value: String(analytics.totalUsers), delta: "Live" },
      { label: "Total Chats", value: String(analytics.totalChats), delta: "Live" },
      { label: "Docs Indexed", value: String(analytics.totalDocuments), delta: "Live" },
      { label: "Feedback Records", value: String(analytics.totalFeedback), delta: "Live" },
    ],
    [analytics]
  );

  const loadAdminData = async () => {
    setLoadingData(true);
    setError("");
    try {
      const [analyticsResponse, docsResponse] = await Promise.all([
        fetchAdminAnalytics(),
        fetchAdminDocuments(),
      ]);
      setAnalytics(analyticsResponse.data || {});
      setDocuments(docsResponse.data || []);
    } catch (err) {
      setError(err.message || "Failed to load admin data");
      pushToast({ title: "Admin data unavailable", message: err.message || "Please retry shortly.", type: "error" });
    } finally {
      setLoadingData(false);
    }
  };

  useEffect(() => {
    loadAdminData();
  }, []);

  const onUpload = async () => {
    if (!selectedFile) {
      setError("Please select a file to upload");
      return;
    }

    setUploading(true);
    setError("");

    try {
      await uploadAdminDocument(selectedFile);
      setShowUploadModal(false);
      setSelectedFile(null);
      await loadAdminData();
      pushToast({ title: "Upload complete", message: "Document embedded successfully.", type: "success" });
    } catch (err) {
      setError(err.message || "Upload failed");
      pushToast({ title: "Upload failed", message: err.message || "Please try again.", type: "error" });
    } finally {
      setUploading(false);
    }
  };

  const onDelete = async (id) => {
    setError("");
    try {
      await deleteAdminDocument(id);
      await loadAdminData();
      pushToast({ title: "Document removed", message: "The file was deleted successfully.", type: "info" });
    } catch (err) {
      setError(err.message || "Delete failed");
      pushToast({ title: "Delete failed", message: err.message || "Please try again.", type: "error" });
    }
  };

  const onCreateAdmin = async () => {
    if (!adminForm.name || !adminForm.email || !adminForm.password) {
      setError("Please fill in all fields");
      return;
    }

    setCreatingAdmin(true);
    setError("");
    try {
      await createAdminUser({
        name: adminForm.name,
        email: adminForm.email,
        password: adminForm.password,
      });
      setShowCreateAdminModal(false);
      setAdminForm({ name: "", email: "", password: "" });
      pushToast({ title: "Admin created", message: "New admin account created successfully.", type: "success" });
    } catch (err) {
      setError(err.message || "Failed to create admin");
      pushToast({ title: "Creation failed", message: err.message || "Please try again.", type: "error" });
    } finally {
      setCreatingAdmin(false);
    }
  };

  return (
    <AppLayout>
      <motion.div className="space-y-4" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.28 }}>
        <h1 className="text-xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">Admin Dashboard</h1>

        <Card className="p-4 sm:p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">Create Admin Account</h2>
              <p className="text-sm text-slate-600 dark:text-slate-400">Add a new administrator to the Smart Campus AI system.</p>
            </div>
            <Button onClick={() => setShowCreateAdminModal(true)}>
              <UserPlus size={16} className="mr-2" /> Create New Admin
            </Button>
          </div>
        </Card>

        <Card className="p-4 sm:p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">Upload Documents</h2>
              <p className="text-sm text-slate-600 dark:text-slate-400">Add PDFs, circulars, notices, and policy files for the AI assistant.</p>
            </div>
            <Button onClick={() => setShowUploadModal(true)}>
              <FileUp size={16} className="mr-2" /> Upload New File
            </Button>
          </div>
        </Card>

        {error ? <p className="text-sm font-semibold text-rose-600">{error}</p> : null}

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          {loadingData
            ? Array.from({ length: 4 }).map((_, idx) => (
                <Card key={`skeleton-${idx}`} className="space-y-2 p-4">
                  <Skeleton className="h-8 w-8" />
                  <Skeleton className="h-4 w-28" />
                  <Skeleton className="h-8 w-20" />
                  <Skeleton className="h-3 w-16" />
                </Card>
              ))
            : cards.map((card, index) => {
                const icons = [Activity, MessageSquareMore, FileUp, UsersRound];
                const Icon = icons[index % icons.length];
                return (
                  <Card key={card.label} className="p-4">
                    <div className="mb-3 inline-flex rounded-2xl bg-slate-100 p-2 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                      <Icon size={18} />
                    </div>
                    <p className="text-sm text-slate-500 dark:text-slate-400">{card.label}</p>
                    <p className="mt-1 text-2xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">{card.value}</p>
                    <p className="mt-1 text-xs font-semibold text-cyan-700">{card.delta}</p>
                  </Card>
                );
              })}
        </div>

        <Card className="overflow-hidden">
          <div className="border-b border-slate-200 px-4 py-3 sm:px-5">
            <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">Indexed Documents</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wider text-slate-500 dark:bg-slate-900/70 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-3 sm:px-5">ID</th>
                  <th className="px-4 py-3 sm:px-5">Document</th>
                  <th className="px-4 py-3 sm:px-5">Uploaded By</th>
                  <th className="px-4 py-3 sm:px-5">Status</th>
                  <th className="px-4 py-3 sm:px-5">Time</th>
                  <th className="px-4 py-3 sm:px-5">Action</th>
                </tr>
              </thead>
              <tbody>
                {loadingData ? (
                  <tr className="border-t border-slate-200/80 dark:border-slate-800">
                    <td colSpan={6} className="p-4">
                      <div className="space-y-2">
                        <Skeleton className="h-9 w-full" />
                        <Skeleton className="h-9 w-full" />
                        <Skeleton className="h-9 w-full" />
                      </div>
                    </td>
                  </tr>
                ) : documents.length === 0 ? (
                  <tr className="border-t border-slate-200/80 dark:border-slate-800">
                    <td colSpan={6} className="p-4">
                      <EmptyState
                        title="No documents indexed"
                        description="Upload your first file to power retrieval responses."
                      />
                    </td>
                  </tr>
                ) : (
                  documents.map((doc) => (
                    <tr key={doc.id} className="border-t border-slate-200/80">
                      <td className="px-4 py-3 font-semibold text-slate-700 sm:px-5 dark:text-slate-200">{doc.id}</td>
                      <td className="max-w-88 truncate px-4 py-3 text-slate-600 sm:px-5 dark:text-slate-300">{doc.original_name}</td>
                      <td className="px-4 py-3 text-slate-700 sm:px-5 dark:text-slate-200">{doc.uploaded_by_name || "Admin"}</td>
                      <td className="px-4 py-3 sm:px-5">
                        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${statusChip("Resolved")}`}>
                          Embedded
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-500 sm:px-5 dark:text-slate-400">
                        {new Date(doc.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </td>
                      <td className="px-4 py-3 sm:px-5">
                        <button
                          type="button"
                          onClick={() => onDelete(doc.id)}
                          className="rounded-xl bg-rose-50 px-2.5 py-1 text-xs font-semibold text-rose-700 hover:bg-rose-100"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </motion.div>

      <Modal open={showCreateAdminModal} title="Create Admin Account" onClose={() => setShowCreateAdminModal(false)}>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-200" htmlFor="admin-name">
              Full Name
            </label>
            <input
              id="admin-name"
              type="text"
              value={adminForm.name}
              onChange={(e) => setAdminForm((prev) => ({ ...prev, name: e.target.value }))}
              placeholder="Enter full name"
              className="mt-2 block w-full rounded-2xl border border-slate-200 px-3 py-2 text-sm outline-none ring-blue-400/40 transition focus:ring dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-200" htmlFor="admin-email">
              Email
            </label>
            <input
              id="admin-email"
              type="email"
              value={adminForm.email}
              onChange={(e) => setAdminForm((prev) => ({ ...prev, email: e.target.value }))}
              placeholder="Enter email address"
              className="mt-2 block w-full rounded-2xl border border-slate-200 px-3 py-2 text-sm outline-none ring-blue-400/40 transition focus:ring dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-200" htmlFor="admin-password">
              Password
            </label>
            <input
              id="admin-password"
              type="password"
              value={adminForm.password}
              onChange={(e) => setAdminForm((prev) => ({ ...prev, password: e.target.value }))}
              placeholder="Enter password"
              className="mt-2 block w-full rounded-2xl border border-slate-200 px-3 py-2 text-sm outline-none ring-blue-400/40 transition focus:ring dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            />
          </div>
          {error ? <p className="text-sm font-semibold text-rose-600">{error}</p> : null}
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setShowCreateAdminModal(false)}
              className="rounded-2xl bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={onCreateAdmin}
              disabled={creatingAdmin}
              className="rounded-2xl gradient-accent px-4 py-2 text-sm font-semibold text-white"
            >
              {creatingAdmin ? "Creating..." : "Create Admin"}
            </button>
          </div>
        </div>
      </Modal>

      <Modal open={showUploadModal} title="Upload Academic Documents" onClose={() => setShowUploadModal(false)}>
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-200" htmlFor="upload">
          Select file
        </label>
        <input
          id="upload"
          type="file"
          onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
          className="mt-2 block w-full rounded-2xl border border-slate-200 px-3 py-2 text-sm file:mr-3 file:rounded-xl file:border-0 file:bg-blue-50 file:px-3 file:py-1.5 file:text-blue-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
        />
        {selectedFile ? <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">Selected: {selectedFile.name}</p> : null}
        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={() => setShowUploadModal(false)}
            className="rounded-2xl bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onUpload}
            disabled={uploading}
            className="rounded-2xl gradient-accent px-4 py-2 text-sm font-semibold text-white"
          >
            {uploading ? "Uploading..." : "Upload"}
          </button>
        </div>
      </Modal>
    </AppLayout>
  );
}

export default AdminDashboardPage;
