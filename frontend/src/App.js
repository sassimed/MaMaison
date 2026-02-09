import React, { Suspense, lazy, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./guards/ProtectedRoute";
import ChatWidget from "./components/chat/ChatWidget";
import ScrollToTop from "./components/ScrollToTop";
import PageTracker from "./components/PageTracker";
import errorLogger from "./services/errorLogger";

// Initialize error logging
errorLogger.init();

// ============ PERFORMANCE: LAZY LOADING ============
// Critical pages loaded immediately
import HomePage from "./pages/public/HomePage";
import Login from "./pages/auth/Login";
import CatalogPage from "./pages/public/CatalogPage";

// Lazy load non-critical pages (code splitting)
const ServicesPage = lazy(() => import("./pages/public/Services"));
const GalleryPage = lazy(() => import("./pages/public/GalleryPage"));
const ProductDetailPage = lazy(() => import("./pages/public/ProductDetailPage"));
const AppointmentsPage = lazy(() => import("./pages/public/AppointmentsPage"));
const ContactPage = lazy(() => import("./pages/public/ContactPage"));
const AnnoncesPage = lazy(() => import("./pages/public/AnnoncesPage"));
const LegalPages = lazy(() => import("./pages/public/LegalPages"));

// Auth Pages (lazy)
const Register = lazy(() => import("./pages/auth/Register"));
const ForgotPassword = lazy(() => import("./pages/auth/ForgotPassword"));
const ResetPassword = lazy(() => import("./pages/auth/ResetPassword"));
const VerifyEmail = lazy(() => import("./pages/auth/VerifyEmail"));
const GoogleCallback = lazy(() => import("./pages/auth/GoogleCallback"));
const SelectRole = lazy(() => import("./pages/auth/SelectRole"));

// Dashboard Pages (lazy)
const DashboardHome = lazy(() => import("./pages/dashboard/DashboardHome"));
const Profile = lazy(() => import("./pages/dashboard/Profile"));
const MyRequests = lazy(() => import("./pages/dashboard/MyRequests"));
const MyAppointments = lazy(() => import("./pages/dashboard/MyAppointments"));
const Messages = lazy(() => import("./pages/dashboard/Messages"));
const DirectMessages = lazy(() => import("./pages/dashboard/DirectMessages"));
const CompanyInfo = lazy(() => import("./pages/dashboard/CompanyInfo"));
const CartPage = lazy(() => import("./pages/dashboard/CartPage"));
const FavoritesPage = lazy(() => import("./pages/dashboard/FavoritesPage"));
const MyPurchaseRequestsPage = lazy(() => import("./pages/dashboard/MyPurchaseRequestsPage"));
const MyAnnoncesPage = lazy(() => import("./pages/dashboard/MyAnnoncesPage"));
const AnnonceDetailPage = lazy(() => import("./pages/dashboard/AnnonceDetailPage"));
const AnnoncesPublicPage = lazy(() => import("./pages/dashboard/AnnoncesPublicPage"));
const MyResponsesPage = lazy(() => import("./pages/dashboard/MyResponsesPage"));
const ProfessionalProfilePage = lazy(() => import("./pages/dashboard/ProfessionalProfilePage"));

// Admin Pages (lazy - heavy components)
const AdminUsers = lazy(() => import("./pages/admin/AdminUsers"));
const AdminRequests = lazy(() => import("./pages/admin/AdminRequests"));
const AdminAppointments = lazy(() => import("./pages/admin/AdminAppointments"));
const AdminProducts = lazy(() => import("./pages/admin/AdminProducts"));
const AdminCategories = lazy(() => import("./pages/admin/AdminCategories"));
const AdminServices = lazy(() => import("./pages/admin/AdminServices"));
const AdminMessages = lazy(() => import("./pages/admin/AdminMessages"));
const AdminPurchaseRequests = lazy(() => import("./pages/admin/AdminPurchaseRequests"));
const AdminStatistics = lazy(() => import("./pages/admin/AdminStatistics"));
const AdminAnnonces = lazy(() => import("./pages/admin/AdminAnnonces"));
const AdminChatbot = lazy(() => import("./pages/admin/AdminChatbot"));
const AdminAnalytics = lazy(() => import("./pages/admin/AdminAnalytics"));
const AdminLogs = lazy(() => import("./pages/admin/AdminLogs"));

// Loading fallback component
const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="text-center">
      <div className="w-12 h-12 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
      <p className="mt-4 text-gray-600">Chargement...</p>
    </div>
  </div>
);

function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <PageTracker />
      <AuthProvider>
        <Suspense fallback={<PageLoader />}>
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
            <Route path="/dashboard/admin/analytics" element={<ProtectedRoute><AdminAnalytics /></ProtectedRoute>} />
            <Route path="/dashboard/admin/logs" element={<ProtectedRoute><AdminLogs /></ProtectedRoute>} />

            {/* Catch all - redirect to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
        
        {/* Global Chat Widget */}
        <ChatWidget />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
