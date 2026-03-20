import { create } from 'zustand';
import { config } from '../config';

export interface AuthUser {
  email: string;
  name: string;
  picture: string;
  is_owner: boolean;
}

interface AuthStore {
  user: AuthUser | null;
  loading: boolean;
  fetchUser: () => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  loading: true,

  fetchUser: async () => {
    try {
      const res = await fetch(`${config.api.baseUrl}/auth/me`, {
        credentials: 'include',
      });
      if (!res.ok) throw new Error('Failed to fetch user');
      const data = await res.json();
      set({ user: data.authenticated ? data.user : null, loading: false });
    } catch {
      set({ user: null, loading: false });
    }
  },

  logout: async () => {
    try {
      await fetch(`${config.api.baseUrl}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } finally {
      set({ user: null });
    }
  },
}));
