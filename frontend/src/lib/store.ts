// Global State Management System
import type { User } from './auth';

export interface AppState {
  // Authentication
  auth: {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    error: string | null;
  };
  
  // UI State
  ui: {
    theme: 'light' | 'dark';
    sidebarOpen: boolean;
    mobileMenuOpen: boolean;
    loading: {
      global: boolean;
      [key: string]: boolean;
    };
  };
  
  // Notifications
  notifications: Array<{
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    title?: string;
    message: string;
    duration?: number;
    timestamp: number;
  }>;
  
  // Data
  data: {
    chatbots: any[];
    conversations: any[];
    analytics: any;
    company: any;
  };
  
  // Network
  network: {
    isOnline: boolean;
    lastSync: number | null;
    pendingRequests: number;
  };
}

type StateListener = (state: AppState) => void;
type StateUpdater = (state: AppState) => Partial<AppState>;

class Store {
  private state: AppState;
  private listeners: Set<StateListener> = new Set();
  private persistKeys: Set<keyof AppState> = new Set(['ui']);

  constructor() {
    this.state = this.getInitialState();
    this.loadPersistedState();
    this.setupNetworkListeners();
  }

  private getInitialState(): AppState {
    return {
      auth: {
        user: null,
        isAuthenticated: false,
        isLoading: true,
        error: null,
      },
      ui: {
        theme: 'light',
        sidebarOpen: false,
        mobileMenuOpen: false,
        loading: {
          global: false,
        },
      },
      notifications: [],
      data: {
        chatbots: [],
        conversations: [],
        analytics: null,
        company: null,
      },
      network: {
        isOnline: navigator.onLine,
        lastSync: null,
        pendingRequests: 0,
      },
    };
  }

  private loadPersistedState(): void {
    if (typeof window === 'undefined') return;

    try {
      this.persistKeys.forEach(key => {
        const stored = localStorage.getItem(`store_${key}`);
        if (stored) {
          const parsedData = JSON.parse(stored);
          this.state = { ...this.state, [key]: { ...this.state[key], ...parsedData } };
        }
      });
    } catch (error) {
      console.warn('Failed to load persisted state:', error);
    }
  }

  private persistState(key: keyof AppState): void {
    if (typeof window === 'undefined' || !this.persistKeys.has(key)) return;

    try {
      localStorage.setItem(`store_${key}`, JSON.stringify(this.state[key]));
    } catch (error) {
      console.warn('Failed to persist state:', error);
    }
  }

  private setupNetworkListeners(): void {
    if (typeof window === 'undefined') return;

    window.addEventListener('online', () => {
      this.updateState(state => ({
        network: { ...state.network, isOnline: true }
      }));
    });

    window.addEventListener('offline', () => {
      this.updateState(state => ({
        network: { ...state.network, isOnline: false }
      }));
    });
  }

  // Get current state
  getState(): AppState {
    return { ...this.state };
  }

  // Subscribe to state changes
  subscribe(listener: StateListener): () => void {
    this.listeners.add(listener);
    
    // Return unsubscribe function
    return () => {
      this.listeners.delete(listener);
    };
  }

  // Update state
  updateState(updater: StateUpdater | Partial<AppState>): void {
    const updates = typeof updater === 'function' ? updater(this.state) : updater;
    
    const newState = this.mergeState(this.state, updates);
    const hasChanges = JSON.stringify(newState) !== JSON.stringify(this.state);
    
    if (hasChanges) {
      this.state = newState;
      
      // Persist relevant state changes
      Object.keys(updates).forEach(key => {
        if (this.persistKeys.has(key as keyof AppState)) {
          this.persistState(key as keyof AppState);
        }
      });
      
      // Notify listeners
      this.listeners.forEach(listener => {
        try {
          listener(this.getState());
        } catch (error) {
          console.error('State listener error:', error);
        }
      });
    }
  }

  private mergeState(current: AppState, updates: Partial<AppState>): AppState {
    const newState = { ...current };
    
    Object.entries(updates).forEach(([key, value]) => {
      if (value && typeof value === 'object' && !Array.isArray(value)) {
        newState[key as keyof AppState] = { 
          ...current[key as keyof AppState], 
          ...value 
        } as any;
      } else {
        newState[key as keyof AppState] = value as any;
      }
    });
    
    return newState;
  }

  // Auth actions
  setAuth(auth: Partial<AppState['auth']>): void {
    this.updateState({ auth });
  }

  setUser(user: User | null): void {
    this.updateState({
      auth: {
        user,
        isAuthenticated: !!user,
        isLoading: false,
        error: null,
      }
    });
  }

  setAuthError(error: string | null): void {
    this.updateState({
      auth: { error, isLoading: false }
    });
  }

