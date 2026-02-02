import { create } from 'zustand';
import { api } from '../services/api';

interface User {
  id: number;
  username: string;
  email: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post('/auth/login', { email, password });

      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      set({ token: access_token, isLoading: false });

      // Load user data
      const userResponse = await api.get('/auth/me');
      set({ user: userResponse.data });
    } catch (error: any) {
      // Handle FastAPI validation errors (array) or string errors
      let errorMessage = 'Login failed';
      const detail = error.response?.data?.detail;
      if (typeof detail === 'string') {
        errorMessage = detail;
      } else if (Array.isArray(detail) && detail.length > 0) {
        errorMessage = detail[0].msg || 'Validation error';
      }
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  register: async (username, email, password) => {
    set({ isLoading: true, error: null });
    try {
      await api.post('/auth/register', { username, email, password });
      set({ isLoading: false });
    } catch (error: any) {
      let errorMessage = 'Registration failed';
      const detail = error.response?.data?.detail;
      if (typeof detail === 'string') {
        errorMessage = detail;
      } else if (Array.isArray(detail) && detail.length > 0) {
        errorMessage = detail[0].msg || 'Validation error';
      }
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    set({ user: null, token: null });
  },

  loadUser: async () => {
    const token = localStorage.getItem('token');
    if (!token) return;

    set({ isLoading: true });
    try {
      const response = await api.get('/auth/me');
      set({ user: response.data, isLoading: false });
    } catch {
      localStorage.removeItem('token');
      set({ user: null, token: null, isLoading: false });
    }
  },
}));
