"""
Sistema de backup automático para chatbots
"""
import asyncio
import json
import os
import zipfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class BackupType(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    SELECTIVE = "selective"

class BackupStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BackupFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    MANUAL = "manual"

class BackupJob:
    def __init__(
        self,
        id: str,
        name: str,
        backup_type: BackupType,
        frequency: BackupFrequency,
        company_id: str,
        created_by: str,
        config: Dict[str, Any]
    ):
        self.id = id
        self.name = name
        self.backup_type = backup_type
        self.frequency = frequency
        self.company_id = company_id
        self.created_by = created_by
        self.config = config
        self.status = BackupStatus.PENDING
        self.created_at = datetime.now()
        self.last_run = None
        self.next_run = self._calculate_next_run()
        self.runs_count = 0
        self.last_error = None
    
    def _calculate_next_run(self) -> Optional[datetime]:
        """Calcular próxima ejecución"""
        if self.frequency == BackupFrequency.MANUAL:
            return None
        
        now = datetime.now()
        if self.frequency == BackupFrequency.DAILY:
            return now + timedelta(days=1)
        elif self.frequency == BackupFrequency.WEEKLY:
            return now + timedelta(weeks=1)
        elif self.frequency == BackupFrequency.MONTHLY:
            return now + timedelta(days=30)
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "backup_type": self.backup_type.value,
            "frequency": self.frequency.value,
            "company_id": self.company_id,
            "created_by": self.created_by,
            "config": self.config,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "runs_count": self.runs_count,
            "last_error": self.last_error
        }

class BackupExecution:
    def __init__(self, job_id: str, execution_id: str):
        self.job_id = job_id
        self.execution_id = execution_id
        self.status = BackupStatus.PENDING
        self.started_at = datetime.now()
        self.completed_at = None
        self.file_path = None
        self.file_size = 0
        self.chatbots_count = 0
        self.error_message = None
        self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "execution_id": self.execution_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "chatbots_count": self.chatbots_count,
            "error_message": self.error_message,
            "metadata": self.metadata
        }

