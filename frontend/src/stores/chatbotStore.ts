// Store de chatbots con Zustand
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import type { Chatbot, CreateChatbotRequest, UpdateChatbotRequest, PaginatedResponse } from '@/types/api';
import { apiUrl, authHeaders } from '@/lib/config';

interface ChatbotState {
  // Estado
  chatbots: Chatbot[];
  currentChatbot: Chatbot | null;
  loading: boolean;
  error: string | null;
  pagination: {
    total: number;
    page: number;
    size: number;
    pages: number;
  };

  // Acciones
  fetchChatbots: (token: string, page?: number, size?: number) => Promise<void>;
  fetchChatbot: (id: string, token: string) => Promise<void>;
  createChatbot: (data: CreateChatbotRequest, token: string) => Promise<Chatbot | null>;
  updateChatbot: (id: string, data: UpdateChatbotRequest, token: string) => Promise<boolean>;
  deleteChatbot: (id: string, token: string) => Promise<boolean>;
  setCurrentChatbot: (chatbot: Chatbot | null) => void;
  clearError: () => void;
  reset: () => void;
}

export const useChatbotStore = create<ChatbotState>()(
  immer((set, get) => ({
    // Estado inicial
    chatbots: [],
    currentChatbot: null,
    loading: false,
    error: null,
    pagination: {
      total: 0,
      page: 1,
      size: 20,
      pages: 0,
    },

    // Obtener lista de chatbots
    fetchChatbots: async (token: string, page = 1, size = 20) => {
      set((state) => {
        state.loading = true;
        state.error = null;
      });

      try {
        const response = await fetch(
          apiUrl(`/api/v1/chatbots/?page=${page}&size=${size}`),
          {
            headers: authHeaders(token),
          }
        );

        if (!response.ok) {
          throw new Error('Error al obtener chatbots');
        }

        const data: PaginatedResponse<Chatbot> = await response.json();

        set((state) => {
          state.chatbots = data.items;
          state.pagination = {
            total: data.total,
            page: data.page,
            size: data.size,
            pages: data.pages,
          };
          state.loading = false;
        });
      } catch (error) {
        set((state) => {
          state.loading = false;
          state.error = error instanceof Error ? error.message : 'Error desconocido';
        });
      }
    },

    // Obtener un chatbot específico
    fetchChatbot: async (id: string, token: string) => {
      set((state) => {
        state.loading = true;
        state.error = null;
      });

      try {
        const response = await fetch(apiUrl(`/api/v1/chatbots/${id}`), {
          headers: authHeaders(token),
        });

        if (!response.ok) {
          throw new Error('Error al obtener el chatbot');
        }

        const chatbot: Chatbot = await response.json();

        set((state) => {
          state.currentChatbot = chatbot;
          state.loading = false;
        });
      } catch (error) {
        set((state) => {
          state.loading = false;
          state.error = error instanceof Error ? error.message : 'Error desconocido';
        });
      }
    },

    // Crear nuevo chatbot
    createChatbot: async (data: CreateChatbotRequest, token: string) => {
      set((state) => {
        state.loading = true;
        state.error = null;
      });

      try {
        const response = await fetch(apiUrl('/api/v1/chatbots/'), {
          method: 'POST',
          headers: authHeaders(token),
          body: JSON.stringify(data),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Error al crear el chatbot');
        }

        const newChatbot: Chatbot = await response.json();

        set((state) => {
          state.chatbots.unshift(newChatbot);
          state.currentChatbot = newChatbot;
          state.loading = false;
        });

        return newChatbot;
      } catch (error) {
        set((state) => {
          state.loading = false;
          state.error = error instanceof Error ? error.message : 'Error desconocido';
        });
        return null;
      }
    },

    // Actualizar chatbot
    updateChatbot: async (id: string, data: UpdateChatbotRequest, token: string) => {
      set((state) => {
        state.loading = true;
        state.error = null;
      });

      try {
        const response = await fetch(apiUrl(`/api/v1/chatbots/${id}`), {
          method: 'PUT',
          headers: authHeaders(token),
          body: JSON.stringify(data),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Error al actualizar el chatbot');
        }

        const updatedChatbot: Chatbot = await response.json();

        set((state) => {
          const index = state.chatbots.findIndex((bot) => bot.id === id);
          if (index !== -1) {
            state.chatbots[index] = updatedChatbot;
          }
          if (state.currentChatbot?.id === id) {
            state.currentChatbot = updatedChatbot;
          }
          state.loading = false;
        });

        return true;
      } catch (error) {
        set((state) => {
          state.loading = false;
          state.error = error instanceof Error ? error.message : 'Error desconocido';
        });
        return false;
      }
    },

    // Eliminar chatbot
    deleteChatbot: async (id: string, token: string) => {
      set((state) => {
        state.loading = true;
        state.error = null;
      });

      try {
        const response = await fetch(apiUrl(`/api/v1/chatbots/${id}`), {
          method: 'DELETE',
          headers: authHeaders(token),
        });

        if (!response.ok) {
          throw new Error('Error al eliminar el chatbot');
        }

        set((state) => {
          state.chatbots = state.chatbots.filter((bot) => bot.id !== id);
          if (state.currentChatbot?.id === id) {
            state.currentChatbot = null;
          }
          state.loading = false;
        });

        return true;
      } catch (error) {
        set((state) => {
          state.loading = false;
          state.error = error instanceof Error ? error.message : 'Error desconocido';
        });
        return false;
      }
    },

    // Setters
    setCurrentChatbot: (chatbot: Chatbot | null) => {
      set((state) => {
        state.currentChatbot = chatbot;
      });
    },

    clearError: () => {
      set((state) => {
        state.error = null;
      });
    },

    reset: () => {
      set((state) => {
        state.chatbots = [];
        state.currentChatbot = null;
        state.loading = false;
        state.error = null;
        state.pagination = {
          total: 0,
          page: 1,
          size: 20,
          pages: 0,
        };
      });
    },
  }))
);

// Selectores optimizados
export const useChatbots = () => useChatbotStore((state) => ({
  chatbots: state.chatbots,
  loading: state.loading,
  error: state.error,
  pagination: state.pagination,
}));

export const useCurrentChatbot = () => useChatbotStore((state) => ({
  currentChatbot: state.currentChatbot,
  loading: state.loading,
  error: state.error,
}));

export const useChatbotActions = () => useChatbotStore((state) => ({
  fetchChatbots: state.fetchChatbots,
  fetchChatbot: state.fetchChatbot,
  createChatbot: state.createChatbot,
  updateChatbot: state.updateChatbot,
  deleteChatbot: state.deleteChatbot,
  setCurrentChatbot: state.setCurrentChatbot,
  clearError: state.clearError,
  reset: state.reset,
}));
