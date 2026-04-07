import { Navigate, Route, Routes } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ChatDashboardPage from "./pages/ChatDashboardPage";
import AdminDashboardPage from "./pages/AdminDashboardPage";
import ProfilePage from "./pages/ProfilePage";

function ProtectedAdminRoute({ element }) {
  const user = JSON.parse(localStorage.getItem("sca_user") || "{}");
  return user?.role === "admin" ? element : <Navigate to="/chat" replace />;
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/chat" element={<ChatDashboardPage />} />
      <Route path="/admin" element={<ProtectedAdminRoute element={<AdminDashboardPage />} />} />
      <Route path="/profile" element={<ProfilePage />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default App;