  // UI actions
  setTheme(theme: 'light' | 'dark'): void {
    this.updateState({ ui: { theme } });
    
    // Apply theme to document
    if (typeof document !== 'undefined') {
      document.documentElement.classList.toggle('dark', theme === 'dark');
    }
  }

  toggleSidebar(): void {
    this.updateState(state => ({
      ui: { sidebarOpen: !state.ui.sidebarOpen }
    }));
  }

  toggleMobileMenu(): void {
    this.updateState(state => ({
      ui: { mobileMenuOpen: !state.ui.mobileMenuOpen }
    }));
  }

  setLoading(key: string, loading: boolean): void {
    this.updateState(state => ({
      ui: {
        loading: {
          ...state.ui.loading,
          [key]: loading,
        }
      }
    }));
  }

  setGlobalLoading(loading: boolean): void {
    this.updateState({
      ui: { loading: { global: loading } }
    });
  }

  // Notification actions
  addNotification(notification: Omit<AppState['notifications'][0], 'id' | 'timestamp'>): string {
    const id = `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const newNotification = {
      ...notification,
      id,
      timestamp: Date.now(),
    };

    this.updateState(state => ({
      notifications: [...state.notifications, newNotification]
    }));

    // Auto-remove notification after duration
    if (notification.duration !== 0) {
      const duration = notification.duration || 5000;
      setTimeout(() => {
        this.removeNotification(id);
      }, duration);
    }

    return id;
  }

  removeNotification(id: string): void {
    this.updateState(state => ({
      notifications: state.notifications.filter(n => n.id !== id)
    }));
  }

  clearNotifications(): void {
    this.updateState({ notifications: [] });
  }

  // Data actions
  setChatbots(chatbots: any[]): void {
    this.updateState({ data: { chatbots } });
  }

  setConversations(conversations: any[]): void {
    this.updateState({ data: { conversations } });
  }

  setAnalytics(analytics: any): void {
    this.updateState({ data: { analytics } });
  }

  setCompany(company: any): void {
    this.updateState({ data: { company } });
  }

  // Network actions
  incrementPendingRequests(): void {
    this.updateState(state => ({
      network: {
        pendingRequests: state.network.pendingRequests + 1
      }
    }));
  }

  decrementPendingRequests(): void {
    this.updateState(state => ({
      network: {
        pendingRequests: Math.max(0, state.network.pendingRequests - 1)
      }
    }));
  }

  setLastSync(timestamp: number): void {
    this.updateState({
      network: { lastSync: timestamp }
    });
  }

  // Utility methods
  isLoading(key?: string): boolean {
    if (key) {
      return this.state.ui.loading[key] || false;
    }
    return this.state.ui.loading.global;
  }

  hasNotifications(): boolean {
    return this.state.notifications.length > 0;
  }

  isOnline(): boolean {
    return this.state.network.isOnline;
  }

  hasPendingRequests(): boolean {
    return this.state.network.pendingRequests > 0;
  }
}

// Export singleton instance
export const store = new Store();

// Export convenience functions
export const getState = () => store.getState();
export const updateState = (updater: StateUpdater | Partial<AppState>) => store.updateState(updater);
export const subscribe = (listener: StateListener) => store.subscribe(listener);

// Export specific action creators
export const authActions = {
  setUser: (user: User | null) => store.setUser(user),
  setAuth: (auth: Partial<AppState['auth']>) => store.setAuth(auth),
  setError: (error: string | null) => store.setAuthError(error),
};

export const uiActions = {
  setTheme: (theme: 'light' | 'dark') => store.setTheme(theme),
  toggleSidebar: () => store.toggleSidebar(),
  toggleMobileMenu: () => store.toggleMobileMenu(),
  setLoading: (key: string, loading: boolean) => store.setLoading(key, loading),
  setGlobalLoading: (loading: boolean) => store.setGlobalLoading(loading),
};

export const notificationActions = {
  add: (notification: Omit<AppState['notifications'][0], 'id' | 'timestamp'>) => 
    store.addNotification(notification),
  remove: (id: string) => store.removeNotification(id),
  clear: () => store.clearNotifications(),
  success: (message: string, title?: string) => 
    store.addNotification({ type: 'success', message, title }),
  error: (message: string, title?: string) => 
    store.addNotification({ type: 'error', message, title }),
  warning: (message: string, title?: string) => 
    store.addNotification({ type: 'warning', message, title }),
  info: (message: string, title?: string) => 
    store.addNotification({ type: 'info', message, title }),
};

export const dataActions = {
  setChatbots: (chatbots: any[]) => store.setChatbots(chatbots),
  setConversations: (conversations: any[]) => store.setConversations(conversations),
  setAnalytics: (analytics: any) => store.setAnalytics(analytics),
  setCompany: (company: any) => store.setCompany(company),
};

export default store;
