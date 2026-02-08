import React from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./guards/ProtectedRoute";
import ChatWidget from "./components/chat/ChatWidget";
import ScrollToTop from "./components/ScrollToTop";

// Public Pages
import HomePage from "./pages/public/HomePage";
import ServicesPage from "./pages/public/Services";
import GalleryPage from "./pages/public/GalleryPage";
import CatalogPage from "./pages/public/CatalogPage";
import ProductDetailPage from "./pages/public/ProductDetailPage";
import AppointmentsPage from "./pages/public/AppointmentsPage";
import ContactPage from "./pages/public/ContactPage";
import AnnoncesPage from "./pages/public/AnnoncesPage";
import LegalPages from "./pages/public/LegalPages";

// Auth Pages
import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";
import ForgotPassword from "./pages/auth/ForgotPassword";
import ResetPassword from "./pages/auth/ResetPassword";
import VerifyEmail from "./pages/auth/VerifyEmail";
import GoogleCallback from "./pages/auth/GoogleCallback";
import SelectRole from "./pages/auth/SelectRole";

// Dashboard Pages
import DashboardHome from "./pages/dashboard/DashboardHome";
import Profile from "./pages/dashboard/Profile";
import MyRequests from "./pages/dashboard/MyRequests";
import MyAppointments from "./pages/dashboard/MyAppointments";
import Messages from "./pages/dashboard/Messages";
import DirectMessages from "./pages/dashboard/DirectMessages";
import CompanyInfo from "./pages/dashboard/CompanyInfo";
import CartPage from "./pages/dashboard/CartPage";
import FavoritesPage from "./pages/dashboard/FavoritesPage";
import MyPurchaseRequestsPage from "./pages/dashboard/MyPurchaseRequestsPage";
import MyAnnoncesPage from "./pages/dashboard/MyAnnoncesPage";
import AnnonceDetailPage from "./pages/dashboard/AnnonceDetailPage";
import AnnoncesPublicPage from "./pages/dashboard/AnnoncesPublicPage";
import MyResponsesPage from "./pages/dashboard/MyResponsesPage";
import ProfessionalProfilePage from "./pages/dashboard/ProfessionalProfilePage";

// Admin Pages
import AdminUsers from "./pages/admin/AdminUsers";
import AdminRequests from "./pages/admin/AdminRequests";
import AdminAppointments from "./pages/admin/AdminAppointments";
import AdminProducts from "./pages/admin/AdminProducts";
import AdminCategories from "./pages/admin/AdminCategories";
import AdminServices from "./pages/admin/AdminServices";
import AdminMessages from "./pages/admin/AdminMessages";
import AdminPurchaseRequests from "./pages/admin/AdminPurchaseRequests";
import AdminStatistics from "./pages/admin/AdminStatistics";
import AdminAnnonces from "./pages/admin/AdminAnnonces";
import AdminChatbot from "./pages/admin/AdminChatbot";

function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<HomePage />} />
          <Route path="/services" element={<ServicesPage />} />
          <Route path="/realisations" element={<GalleryPage />} />
          <Route path="/catalogue" element={<CatalogPage />} />
          <Route path="/catalog" element={<CatalogPage />} />
          <Route path="/catalog/:productId" element={<ProductDetailPage />} />
          <Route path="/rendez-vous" element={<AppointmentsPage />} />
          <Route path="/contact" element={<ContactPage />} />
          <Route path="/annonces" element={<AnnoncesPage />} />
          <Route path="/mentions-legales" element={<LegalPages />} />
          <Route path="/politique-confidentialite" element={<LegalPages />} />

          {/* Auth routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/auth/google/callback" element={<GoogleCallback />} />
          <Route path="/select-role" element={<SelectRole />} />

          {/* Dashboard routes (protected) */}
          <Route path="/dashboard" element={<ProtectedRoute><DashboardHome /></ProtectedRoute>} />
          <Route path="/dashboard/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          <Route path="/dashboard/requests" element={<ProtectedRoute><MyRequests /></ProtectedRoute>} />
          <Route path="/dashboard/appointments" element={<ProtectedRoute><MyAppointments /></ProtectedRoute>} />
          <Route path="/dashboard/messages" element={<ProtectedRoute><DirectMessages /></ProtectedRoute>} />
          <Route path="/dashboard/messages-admin" element={<ProtectedRoute><Messages /></ProtectedRoute>} />
          <Route path="/dashboard/company" element={<ProtectedRoute><CompanyInfo /></ProtectedRoute>} />
          <Route path="/dashboard/cart" element={<ProtectedRoute><CartPage /></ProtectedRoute>} />
          <Route path="/dashboard/favorites" element={<ProtectedRoute><FavoritesPage /></ProtectedRoute>} />
          <Route path="/dashboard/my-purchase-requests" element={<ProtectedRoute><MyPurchaseRequestsPage /></ProtectedRoute>} />
          <Route path="/dashboard/my-annonces" element={<ProtectedRoute><MyAnnoncesPage /></ProtectedRoute>} />
          <Route path="/dashboard/my-annonces/:annonceId" element={<ProtectedRoute><AnnonceDetailPage /></ProtectedRoute>} />
          <Route path="/dashboard/annonces" element={<ProtectedRoute><AnnoncesPublicPage /></ProtectedRoute>} />
          <Route path="/dashboard/my-responses" element={<ProtectedRoute><MyResponsesPage /></ProtectedRoute>} />
          <Route path="/dashboard/professional/:professionalId" element={<ProtectedRoute><ProfessionalProfilePage /></ProtectedRoute>} />

          {/* Admin routes (protected) */}
          <Route path="/dashboard/admin/users" element={<ProtectedRoute><AdminUsers /></ProtectedRoute>} />
          <Route path="/dashboard/admin/requests" element={<ProtectedRoute><AdminRequests /></ProtectedRoute>} />
          <Route path="/dashboard/admin/appointments" element={<ProtectedRoute><AdminAppointments /></ProtectedRoute>} />
          <Route path="/dashboard/admin/products" element={<ProtectedRoute><AdminProducts /></ProtectedRoute>} />
          <Route path="/dashboard/admin/categories" element={<ProtectedRoute><AdminCategories /></ProtectedRoute>} />
          <Route path="/dashboard/admin/services" element={<ProtectedRoute><AdminServices /></ProtectedRoute>} />
          <Route path="/dashboard/admin/messages" element={<ProtectedRoute><AdminMessages /></ProtectedRoute>} />
          <Route path="/dashboard/admin/purchase-requests" element={<ProtectedRoute><AdminPurchaseRequests /></ProtectedRoute>} />
          <Route path="/dashboard/admin/statistics" element={<ProtectedRoute><AdminStatistics /></ProtectedRoute>} />
          <Route path="/dashboard/admin/annonces" element={<ProtectedRoute><AdminAnnonces /></ProtectedRoute>} />
          <Route path="/dashboard/admin/chatbot" element={<ProtectedRoute><AdminChatbot /></ProtectedRoute>} />

          {/* Catch all - redirect to home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        
        {/* Global Chat Widget */}
        <ChatWidget />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
