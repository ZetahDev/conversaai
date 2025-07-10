// Exportaciones principales de los stores
export { useAuthStore, useAuth, useAuthActions } from './authStore';
export { useChatbotStore, useChatbots, useCurrentChatbot, useChatbotActions } from './chatbotStore';
export { useConversationStore, useConversations, useCurrentConversation, useConversationActions } from './conversationStore';
export { useAnalyticsStore, useDashboardStats, useConversationMetrics, useAnalyticsActions, useAutoRefreshAnalytics } from './analyticsStore';

// Store principal que combina funcionalidades comunes
import { create } from 'zustand';
import { useAuthStore } from './authStore';
import { useChatbotStore } from './chatbotStore';
import { useConversationStore } from './conversationStore';
import { useAnalyticsStore } from './analyticsStore';

interface AppState {
  // Estado global de la aplicación
  isInitialized: boolean;
  theme: 'light' | 'dark' | 'system';
  sidebarOpen: boolean;
  notifications: Notification[];
  
  // Acciones globales
  initialize: () => Promise<void>;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  toggleSidebar: () => void;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
  resetAllStores: () => void;
}

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  timestamp: Date;
  duration?: number;
}

export const useAppStore = create<AppState>((set, get) => ({
  // Estado inicial
  isInitialized: false,
  theme: 'system',
  sidebarOpen: true,
  notifications: [],

  // Inicializar la aplicación
  initialize: async () => {
    try {
      // Verificar autenticación
      const authStore = useAuthStore.getState();
      if (authStore.token) {
        await authStore.checkAuth();
      }

      // Cargar tema desde localStorage
      const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | 'system' | null;
      if (savedTheme) {
        get().setTheme(savedTheme);
      }

      // Aplicar tema
      const theme = get().theme;
      if (theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }

      set({ isInitialized: true });
    } catch (error) {
      console.error('Error inicializando la aplicación:', error);
      set({ isInitialized: true });
    }
  },

  // Cambiar tema
  setTheme: (theme: 'light' | 'dark' | 'system') => {
    set({ theme });
    localStorage.setItem('theme', theme);

    // Aplicar tema inmediatamente
    if (theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  },

  // Toggle sidebar
  toggleSidebar: () => {
    set((state) => ({ sidebarOpen: !state.sidebarOpen }));
  },

  // Agregar notificación
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date(),
    };

    set((state) => ({
      notifications: [...state.notifications, newNotification],
    }));

    // Auto-remover después del tiempo especificado
    if (notification.duration !== 0) {
      setTimeout(() => {
        get().removeNotification(newNotification.id);
      }, notification.duration || 5000);
    }
  },

  // Remover notificación
  removeNotification: (id: string) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    }));
  },

  // Limpiar todas las notificaciones
  clearNotifications: () => {
    set({ notifications: [] });
  },

  // Reset de todos los stores
  resetAllStores: () => {
    useAuthStore.getState().logout();
    useChatbotStore.getState().reset();
    useConversationStore.getState().reset();
    useAnalyticsStore.getState().reset();
    set({
      notifications: [],
      sidebarOpen: true,
    });
  },
}));

// Selectores optimizados para el store principal
export const useApp = () => useAppStore((state) => ({
  isInitialized: state.isInitialized,
  theme: state.theme,
  sidebarOpen: state.sidebarOpen,
}));

export const useNotifications = () => useAppStore((state) => ({
  notifications: state.notifications,
}));

export const useAppActions = () => useAppStore((state) => ({
  initialize: state.initialize,
  setTheme: state.setTheme,
  toggleSidebar: state.toggleSidebar,
  addNotification: state.addNotification,
  removeNotification: state.removeNotification,
  clearNotifications: state.clearNotifications,
  resetAllStores: state.resetAllStores,
}));

// Hook personalizado para manejo de errores globales
export const useErrorHandler = () => {
  const { addNotification } = useAppActions();

  const handleError = (error: unknown, title = 'Error') => {
    let message = 'Ha ocurrido un error inesperado';

    if (error instanceof Error) {
      message = error.message;
    } else if (typeof error === 'string') {
      message = error;
    }

    addNotification({
      type: 'error',
      title,
      message,
    });
  };

  const handleSuccess = (title: string, message?: string) => {
    addNotification({
      type: 'success',
      title,
      message,
    });
  };

  const handleWarning = (title: string, message?: string) => {
    addNotification({
      type: 'warning',
      title,
      message,
    });
  };

  const handleInfo = (title: string, message?: string) => {
    addNotification({
      type: 'info',
      title,
      message,
    });
  };

  return {
    handleError,
    handleSuccess,
    handleWarning,
    handleInfo,
  };
};

// Hook para inicialización automática
export const useInitializeApp = () => {
  const { initialize, isInitialized } = useAppStore();

  if (typeof window !== 'undefined' && !isInitialized) {
    initialize();
  }

  return { isInitialized };
};

// Tipos exportados
export type { Notification };

// Utilidades para desarrollo
export const devTools = {
  // Obtener estado completo de todos los stores
  getAllStates: () => ({
    app: useAppStore.getState(),
    auth: useAuthStore.getState(),
    chatbots: useChatbotStore.getState(),
    conversations: useConversationStore.getState(),
    analytics: useAnalyticsStore.getState(),
  }),

  // Reset completo de la aplicación
  resetAll: () => {
    useAppStore.getState().resetAllStores();
  },

  // Log del estado actual
  logStates: () => {
    console.group('🏪 Zustand Stores State');
    console.log('App:', useAppStore.getState());
    console.log('Auth:', useAuthStore.getState());
    console.log('Chatbots:', useChatbotStore.getState());
    console.log('Conversations:', useConversationStore.getState());
    console.log('Analytics:', useAnalyticsStore.getState());
    console.groupEnd();
  },
};

// Hacer devTools disponible globalmente en desarrollo
if (typeof window !== 'undefined' && import.meta.env.DEV) {
  (window as any).zustandDevTools = devTools;
}
