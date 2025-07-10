/**
 * API functions for integrations
 */

const API_BASE = 'http://localhost:8000/api/v1';

export interface Integration {
  id: string;
  name: string;
  integration_type: string;
  status: string;
  channel_config: Record<string, any>;
  api_key?: string;
  webhook_url?: string;
  is_active: boolean;
  last_connected_at?: string;
  total_messages_sent: number;
  total_messages_received: number;
}

export interface IntegrationStatus {
  chatbot_id: string;
  integrations: Record<string, {
    id?: string;
    active: boolean;
    configured: boolean;
    status?: string;
    last_connected?: string;
    total_messages?: number;
  }>;
}

export interface CreateIntegrationRequest {
  chatbot_id: string;
  integration_type: 'whatsapp' | 'telegram' | 'web_widget';
  name: string;
  config: Record<string, any>;
}

export interface WhatsAppConfig {
  phone_number_id: string;
  access_token: string;
  webhook_verify_token?: string;
}

export interface TelegramConfig {
  bot_token: string;
  bot_username?: string;
}

export interface WebWidgetConfig {
  widget_type: 'embedded' | 'iframe' | 'popup';
  primary_color?: string;
  title?: string;
  subtitle?: string;
  position?: string;
}

class IntegrationsAPI {
  private getHeaders(token: string) {
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }

  async getAvailableIntegrations() {
    const response = await fetch(`${API_BASE}/integrations/available`);
    if (!response.ok) {
      throw new Error('Failed to fetch available integrations');
    }
    return response.json();
  }

  async getIntegrationStatus(chatbotId: string, token: string): Promise<IntegrationStatus> {
    const response = await fetch(`${API_BASE}/integrations/status/${chatbotId}`, {
      headers: this.getHeaders(token),
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch integration status');
    }
    
    return response.json();
  }

  async createIntegration(data: CreateIntegrationRequest, token: string): Promise<Integration> {
    const response = await fetch(`${API_BASE}/integrations/create`, {
      method: 'POST',
      headers: this.getHeaders(token),
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create integration');
    }

    return response.json();
  }

  async updateIntegration(integrationId: string, config: Record<string, any>, token: string): Promise<Integration> {
    const response = await fetch(`${API_BASE}/integrations/${integrationId}`, {
      method: 'PUT',
      headers: this.getHeaders(token),
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update integration');
    }

    return response.json();
  }

  async deleteIntegration(integrationId: string, token: string): Promise<void> {
    const response = await fetch(`${API_BASE}/integrations/${integrationId}`, {
      method: 'DELETE',
      headers: this.getHeaders(token),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete integration');
    }
  }

  // WhatsApp specific
  async setupWhatsApp(chatbotId: string, config: WhatsAppConfig, token: string) {
    const response = await fetch(`${API_BASE}/integrations/whatsapp/setup/${chatbotId}`, {
      method: 'POST',
      headers: this.getHeaders(token),
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to setup WhatsApp integration');
    }

    return response.json();
  }

  async getWhatsAppConfig() {
    const response = await fetch(`${API_BASE}/integrations/whatsapp/config`);
    if (!response.ok) {
      throw new Error('Failed to fetch WhatsApp config');
    }
    return response.json();
  }

  // Telegram specific
  async setupTelegram(chatbotId: string, botToken: string, token: string) {
    const response = await fetch(`${API_BASE}/integrations/telegram/setup/${chatbotId}`, {
      method: 'POST',
      headers: this.getHeaders(token),
      body: JSON.stringify({ bot_token: botToken }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to setup Telegram integration');
    }

    return response.json();
  }

  async getTelegramConfig() {
    const response = await fetch(`${API_BASE}/integrations/telegram/config`);
    if (!response.ok) {
      throw new Error('Failed to fetch Telegram config');
    }
    return response.json();
  }

  async deleteTelegramWebhook(botToken: string, token: string) {
    const response = await fetch(`${API_BASE}/integrations/telegram/webhook/${botToken}`, {
      method: 'DELETE',
      headers: this.getHeaders(token),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete Telegram webhook');
    }

    return response.json();
  }

  // Web Widget specific
  async getWidgetCode(chatbotId: string, widgetType: string, config: WebWidgetConfig, token: string) {
    const params = new URLSearchParams({
      widget_type: widgetType,
      ...config
    });

    const response = await fetch(`${API_BASE}/integrations/web/widget-code/${chatbotId}?${params}`, {
      headers: this.getHeaders(token),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate widget code');
    }

    return response.json();
  }

  async getWebWidgetConfig() {
    const response = await fetch(`${API_BASE}/integrations/web/config`);
    if (!response.ok) {
      throw new Error('Failed to fetch Web Widget config');
    }
    return response.json();
  }

  // Chat with web widget
  async sendWebWidgetMessage(chatbotId: string, message: string, sessionId: string, userData?: Record<string, any>) {
    const response = await fetch(`${API_BASE}/integrations/web/message/${chatbotId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        user_data: userData,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to send message');
    }

    return response.json();
  }
}

export const integrationsAPI = new IntegrationsAPI();
