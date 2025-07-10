"""
Modelos de base de datos para el sistema multi-tenant
"""

from .base import Base, TimestampMixin, UUIDMixin, SoftDeleteMixin, TenantMixin, AuditMixin, BaseModel
from .company import Company, CompanyStatus, CompanyType
from .user import User, UserRole, UserStatus, Permission
from .chatbot import Chatbot, ChatbotConfig, ChatbotStatus, ChatbotPersonality, AIProvider
from .conversation import Conversation, Message, ConversationStatus, MessageType, MessageSender, ConversationChannel
from .knowledge import KnowledgeBase, Document, DocumentChunk, KnowledgeBaseStatus, DocumentType, DocumentStatus, ChunkType
from .integration import Integration, Channel, WebhookEvent, APIKey, IntegrationType, IntegrationStatus, ChannelType
from .subscription import Subscription, Plan, Invoice, UsageLog, PlanType, BillingCycle, SubscriptionStatus, PaymentStatus, UsageType
from .analytics import Analytics, ConversationMetrics, EventLog, DashboardWidget, Report, AlertRule, MetricType, TimeGranularity, EventType
from .notification import Notification, NotificationType, NotificationPriority

__all__ = [
    # Base classes
    "Base",
    "TimestampMixin",
    "UUIDMixin",
    "SoftDeleteMixin",
    "TenantMixin",
    "AuditMixin",
    "BaseModel",

    # Company models
    "Company",
    "CompanyStatus",
    "CompanyType",

    # User models
    "User",
    "UserRole",
    "UserStatus",
    "Permission",

    # Chatbot models
    "Chatbot",
    "ChatbotConfig",
    "ChatbotStatus",
    "ChatbotPersonality",
    "AIProvider",

    # Conversation models
    "Conversation",
    "Message",
    "ConversationStatus",
    "MessageType",
    "MessageSender",
    "ConversationChannel",

    # Knowledge models
    "KnowledgeBase",
    "Document",
    "DocumentChunk",
    "KnowledgeBaseStatus",
    "DocumentType",
    "DocumentStatus",
    "ChunkType",

    # Integration models
    "Integration",
    "Channel",
    "WebhookEvent",
    "APIKey",
    "IntegrationType",
    "IntegrationStatus",
    "ChannelType",

    # Subscription models
    "Subscription",
    "Plan",
    "Invoice",
    "UsageLog",
    "PlanType",
    "BillingCycle",
    "SubscriptionStatus",
    "PaymentStatus",
    "UsageType",

    # Analytics models
    "Analytics",
    "ConversationMetrics",
    "EventLog",
    "DashboardWidget",
    "Report",
    "AlertRule",
    "MetricType",
    "TimeGranularity",
    "EventType",

    # Notification models
    "Notification",
    "NotificationType",
    "NotificationPriority"
]
