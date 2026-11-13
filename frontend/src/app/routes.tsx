import { Routes, Route } from "react-router-dom";
import LandingPage from "../features/landing/LandingPage";
import LoginPage from "../features/auth/LoginPage";
import RegisterPage from "../features/auth/RegisterPage";
import FarmerDashboard from "../features/farmer/FarmerDashboard";
import InsurerDashboard from "../features/insurer/InsurerDashboard";
import AuditorDashboard from "../features/auditor/AuditorDashboard";
import AdminDashboard from "../features/admin/AdminDashboard";
import ProtectedRoute from "../features/shared/ProtectedRoute";
import AccessDenied from "../features/shared/AccessDenied";
import NotFound from "../features/shared/NotFound";

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route
        path="/farmer"
        element={
          <ProtectedRoute allowedRoles={["farmer"]}>
            <FarmerDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/insurer"
        element={
          <ProtectedRoute allowedRoles={["insurer", "admin"]}>
            <InsurerDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/auditor"
        element={
          <ProtectedRoute allowedRoles={["auditor", "admin"]}>
            <AuditorDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <ProtectedRoute allowedRoles={["admin"]}>
            <AdminDashboard />
          </ProtectedRoute>
        }
      />

      <Route path="/access-denied" element={<AccessDenied />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
