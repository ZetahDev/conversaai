// Structured Logging and Monitoring System
import { config } from './config';

export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal';

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: Record<string, any>;
  error?: Error;
  userId?: string;
  sessionId?: string;
  requestId?: string;
  userAgent?: string;
  ip?: string;
  url?: string;
  method?: string;
  duration?: number;
  stack?: string;
}

export interface PerformanceMetric {
  name: string;
  value: number;
  unit: 'ms' | 'bytes' | 'count';
  timestamp: number;
  context?: Record<string, any>;
}

class Logger {
  private sessionId: string;
  private userId?: string;
  private buffer: LogEntry[] = [];
  private metricsBuffer: PerformanceMetric[] = [];
  private flushInterval: NodeJS.Timeout | null = null;

  constructor() {
    this.sessionId = this.generateSessionId();
    this.setupAutoFlush();
    this.setupErrorHandlers();
    this.setupPerformanceMonitoring();
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private setupAutoFlush(): void {
    if (typeof window === 'undefined') return;

    // Flush logs every 30 seconds
    this.flushInterval = setInterval(() => {
      this.flush();
    }, 30000);

    // Flush on page unload
    window.addEventListener('beforeunload', () => {
      this.flush();
    });

    // Flush on visibility change (tab switch)
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        this.flush();
      }
    });
  }

  private setupErrorHandlers(): void {
    if (typeof window === 'undefined') return;

    // Global error handler
    window.addEventListener('error', (event) => {
      this.error('Global error caught', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
      });
    });

    // Unhandled promise rejection handler
    window.addEventListener('unhandledrejection', (event) => {
      this.error('Unhandled promise rejection', {
        reason: event.reason,
        stack: event.reason?.stack,
      });
    });
  }

  private setupPerformanceMonitoring(): void {
    if (typeof window === 'undefined' || !window.performance) return;

    // Monitor page load performance
    window.addEventListener('load', () => {
      setTimeout(() => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        if (navigation) {
          this.metric('page_load_time', navigation.loadEventEnd - navigation.fetchStart, 'ms');
          this.metric('dom_content_loaded', navigation.domContentLoadedEventEnd - navigation.fetchStart, 'ms');
          this.metric('first_byte', navigation.responseStart - navigation.fetchStart, 'ms');
        }

        // Core Web Vitals
        this.measureCoreWebVitals();
      }, 0);
    });
  }

  private measureCoreWebVitals(): void {
    if (typeof window === 'undefined') return;

    // Largest Contentful Paint (LCP)
    if ('PerformanceObserver' in window) {
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          this.metric('lcp', lastEntry.startTime, 'ms');
        });
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });

        // First Input Delay (FID)
        const fidObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: any) => {
            this.metric('fid', entry.processingStart - entry.startTime, 'ms');
          });
        });
        fidObserver.observe({ entryTypes: ['first-input'] });

        // Cumulative Layout Shift (CLS)
        let clsValue = 0;
        const clsObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: any) => {
            if (!entry.hadRecentInput) {
              clsValue += entry.value;
            }
          });
          this.metric('cls', clsValue, 'count');
        });
        clsObserver.observe({ entryTypes: ['layout-shift'] });
      } catch (error) {
        this.warn('Failed to setup performance observers', { error: error.message });
      }
    }
  }

  private createLogEntry(level: LogLevel, message: string, context?: Record<string, any>, error?: Error): LogEntry {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      sessionId: this.sessionId,
      userId: this.userId,
    };

    if (context) {
      entry.context = context;
    }

    if (error) {
      entry.error = error;
      entry.stack = error.stack;
    }

    // Add browser context if available
    if (typeof window !== 'undefined') {
      entry.userAgent = navigator.userAgent;
      entry.url = window.location.href;
    }

    return entry;
  }

  private shouldLog(level: LogLevel): boolean {
    const levels: Record<LogLevel, number> = {
      debug: 0,
      info: 1,
      warn: 2,
      error: 3,
      fatal: 4,
    };

    const minLevel = config.isDev ? 'debug' : 'info';
    return levels[level] >= levels[minLevel];
  }

  private outputToConsole(entry: LogEntry): void {
    if (!this.shouldLog(entry.level)) return;

    const style = this.getConsoleStyle(entry.level);
    const prefix = `[${entry.level.toUpperCase()}] ${entry.timestamp}`;
    
    if (entry.error) {
      console.error(`${prefix} ${entry.message}`, entry.context || '', entry.error);
    } else {
      const logFn = entry.level === 'error' ? console.error :
                   entry.level === 'warn' ? console.warn :
                   entry.level === 'debug' ? console.debug :
                   console.log;
      
      logFn(`%c${prefix}%c ${entry.message}`, style, '', entry.context || '');
    }
  }

  private getConsoleStyle(level: LogLevel): string {
    const styles = {
      debug: 'color: #6b7280; font-weight: normal;',
      info: 'color: #3b82f6; font-weight: normal;',
      warn: 'color: #f59e0b; font-weight: bold;',
      error: 'color: #ef4444; font-weight: bold;',
      fatal: 'color: #dc2626; font-weight: bold; background: #fee2e2;',
    };
    return styles[level];
  }

  // Public logging methods
  debug(message: string, context?: Record<string, any>): void {
    const entry = this.createLogEntry('debug', message, context);
    this.buffer.push(entry);
    this.outputToConsole(entry);
  }

  info(message: string, context?: Record<string, any>): void {
    const entry = this.createLogEntry('info', message, context);
    this.buffer.push(entry);
    this.outputToConsole(entry);
  }

  warn(message: string, context?: Record<string, any>): void {
    const entry = this.createLogEntry('warn', message, context);
    this.buffer.push(entry);
    this.outputToConsole(entry);
  }

  error(message: string, context?: Record<string, any>, error?: Error): void {
    const entry = this.createLogEntry('error', message, context, error);
    this.buffer.push(entry);
    this.outputToConsole(entry);
  }

  fatal(message: string, context?: Record<string, any>, error?: Error): void {
    const entry = this.createLogEntry('fatal', message, context, error);
    this.buffer.push(entry);
    this.outputToConsole(entry);
    this.flush(); // Immediately flush fatal errors
  }

  // Performance metrics
  metric(name: string, value: number, unit: 'ms' | 'bytes' | 'count' = 'ms', context?: Record<string, any>): void {
    const metric: PerformanceMetric = {
      name,
      value,
      unit,
      timestamp: Date.now(),
      context,
    };

    this.metricsBuffer.push(metric);
    
    if (config.isDev) {
      console.log(`[METRIC] ${name}: ${value}${unit}`, context || '');
    }
  }

  // Timing utilities
  time(label: string): () => void {
    const start = performance.now();
    return () => {
      const duration = performance.now() - start;
      this.metric(`timer_${label}`, duration, 'ms');
    };
  }

  // User context
  setUserId(userId: string): void {
    this.userId = userId;
  }

  clearUserId(): void {
    this.userId = undefined;
  }

  // API request logging
  logApiRequest(method: string, url: string, status: number, duration: number, context?: Record<string, any>): void {
    const level = status >= 400 ? 'error' : status >= 300 ? 'warn' : 'info';
    
    this[level](`API ${method} ${url}`, {
      method,
      url,
      status,
      duration,
      ...context,
    });

    this.metric('api_request_duration', duration, 'ms', {
      method,
      url,
      status,
    });
  }

  // Flush logs to server
  async flush(): Promise<void> {
    if (this.buffer.length === 0 && this.metricsBuffer.length === 0) return;

    const payload = {
      logs: [...this.buffer],
      metrics: [...this.metricsBuffer],
      sessionId: this.sessionId,
      userId: this.userId,
      timestamp: new Date().toISOString(),
    };

    // Clear buffers
    this.buffer = [];
    this.metricsBuffer = [];

    // Send to logging endpoint (if configured)
    if (config.services.logging?.endpoint) {
      try {
        await fetch(config.services.logging.endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        });
      } catch (error) {
        console.error('Failed to send logs to server:', error);
      }
    }

    // Store in localStorage as backup (limited)
    if (typeof window !== 'undefined') {
      try {
        const stored = JSON.parse(localStorage.getItem('app_logs') || '[]');
        stored.push(payload);
        
        // Keep only last 10 log batches
        const limited = stored.slice(-10);
        localStorage.setItem('app_logs', JSON.stringify(limited));
      } catch (error) {
        console.warn('Failed to store logs locally:', error);
      }
    }
  }

  // Get stored logs (for debugging)
  getStoredLogs(): any[] {
    if (typeof window === 'undefined') return [];
    
    try {
      return JSON.parse(localStorage.getItem('app_logs') || '[]');
    } catch {
      return [];
    }
  }

  // Clear stored logs
  clearStoredLogs(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('app_logs');
    }
  }

  // Cleanup
  destroy(): void {
    if (this.flushInterval) {
      clearInterval(this.flushInterval);
    }
    this.flush();
  }
}

// Export singleton instance
export const logger = new Logger();

// Export convenience functions
export const log = {
  debug: (message: string, context?: Record<string, any>) => logger.debug(message, context),
  info: (message: string, context?: Record<string, any>) => logger.info(message, context),
  warn: (message: string, context?: Record<string, any>) => logger.warn(message, context),
  error: (message: string, context?: Record<string, any>, error?: Error) => logger.error(message, context, error),
  fatal: (message: string, context?: Record<string, any>, error?: Error) => logger.fatal(message, context, error),
  metric: (name: string, value: number, unit?: 'ms' | 'bytes' | 'count', context?: Record<string, any>) => 
    logger.metric(name, value, unit, context),
  time: (label: string) => logger.time(label),
  apiRequest: (method: string, url: string, status: number, duration: number, context?: Record<string, any>) =>
    logger.logApiRequest(method, url, status, duration, context),
  setUserId: (userId: string) => logger.setUserId(userId),
  clearUserId: () => logger.clearUserId(),
};

export default logger;
