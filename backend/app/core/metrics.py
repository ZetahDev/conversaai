"""
Sistema de métricas para el dashboard
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class MetricsCollector:
    def __init__(self):
        # Métricas en tiempo real (en memoria)
        self.real_time_metrics = {
            "requests_per_minute": deque(maxlen=60),  # Últimos 60 minutos
            "active_users": set(),
            "chatbot_operations": defaultdict(int),
            "error_counts": defaultdict(int),
            "response_times": deque(maxlen=1000),  # Últimos 1000 requests
            "popular_models": defaultdict(int),
            "status_changes": deque(maxlen=100)  # Últimos 100 cambios de status
        }
        
        # Lock para operaciones thread-safe
        self._lock = asyncio.Lock()
    
    async def record_request(self, user_id: str, endpoint: str, response_time: float, status_code: int):
        """Registrar una request para métricas"""
        async with self._lock:
            current_minute = datetime.now().replace(second=0, microsecond=0)
            
            # Registrar request por minuto
            self.real_time_metrics["requests_per_minute"].append({
                "timestamp": current_minute.isoformat(),
                "endpoint": endpoint,
                "user_id": user_id,
                "response_time": response_time,
                "status_code": status_code
            })
            
            # Registrar usuario activo
            self.real_time_metrics["active_users"].add(user_id)
            
            # Registrar tiempo de respuesta
            self.real_time_metrics["response_times"].append(response_time)
            
            # Registrar errores
            if status_code >= 400:
                self.real_time_metrics["error_counts"][f"{status_code}"] += 1
    
    async def record_chatbot_operation(self, operation: str, model: str, user_id: str):
        """Registrar operación de chatbot"""
        async with self._lock:
            self.real_time_metrics["chatbot_operations"][operation] += 1
            self.real_time_metrics["popular_models"][model] += 1
    
    async def record_status_change(self, chatbot_id: str, old_status: str, new_status: str, user_id: str):
        """Registrar cambio de status de chatbot"""
        async with self._lock:
            self.real_time_metrics["status_changes"].append({
                "timestamp": datetime.now().isoformat(),
                "chatbot_id": chatbot_id,
                "old_status": old_status,
                "new_status": new_status,
                "user_id": user_id
            })
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Obtener métricas en tiempo real"""
        current_time = datetime.now()
        
        # Calcular requests por minuto en la última hora
        hour_ago = current_time - timedelta(hours=1)
        recent_requests = [
            req for req in self.real_time_metrics["requests_per_minute"]
            if datetime.fromisoformat(req["timestamp"]) > hour_ago
        ]
        
        # Calcular tiempo de respuesta promedio
        response_times = list(self.real_time_metrics["response_times"])
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Top modelos
        top_models = sorted(
            self.real_time_metrics["popular_models"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "current_active_users": len(self.real_time_metrics["active_users"]),
            "requests_last_hour": len(recent_requests),
            "requests_per_minute": len([
                req for req in recent_requests
                if datetime.fromisoformat(req["timestamp"]) > current_time - timedelta(minutes=1)
            ]),
            "average_response_time": round(avg_response_time, 3),
            "total_operations": dict(self.real_time_metrics["chatbot_operations"]),
            "error_counts": dict(self.real_time_metrics["error_counts"]),
            "top_models": top_models,
            "recent_status_changes": list(self.real_time_metrics["status_changes"])[-10:]
        }

class DashboardMetrics:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_company_overview(self, company_id: str) -> Dict[str, Any]:
        """Obtener resumen general de la empresa"""
        try:
            # Total de chatbots
            total_query = "SELECT COUNT(*) FROM chatbots WHERE company_id = :company_id"
            total_result = await self.db.execute(text(total_query), {"company_id": company_id})
            total_chatbots = total_result.scalar()
            
            # Chatbots por status
            status_query = """
            SELECT status, COUNT(*) as count 
            FROM chatbots 
            WHERE company_id = :company_id 
            GROUP BY status
            """
            status_result = await self.db.execute(text(status_query), {"company_id": company_id})
            status_distribution = {row.status: row.count for row in status_result.fetchall()}
            
            # Chatbots por modelo
            model_query = """
            SELECT model, COUNT(*) as count 
            FROM chatbots 
            WHERE company_id = :company_id 
            GROUP BY model
            """
            model_result = await self.db.execute(text(model_query), {"company_id": company_id})
            model_distribution = {row.model: row.count for row in model_result.fetchall()}
            
            # Actividad reciente (últimos 7 días)
            recent_query = """
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM chatbots 
            WHERE company_id = :company_id 
            AND created_at >= datetime('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date
            """
            recent_result = await self.db.execute(text(recent_query), {"company_id": company_id})
            recent_activity = [
                {"date": row.date, "count": row.count} 
                for row in recent_result.fetchall()
            ]
            
            return {
                "total_chatbots": total_chatbots,
                "status_distribution": status_distribution,
                "model_distribution": model_distribution,
                "recent_activity": recent_activity,
                "active_chatbots": status_distribution.get("ACTIVE", 0),
                "draft_chatbots": status_distribution.get("DRAFT", 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting company overview: {e}")
            raise
    
    async def get_usage_trends(self, company_id: str, days: int = 30) -> Dict[str, Any]:
        """Obtener tendencias de uso"""
        try:
            # Chatbots creados por día
            creation_query = """
            SELECT DATE(created_at) as date, COUNT(*) as created
            FROM chatbots 
            WHERE company_id = :company_id 
            AND created_at >= datetime('now', '-{} days')
            GROUP BY DATE(created_at)
            ORDER BY date
            """.format(days)
            
            creation_result = await self.db.execute(text(creation_query), {"company_id": company_id})
            creation_trend = [
                {"date": row.date, "created": row.created}
                for row in creation_result.fetchall()
            ]
            
            # Chatbots actualizados por día
            update_query = """
            SELECT DATE(updated_at) as date, COUNT(*) as updated
            FROM chatbots 
            WHERE company_id = :company_id 
            AND updated_at >= datetime('now', '-{} days')
            AND updated_at != created_at
            GROUP BY DATE(updated_at)
            ORDER BY date
            """.format(days)
            
            update_result = await self.db.execute(text(update_query), {"company_id": company_id})
            update_trend = [
                {"date": row.date, "updated": row.updated}
                for row in update_result.fetchall()
            ]
            
            return {
                "creation_trend": creation_trend,
                "update_trend": update_trend,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting usage trends: {e}")
            raise
    
    async def get_performance_metrics(self, company_id: str) -> Dict[str, Any]:
        """Obtener métricas de rendimiento"""
        try:
            # Distribución de configuraciones
            config_query = """
            SELECT 
                model,
                AVG(temperature) as avg_temperature,
                AVG(max_tokens) as avg_max_tokens,
                COUNT(*) as count
            FROM chatbots 
            WHERE company_id = :company_id 
            GROUP BY model
            """
            
            config_result = await self.db.execute(text(config_query), {"company_id": company_id})
            model_configs = [
                {
                    "model": row.model,
                    "avg_temperature": round(row.avg_temperature, 2),
                    "avg_max_tokens": round(row.avg_max_tokens, 0),
                    "count": row.count
                }
                for row in config_result.fetchall()
            ]
            
            # Chatbots más antiguos y más nuevos
            age_query = """
            SELECT 
                name,
                created_at,
                julianday('now') - julianday(created_at) as age_days
            FROM chatbots 
            WHERE company_id = :company_id 
            ORDER BY created_at DESC
            LIMIT 5
            """
            
            age_result = await self.db.execute(text(age_query), {"company_id": company_id})
            newest_chatbots = [
                {
                    "name": row.name,
                    "created_at": row.created_at,
                    "age_days": round(row.age_days, 1)
                }
                for row in age_result.fetchall()
            ]
            
            return {
                "model_configurations": model_configs,
                "newest_chatbots": newest_chatbots
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            raise
    
    async def get_user_activity(self, company_id: str) -> Dict[str, Any]:
        """Obtener actividad de usuarios"""
        try:
            # Chatbots por usuario creador
            user_query = """
            SELECT 
                created_by,
                COUNT(*) as chatbot_count,
                MAX(created_at) as last_activity
            FROM chatbots 
            WHERE company_id = :company_id 
            GROUP BY created_by
            ORDER BY chatbot_count DESC
            """
            
            user_result = await self.db.execute(text(user_query), {"company_id": company_id})
            user_activity = [
                {
                    "user_id": row.created_by,
                    "chatbot_count": row.chatbot_count,
                    "last_activity": row.last_activity
                }
                for row in user_result.fetchall()
            ]
            
            return {
                "user_activity": user_activity,
                "total_active_users": len(user_activity)
            }
            
        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            raise

# Instancia global del collector de métricas
metrics_collector = MetricsCollector()
