import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const RoleGuard = ({ children, allowedRoles }) => {
  const { hasRole, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!hasRole(allowedRoles)) {
    return <Navigate to="/" replace />;
  }

  return children;
};

export default RoleGuard;
