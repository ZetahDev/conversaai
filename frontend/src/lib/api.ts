// Utilidades para manejo de API

import type { ApiResponse, ApiError, ValidationError } from '@/types/api';
import { apiUrl, authHeaders } from './config';

// Clase para errores de API
export class ApiException extends Error {
  public status: number;
  public errors: ApiError[];

  constructor(status: number, message: string, errors: ApiError[] = []) {
    super(message);
    this.name = 'ApiException';
    this.status = status;
    this.errors = errors;
  }
}

// Cliente API genérico
export class ApiClient {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || 'http://localhost:8000';
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  // Método genérico para hacer requests
  async request<T>(
    endpoint: string,
    options: RequestInit = {},
    token?: string
  ): Promise<T> {
    const url = apiUrl(endpoint);
    const headers = {
      ...this.defaultHeaders,
      ...authHeaders(token),
      ...options.headers,
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        await this.handleErrorResponse(response);
      }

      // Si la respuesta está vacía, retornar un objeto vacío
      const text = await response.text();
      if (!text) {
        return {} as T;
      }

      return JSON.parse(text) as T;
    } catch (error) {
      if (error instanceof ApiException) {
        throw error;
      }
      
      // Error de red o parsing
      throw new ApiException(0, 'Error de conexión', [
        { detail: error instanceof Error ? error.message : 'Error desconocido' }
      ]);
    }
  }

  // Manejar respuestas de error
  private async handleErrorResponse(response: Response): Promise<never> {
    let errorData: any;
    
    try {
      const text = await response.text();
      errorData = text ? JSON.parse(text) : {};
    } catch {
      errorData = { detail: 'Error del servidor' };
    }

    const errors: ApiError[] = [];

    // Manejar diferentes formatos de error
    if (errorData.detail) {
      if (Array.isArray(errorData.detail)) {
        // Errores de validación de FastAPI
        errors.push(...errorData.detail.map((err: ValidationError) => ({
          detail: err.msg,
          field: err.loc?.join('.'),
          code: err.type
        })));
      } else {
        errors.push({ detail: errorData.detail });
      }
    } else if (errorData.message) {
      errors.push({ detail: errorData.message });
    } else if (errorData.errors) {
      errors.push(...errorData.errors);
    } else {
      errors.push({ detail: `Error ${response.status}: ${response.statusText}` });
    }

    throw new ApiException(response.status, errors[0]?.detail || 'Error desconocido', errors);
  }

  // Métodos de conveniencia
  async get<T>(endpoint: string, token?: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' }, token);
  }

  async post<T>(endpoint: string, data?: any, token?: string): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: 'POST',
        body: data ? JSON.stringify(data) : undefined,
      },
      token
    );
  }

  async put<T>(endpoint: string, data?: any, token?: string): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: 'PUT',
        body: data ? JSON.stringify(data) : undefined,
      },
      token
    );
  }

  async patch<T>(endpoint: string, data?: any, token?: string): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: 'PATCH',
        body: data ? JSON.stringify(data) : undefined,
      },
      token
    );
  }

  async delete<T>(endpoint: string, token?: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' }, token);
  }
}

// Instancia global del cliente API
export const api = new ApiClient();

// Funciones de utilidad para manejo de errores
export const getErrorMessage = (error: unknown): string => {
  if (error instanceof ApiException) {
    return error.message;
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  return 'Error desconocido';
};

export const getErrorMessages = (error: unknown): string[] => {
  if (error instanceof ApiException) {
    return error.errors.map(err => err.detail);
  }
  
  return [getErrorMessage(error)];
};

export const isValidationError = (error: unknown): boolean => {
  return error instanceof ApiException && error.status === 422;
};

export const isAuthError = (error: unknown): boolean => {
  return error instanceof ApiException && (error.status === 401 || error.status === 403);
};

export const isNotFoundError = (error: unknown): boolean => {
  return error instanceof ApiException && error.status === 404;
};

// Funciones específicas para endpoints comunes
export const authApi = {
  login: async (email: string, password: string) => {
    return api.post('/api/v1/auth/login', { email, password });
  },
  
  register: async (data: any) => {
    return api.post('/api/v1/auth/register', data);
  },
  
  me: async (token: string) => {
    return api.get('/api/v1/auth/me', token);
  },
  
  logout: async (token: string) => {
    return api.post('/api/v1/auth/logout', {}, token);
  }
};

export const companiesApi = {
  getMyCompany: async (token: string) => {
    return api.get('/api/v1/companies/me', token);
  },
  
  updateCompany: async (id: string, data: any, token: string) => {
    return api.put(`/api/v1/companies/${id}`, data, token);
  }
};

export const chatbotsApi = {
  list: async (token: string, page = 1, size = 20) => {
    return api.get(`/api/v1/chatbots/?page=${page}&size=${size}`, token);
  },
  
  get: async (id: string, token: string) => {
    return api.get(`/api/v1/chatbots/${id}`, token);
  },
  
  create: async (data: any, token: string) => {
    return api.post('/api/v1/chatbots/', data, token);
  },
  
  update: async (id: string, data: any, token: string) => {
    return api.put(`/api/v1/chatbots/${id}`, data, token);
  },
  
  delete: async (id: string, token: string) => {
    return api.delete(`/api/v1/chatbots/${id}`, token);
  }
};

export const analyticsApi = {
  getDashboard: async (token: string) => {
    return api.get('/api/v1/analytics/dashboard', token);
  },

  getConversations: async (token: string, period = '7d') => {
    return api.get(`/api/v1/analytics/conversations?period=${period}`, token);
  }
};

// API para el nuevo dashboard de métricas
export const dashboardApi = {
  getOverview: async (token: string) => {
    return api.get('/api/v1/dashboard/overview', token);
  },

  getUsageTrends: async (token: string, days = 30) => {
    return api.get(`/api/v1/dashboard/usage-trends?days=${days}`, token);
  },

  getPerformanceMetrics: async (token: string) => {
    return api.get('/api/v1/dashboard/performance', token);
  },

  getUserActivity: async (token: string) => {
    return api.get('/api/v1/dashboard/user-activity', token);
  },

  getRealTimeMetrics: async (token: string) => {
    return api.get('/api/v1/dashboard/real-time', token);
  },

  getCompleteDashboard: async (token: string, days = 30) => {
    return api.get(`/api/v1/dashboard/complete?days=${days}`, token);
  },

  exportData: async (token: string, format = 'json', days = 30) => {
    return api.get(`/api/v1/dashboard/export?format=${format}&days=${days}`, token);
  }
};

// Helper para retry de requests
export const withRetry = async <T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  delay = 1000
): Promise<T> => {
  let lastError: unknown;
  
  for (let i = 0; i <= maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      // No reintentar errores de autenticación o validación
      if (isAuthError(error) || isValidationError(error)) {
        throw error;
      }
      
      // Si es el último intento, lanzar el error
      if (i === maxRetries) {
        throw error;
      }
      
      // Esperar antes del siguiente intento
      await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
    }
  }
  
  throw lastError;
};

export default api;
