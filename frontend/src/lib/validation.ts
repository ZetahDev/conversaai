// Input Validation and Sanitization System
import { config } from './config';

export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: any) => boolean | string;
  sanitize?: (value: string) => string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  sanitizedValue?: any;
}

export interface FormValidationResult {
  isValid: boolean;
  errors: Record<string, string[]>;
  sanitizedData: Record<string, any>;
}

class Validator {
  // Sanitization functions
  static sanitizeString(input: string): string {
    if (typeof input !== 'string') return '';
    
    return input
      .trim()
      .replace(/[<>]/g, '') // Remove potential HTML tags
      .replace(/javascript:/gi, '') // Remove javascript: protocol
      .replace(/on\w+=/gi, '') // Remove event handlers
      .slice(0, 10000); // Limit length
  }

  static sanitizeEmail(email: string): string {
    if (typeof email !== 'string') return '';
    
    return email
      .toLowerCase()
      .trim()
      .replace(/[^\w@.-]/g, '') // Only allow word chars, @, ., -
      .slice(0, 254); // RFC 5321 limit
  }

  static sanitizeHTML(input: string): string {
    if (typeof input !== 'string') return '';
    
    // Basic HTML sanitization - in production use DOMPurify
    return input
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;')
      .replace(/\//g, '&#x2F;');
  }

  static sanitizeNumber(input: any): number | null {
    const num = parseFloat(input);
    return isNaN(num) ? null : num;
  }

  // Validation functions
  static validateField(value: any, rules: ValidationRule): ValidationResult {
    const errors: string[] = [];
    let sanitizedValue = value;

    // Sanitize first if sanitization function provided
    if (rules.sanitize && typeof value === 'string') {
      sanitizedValue = rules.sanitize(value);
    }

    // Required validation
    if (rules.required && (!sanitizedValue || sanitizedValue.toString().trim() === '')) {
      errors.push('Este campo es requerido');
      return { isValid: false, errors, sanitizedValue };
    }

    // Skip other validations if field is empty and not required
    if (!sanitizedValue && !rules.required) {
      return { isValid: true, errors: [], sanitizedValue };
    }

    // Length validations
    if (rules.minLength && sanitizedValue.toString().length < rules.minLength) {
      errors.push(`Debe tener al menos ${rules.minLength} caracteres`);
    }

    if (rules.maxLength && sanitizedValue.toString().length > rules.maxLength) {
      errors.push(`No puede tener más de ${rules.maxLength} caracteres`);
    }

    // Pattern validation
    if (rules.pattern && !rules.pattern.test(sanitizedValue.toString())) {
      errors.push('El formato no es válido');
    }

    // Custom validation
    if (rules.custom) {
      const customResult = rules.custom(sanitizedValue);
      if (typeof customResult === 'string') {
        errors.push(customResult);
      } else if (!customResult) {
        errors.push('El valor no es válido');
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
      sanitizedValue
    };
  }

  static validateForm(data: Record<string, any>, schema: Record<string, ValidationRule>): FormValidationResult {
    const errors: Record<string, string[]> = {};
    const sanitizedData: Record<string, any> = {};
    let isValid = true;

    // Validate each field
    for (const [fieldName, rules] of Object.entries(schema)) {
      const fieldValue = data[fieldName];
      const result = this.validateField(fieldValue, rules);
      
      if (!result.isValid) {
        errors[fieldName] = result.errors;
        isValid = false;
      }
      
      sanitizedData[fieldName] = result.sanitizedValue;
    }

    return { isValid, errors, sanitizedData };
  }
}

// Pre-defined validation schemas
export const validationSchemas = {
  // User authentication
  login: {
    email: {
      required: true,
      pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
      maxLength: 254,
      sanitize: Validator.sanitizeEmail,
    },
    password: {
      required: true,
      minLength: 1, // For login, just check it exists
      maxLength: 128,
      sanitize: Validator.sanitizeString,
    },
  },

  register: {
    email: {
      required: true,
      pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
      maxLength: 254,
      sanitize: Validator.sanitizeEmail,
    },
    password: {
      required: true,
      minLength: config.validation.password.minLength,
      maxLength: 128,
      pattern: config.validation.password.requireUppercase 
        ? /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/
        : undefined,
      sanitize: Validator.sanitizeString,
      custom: (value: string) => {
        const result = validatePassword(value);
        return result.isValid ? true : result.errors.join(', ');
      },
    },
    full_name: {
      required: true,
      minLength: 2,
      maxLength: 100,
      pattern: /^[a-zA-ZÀ-ÿ\s]+$/,
      sanitize: Validator.sanitizeString,
    },
  },

  // Chatbot creation
  chatbot: {
    name: {
      required: true,
      minLength: 3,
      maxLength: 100,
      sanitize: Validator.sanitizeString,
    },
    description: {
      required: false,
      maxLength: 500,
      sanitize: Validator.sanitizeString,
    },
    model: {
      required: true,
      pattern: /^(gpt-3\.5-turbo|gpt-4|claude-3-sonnet|claude-3-haiku)$/,
      sanitize: Validator.sanitizeString,
    },
    system_prompt: {
      required: true,
      minLength: 10,
      maxLength: 4000,
      sanitize: Validator.sanitizeString,
    },
    temperature: {
      required: true,
      custom: (value: any) => {
        const num = Validator.sanitizeNumber(value);
        return num !== null && num >= 0 && num <= 1;
      },
    },
    max_tokens: {
      required: true,
      custom: (value: any) => {
        const num = Validator.sanitizeNumber(value);
        return num !== null && num >= 50 && num <= 4000;
      },
    },
  },

  // Company information
  company: {
    name: {
      required: true,
      minLength: 2,
      maxLength: 100,
      sanitize: Validator.sanitizeString,
    },
    industry: {
      required: false,
      maxLength: 50,
      sanitize: Validator.sanitizeString,
    },
  },

  // Contact form
  contact: {
    name: {
      required: true,
      minLength: 2,
      maxLength: 100,
      sanitize: Validator.sanitizeString,
    },
    email: {
      required: true,
      pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
      maxLength: 254,
      sanitize: Validator.sanitizeEmail,
    },
    subject: {
      required: true,
      minLength: 5,
      maxLength: 200,
      sanitize: Validator.sanitizeString,
    },
    message: {
      required: true,
      minLength: 10,
      maxLength: 2000,
      sanitize: Validator.sanitizeHTML,
    },
  },
};

// Password validation function
export function validatePassword(password: string): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];
  const { validation } = config;

