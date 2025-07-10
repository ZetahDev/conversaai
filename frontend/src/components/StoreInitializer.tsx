// Componente para inicializar los stores de Zustand con datos SSR
import React, { useEffect } from 'react';
import { useAuthStore, useChatbotStore, useAnalyticsStore } from '@/stores';
import type { User, Company, Chatbot, DashboardStats } from '@/types/api';

interface StoreInitializerProps {
  user?: User | null;
  company?: Company | null;
  chatbots?: Chatbot[];
  stats?: DashboardStats | null;
  token?: string;
}

const StoreInitializer: React.FC<StoreInitializerProps> = ({
  user,
  company,
  chatbots = [],
  stats,
  token
}) => {
  useEffect(() => {
    // Inicializar store de autenticación
    if (token && user) {
      const authStore = useAuthStore.getState();
      authStore.setToken(token);
      authStore.setUser(user);
      if (company) {
        authStore.setCompany(company);
      }
    }

    // Inicializar store de chatbots
    if (chatbots.length > 0) {
      const chatbotStore = useChatbotStore.getState();
      // Simular respuesta paginada
      chatbotStore.chatbots = chatbots;
      chatbotStore.pagination = {
        total: chatbots.length,
        page: 1,
        size: 20,
        pages: Math.ceil(chatbots.length / 20)
      };
    }

    // Inicializar store de analytics
    if (stats) {
      const analyticsStore = useAnalyticsStore.getState();
      analyticsStore.dashboardStats = stats;
      analyticsStore.lastUpdated = new Date();
    }
  }, [user, company, chatbots, stats, token]);

  // Este componente no renderiza nada
  return null;
};

export default StoreInitializer;
