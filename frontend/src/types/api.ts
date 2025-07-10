// Tipos para la API del ChatBot SAAS

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: 'SUPERADMIN' | 'ADMIN' | 'USER';
  status: 'ACTIVE' | 'INACTIVE' | 'SUSPENDED';
  company_id: string;
  created_at: string;
  updated_at: string;
}

export interface Company {
  id: string;
  name: string;
  slug: string;
  email: string;
  status: 'ACTIVE' | 'INACTIVE' | 'SUSPENDED';
  company_type: 'FOOD' | 'BARBERSHOP' | 'ECOMMERCE' | 'RETAIL' | 'SERVICES' | 'HEALTH' | 'EDUCATION' | 'OTHER';
  created_at: string;
  updated_at: string;
}

export interface ChatbotConfig {
  ai_provider?: 'OPENAI' | 'ANTHROPIC' | 'GEMINI';
  model?: string;
  temperature?: number;
  max_tokens?: number;
  system_prompt?: string;
  [key: string]: any;
}

export interface Chatbot {
  id: string;
  name: string;
  description: string;
  status: 'ACTIVE' | 'INACTIVE' | 'TRAINING';
  personality: 'PROFESSIONAL' | 'FRIENDLY' | 'CASUAL' | 'TECHNICAL';
  config: ChatbotConfig;
  company_id: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface Conversation {
  id: string;
  session_id: string;
  status: 'ACTIVE' | 'CLOSED' | 'TRANSFERRED';
  user_name?: string;
  user_email?: string;
  user_phone?: string;
  channel: 'WEB' | 'WHATSAPP' | 'TELEGRAM' | 'SLACK' | 'DISCORD';
  chatbot_id: string;
  company_id: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  content: string;
  message_type: 'TEXT' | 'IMAGE' | 'AUDIO' | 'VIDEO' | 'DOCUMENT' | 'LOCATION';
  sender: 'USER' | 'BOT' | 'AGENT';
  metadata?: Record<string, any>;
  conversation_id: string;
  company_id: string;
  created_at: string;
  updated_at: string;
}

export interface DashboardStats {
  total_chatbots: number;
  active_chatbots: number;
  conversations_today: number;
  conversations_this_month: number;
  messages_today: number;
  messages_this_month: number;
  unique_users: number;
  satisfaction_rate?: number;
  response_time_avg?: number;
}

// Tipos para el nuevo dashboard de métricas
export interface DashboardOverview {
  total_chatbots: number;
  status_distribution: Record<string, number>;
  model_distribution: Record<string, number>;
  recent_activity: Array<{
    date: string;
    count: number;
  }>;
  active_chatbots: number;
  draft_chatbots: number;
}

export interface UsageTrends {
  creation_trend: Array<{
    date: string;
    created: number;
  }>;
  update_trend: Array<{
    date: string;
    updated: number;
  }>;
  period_days: number;
}

export interface PerformanceMetrics {
  model_configurations: Array<{
    model: string;
    avg_temperature: number;
    avg_max_tokens: number;
    count: number;
  }>;
  newest_chatbots: Array<{
    name: string;
    created_at: string;
    age_days: number;
  }>;
}

export interface UserActivity {
  user_activity: Array<{
    user_id: string;
    chatbot_count: number;
    last_activity: string;
  }>;
  total_active_users: number;
}

export interface RealTimeMetrics {
  current_active_users: number;
  requests_last_hour: number;
  requests_per_minute: number;
  average_response_time: number;
  total_operations: Record<string, number>;
  error_counts: Record<string, number>;
  top_models: Array<[string, number]>;
  recent_status_changes: Array<{
    timestamp: string;
    chatbot_id: string;
    old_status: string;
    new_status: string;
    user_id: string;
  }>;
}

export interface CompleteDashboard {
  overview: DashboardOverview;
  usage_trends: UsageTrends;
  performance_metrics: PerformanceMetrics;
  user_activity: UserActivity;
  real_time_metrics: RealTimeMetrics;
}

export interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  chatbot_id: string;
  company_id: string;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string;
  title: string;
  content: string;
  document_type: 'FAQ' | 'MANUAL' | 'POLICY' | 'GUIDE' | 'OTHER';
  file_url?: string;
  knowledge_base_id: string;
  company_id: string;
  created_at: string;
  updated_at: string;
}

export interface Integration {
  id: string;
  name: string;
  type: 'WHATSAPP' | 'TELEGRAM' | 'SLACK' | 'DISCORD' | 'WEBHOOK';
  status: 'ACTIVE' | 'INACTIVE' | 'ERROR';
  config: Record<string, any>;
  chatbot_id: string;
  company_id: string;
  created_at: string;
  updated_at: string;
}

export interface Subscription {
  id: string;
  plan_name: string;
  status: 'ACTIVE' | 'CANCELLED' | 'PAST_DUE' | 'TRIALING';
  current_period_start: string;
  current_period_end: string;
  trial_end?: string;
  company_id: string;
  created_at: string;
  updated_at: string;
}

// Tipos para respuestas de la API
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: string[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name: string;
  company_name: string;
  company_email: string;
  company_type: Company['company_type'];
}

export interface RegisterResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  company: Company;
}

// Tipos para formularios
export interface CreateChatbotRequest {
  name: string;
  description: string;
  personality: Chatbot['personality'];
  config?: ChatbotConfig;
}

export interface UpdateChatbotRequest {
  name?: string;
  description?: string;
  status?: Chatbot['status'];
  personality?: Chatbot['personality'];
  config?: ChatbotConfig;
}

export interface CreateConversationRequest {
  chatbot_id: string;
  user_name?: string;
  user_email?: string;
  user_phone?: string;
  channel: Conversation['channel'];
}

export interface SendMessageRequest {
  content: string;
  message_type?: Message['message_type'];
  metadata?: Record<string, any>;
}

// Tipos para errores
export interface ApiError {
  detail: string;
  code?: string;
  field?: string;
}

export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

// Tipos para configuración
export interface AppConfig {
  apiUrl: string;
  publicApiUrl: string;
  environment: 'development' | 'production' | 'staging';
}

// Tipos para el estado de la aplicación
export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  company: Company | null;
  token: string | null;
}

export interface AppState {
  auth: AuthState;
  chatbots: Chatbot[];
  conversations: Conversation[];
  loading: boolean;
  error: string | null;
}