class BackupManager:
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Almacenar jobs y ejecuciones en memoria (en producción usar BD)
        self.backup_jobs: Dict[str, BackupJob] = {}
        self.backup_executions: Dict[str, BackupExecution] = {}
        
        # Configuración
        self.max_backup_age_days = 30
        self.max_backups_per_job = 10
        
        # Lock para operaciones thread-safe
        self._lock = asyncio.Lock()
    
    async def create_backup_job(
        self,
        name: str,
        backup_type: BackupType,
        frequency: BackupFrequency,
        company_id: str,
        created_by: str,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Crear un nuevo job de backup"""
        async with self._lock:
            import uuid
            
            job_id = str(uuid.uuid4())
            config = config or {}
            
            # Configuración por defecto
            default_config = {
                "include_inactive": False,
                "include_archived": False,
                "compress": True,
                "encrypt": False,
                "chatbot_ids": [],  # Si está vacío, incluye todos
                "exclude_large_prompts": False
            }
            default_config.update(config)
            
            job = BackupJob(
                id=job_id,
                name=name,
                backup_type=backup_type,
                frequency=frequency,
                company_id=company_id,
                created_by=created_by,
                config=default_config
            )
            
            self.backup_jobs[job_id] = job
            
            logger.info(f"Backup job created: {name} ({job_id}) for company {company_id}")
            return job_id
    
    async def execute_backup(self, job_id: str, db: AsyncSession) -> str:
        """Ejecutar un backup"""
        if job_id not in self.backup_jobs:
            raise ValueError(f"Backup job {job_id} not found")
        
        job = self.backup_jobs[job_id]
        
        import uuid
        execution_id = str(uuid.uuid4())
        execution = BackupExecution(job_id, execution_id)
        
        self.backup_executions[execution_id] = execution
        
        try:
            execution.status = BackupStatus.IN_PROGRESS
            job.status = BackupStatus.IN_PROGRESS
            
            # Obtener chatbots según configuración
            chatbots_data = await self._get_chatbots_for_backup(job, db)
            execution.chatbots_count = len(chatbots_data)
            
            # Crear archivo de backup
            backup_filename = self._generate_backup_filename(job, execution)
            backup_path = self.backup_dir / backup_filename
            
            # Crear backup
            await self._create_backup_file(chatbots_data, backup_path, job.config)
            
            # Actualizar información
            execution.file_path = str(backup_path)
            execution.file_size = backup_path.stat().st_size
            execution.completed_at = datetime.now()
            execution.status = BackupStatus.COMPLETED
            
            # Actualizar job
            job.status = BackupStatus.COMPLETED
            job.last_run = datetime.now()
            job.runs_count += 1
            job.next_run = job._calculate_next_run()
            
            # Limpiar backups antiguos
            await self._cleanup_old_backups(job_id)
            
            logger.info(f"Backup completed: {execution_id} ({execution.file_size} bytes, {execution.chatbots_count} chatbots)")
            
        except Exception as e:
            execution.status = BackupStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            
            job.status = BackupStatus.FAILED
            job.last_error = str(e)
            
            logger.error(f"Backup failed: {execution_id} - {str(e)}")
            raise
        
        return execution_id
    
    async def _get_chatbots_for_backup(self, job: BackupJob, db: AsyncSession) -> List[Dict[str, Any]]:
        """Obtener chatbots para backup según configuración"""
        config = job.config
        
        # Construir query base
        query = """
        SELECT id, name, description, model, system_prompt, temperature, max_tokens,
               status, company_id, created_by, created_at, updated_at
        FROM chatbots
        WHERE company_id = :company_id
        """
        
        params = {"company_id": job.company_id}
        conditions = []
        
        # Filtros por status
        if not config.get("include_inactive", False):
            conditions.append("status != 'INACTIVE'")
        
        if not config.get("include_archived", False):
            conditions.append("status != 'ARCHIVED'")
        
        # Filtros por chatbots específicos
        if config.get("chatbot_ids"):
            placeholders = ",".join([f":chatbot_id_{i}" for i in range(len(config["chatbot_ids"]))])
            conditions.append(f"id IN ({placeholders})")
            for i, chatbot_id in enumerate(config["chatbot_ids"]):
                params[f"chatbot_id_{i}"] = chatbot_id
        
        # Agregar condiciones
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC"
        
        result = await db.execute(text(query), params)
        rows = result.fetchall()
        
        chatbots = []
        for row in rows:
            chatbot_data = {
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "model": row.model,
                "system_prompt": row.system_prompt if not config.get("exclude_large_prompts", False) else "...",
                "temperature": row.temperature,
                "max_tokens": row.max_tokens,
                "status": row.status,
                "company_id": row.company_id,
                "created_by": row.created_by,
                "created_at": row.created_at.isoformat() if hasattr(row.created_at, 'isoformat') else str(row.created_at),
                "updated_at": row.updated_at.isoformat() if hasattr(row.updated_at, 'isoformat') else str(row.updated_at)
            }
            chatbots.append(chatbot_data)
        
        return chatbots
    
    def _generate_backup_filename(self, job: BackupJob, execution: BackupExecution) -> str:
        """Generar nombre de archivo de backup"""
        timestamp = execution.started_at.strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in job.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        
        extension = ".zip" if job.config.get("compress", True) else ".json"
        return f"backup_{safe_name}_{timestamp}_{execution.execution_id[:8]}{extension}"
    
    async def _create_backup_file(
        self, 
        chatbots_data: List[Dict[str, Any]], 
        backup_path: Path, 
        config: Dict[str, Any]
    ):
        """Crear archivo de backup"""
        backup_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "chatbots_count": len(chatbots_data),
                "config": config
            },
            "chatbots": chatbots_data
        }
        
        if config.get("compress", True):
            # Crear archivo ZIP
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr("backup.json", json.dumps(backup_data, indent=2, ensure_ascii=False))
        else:
            # Crear archivo JSON simple
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    async def _cleanup_old_backups(self, job_id: str):
        """Limpiar backups antiguos"""
        job = self.backup_jobs[job_id]
        
        # Obtener todas las ejecuciones de este job
        job_executions = [
            exec for exec in self.backup_executions.values() 
            if exec.job_id == job_id and exec.status == BackupStatus.COMPLETED
        ]
        
        # Ordenar por fecha
        job_executions.sort(key=lambda x: x.started_at, reverse=True)
        
        # Eliminar archivos antiguos
        for execution in job_executions[self.max_backups_per_job:]:
            if execution.file_path and Path(execution.file_path).exists():
                try:
                    Path(execution.file_path).unlink()
                    logger.info(f"Deleted old backup: {execution.file_path}")
                except Exception as e:
                    logger.error(f"Error deleting backup {execution.file_path}: {e}")
        
        # Eliminar backups por edad
        cutoff_date = datetime.now() - timedelta(days=self.max_backup_age_days)
        for execution in job_executions:
            if execution.started_at < cutoff_date and execution.file_path:
                if Path(execution.file_path).exists():
                    try:
                        Path(execution.file_path).unlink()
                        logger.info(f"Deleted expired backup: {execution.file_path}")
                    except Exception as e:
                        logger.error(f"Error deleting expired backup {execution.file_path}: {e}")
    
    async def restore_backup(self, execution_id: str, db: AsyncSession, target_company_id: Optional[str] = None) -> Dict[str, Any]:
        """Restaurar desde un backup"""
        if execution_id not in self.backup_executions:
            raise ValueError(f"Backup execution {execution_id} not found")
        
        execution = self.backup_executions[execution_id]
        
        if not execution.file_path or not Path(execution.file_path).exists():
            raise ValueError(f"Backup file not found: {execution.file_path}")
        
        # Leer archivo de backup
        backup_data = await self._read_backup_file(Path(execution.file_path))
        
        # Restaurar chatbots
        restored_count = 0
        errors = []
        
        for chatbot_data in backup_data["chatbots"]:
            try:
                # Generar nuevo ID para evitar conflictos
                import uuid
                new_id = str(uuid.uuid4())
                
                # Usar company_id objetivo si se especifica
                company_id = target_company_id or chatbot_data["company_id"]
                
                # Insertar chatbot
                insert_query = """
                INSERT INTO chatbots (id, name, description, model, system_prompt, temperature, max_tokens, status, company_id, created_by, created_at, updated_at)
                VALUES (:id, :name, :description, :model, :system_prompt, :temperature, :max_tokens, :status, :company_id, :created_by, :created_at, :updated_at)
                """
                
                params = {
                    "id": new_id,
                    "name": f"[RESTORED] {chatbot_data['name']}",
                    "description": chatbot_data["description"],
                    "model": chatbot_data["model"],
                    "system_prompt": chatbot_data["system_prompt"],
                    "temperature": chatbot_data["temperature"],
                    "max_tokens": chatbot_data["max_tokens"],
                    "status": "DRAFT",  # Restaurar como borrador
                    "company_id": company_id,
                    "created_by": chatbot_data["created_by"],
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                
                await db.execute(text(insert_query), params)
                restored_count += 1
                
            except Exception as e:
                errors.append(f"Error restoring chatbot {chatbot_data.get('name', 'unknown')}: {str(e)}")
                logger.error(f"Error restoring chatbot: {e}")
        
        await db.commit()
        
        return {
            "restored_count": restored_count,
            "total_chatbots": len(backup_data["chatbots"]),
            "errors": errors,
            "backup_metadata": backup_data["metadata"]
        }
    
    async def _read_backup_file(self, backup_path: Path) -> Dict[str, Any]:
        """Leer archivo de backup"""
        if backup_path.suffix == '.zip':
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                with zipf.open('backup.json') as f:
                    return json.load(f)
        else:
            with open(backup_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def get_backup_jobs(self, company_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtener jobs de backup"""
        jobs = list(self.backup_jobs.values())
        
        if company_id:
            jobs = [job for job in jobs if job.company_id == company_id]
        
        return [job.to_dict() for job in jobs]
    
    def get_backup_executions(self, job_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtener ejecuciones de backup"""
        executions = list(self.backup_executions.values())
        
        if job_id:
            executions = [exec for exec in executions if exec.job_id == job_id]
        
        # Ordenar por fecha
        executions.sort(key=lambda x: x.started_at, reverse=True)
        
        return [exec.to_dict() for exec in executions]
    
    async def delete_backup_job(self, job_id: str) -> bool:
        """Eliminar job de backup"""
        if job_id not in self.backup_jobs:
            return False
        
        # Eliminar archivos de backup asociados
        job_executions = [
            exec for exec in self.backup_executions.values() 
            if exec.job_id == job_id
        ]
        
        for execution in job_executions:
            if execution.file_path and Path(execution.file_path).exists():
                try:
                    Path(execution.file_path).unlink()
                except Exception as e:
                    logger.error(f"Error deleting backup file {execution.file_path}: {e}")
            
            # Eliminar ejecución
            if execution.execution_id in self.backup_executions:
                del self.backup_executions[execution.execution_id]
        
        # Eliminar job
        del self.backup_jobs[job_id]
        
        logger.info(f"Backup job deleted: {job_id}")
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de backup"""
        total_jobs = len(self.backup_jobs)
        total_executions = len(self.backup_executions)
        
        completed_executions = [
            exec for exec in self.backup_executions.values() 
            if exec.status == BackupStatus.COMPLETED
        ]
        
        failed_executions = [
            exec for exec in self.backup_executions.values() 
            if exec.status == BackupStatus.FAILED
        ]
        
        total_size = sum(exec.file_size for exec in completed_executions)
        total_chatbots = sum(exec.chatbots_count for exec in completed_executions)
        
        return {
            "total_jobs": total_jobs,
            "total_executions": total_executions,
            "completed_executions": len(completed_executions),
            "failed_executions": len(failed_executions),
            "total_backup_size": total_size,
            "total_chatbots_backed_up": total_chatbots,
            "success_rate": len(completed_executions) / total_executions * 100 if total_executions > 0 else 0
        }

# Instancia global del manager de backup
backup_manager = BackupManager()

# Función para ejecutar backups programados
async def run_scheduled_backups(db: AsyncSession):
    """Ejecutar backups programados"""
    now = datetime.now()

    for job in backup_manager.backup_jobs.values():
        if (job.next_run and
            job.next_run <= now and
            job.status != BackupStatus.IN_PROGRESS and
            job.frequency != BackupFrequency.MANUAL):

            try:
                logger.info(f"Running scheduled backup: {job.name} ({job.id})")
                await backup_manager.execute_backup(job.id, db)
            except Exception as e:
                logger.error(f"Scheduled backup failed: {job.name} - {str(e)}")
