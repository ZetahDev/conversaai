"""
Endpoints de backup automático
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from pathlib import Path

from app.core.database import get_async_db
from app.core.security import get_current_active_user
from app.core.backup import (
    backup_manager, 
    BackupType, 
    BackupFrequency,
    BackupStatus,
    run_scheduled_backups
)
from app.core.permissions import permission_checker, Permission, require_permission

router = APIRouter()

# Modelos de request/response
class CreateBackupJobRequest(BaseModel):
    name: str
    backup_type: BackupType
    frequency: BackupFrequency
    config: Optional[Dict[str, Any]] = None

class BackupJobResponse(BaseModel):
    id: str
    name: str
    backup_type: str
    frequency: str
    company_id: str
    created_by: str
    config: Dict[str, Any]
    status: str
    created_at: str
    last_run: Optional[str]
    next_run: Optional[str]
    runs_count: int
    last_error: Optional[str]

class BackupExecutionResponse(BaseModel):
    job_id: str
    execution_id: str
    status: str
    started_at: str
    completed_at: Optional[str]
    file_path: Optional[str]
    file_size: int
    chatbots_count: int
    error_message: Optional[str]
    metadata: Dict[str, Any]

class RestoreBackupRequest(BaseModel):
    execution_id: str
    target_company_id: Optional[str] = None

class BackupStatsResponse(BaseModel):
    total_jobs: int
    total_executions: int
    completed_executions: int
    failed_executions: int
    total_backup_size: int
    total_chatbots_backed_up: int
    success_rate: float

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

@router.post("/jobs", response_model=Dict[str, str])
async def create_backup_job(
    request: CreateBackupJobRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, str]:
    """
    Crear un nuevo job de backup
    """
    try:
        # Verificar permisos
        if not permission_checker.check_permission(current_user, Permission.SYSTEM_BACKUP):
            raise HTTPException(
                status_code=403,
                detail="Permission denied. You don't have permission to create backup jobs."
            )
        
        company_id = get_user_attr(current_user, "company_id")
        user_id = get_user_attr(current_user, "id")
        
        job_id = await backup_manager.create_backup_job(
            name=request.name,
            backup_type=request.backup_type,
            frequency=request.frequency,
            company_id=company_id,
            created_by=user_id,
            config=request.config
        )
        
        return {
            "message": "Backup job created successfully",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating backup job: {str(e)}"
        )

@router.get("/jobs", response_model=List[BackupJobResponse])
async def get_backup_jobs(
    current_user: dict = Depends(get_current_active_user)
) -> List[BackupJobResponse]:
    """
    Obtener jobs de backup de la empresa
    """
    try:
        # Verificar permisos
        if not permission_checker.check_permission(current_user, Permission.SYSTEM_BACKUP):
            raise HTTPException(
                status_code=403,
                detail="Permission denied. You don't have permission to view backup jobs."
            )
        
        company_id = get_user_attr(current_user, "company_id")
        
        jobs_data = backup_manager.get_backup_jobs(company_id)
        
        return [BackupJobResponse(**job) for job in jobs_data]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving backup jobs: {str(e)}"
        )

@router.post("/jobs/{job_id}/execute")
async def execute_backup_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, str]:
    """
    Ejecutar un job de backup manualmente
    """
    try:
        # Verificar permisos
        if not permission_checker.check_permission(current_user, Permission.SYSTEM_BACKUP):
            raise HTTPException(
                status_code=403,
                detail="Permission denied. You don't have permission to execute backups."
            )
        
        # Verificar que el job existe y pertenece a la empresa
        company_id = get_user_attr(current_user, "company_id")
        jobs = backup_manager.get_backup_jobs(company_id)
        
        if not any(job["id"] == job_id for job in jobs):
            raise HTTPException(
                status_code=404,
                detail="Backup job not found"
            )
        
        # Ejecutar backup en background
        background_tasks.add_task(backup_manager.execute_backup, job_id, db)
        
        return {
            "message": "Backup execution started",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error executing backup: {str(e)}"
        )

@router.get("/jobs/{job_id}/executions", response_model=List[BackupExecutionResponse])
async def get_backup_executions(
    job_id: str,
    current_user: dict = Depends(get_current_active_user)
) -> List[BackupExecutionResponse]:
    """
    Obtener ejecuciones de un job de backup
    """
    try:
        # Verificar permisos
        if not permission_checker.check_permission(current_user, Permission.SYSTEM_BACKUP):
            raise HTTPException(
                status_code=403,
                detail="Permission denied. You don't have permission to view backup executions."
            )
        
        # Verificar que el job existe y pertenece a la empresa
        company_id = get_user_attr(current_user, "company_id")
        jobs = backup_manager.get_backup_jobs(company_id)
        
        if not any(job["id"] == job_id for job in jobs):
            raise HTTPException(
                status_code=404,
                detail="Backup job not found"
            )
        
        executions_data = backup_manager.get_backup_executions(job_id)
        
        return [BackupExecutionResponse(**execution) for execution in executions_data]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving backup executions: {str(e)}"
        )

@router.get("/executions/{execution_id}/download")
async def download_backup(
    execution_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Descargar archivo de backup
    """
    try:
        # Verificar permisos
        if not permission_checker.check_permission(current_user, Permission.SYSTEM_BACKUP):
            raise HTTPException(
                status_code=403,
                detail="Permission denied. You don't have permission to download backups."
            )
        
        # Verificar que la ejecución existe
        executions = backup_manager.get_backup_executions()
        execution = next((exec for exec in executions if exec["execution_id"] == execution_id), None)
        
        if not execution:
            raise HTTPException(
                status_code=404,
                detail="Backup execution not found"
            )
        
        # Verificar que pertenece a la empresa del usuario
        company_id = get_user_attr(current_user, "company_id")
        jobs = backup_manager.get_backup_jobs(company_id)
        
        if not any(job["id"] == execution["job_id"] for job in jobs):
            raise HTTPException(
                status_code=403,
                detail="Access denied to this backup"
            )
        
        # Verificar que el archivo existe
        if not execution["file_path"] or not Path(execution["file_path"]).exists():
            raise HTTPException(
                status_code=404,
                detail="Backup file not found"
            )
        
        return FileResponse(
            path=execution["file_path"],
            filename=Path(execution["file_path"]).name,
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading backup: {str(e)}"
        )

