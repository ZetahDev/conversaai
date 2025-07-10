// Store de analytics con Zustand
import { create } from 'zustand';
import type { DashboardStats } from '@/types/api';
import { apiUrl, authHeaders } from '@/lib/config';

interface ConversationMetrics {
  total_conversations: number;
  active_conversations: number;
  closed_conversations: number;
  avg_response_time: number;
  satisfaction_rate: number;
  messages_per_conversation: number;
  peak_hours: { hour: number; count: number }[];
  daily_stats: { date: string; conversations: number; messages: number }[];
}

interface AnalyticsState {
  // Estado
  dashboardStats: DashboardStats | null;
  conversationMetrics: ConversationMetrics | null;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;

  // Acciones
  fetchDashboardStats: (token: string) => Promise<void>;
  fetchConversationMetrics: (token: string, period?: string, chatbotId?: string) => Promise<void>;
  refreshAll: (token: string) => Promise<void>;
  clearError: () => void;
  reset: () => void;
}

export const useAnalyticsStore = create<AnalyticsState>((set, get) => ({
  // Estado inicial
  dashboardStats: null,
  conversationMetrics: null,
  loading: false,
  error: null,
  lastUpdated: null,

  // Obtener estadísticas del dashboard
  fetchDashboardStats: async (token: string) => {
    set({ loading: true, error: null });

    try {
      const response = await fetch(apiUrl('/api/v1/analytics/dashboard'), {
        headers: authHeaders(token),
      });

      if (!response.ok) {
        throw new Error('Error al obtener estadísticas del dashboard');
      }

      const stats: DashboardStats = await response.json();

      set({
        dashboardStats: stats,
        loading: false,
        lastUpdated: new Date(),
      });
    } catch (error) {
      set({
        loading: false,
        error: error instanceof Error ? error.message : 'Error desconocido',
      });
    }
  },

  // Obtener métricas de conversaciones
  fetchConversationMetrics: async (token: string, period = '7d', chatbotId?: string) => {
    set({ loading: true, error: null });

    try {
      let url = `/api/v1/analytics/conversations?period=${period}`;
      if (chatbotId) {
        url += `&chatbot_id=${chatbotId}`;
      }

      const response = await fetch(apiUrl(url), {
        headers: authHeaders(token),
      });

      if (!response.ok) {
        throw new Error('Error al obtener métricas de conversaciones');
      }

      const metrics: ConversationMetrics = await response.json();

      set({
        conversationMetrics: metrics,
        loading: false,
        lastUpdated: new Date(),
      });
    } catch (error) {
      set({
        loading: false,
        error: error instanceof Error ? error.message : 'Error desconocido',
      });
    }
  },

  // Refrescar todas las métricas
  refreshAll: async (token: string) => {
    const promises = [
      get().fetchDashboardStats(token),
      get().fetchConversationMetrics(token),
    ];

    await Promise.allSettled(promises);
  },

  // Limpiar error
  clearError: () => {
    set({ error: null });
  },

  // Reset del store
  reset: () => {
    set({
      dashboardStats: null,
      conversationMetrics: null,
      loading: false,
      error: null,
      lastUpdated: null,
    });
  },
}));

// Selectores optimizados
export const useDashboardStats = () => useAnalyticsStore((state) => ({
  stats: state.dashboardStats,
  loading: state.loading,
  error: state.error,
  lastUpdated: state.lastUpdated,
}));

export const useConversationMetrics = () => useAnalyticsStore((state) => ({
  metrics: state.conversationMetrics,
  loading: state.loading,
  error: state.error,
  lastUpdated: state.lastUpdated,
}));

export const useAnalyticsActions = () => useAnalyticsStore((state) => ({
  fetchDashboardStats: state.fetchDashboardStats,
  fetchConversationMetrics: state.fetchConversationMetrics,
  refreshAll: state.refreshAll,
  clearError: state.clearError,
  reset: state.reset,
}));

// Hook personalizado para auto-refresh
export const useAutoRefreshAnalytics = (token: string, intervalMs = 30000) => {
  const { refreshAll } = useAnalyticsActions();

  // En un entorno real, usarías useEffect aquí
  // pero como estamos en Astro, esto sería para componentes React/Vue
  const startAutoRefresh = () => {
    const interval = setInterval(() => {
      refreshAll(token);
    }, intervalMs);

    return () => clearInterval(interval);
  };

  return { startAutoRefresh };
};
