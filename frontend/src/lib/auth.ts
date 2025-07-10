// Utilidades de autenticación para el frontend
import type { LoginRequest, LoginResponse, RegisterRequest, RegisterResponse, User } from '@/types/api';
import { apiUrl, authHeaders } from './config';

// Configuración de cookies
const COOKIE_CONFIG = {
  httpOnly: false, // Cambiado a false para poder acceder desde JavaScript
  secure: import.meta.env.PROD,
  sameSite: 'lax' as const, // Cambiado de 'strict' a 'lax' para cross-origin
  maxAge: 60 * 60 * 24 * 7, // 7 días
  path: '/',
};

// Función para hacer login
export async function login(email: string, password: string): Promise<{ success: boolean; error?: string }> {
  try {
    const loginData: LoginRequest = { email, password };

    const response = await fetch(apiUrl('/api/v1/auth/login'), {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(loginData),
      credentials: 'include', // Importante para cookies cross-origin
    });

    if (response.ok) {
      const data: LoginResponse = await response.json();
      
      // Guardar el token en localStorage como respaldo
      if (typeof window !== 'undefined') {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
      }

      return { success: true };
    } else {
      const error = await response.json();
      return { success: false, error: error.detail || 'Error en el login' };
    }
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Error de conexión' 
    };
  }
}

// Función para hacer registro
export async function register(data: RegisterRequest): Promise<{ success: boolean; error?: string }> {
  try {
    const response = await fetch(apiUrl('/api/v1/auth/register'), {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(data),
      credentials: 'include',
    });

    if (response.ok) {
      const responseData: RegisterResponse = await response.json();
      
      // Guardar el token en localStorage como respaldo
      if (typeof window !== 'undefined') {
        localStorage.setItem('access_token', responseData.access_token);
        localStorage.setItem('user', JSON.stringify(responseData.user));
        localStorage.setItem('company', JSON.stringify(responseData.company));
      }

      return { success: true };
    } else {
      const error = await response.json();
      return { success: false, error: error.detail || 'Error en el registro' };
    }
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Error de conexión' 
    };
  }
}

// Función para obtener el token
export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  
  // Intentar obtener de localStorage primero
  return localStorage.getItem('access_token');
}

// Función para obtener datos del usuario
export function getUser(): User | null {
  if (typeof window === 'undefined') return null;
  
  const userStr = localStorage.getItem('user');
  if (!userStr) return null;
  
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
}

// Función para verificar si está autenticado
export function isAuthenticated(): boolean {
  return getToken() !== null;
}

// Función para hacer logout
export function logout(): void {
  if (typeof window === 'undefined') return;
  
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
  localStorage.removeItem('company');
}

// Función para verificar el token con el backend
export async function verifyToken(token: string): Promise<{ valid: boolean; user?: User }> {
  try {
    const response = await fetch(apiUrl('/api/v1/auth/me'), {
      headers: authHeaders(token),
      credentials: 'include',
    });

    if (response.ok) {
      const user: User = await response.json();
      return { valid: true, user };
    } else {
      return { valid: false };
    }
  } catch (error) {
    console.error('Error verificando token:', error);
    return { valid: false };
  }
}

// Función para refrescar la autenticación
export async function refreshAuth(): Promise<{ success: boolean; user?: User }> {
  const token = getToken();
  if (!token) {
    return { success: false };
  }

  const result = await verifyToken(token);
  if (result.valid && result.user) {
    // Actualizar datos del usuario en localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('user', JSON.stringify(result.user));
    }
    return { success: true, user: result.user };
  } else {
    // Token inválido, limpiar datos
    logout();
    return { success: false };
  }
}

// Hook para usar en componentes React
export function useAuth() {
  if (typeof window === 'undefined') {
    return {
      isAuthenticated: false,
      user: null,
      token: null,
    };
  }

  return {
    isAuthenticated: isAuthenticated(),
    user: getUser(),
    token: getToken(),
  };
}

// Función para hacer peticiones autenticadas
export async function authenticatedFetch(
  endpoint: string, 
  options: RequestInit = {}
): Promise<Response> {
  const token = getToken();
  
  if (!token) {
    throw new Error('No hay token de autenticación');
  }

  const headers = {
    ...authHeaders(token),
    ...options.headers,
  };

  return fetch(apiUrl(endpoint), {
    ...options,
    headers,
    credentials: 'include',
  });
}

// Interceptor para manejar respuestas 401
export async function handleAuthenticatedRequest<T>(
  requestFn: () => Promise<Response>
): Promise<T> {
  try {
    const response = await requestFn();
    
    if (response.status === 401) {
      // Token expirado o inválido
      logout();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      throw new Error('Sesión expirada');
    }
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error en la petición');
    }
    
    return await response.json();
  } catch (error) {
    if (error instanceof Error && error.message === 'Sesión expirada') {
      throw error;
    }
    throw new Error('Error de conexión');
  }
}
