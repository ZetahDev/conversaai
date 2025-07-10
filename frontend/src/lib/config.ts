// Configuración de la aplicación

export const config = {
  // URLs de la API
  api: {
    baseUrl: import.meta.env.PUBLIC_API_URL || 'http://localhost:8000',
    endpoints: {
      // Autenticación
      login: '/api/v1/auth/login',
      register: '/api/v1/auth/register',
      me: '/api/v1/auth/me',
      logout: '/api/v1/auth/logout',

      // Empresas
      companies: '/api/v1/companies',
      myCompany: '/api/v1/companies/me',

      // Usuarios
      users: '/api/v1/users',

      // Chatbots
      chatbots: '/api/v1/chatbots',

      // Conversaciones
      conversations: '/api/v1/conversations',

      // Mensajes
      messages: '/api/v1/conversations/{id}/messages',

      // Base de conocimiento
      knowledge: '/api/v1/knowledge',
      documents: '/api/v1/knowledge/documents',

      // Integraciones
      integrations: '/api/v1/integrations',

      // Suscripciones
      subscriptions: '/api/v1/subscriptions',

      // Analytics
      analytics: '/api/v1/analytics',
      dashboard: '/api/v1/analytics/dashboard',
    },
  },

  // Configuración de la aplicación
  app: {
    name: 'ConversaAI',
    version: '1.0.0',
    environment: import.meta.env.MODE || 'development',
    siteUrl: import.meta.env.PUBLIC_SITE_URL || 'http://localhost:4321',
  },

  // Environment helpers
  isProd: import.meta.env.PROD,
  isDev: import.meta.env.DEV,

  // Configuración de autenticación
  auth: {
    tokenKey: 'access_token',
    cookieOptions: {
      httpOnly: true,
      secure: import.meta.env.PROD,
      sameSite: 'strict' as const,
      maxAge: 60 * 60 * 24 * 7, // 7 días
      path: '/',
    },
  },

  // Configuración de paginación
  pagination: {
    defaultPageSize: 20,
    maxPageSize: 100,
  },

  // Configuración de validación
  validation: {
    password: {
      minLength: 8,
      requireUppercase: true,
      requireLowercase: true,
      requireNumbers: true,
      requireSpecialChars: false,
    },
    username: {
      minLength: 3,
      maxLength: 30,
      pattern: /^[a-zA-Z0-9_-]+$/,
    },
    email: {
      pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    },
  },

  // Configuración de UI
  ui: {
    theme: {
      default: 'light',
      storageKey: 'theme',
    },
    notifications: {
      duration: 5000,
      position: 'top-right' as const,
    },
    loading: {
      debounceMs: 300,
    },
  },

  // Configuración de features
  features: {
    darkMode: true,
    notifications: true,
    analytics: true,
    multiLanguage: false,
  },

  // Security settings
  security: {
    enableCSRF: import.meta.env.PUBLIC_ENABLE_CSRF !== 'false',
    enableRateLimiting: import.meta.env.PUBLIC_ENABLE_RATE_LIMITING !== 'false',
    sessionTimeout: parseInt(import.meta.env.PUBLIC_SESSION_TIMEOUT || '3600'), // 1 hour
    maxFileSize: parseInt(import.meta.env.PUBLIC_MAX_FILE_SIZE || '10485760'), // 10MB
    allowedOrigins: (
      import.meta.env.PUBLIC_ALLOWED_ORIGINS ||
      'http://localhost:4321,http://localhost:3000,http://127.0.0.1:4321,http://127.0.0.1:3000,http://192.168.1.7:4321,http://192.168.56.1:4321'
    )
      .split(',')
      .filter(Boolean),
  },

  // Rate limiting configuration
  rateLimiting: {
    loginAttempts: parseInt(import.meta.env.PUBLIC_LOGIN_MAX_ATTEMPTS || '5'),
    loginWindowMs: parseInt(import.meta.env.PUBLIC_LOGIN_WINDOW_MS || '300000'), // 5 minutes
    apiRequestsPerMinute: parseInt(
      import.meta.env.PUBLIC_API_REQUESTS_PER_MINUTE || '60'
    ),
  },
} as const;

// Helper para construir URLs de API
export const apiUrl = (endpoint: string, params?: Record<string, string>) => {
  let url = `${config.api.baseUrl}${endpoint}`;

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url = url.replace(`{${key}}`, value);
    });
  }

  return url;
};

// Helper para headers de autenticación
export const authHeaders = (token?: string) => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return headers;
};

// Helper para validar contraseña
export const validatePassword = (
  password: string
): { isValid: boolean; errors: string[] } => {
  const errors: string[] = [];
  const { validation } = config;

  if (password.length < validation.password.minLength) {
    errors.push(
      `La contraseña debe tener al menos ${validation.password.minLength} caracteres`
    );
  }

  if (validation.password.requireUppercase && !/[A-Z]/.test(password)) {
    errors.push('La contraseña debe contener al menos una letra mayúscula');
  }

  if (validation.password.requireLowercase && !/[a-z]/.test(password)) {
    errors.push('La contraseña debe contener al menos una letra minúscula');
  }

  if (validation.password.requireNumbers && !/[0-9]/.test(password)) {
    errors.push('La contraseña debe contener al menos un número');
  }

  if (
    validation.password.requireSpecialChars &&
    !/[!@#$%^&*(),.?":{}|<>]/.test(password)
  ) {
    errors.push('La contraseña debe contener al menos un carácter especial');
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
};

// Helper para validar email
export const validateEmail = (email: string): boolean => {
  return config.validation.email.pattern.test(email);
};

// Helper para validar username
export const validateUsername = (
  username: string
): { isValid: boolean; errors: string[] } => {
  const errors: string[] = [];
  const { validation } = config;

  if (username.length < validation.username.minLength) {
    errors.push(
      `El nombre de usuario debe tener al menos ${validation.username.minLength} caracteres`
    );
  }

  if (username.length > validation.username.maxLength) {
    errors.push(
      `El nombre de usuario no puede tener más de ${validation.username.maxLength} caracteres`
    );
  }

  if (!validation.username.pattern.test(username)) {
    errors.push(
      'El nombre de usuario solo puede contener letras, números, guiones y guiones bajos'
    );
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
};

export default config;
