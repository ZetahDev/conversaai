"""
Endpoints del dashboard de métricas
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_async_db
from app.core.security import get_current_active_user
from app.core.metrics import DashboardMetrics, metrics_collector

router = APIRouter()

# Modelos de respuesta
class DashboardOverview(BaseModel):
    total_chatbots: int
    status_distribution: Dict[str, int]
    model_distribution: Dict[str, int]
    recent_activity: list
    active_chatbots: int
    draft_chatbots: int

class UsageTrends(BaseModel):
    creation_trend: list
    update_trend: list
    period_days: int

class PerformanceMetrics(BaseModel):
    model_configurations: list
    newest_chatbots: list

class UserActivity(BaseModel):
    user_activity: list
    total_active_users: int

class RealTimeMetrics(BaseModel):
    current_active_users: int
    requests_last_hour: int
    requests_per_minute: int
    average_response_time: float
    total_operations: Dict[str, int]
    error_counts: Dict[str, int]
    top_models: list
    recent_status_changes: list

class CompleteDashboard(BaseModel):
    overview: DashboardOverview
    usage_trends: UsageTrends
    performance_metrics: PerformanceMetrics
    user_activity: UserActivity
    real_time_metrics: RealTimeMetrics

# Helper function para obtener atributos del usuario
def get_user_attr(user, attr):
    """Obtener atributo del usuario, compatible con dict y objeto"""
    if isinstance(user, dict):
        if attr == "id":
            return user.get("sub")
        elif attr == "company_id":
            email = user.get("email", "")
            if "johan@techcorp.com" in email:
                return "company_1"
            elif "admin@techcorp.com" in email:
                return "company_1"
            elif "usuario1@techcorp.com" in email:
                return "company_1"
            else:
                return "company_1"
        return user.get(attr)
    return getattr(user, attr, None)

@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> DashboardOverview:
    """
    Obtener resumen general del dashboard
    """
    try:
        company_id = get_user_attr(current_user, "company_id")
        dashboard_metrics = DashboardMetrics(db)
        
        overview_data = await dashboard_metrics.get_company_overview(company_id)
        
        return DashboardOverview(**overview_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving dashboard overview: {str(e)}"
        )

@router.get("/usage-trends", response_model=UsageTrends)
async def get_usage_trends(
    days: int = Query(30, ge=1, le=365, description="Número de días para el análisis"),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> UsageTrends:
    """
    Obtener tendencias de uso
    """
    try:
        company_id = get_user_attr(current_user, "company_id")
        dashboard_metrics = DashboardMetrics(db)
        
        trends_data = await dashboard_metrics.get_usage_trends(company_id, days)
        
        return UsageTrends(**trends_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving usage trends: {str(e)}"
        )

@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> PerformanceMetrics:
    """
    Obtener métricas de rendimiento
    """
    try:
        company_id = get_user_attr(current_user, "company_id")
        dashboard_metrics = DashboardMetrics(db)
        
        performance_data = await dashboard_metrics.get_performance_metrics(company_id)
        
        return PerformanceMetrics(**performance_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving performance metrics: {str(e)}"
        )

@router.get("/user-activity", response_model=UserActivity)
async def get_user_activity(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> UserActivity:
    """
    Obtener actividad de usuarios
    """
    try:
        company_id = get_user_attr(current_user, "company_id")
        dashboard_metrics = DashboardMetrics(db)
        
        activity_data = await dashboard_metrics.get_user_activity(company_id)
        
        return UserActivity(**activity_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving user activity: {str(e)}"
        )

@router.get("/real-time", response_model=RealTimeMetrics)
async def get_real_time_metrics(
    current_user: dict = Depends(get_current_active_user)
) -> RealTimeMetrics:
    """
    Obtener métricas en tiempo real
    """
    try:
        real_time_data = metrics_collector.get_real_time_metrics()
        
        return RealTimeMetrics(**real_time_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving real-time metrics: {str(e)}"
        )

@router.get("/complete", response_model=CompleteDashboard)
async def get_complete_dashboard(
    days: int = Query(30, ge=1, le=365, description="Número de días para tendencias"),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> CompleteDashboard:
    """
    Obtener dashboard completo con todas las métricas
    """
    try:
        company_id = get_user_attr(current_user, "company_id")
        dashboard_metrics = DashboardMetrics(db)
        
        # Obtener todas las métricas secuencialmente para evitar problemas de sesión
        dashboard_metrics = DashboardMetrics(db)

        overview_data = await dashboard_metrics.get_company_overview(company_id)
        trends_data = await dashboard_metrics.get_usage_trends(company_id, days)
        performance_data = await dashboard_metrics.get_performance_metrics(company_id)
        activity_data = await dashboard_metrics.get_user_activity(company_id)
        
        # Obtener métricas en tiempo real
        real_time_data = metrics_collector.get_real_time_metrics()
        
        return CompleteDashboard(
            overview=DashboardOverview(**overview_data),
            usage_trends=UsageTrends(**trends_data),
            performance_metrics=PerformanceMetrics(**performance_data),
            user_activity=UserActivity(**activity_data),
            real_time_metrics=RealTimeMetrics(**real_time_data)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving complete dashboard: {str(e)}"
        )

@router.get("/export")
async def export_dashboard_data(
    format: str = Query("json", description="Formato de exportación (json, csv)"),
    days: int = Query(30, ge=1, le=365, description="Número de días para el reporte"),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Exportar datos del dashboard
    """
    try:
        # Solo permitir a administradores
        user_email = current_user.get("email", "")
        if "johan@techcorp.com" not in user_email and "admin@techcorp.com" not in user_email:
            raise HTTPException(
                status_code=403,
                detail="Access denied. Admin privileges required."
            )
        
        company_id = get_user_attr(current_user, "company_id")
        dashboard_metrics = DashboardMetrics(db)
        
        # Obtener datos completos
        overview_data = await dashboard_metrics.get_company_overview(company_id)
        trends_data = await dashboard_metrics.get_usage_trends(company_id, days)
        performance_data = await dashboard_metrics.get_performance_metrics(company_id)
        activity_data = await dashboard_metrics.get_user_activity(company_id)
        real_time_data = metrics_collector.get_real_time_metrics()
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "company_id": company_id,
            "period_days": days,
            "overview": overview_data,
            "usage_trends": trends_data,
            "performance_metrics": performance_data,
            "user_activity": activity_data,
            "real_time_metrics": real_time_data
        }
        
        if format.lower() == "csv":
            # Para CSV, aplanar los datos principales
            csv_data = {
                "summary": {
                    "total_chatbots": overview_data["total_chatbots"],
                    "active_chatbots": overview_data["active_chatbots"],
                    "draft_chatbots": overview_data["draft_chatbots"],
                    "total_active_users": activity_data["total_active_users"],
                    "current_active_users": real_time_data["current_active_users"]
                },
                "detailed_data": export_data
            }
            return csv_data
        
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting dashboard data: {str(e)}"
        )
