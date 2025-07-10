// Store de conversaciones con Zustand
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import type { Conversation, Message, CreateConversationRequest, SendMessageRequest } from '@/types/api';
import { apiUrl, authHeaders } from '@/lib/config';

interface ConversationState {
  // Estado
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  loading: boolean;
  sendingMessage: boolean;
  error: string | null;

  // Acciones
  fetchConversations: (token: string, chatbotId?: string) => Promise<void>;
  fetchConversation: (id: string, token: string) => Promise<void>;
  fetchMessages: (conversationId: string, token: string) => Promise<void>;
  createConversation: (data: CreateConversationRequest, token: string) => Promise<Conversation | null>;
  sendMessage: (conversationId: string, data: SendMessageRequest, token: string) => Promise<Message | null>;
  setCurrentConversation: (conversation: Conversation | null) => void;
  addMessage: (message: Message) => void;
  markAsRead: (conversationId: string, token: string) => Promise<void>;
  closeConversation: (conversationId: string, token: string) => Promise<void>;
  clearError: () => void;
  reset: () => void;
}

export const useConversationStore = create<ConversationState>()(
  immer((set, get) => ({
    // Estado inicial
    conversations: [],
    currentConversation: null,
    messages: [],
    loading: false,
    sendingMessage: false,
    error: null,

    // Obtener conversaciones
    fetchConversations: async (token: string, chatbotId?: string) => {
      set((state) => {
        state.loading = true;
        state.error = null;
      });

      try {
        let url = '/api/v1/conversations/';
        if (chatbotId) {
          url += `?chatbot_id=${chatbotId}`;
        }

        const response = await fetch(apiUrl(url), {
          headers: authHeaders(token),
        });

        if (!response.ok) {
          throw new Error('Error al obtener conversaciones');
        }

        const data = await response.json();
        const conversations = Array.isArray(data) ? data : data.items || [];

        set((state) => {
          state.conversations = conversations;
          state.loading = false;
        });
      } catch (error) {
        set((state) => {
          state.loading = false;
          state.error = error instanceof Error ? error.message : 'Error desconocido';
        });
      }
    },

    // Obtener una conversación específica
    fetchConversation: async (id: string, token: string) => {
      set((state) => {
        state.loading = true;
        state.error = null;
      });

      try {
        const response = await fetch(apiUrl(`/api/v1/conversations/${id}`), {
          headers: authHeaders(token),
        });

        if (!response.ok) {
          throw new Error('Error al obtener la conversación');
        }

        const conversation: Conversation = await response.json();

        set((state) => {
          state.currentConversation = conversation;
          state.loading = false;
        });

        // Obtener mensajes de la conversación
        await get().fetchMessages(id, token);
      } catch (error) {
        set((state) => {
          state.loading = false;
          state.error = error instanceof Error ? error.message : 'Error desconocido';
        });
      }
    },

    // Obtener mensajes de una conversación
    fetchMessages: async (conversationId: string, token: string) => {
      try {
        const response = await fetch(
          apiUrl(`/api/v1/conversations/${conversationId}/messages`),
          {
            headers: authHeaders(token),
          }
        );

        if (!response.ok) {
          throw new Error('Error al obtener mensajes');
        }

        const data = await response.json();
        const messages = Array.isArray(data) ? data : data.items || [];

        set((state) => {
          state.messages = messages;
        });
      } catch (error) {
        set((state) => {
          state.error = error instanceof Error ? error.message : 'Error desconocido';
        });
      }
    },

    // Crear nueva conversación
    createConversation: async (data: CreateConversationRequest, token: string) => {
      set((state) => {
        state.loading = true;
        state.error = null;
      });

      try {
        const response = await fetch(apiUrl('/api/v1/conversations/'), {
          method: 'POST',
          headers: authHeaders(token),
          body: JSON.stringify(data),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Error al crear la conversación');
        }

        const newConversation: Conversation = await response.json();

        set((state) => {
          state.conversations.unshift(newConversation);
          state.currentConversation = newConversation;
          state.messages = [];
          state.loading = false;
        });

        return newConversation;
      } catch (error) {
        set((state) => {
          state.loading = false;
          state.error = error instanceof Error ? error.message : 'Error desconocido';
        });
        return null;
      }
    },

    // Enviar mensaje
    sendMessage: async (conversationId: string, data: SendMessageRequest, token: string) => {
      set((state) => {
        state.sendingMessage = true;
        state.error = null;
      });

      try {
        const response = await fetch(
          apiUrl(`/api/v1/conversations/${conversationId}/messages`),
          {
            method: 'POST',
            headers: authHeaders(token),
            body: JSON.stringify(data),
          }
        );

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Error al enviar el mensaje');
        }

        const newMessage: Message = await response.json();

        set((state) => {
          state.messages.push(newMessage);
          state.sendingMessage = false;
        });

        return newMessage;
      } catch (error) {
        set((state) => {
          state.sendingMessage = false;
          state.error = error instanceof Error ? error.message : 'Error desconocido';
        });
        return null;
      }
    },

    // Marcar conversación como leída
    markAsRead: async (conversationId: string, token: string) => {
      try {
        await fetch(apiUrl(`/api/v1/conversations/${conversationId}/read`), {
          method: 'POST',
          headers: authHeaders(token),
        });

        set((state) => {
          const conversation = state.conversations.find((c) => c.id === conversationId);
          if (conversation) {
            // Actualizar estado de leído si existe esa propiedad
            (conversation as any).unread_count = 0;
          }
        });
      } catch (error) {
        console.error('Error marcando como leído:', error);
      }
    },

    // Cerrar conversación
    closeConversation: async (conversationId: string, token: string) => {
      try {
        await fetch(apiUrl(`/api/v1/conversations/${conversationId}/close`), {
          method: 'POST',
          headers: authHeaders(token),
        });

        set((state) => {
          const conversation = state.conversations.find((c) => c.id === conversationId);
          if (conversation) {
            conversation.status = 'CLOSED';
          }
          if (state.currentConversation?.id === conversationId) {
            state.currentConversation.status = 'CLOSED';
          }
        });
      } catch (error) {
        set((state) => {
          state.error = error instanceof Error ? error.message : 'Error desconocido';
        });
      }
    },

    // Setters
    setCurrentConversation: (conversation: Conversation | null) => {
      set((state) => {
        state.currentConversation = conversation;
        state.messages = [];
      });
    },

    addMessage: (message: Message) => {
      set((state) => {
        state.messages.push(message);
      });
    },

    clearError: () => {
      set((state) => {
        state.error = null;
      });
    },

    reset: () => {
      set((state) => {
        state.conversations = [];
        state.currentConversation = null;
        state.messages = [];
        state.loading = false;
        state.sendingMessage = false;
        state.error = null;
      });
    },
  }))
);

// Selectores optimizados
export const useConversations = () => useConversationStore((state) => ({
  conversations: state.conversations,
  loading: state.loading,
  error: state.error,
}));

export const useCurrentConversation = () => useConversationStore((state) => ({
  currentConversation: state.currentConversation,
  messages: state.messages,
  sendingMessage: state.sendingMessage,
  error: state.error,
}));

export const useConversationActions = () => useConversationStore((state) => ({
  fetchConversations: state.fetchConversations,
  fetchConversation: state.fetchConversation,
  fetchMessages: state.fetchMessages,
  createConversation: state.createConversation,
  sendMessage: state.sendMessage,
  setCurrentConversation: state.setCurrentConversation,
  addMessage: state.addMessage,
  markAsRead: state.markAsRead,
  closeConversation: state.closeConversation,
  clearError: state.clearError,
  reset: state.reset,
}));
