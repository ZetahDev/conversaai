// Store de autenticación con Zustand
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { User, Company, LoginResponse, RegisterResponse } from '@/types/api';
import { apiUrl, authHeaders } from '@/lib/config';

interface AuthState {
  // Estado
  isAuthenticated: boolean;
  user: User | null;
  company: Company | null;
  token: string | null;
  loading: boolean;
  error: string | null;

  // Acciones
  login: (email: string, password: string) => Promise<boolean>;
  register: (data: any) => Promise<boolean>;
  logout: () => void;
  setUser: (user: User) => void;
  setCompany: (company: Company) => void;
  setToken: (token: string) => void;
  clearError: () => void;
  checkAuth: () => Promise<boolean>;
  refreshUserData: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Estado inicial
      isAuthenticated: false,
      user: null,
      company: null,
      token: null,
      loading: false,
      error: null,

      // Acción de login
      login: async (email: string, password: string) => {
        set({ loading: true, error: null });

        try {
          const response = await fetch(apiUrl('/api/v1/auth/login'), {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ email, password }),
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error en el login');
          }

          const data: LoginResponse = await response.json();

          set({
            isAuthenticated: true,
            user: data.user,
            token: data.access_token,
            loading: false,
            error: null,
          });

          // Obtener datos de la empresa
          await get().refreshUserData();

          return true;
        } catch (error) {
          set({
            loading: false,
            error: error instanceof Error ? error.message : 'Error desconocido',
            isAuthenticated: false,
            user: null,
            token: null,
          });
          return false;
        }
      },

      // Acción de registro
      register: async (data: any) => {
        set({ loading: true, error: null });

        try {
          const response = await fetch(apiUrl('/api/v1/auth/register'), {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(data),
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error en el registro');
          }

          const responseData: RegisterResponse = await response.json();

          set({
            isAuthenticated: true,
            user: responseData.user,
            company: responseData.company,
            token: responseData.access_token,
            loading: false,
            error: null,
          });

          return true;
        } catch (error) {
          set({
            loading: false,
            error: error instanceof Error ? error.message : 'Error desconocido',
            isAuthenticated: false,
            user: null,
            company: null,
            token: null,
          });
          return false;
        }
      },

      // Acción de logout
      logout: () => {
        set({
          isAuthenticated: false,
          user: null,
          company: null,
          token: null,
          error: null,
        });
      },

      // Setters
      setUser: (user: User) => set({ user }),
      setCompany: (company: Company) => set({ company }),
      setToken: (token: string) => set({ token, isAuthenticated: true }),
      clearError: () => set({ error: null }),

      // Verificar autenticación
      checkAuth: async () => {
        const { token } = get();
        if (!token) {
          return false;
        }

        set({ loading: true });

        try {
          const response = await fetch(apiUrl('/api/v1/auth/me'), {
            headers: authHeaders(token),
          });

          if (!response.ok) {
            throw new Error('Token inválido');
          }

          const user: User = await response.json();
          set({ user, isAuthenticated: true, loading: false });

          // Obtener datos de la empresa si no los tenemos
          if (!get().company) {
            await get().refreshUserData();
          }

          return true;
        } catch (error) {
          set({
            isAuthenticated: false,
            user: null,
            company: null,
            token: null,
            loading: false,
          });
          return false;
        }
      },

      // Refrescar datos del usuario y empresa
      refreshUserData: async () => {
        const { token } = get();
        if (!token) return;

        try {
          // Obtener datos de la empresa
          const companyResponse = await fetch(apiUrl('/api/v1/companies/me'), {
            headers: authHeaders(token),
          });

          if (companyResponse.ok) {
            const company: Company = await companyResponse.json();
            set({ company });
          }
        } catch (error) {
          console.error('Error obteniendo datos de la empresa:', error);
        }
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        company: state.company,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Selectores para optimizar re-renders
export const useAuth = () => useAuthStore((state) => ({
  isAuthenticated: state.isAuthenticated,
  user: state.user,
  company: state.company,
  loading: state.loading,
  error: state.error,
}));

export const useAuthActions = () => useAuthStore((state) => ({
  login: state.login,
  register: state.register,
  logout: state.logout,
  checkAuth: state.checkAuth,
  clearError: state.clearError,
  refreshUserData: state.refreshUserData,
}));
