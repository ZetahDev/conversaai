// Security Middleware for Astro
import { defineMiddleware } from 'astro:middleware';
import { config } from '~/lib/config';

// Rate limiting store (in-memory for development, use Redis in production)
const rateLimitStore = new Map<string, { count: number; resetTime: number }>();

// CSRF token store (in-memory for development)
const csrfTokens = new Set<string>();

// Security headers
const securityHeaders = {
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  'Content-Security-Policy': [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
    "img-src 'self' data: https:",
    "font-src 'self' https://fonts.gstatic.com",
    "connect-src 'self' " + config.api.baseUrl,
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join('; '),
};

// Rate limiting function
function checkRateLimit(
  ip: string,
  endpoint: string
): { allowed: boolean; resetTime?: number } {
  const key = `${ip}:${endpoint}`;
  const now = Date.now();
  const windowMs = config.rateLimiting.loginWindowMs;
  const maxAttempts = config.rateLimiting.loginAttempts;

  const current = rateLimitStore.get(key);

  if (!current || now > current.resetTime) {
    // New window or expired window
    rateLimitStore.set(key, { count: 1, resetTime: now + windowMs });
    return { allowed: true };
  }

  if (current.count >= maxAttempts) {
    return { allowed: false, resetTime: current.resetTime };
  }

  // Increment count
  current.count++;
  rateLimitStore.set(key, current);

  return { allowed: true };
}

// Generate CSRF token
function generateCSRFToken(): string {
  const token = crypto.randomUUID();
  csrfTokens.add(token);

  // Clean up old tokens (keep last 100)
  if (csrfTokens.size > 100) {
    const tokensArray = Array.from(csrfTokens);
    const toRemove = tokensArray.slice(0, tokensArray.length - 100);
    toRemove.forEach(token => csrfTokens.delete(token));
  }

  return token;
}

// Validate CSRF token
function validateCSRFToken(token: string): boolean {
  const isValid = csrfTokens.has(token);
  if (isValid) {
    csrfTokens.delete(token); // One-time use
  }
  return isValid;
}

// Get client IP
function getClientIP(request: Request): string {
  // Check various headers for real IP
  const headers = request.headers;

  return (
    headers.get('cf-connecting-ip') || // Cloudflare
    headers.get('x-real-ip') || // Nginx
    headers.get('x-forwarded-for')?.split(',')[0] || // Load balancer
    headers.get('x-client-ip') ||
    '127.0.0.1' // Fallback
  );
}

// Sanitize input
function sanitizeInput(input: string): string {
  return input
    .replace(/[<>]/g, '') // Remove potential HTML tags
    .replace(/javascript:/gi, '') // Remove javascript: protocol
    .replace(/on\w+=/gi, '') // Remove event handlers
    .trim()
    .slice(0, 10000); // Limit length
}

// Validate origin
function validateOrigin(request: Request): boolean {
  const origin = request.headers.get('origin');
  const referer = request.headers.get('referer');

  if (!origin && !referer) {
    return true; // Allow requests without origin (direct navigation)
  }

  const allowedOrigins = config.security.allowedOrigins;
  if (allowedOrigins.length === 0) {
    return true; // No restrictions configured
  }

  const requestOrigin = origin || (referer ? new URL(referer).origin : '');
  return allowedOrigins.includes(requestOrigin);
}

export const onRequest = defineMiddleware(async (context, next) => {
  const { request, url } = context;
  const method = request.method;
  const pathname = url.pathname;

  // Get client IP
  const clientIP = getClientIP(request);

  // Skip middleware for static assets
  if (
    pathname.startsWith('/_astro/') ||
    pathname.startsWith('/favicon') ||
    pathname.match(/\.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf)$/)
  ) {
    return next();
  }

  // Apply security headers
  const response = await next();

  // Add security headers
  Object.entries(securityHeaders).forEach(([key, value]) => {
    response.headers.set(key, value);
  });

  // CORS handling
  if (config.security.allowedOrigins.length > 0) {
    const origin = request.headers.get('origin');
    if (origin && config.security.allowedOrigins.includes(origin)) {
      response.headers.set('Access-Control-Allow-Origin', origin);
      response.headers.set('Access-Control-Allow-Credentials', 'true');
    }
  }

  // Handle preflight requests
  if (method === 'OPTIONS') {
    response.headers.set(
      'Access-Control-Allow-Methods',
      'GET, POST, PUT, DELETE, OPTIONS'
    );
    response.headers.set(
      'Access-Control-Allow-Headers',
      'Content-Type, Authorization, X-CSRF-Token'
    );
    response.headers.set('Access-Control-Max-Age', '86400');
    return new Response(null, { status: 200, headers: response.headers });
  }

  // Rate limiting for sensitive endpoints
  if (config.security.enableRateLimiting) {
    const sensitiveEndpoints = ['/login', '/register', '/api/', '/auth/'];
    const isSensitive = sensitiveEndpoints.some(endpoint =>
      pathname.includes(endpoint)
    );

    if (isSensitive) {
      const rateLimit = checkRateLimit(clientIP, pathname);

      if (!rateLimit.allowed) {
        const retryAfter = Math.ceil(
          (rateLimit.resetTime! - Date.now()) / 1000
        );
        response.headers.set('Retry-After', retryAfter.toString());
        response.headers.set(
          'X-RateLimit-Limit',
          config.rateLimiting.loginAttempts.toString()
        );
        response.headers.set('X-RateLimit-Remaining', '0');
        response.headers.set(
          'X-RateLimit-Reset',
          rateLimit.resetTime!.toString()
        );

        return new Response(
          JSON.stringify({
            error: 'Too many requests',
            message: 'Rate limit exceeded. Please try again later.',
            retryAfter,
          }),
          {
            status: 429,
            headers: {
              'Content-Type': 'application/json',
              ...Object.fromEntries(response.headers.entries()),
            },
          }
        );
      }
    }
  }

  // CSRF protection for state-changing requests (only in production)
  if (
    config.isProd &&
    config.security.enableCSRF &&
    ['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)
  ) {
    const contentType = request.headers.get('content-type') || '';

    // Skip CSRF for API requests with proper authentication
    if (
      !pathname.startsWith('/api/') ||
      !request.headers.get('authorization')
    ) {
      const csrfToken =
        request.headers.get('x-csrf-token') ||
        url.searchParams.get('csrf_token');

      if (!csrfToken || !validateCSRFToken(csrfToken)) {
        return new Response(
          JSON.stringify({
            error: 'CSRF token missing or invalid',
            message: 'Request blocked for security reasons',
          }),
          {
            status: 403,
            headers: {
              'Content-Type': 'application/json',
              ...Object.fromEntries(response.headers.entries()),
            },
          }
        );
      }
    }
  }

  // Origin validation
  if (!validateOrigin(request)) {
    return new Response(
      JSON.stringify({
        error: 'Invalid origin',
        message: 'Request from unauthorized origin',
      }),
      {
        status: 403,
        headers: {
          'Content-Type': 'application/json',
          ...Object.fromEntries(response.headers.entries()),
        },
      }
    );
  }

  // Input sanitization for form data
  if (
    method === 'POST' &&
    request.headers
      .get('content-type')
      ?.includes('application/x-www-form-urlencoded')
  ) {
    try {
      const formData = await request.formData();
      const sanitizedData = new FormData();

      for (const [key, value] of formData.entries()) {
        if (typeof value === 'string') {
          sanitizedData.append(key, sanitizeInput(value));
        } else {
          sanitizedData.append(key, value);
        }
      }

      // Create new request with sanitized data
      const newRequest = new Request(request.url, {
        method: request.method,
        headers: request.headers,
        body: sanitizedData,
      });

      // Update context request
      Object.defineProperty(context, 'request', {
        value: newRequest,
        writable: false,
      });
    } catch (error) {
      // If parsing fails, continue with original request
      console.warn('Failed to sanitize form data:', error);
    }
  }

  // Add CSRF token to response for forms
  if (
    config.security.enableCSRF &&
    method === 'GET' &&
    (pathname.includes('/login') ||
      pathname.includes('/register') ||
      pathname.includes('/dashboard'))
  ) {
    const csrfToken = generateCSRFToken();
    response.headers.set('X-CSRF-Token', csrfToken);

    // Also set as cookie for JavaScript access
    response.headers.set(
      'Set-Cookie',
      `csrf_token=${csrfToken}; Path=/; HttpOnly=false; Secure=${config.isProd}; SameSite=Strict; Max-Age=3600`
    );
  }

  // Log security events (in development)
  if (config.isDev) {
    console.log(`[Security] ${method} ${pathname} from ${clientIP}`);
  }

  return response;
});

// Export utility functions for use in pages
export { generateCSRFToken, validateCSRFToken, getClientIP, sanitizeInput };