  if (password.length < validation.password.minLength) {
    errors.push(`La contraseña debe tener al menos ${validation.password.minLength} caracteres`);
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

  if (validation.password.requireSpecialChars && !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('La contraseña debe contener al menos un carácter especial');
  }

  // Check for common weak patterns
  const weakPatterns = [
    /^123456/,
    /^password/i,
    /^qwerty/i,
    /^admin/i,
    /(.)\1{3,}/, // Repeated characters
  ];

  for (const pattern of weakPatterns) {
    if (pattern.test(password)) {
      errors.push('La contraseña es demasiado común o débil');
      break;
    }
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}

// Email validation
export function validateEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// Rate limiting helper (client-side)
export class RateLimiter {
  private attempts: Map<string, number[]> = new Map();

  isAllowed(key: string, maxAttempts: number = 5, windowMs: number = 60000): boolean {
    const now = Date.now();
    const attempts = this.attempts.get(key) || [];
    
    // Remove old attempts outside the window
    const validAttempts = attempts.filter(time => now - time < windowMs);
    
    if (validAttempts.length >= maxAttempts) {
      return false;
    }
    
    // Add current attempt
    validAttempts.push(now);
    this.attempts.set(key, validAttempts);
    
    return true;
  }

  getRemainingTime(key: string, windowMs: number = 60000): number {
    const attempts = this.attempts.get(key) || [];
    if (attempts.length === 0) return 0;
    
    const oldestAttempt = Math.min(...attempts);
    const remaining = windowMs - (Date.now() - oldestAttempt);
    
    return Math.max(0, remaining);
  }
}

// Export main validator
export { Validator };

// Export singleton rate limiter
export const rateLimiter = new RateLimiter();

// Convenience functions
export const validateForm = (data: Record<string, any>, schema: Record<string, ValidationRule>) => 
  Validator.validateForm(data, schema);

export const validateField = (value: any, rules: ValidationRule) => 
  Validator.validateField(value, rules);

export const sanitizeString = Validator.sanitizeString;
export const sanitizeEmail = Validator.sanitizeEmail;
export const sanitizeHTML = Validator.sanitizeHTML;
