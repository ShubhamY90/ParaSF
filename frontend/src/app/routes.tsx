import { Routes, Route } from "react-router-dom";
import LandingPage from "../features/landing/LandingPage";
import LoginPage from "../features/auth/LoginPage";
import RegisterPage from "../features/auth/RegisterPage";
import FarmerDashboard from "../features/farmer/FarmerDashboard";
import FarmerProfilePage from "../features/farmer/FarmerProfilePage";
import FarmRegistrationPage from "../features/farmer/FarmRegistrationPage";
import MyFarmsPage from "../features/farmer/MyFarmsPage";
import MyPolicyPage from "../features/farmer/MyPolicyPage";
import BankAccountPage from "../features/farmer/BankAccountPage";
import InsurerDashboard from "../features/insurer/InsurerDashboard";
import FarmerRegistryPage from "../features/insurer/FarmerRegistryPage";
import FarmerDetailPage from "../features/insurer/FarmerDetailPage";
import PolicyListPage from "../features/insurer/PolicyListPage";
import PolicyFormPage from "../features/insurer/PolicyFormPage";
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

      {/* Farmer Routes */}
      <Route
        path="/farmer"
        element={
          <ProtectedRoute allowedRoles={["farmer"]}>
            <FarmerDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/farmer/profile"
        element={
          <ProtectedRoute allowedRoles={["farmer"]}>
            <FarmerProfilePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/farmer/farms"
        element={
          <ProtectedRoute allowedRoles={["farmer"]}>
            <MyFarmsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/farmer/farms/new"
        element={
          <ProtectedRoute allowedRoles={["farmer"]}>
            <FarmRegistrationPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/farmer/policy"
        element={
          <ProtectedRoute allowedRoles={["farmer"]}>
            <MyPolicyPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/farmer/bank"
        element={
          <ProtectedRoute allowedRoles={["farmer"]}>
            <BankAccountPage />
          </ProtectedRoute>
        }
      />

      {/* Insurer Routes */}
      <Route
        path="/insurer"
        element={
          <ProtectedRoute allowedRoles={["insurer", "admin"]}>
            <InsurerDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/insurer/farmers"
        element={
          <ProtectedRoute allowedRoles={["insurer", "admin", "auditor"]}>
            <FarmerRegistryPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/insurer/farmers/:profileId"
        element={
          <ProtectedRoute allowedRoles={["insurer", "admin", "auditor"]}>
            <FarmerDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/insurer/policies"
        element={
          <ProtectedRoute allowedRoles={["insurer", "admin", "auditor"]}>
            <PolicyListPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/insurer/policies/new"
        element={
          <ProtectedRoute allowedRoles={["insurer", "admin"]}>
            <PolicyFormPage />
          </ProtectedRoute>
        }
      />

      {/* Auditor & Admin Routes */}
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
