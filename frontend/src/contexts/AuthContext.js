import React, { createContext, useState, useContext, useEffect } from 'react';
import authService from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const storedUser = authService.getStoredUser();
    if (storedUser) {
      setUser(storedUser);
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    try {
      const userData = await authService.login(email, password);
      setUser(userData);
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Erreur de connexion' 
      };
    }
  };

  const register = async (userData) => {
    try {
      await authService.register(userData);
      // Auto login after registration
      return await login(userData.email, userData.password);
    } catch (error) {
      console.error('Register error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Erreur lors de l\'inscription' 
      };
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  // Function to directly set user (used by Google OAuth)
  const setUserDirectly = (userData) => {
    setUser(userData);
    if (userData) {
      authService.storeUser(userData);
    }
  };

  const refreshUser = async () => {
    try {
      const userData = await authService.getProfile();
      setUser(userData);
      authService.storeUser(userData);
    } catch (error) {
      console.error('Error refreshing user:', error);
    }
  };

  const isAuthenticated = () => {
    return !!user;
  };

  const hasRole = (allowedRoles) => {
    if (!user) return false;
    return allowedRoles.includes(user.role);
  };

  const value = {
    user,
    setUser: setUserDirectly,
    login,
    register,
    logout,
    refreshUser,
    isAuthenticated,
    hasRole,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
