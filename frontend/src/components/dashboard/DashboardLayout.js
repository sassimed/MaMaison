import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Menu, X, ChevronLeft, ChevronRight, Home, User, ShoppingCart, Heart, Package, FileText, Calendar, MessageSquare, Building, Users, Settings, BarChart3, FolderOpen, LogOut, Megaphone, Send, Store, Bot, Activity, AlertTriangle } from 'lucide-react';
import NotificationBell from '../notifications/NotificationBell';
import PushNotificationToggle from '../notifications/PushNotificationToggle';
import api from '../../services/api';

function DashboardLayout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [unreadMessages, setUnreadMessages] = useState(0);

  // Check screen size
  useEffect(function() {
    function handleResize() {
      var mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) {
        setSidebarOpen(false);
      }
    }
    handleResize();
    window.addEventListener('resize', handleResize);
    return function() {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  // Fetch unread message count
  useEffect(function() {
    async function fetchUnreadCount() {
      try {
        var response = await api.get('/direct-messages/unread-count');
        setUnreadMessages(response.data.unread_count);
      } catch (err) {
        console.log('Could not fetch unread count');
      }
    }
    
    fetchUnreadCount();
    // Poll every 30 seconds
    var interval = setInterval(fetchUnreadCount, 30000);
    return function() { clearInterval(interval); };
  }, []);

  function handleLogout() {
    logout();
    navigate('/login');
  }

  function toggleSidebar() {
    if (isMobile) {
      setMobileMenuOpen(!mobileMenuOpen);
    } else {
      setSidebarOpen(!sidebarOpen);
    }
  }

  function closeMobileMenu() {
    setMobileMenuOpen(false);
  }

  var isAdmin = user?.role === 'ADMIN';
  var isPro = user?.role === 'PROFESSIONNEL';

  function getNavLinkClass(isActive) {
    var base = 'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors';
    if (isActive) {
      return base + ' bg-gradient-to-r from-purple-600 to-cyan-500 text-white';
    }
    return base + ' text-gray-600 hover:bg-gray-100';
  }

  function NavItem({ to, icon, label, testId }) {
    return (
      <NavLink 
        to={to} 
        className={function({ isActive }) { return getNavLinkClass(isActive); }}
        data-testid={testId}
        onClick={closeMobileMenu}
      >
        {icon}
        {(sidebarOpen || isMobile) && <span>{label}</span>}
      </NavLink>
    );
  }

  function NavItemWithBadge({ to, icon, label, testId, badgeCount }) {
    return (
      <NavLink 
        to={to} 
        className={function({ isActive }) { return getNavLinkClass(isActive); }}
        data-testid={testId}
        onClick={closeMobileMenu}
      >
        <div className="relative">
          {icon}
          {badgeCount > 0 && (
            <span className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
              {badgeCount > 9 ? '9+' : badgeCount}
            </span>
          )}
        </div>
        {(sidebarOpen || isMobile) && (
          <span className="flex items-center gap-2">
            {label}
            {badgeCount > 0 && (
              <span className="px-2 py-0.5 bg-red-500 text-white text-xs rounded-full">
                {badgeCount}
              </span>
            )}
          </span>
        )}
      </NavLink>
    );
  }

  function SectionTitle({ title }) {
    if (!sidebarOpen && !isMobile) return null;
    return (
      <div className="pt-4 pb-2">
        <p className="px-4 text-xs font-semibold text-gray-400 uppercase">{title}</p>
      </div>
    );
  }

  // Sidebar content
  var sidebarContent = (
    <React.Fragment>
      {/* Logo */}
      <div className={'border-b ' + (sidebarOpen || isMobile ? 'p-6' : 'p-4')}>
        <NavLink to="/" className="flex items-center gap-2" onClick={closeMobileMenu}>
          {(sidebarOpen || isMobile) ? (
            <img 
              src="/mydar-logo.png" 
              alt="MyDar" 
              className="h-16 w-auto"
            />
          ) : (
            <img 
              src="/mydar-logo.png" 
              alt="MyDar" 
              className="h-12 w-auto"
            />
          )}
        </NavLink>
        {(sidebarOpen || isMobile) && (
          <p className="text-xs text-gray-500 mt-1">Espace {isAdmin ? 'Admin' : 'Client'}</p>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        <NavItem to="/dashboard" icon={<Home className="w-5 h-5 flex-shrink-0" />} label="Tableau de bord" testId="nav-dashboard" />
        <NavItem to="/dashboard/profile" icon={<User className="w-5 h-5 flex-shrink-0" />} label="Mon Profil" testId="nav-profile" />

        {!isAdmin && (
          <React.Fragment>
            <NavItem to="/catalog" icon={<Store className="w-5 h-5 flex-shrink-0" />} label="Boutique" testId="nav-boutique" />
            
            <SectionTitle title="Achats" />
            <NavItem to="/dashboard/cart" icon={<ShoppingCart className="w-5 h-5 flex-shrink-0" />} label="Mon Panier" testId="nav-cart" />
            <NavItem to="/dashboard/favorites" icon={<Heart className="w-5 h-5 flex-shrink-0" />} label="Mes Favoris" testId="nav-favorites" />
            <NavItem to="/dashboard/my-purchase-requests" icon={<Package className="w-5 h-5 flex-shrink-0" />} label="Mes Achats" testId="nav-my-purchases" />

            <SectionTitle title="Annonces" />
            <NavItem to="/dashboard/my-annonces" icon={<Megaphone className="w-5 h-5 flex-shrink-0" />} label="Mes Annonces" testId="nav-my-annonces" />
            {isPro && (
              <React.Fragment>
                <NavItem to="/dashboard/annonces" icon={<Megaphone className="w-5 h-5 flex-shrink-0" />} label="Annonces Publiques" testId="nav-public-annonces" />
                <NavItem to="/dashboard/my-responses" icon={<Send className="w-5 h-5 flex-shrink-0" />} label="Mes Réponses" testId="nav-my-responses" />
              </React.Fragment>
            )}

            <SectionTitle title="Services" />
            <NavItem to="/dashboard/requests" icon={<FileText className="w-5 h-5 flex-shrink-0" />} label="Mes Demandes" testId="nav-requests" />
            <NavItem to="/dashboard/appointments" icon={<Calendar className="w-5 h-5 flex-shrink-0" />} label="Mes Rendez-vous" testId="nav-appointments" />
            <NavItemWithBadge 
              to="/dashboard/messages" 
              icon={<MessageSquare className="w-5 h-5 flex-shrink-0" />} 
              label="Messages" 
              testId="nav-messages"
              badgeCount={unreadMessages}
            />

            {isPro && (
              <NavItem to="/dashboard/company" icon={<Building className="w-5 h-5 flex-shrink-0" />} label="Mon Entreprise" testId="nav-company" />
            )}
          </React.Fragment>
        )}

        {isAdmin && (
          <React.Fragment>
            <SectionTitle title="Administration" />
            <NavItem to="/dashboard/admin/users" icon={<Users className="w-5 h-5 flex-shrink-0" />} label="Utilisateurs" testId="nav-admin-users" />
            <NavItem to="/dashboard/admin/requests" icon={<FileText className="w-5 h-5 flex-shrink-0" />} label="Demandes" testId="nav-admin-requests" />
            <NavItem to="/dashboard/admin/appointments" icon={<Calendar className="w-5 h-5 flex-shrink-0" />} label="Rendez-vous" testId="nav-admin-appointments" />
            <NavItem to="/dashboard/admin/products" icon={<Package className="w-5 h-5 flex-shrink-0" />} label="Produits" testId="nav-admin-products" />
            <NavItem to="/dashboard/admin/categories" icon={<FolderOpen className="w-5 h-5 flex-shrink-0" />} label="Catégories" testId="nav-admin-categories" />
            <NavItem to="/dashboard/admin/services" icon={<Settings className="w-5 h-5 flex-shrink-0" />} label="Services" testId="nav-admin-services" />
            <NavItem to="/dashboard/admin/messages" icon={<MessageSquare className="w-5 h-5 flex-shrink-0" />} label="Messages" testId="nav-admin-messages" />
            <NavItem to="/dashboard/admin/purchase-requests" icon={<ShoppingCart className="w-5 h-5 flex-shrink-0" />} label="Demandes d'Achat" testId="nav-admin-purchases" />
            <NavItem to="/dashboard/admin/annonces" icon={<Megaphone className="w-5 h-5 flex-shrink-0" />} label="Annonces" testId="nav-admin-annonces" />
            <NavItem to="/dashboard/admin/chatbot" icon={<Bot className="w-5 h-5 flex-shrink-0" />} label="Chatbot IA" testId="nav-admin-chatbot" />
            <NavItem to="/dashboard/admin/analytics" icon={<Activity className="w-5 h-5 flex-shrink-0" />} label="Analytics" testId="nav-admin-analytics" />
            <NavItem to="/dashboard/admin/logs" icon={<AlertTriangle className="w-5 h-5 flex-shrink-0" />} label="Logs & Erreurs" testId="nav-admin-logs" />
            <NavItem to="/dashboard/admin/statistics" icon={<BarChart3 className="w-5 h-5 flex-shrink-0" />} label="Statistiques" testId="nav-admin-statistics" />
          </React.Fragment>
        )}
      </nav>

      {/* User info & logout */}
      <div className="p-4 border-t">
        {(sidebarOpen || isMobile) ? (
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-600 to-cyan-500 flex items-center justify-center text-white font-bold flex-shrink-0">
              {user?.full_name?.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">{user?.full_name}</p>
              <p className="text-xs text-gray-500 truncate">{user?.email}</p>
            </div>
          </div>
        ) : (
          <div className="flex justify-center mb-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-600 to-cyan-500 flex items-center justify-center text-white font-bold">
              {user?.full_name?.charAt(0).toUpperCase()}
            </div>
          </div>
        )}
        <button
          onClick={handleLogout}
          data-testid="logout-button"
          className={'w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors ' + (sidebarOpen || isMobile ? 'justify-center' : 'justify-center')}
        >
          <LogOut className="w-4 h-4" />
          {(sidebarOpen || isMobile) && <span>Déconnexion</span>}
        </button>
      </div>
    </React.Fragment>
  );

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Mobile overlay */}
      {mobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={closeMobileMenu}
        />
      )}

      {/* Desktop Sidebar - Fixed */}
      <aside className={'hidden md:flex flex-col bg-white shadow-lg transition-all duration-300 fixed top-0 left-0 h-screen z-40 ' + (sidebarOpen ? 'w-64' : 'w-20')}>
        {sidebarContent}
        
        {/* Toggle button */}
        <button
          onClick={toggleSidebar}
          className="absolute top-6 -right-3 w-6 h-6 bg-white shadow-md rounded-full flex items-center justify-center text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors z-10"
          data-testid="sidebar-toggle"
        >
          {sidebarOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </button>
      </aside>

      {/* Spacer for fixed sidebar */}
      <div className={'hidden md:block flex-shrink-0 transition-all duration-300 ' + (sidebarOpen ? 'w-64' : 'w-20')} />

      {/* Mobile Sidebar */}
      <aside className={'fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 md:hidden flex flex-col ' + (mobileMenuOpen ? 'translate-x-0' : '-translate-x-full')}>
        {/* Close button */}
        <button
          onClick={closeMobileMenu}
          className="absolute top-4 right-4 p-2 text-gray-500 hover:text-gray-700"
          data-testid="mobile-menu-close"
        >
          <X className="w-6 h-6" />
        </button>
        {sidebarContent}
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        {/* Mobile header */}
        <div className="md:hidden bg-white shadow-sm px-4 py-3 flex items-center justify-between sticky top-0 z-30">
          <button
            onClick={toggleSidebar}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
            data-testid="mobile-menu-toggle"
          >
            <Menu className="w-6 h-6" />
          </button>
          <img 
            src="/mydar-logo.png" 
            alt="MyDar" 
            className="h-12 w-auto"
          />
          <div className="flex items-center gap-2">
            <NotificationBell />
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-600 to-cyan-500 flex items-center justify-center text-white font-bold text-sm">
              {user?.full_name?.charAt(0).toUpperCase()}
            </div>
          </div>
        </div>

        {/* Desktop header bar */}
        <div className="hidden md:flex items-center justify-end px-6 py-3 bg-white border-b sticky top-0 z-30">
          <div className="flex items-center gap-4">
            <PushNotificationToggle />
            <NotificationBell />
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-600 to-cyan-500 flex items-center justify-center text-white font-bold text-sm">
                {user?.full_name?.charAt(0).toUpperCase()}
              </div>
              <span className="text-sm text-gray-700">{user?.full_name}</span>
            </div>
          </div>
        </div>

        <div className="p-4 md:p-8">
          {children}
        </div>
      </main>
    </div>
  );
}

export default DashboardLayout;
