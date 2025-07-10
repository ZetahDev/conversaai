"""
Sistema de auditoría para registrar operaciones CRUD
"""
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class AuditAction(str, Enum):
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    SEARCH = "SEARCH"
    EXPORT = "EXPORT"

class AuditLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class AuditLogger:
    def __init__(self):
        # Configurar logger específico para auditoría
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Crear handler para archivo de auditoría
        if not self.logger.handlers:
            handler = logging.FileHandler("logs/audit.log", encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s - AUDIT - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
            # También log a consola en desarrollo
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def log_operation(
        self,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        company_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        level: AuditLevel = AuditLevel.INFO,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        Registrar una operación en el log de auditoría
        """
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action.value,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id,
            "user_email": user_email,
            "company_id": company_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "success": success,
            "details": details or {},
            "error_message": error_message
        }
        
        # Filtrar valores None
        audit_entry = {k: v for k, v in audit_entry.items() if v is not None}
        
        # Convertir a JSON para el log
        log_message = json.dumps(audit_entry, ensure_ascii=False)
        
        # Registrar según el nivel
        if level == AuditLevel.INFO:
            self.logger.info(log_message)
        elif level == AuditLevel.WARNING:
            self.logger.warning(log_message)
        elif level == AuditLevel.ERROR:
            self.logger.error(log_message)
        elif level == AuditLevel.CRITICAL:
            self.logger.critical(log_message)
    
    def log_chatbot_create(
        self,
        chatbot_id: str,
        chatbot_name: str,
        user_id: str,
        user_email: str,
        company_id: str,
        ip_address: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log específico para creación de chatbots"""
        self.log_operation(
            action=AuditAction.CREATE,
            resource_type="chatbot",
            resource_id=chatbot_id,
            user_id=user_id,
            user_email=user_email,
            company_id=company_id,
            details={"chatbot_name": chatbot_name},
            ip_address=ip_address,
            success=success,
            error_message=error_message
        )
    
    def log_chatbot_update(
        self,
        chatbot_id: str,
        updated_fields: Dict[str, Any],
        user_id: str,
        user_email: str,
        company_id: str,
        ip_address: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log específico para actualización de chatbots"""
        self.log_operation(
            action=AuditAction.UPDATE,
            resource_type="chatbot",
            resource_id=chatbot_id,
            user_id=user_id,
            user_email=user_email,
            company_id=company_id,
            details={"updated_fields": updated_fields},
            ip_address=ip_address,
            success=success,
            error_message=error_message
        )
    
    def log_chatbot_delete(
        self,
        chatbot_id: str,
        chatbot_name: str,
        user_id: str,
        user_email: str,
        company_id: str,
        ip_address: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log específico para eliminación de chatbots"""
        self.log_operation(
            action=AuditAction.DELETE,
            resource_type="chatbot",
            resource_id=chatbot_id,
            user_id=user_id,
            user_email=user_email,
            company_id=company_id,
            details={"chatbot_name": chatbot_name},
            ip_address=ip_address,
            success=success,
            error_message=error_message
        )
    
    def log_chatbot_read(
        self,
        chatbot_id: str,
        user_id: str,
        user_email: str,
        company_id: str,
        operation_type: str = "view",  # view, list, search
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log específico para lectura de chatbots"""
        self.log_operation(
            action=AuditAction.READ,
            resource_type="chatbot",
            resource_id=chatbot_id,
            user_id=user_id,
            user_email=user_email,
            company_id=company_id,
            details={"operation_type": operation_type, **(details or {})},
            ip_address=ip_address,
            success=True
        )
    
    def log_authentication(
        self,
        user_id: str,
        user_email: str,
        action: AuditAction,  # LOGIN or LOGOUT
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log específico para autenticación"""
        self.log_operation(
            action=action,
            resource_type="authentication",
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )

# Instancia global del logger de auditoría
audit_logger = AuditLogger()
