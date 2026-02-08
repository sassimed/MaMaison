import api from './api';

const authService = {
  // Register new user
  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  // Login user
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    const { access_token, refresh_token } = response.data;
    
    // Store tokens
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    
    // Get user info
    const user = await authService.getCurrentUser();
    localStorage.setItem('user', JSON.stringify(user));
    
    return user;
  },

  // Logout user
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },

  // Get current user
  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  // Get user profile (alias for getCurrentUser)
  getProfile: async () => {
    const response = await api.get('/user/profile');
    return response.data;
  },

  // Store user in localStorage
  storeUser: (user) => {
    localStorage.setItem('user', JSON.stringify(user));
  },

  // Check if user is authenticated
  isAuthenticated: () => {
    return !!localStorage.getItem('access_token');
  },

  // Get stored user
  getStoredUser: () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },
};

export default authService;