@router.post("/restore")
async def restore_backup(
    request: RestoreBackupRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Restaurar desde un backup
    """
    try:
        # Verificar permisos (solo SuperAdmin puede restaurar)
        user_email = current_user.get("email", "")
        if "johan@techcorp.com" not in user_email:
            raise HTTPException(
                status_code=403,
                detail="Permission denied. Only SuperAdmin can restore backups."
            )
        
        # Usar company_id objetivo o el del usuario actual
        target_company_id = request.target_company_id or get_user_attr(current_user, "company_id")
        
        result = await backup_manager.restore_backup(
            execution_id=request.execution_id,
            db=db,
            target_company_id=target_company_id
        )
        
        return {
            "message": "Backup restored successfully",
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error restoring backup: {str(e)}"
        )

@router.delete("/jobs/{job_id}")
async def delete_backup_job(
    job_id: str,
    current_user: dict = Depends(get_current_active_user)
) -> Dict[str, str]:
    """
    Eliminar un job de backup
    """
    try:
        # Verificar permisos
        if not permission_checker.check_permission(current_user, Permission.SYSTEM_BACKUP):
            raise HTTPException(
                status_code=403,
                detail="Permission denied. You don't have permission to delete backup jobs."
            )
        
        # Verificar que el job existe y pertenece a la empresa
        company_id = get_user_attr(current_user, "company_id")
        jobs = backup_manager.get_backup_jobs(company_id)
        
        if not any(job["id"] == job_id for job in jobs):
            raise HTTPException(
                status_code=404,
                detail="Backup job not found"
            )
        
        success = await backup_manager.delete_backup_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Backup job not found"
            )
        
        return {
            "message": "Backup job deleted successfully",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting backup job: {str(e)}"
        )

@router.get("/stats", response_model=BackupStatsResponse)
async def get_backup_stats(
    current_user: dict = Depends(get_current_active_user)
) -> BackupStatsResponse:
    """
    Obtener estadísticas de backup
    """
    try:
        # Verificar permisos
        if not permission_checker.check_permission(current_user, Permission.SYSTEM_BACKUP):
            raise HTTPException(
                status_code=403,
                detail="Permission denied. You don't have permission to view backup stats."
            )
        
        stats = backup_manager.get_stats()
        
        return BackupStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving backup stats: {str(e)}"
        )

@router.post("/run-scheduled")
async def run_scheduled_backups_endpoint(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, str]:
    """
    Ejecutar backups programados manualmente (solo para testing/admin)
    """
    try:
        # Solo SuperAdmin
        user_email = current_user.get("email", "")
        if "johan@techcorp.com" not in user_email:
            raise HTTPException(
                status_code=403,
                detail="Permission denied. Only SuperAdmin can run scheduled backups."
            )
        
        await run_scheduled_backups(db)
        
        return {
            "message": "Scheduled backups executed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running scheduled backups: {str(e)}"
        )
