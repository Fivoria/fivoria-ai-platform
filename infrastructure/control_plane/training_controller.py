"""
Training Control Plane
Manages training jobs, GPU clusters, and training lifecycle
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Training job statuses"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    STOPPING = "stopping"


class ClusterStatus(Enum):
    """GPU cluster statuses"""
    AVAILABLE = "available"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


@dataclass
class GPUCluster:
    """GPU cluster definition"""
    cluster_id: str
    name: str
    total_gpus: int
    gpu_type: str
    gpu_memory_gb: int
    status: ClusterStatus
    available_gpus: int
    location: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class TrainingJob:
    """Training job definition"""
    job_id: str
    name: str
    model_config: Dict[str, Any]
    dataset_id: str
    cluster_id: str
    status: JobStatus
    priority: int  # 1-10, 10 highest
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_step: int = 0
    total_steps: int = 0
    loss: float = 0.0
    checkpoint_path: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


class TrainingController:
    """Controls training jobs and GPU clusters"""

    def __init__(self):
        self.clusters: Dict[str, GPUCluster] = {}
        self.jobs: Dict[str, TrainingJob] = {}
        self.job_queue: List[str] = []
        self.running = False

    def register_cluster(
        self,
        cluster_id: str,
        name: str,
        total_gpus: int,
        gpu_type: str,
        gpu_memory_gb: int,
        location: str
    ) -> GPUCluster:
        """Register a GPU cluster"""
        cluster = GPUCluster(
            cluster_id=cluster_id,
            name=name,
            total_gpus=total_gpus,
            gpu_type=gpu_type,
            gpu_memory_gb=gpu_memory_gb,
            status=ClusterStatus.AVAILABLE,
            available_gpus=total_gpus,
            location=location
        )
        
        self.clusters[cluster_id] = cluster
        logger.info(f"Registered cluster: {cluster_id}")
        return cluster

    def create_job(
        self,
        job_id: str,
        name: str,
        model_config: Dict,
        dataset_id: str,
        cluster_id: str,
        priority: int = 5,
        total_steps: int = 10000
    ) -> TrainingJob:
        """Create a training job"""
        job = TrainingJob(
            job_id=job_id,
            name=name,
            model_config=model_config,
            dataset_id=dataset_id,
            cluster_id=cluster_id,
            status=JobStatus.PENDING,
            priority=priority,
            created_at=datetime.now(),
            total_steps=total_steps
        )
        
        self.jobs[job_id] = job
        self.job_queue.append(job_id)
        
        logger.info(f"Created job: {job_id}")
        return job

    def schedule_job(self, job_id: str) -> bool:
        """Schedule a job for execution"""
        job = self.jobs.get(job_id)
        if not job:
            logger.warning(f"Job {job_id} not found")
            return False
        
        cluster = self.clusters.get(job.cluster_id)
        if not cluster:
            logger.warning(f"Cluster {job.cluster_id} not found")
            return False
        
        if cluster.status != ClusterStatus.AVAILABLE or cluster.available_gpus <= 0:
            logger.warning(f"Cluster {job.cluster_id} not available")
            return False
        
        # Check if cluster has enough GPUs
        required_gpus = job.model_config.get('world_size', 1)
        if cluster.available_gpus < required_gpus:
            logger.warning(f"Cluster {job.cluster_id} has insufficient GPUs")
            return False
        
        # Schedule job
        job.status = JobStatus.QUEUED
        cluster.available_gpus -= required_gpus
        if cluster.available_gpus == 0:
            cluster.status = ClusterStatus.BUSY
        
        logger.info(f"Scheduled job {job_id} on cluster {job.cluster_id}")
        return True

    def start_job(self, job_id: str) -> bool:
        """Start a training job"""
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        if job.status != JobStatus.QUEUED:
            logger.warning(f"Job {job_id} not in queued state")
            return False
        
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        
        logger.info(f"Started job {job_id}")
        return True

    def pause_job(self, job_id: str) -> bool:
        """Pause a training job"""
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        if job.status != JobStatus.RUNNING:
            logger.warning(f"Job {job_id} not running")
            return False
        
        job.status = JobStatus.PAUSED
        
        # Release cluster resources
        cluster = self.clusters.get(job.cluster_id)
        if cluster:
            required_gpus = job.model_config.get('world_size', 1)
            cluster.available_gpus += required_gpus
            cluster.status = ClusterStatus.AVAILABLE
        
        logger.info(f"Paused job {job_id}")
        return True

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused training job"""
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        if job.status != JobStatus.PAUSED:
            logger.warning(f"Job {job_id} not paused")
            return False
        
        # Re-allocate cluster resources
        cluster = self.clusters.get(job.cluster_id)
        if cluster and cluster.available_gpus >= job.model_config.get('world_size', 1):
            required_gpus = job.model_config.get('world_size', 1)
            cluster.available_gpus -= required_gpus
            if cluster.available_gpus == 0:
                cluster.status = ClusterStatus.BUSY
            
            job.status = JobStatus.RUNNING
            logger.info(f"Resumed job {job_id}")
            return True
        
        logger.warning(f"Cannot resume job {job_id}: insufficient cluster resources")
        return False

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a training job"""
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            logger.warning(f"Job {job_id} already in terminal state")
            return False
        
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now()
        
        # Release cluster resources
        cluster = self.clusters.get(job.cluster_id)
        if cluster:
            required_gpus = job.model_config.get('world_size', 1)
            cluster.available_gpus += required_gpus
            cluster.status = ClusterStatus.AVAILABLE
        
        logger.info(f"Cancelled job {job_id}")
        return True

    def update_job_progress(self, job_id: str, step: int, loss: float):
        """Update job progress"""
        job = self.jobs.get(job_id)
        if not job:
            return
        
        job.current_step = step
        job.loss = loss
        
        if step >= job.total_steps:
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            
            # Release cluster resources
            cluster = self.clusters.get(job.cluster_id)
            if cluster:
                required_gpus = job.model_config.get('world_size', 1)
                cluster.available_gpus += required_gpus
                cluster.status = ClusterStatus.AVAILABLE
            
            logger.info(f"Job {job_id} completed")

    def fail_job(self, job_id: str, error: str):
        """Mark job as failed"""
        job = self.jobs.get(job_id)
        if not job:
            return
        
        job.status = JobStatus.FAILED
        job.error = error
        job.completed_at = datetime.now()
        
        # Release cluster resources
        cluster = self.clusters.get(job.cluster_id)
        if cluster:
            required_gpus = job.model_config.get('world_size', 1)
            cluster.available_gpus += required_gpus
            cluster.status = ClusterStatus.AVAILABLE
        
        logger.error(f"Job {job_id} failed: {error}")

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get job status"""
        job = self.jobs.get(job_id)
        if not job:
            return None
        
        return {
            'job_id': job.job_id,
            'name': job.name,
            'status': job.status.value,
            'current_step': job.current_step,
            'total_steps': job.total_steps,
            'loss': job.loss,
            'cluster_id': job.cluster_id,
            'created_at': job.created_at.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'error': job.error
        }

    def get_cluster_status(self, cluster_id: str) -> Optional[Dict]:
        """Get cluster status"""
        cluster = self.clusters.get(cluster_id)
        if not cluster:
            return None
        
        return {
            'cluster_id': cluster.cluster_id,
            'name': cluster.name,
            'status': cluster.status.value,
            'total_gpus': cluster.total_gpus,
            'available_gpus': cluster.available_gpus,
            'gpu_type': cluster.gpu_type,
            'location': cluster.location
        }

    def list_jobs(self, status: JobStatus = None) -> List[Dict]:
        """List jobs with optional status filter"""
        jobs = []
        
        for job in self.jobs.values():
            if status is None or job.status == status:
                jobs.append(self.get_job_status(job.job_id))
        
        # Sort by priority and creation time
        jobs.sort(key=lambda x: (-self.jobs[x['job_id']].priority, self.jobs[x['job_id']].created_at))
        
        return jobs

    def list_clusters(self, status: ClusterStatus = None) -> List[Dict]:
        """List clusters with optional status filter"""
        clusters = []
        
        for cluster in self.clusters.values():
            if status is None or cluster.status == status:
                clusters.append(self.get_cluster_status(cluster.cluster_id))
        
        return clusters

    async def run_scheduler(self):
        """Run job scheduler"""
        self.running = True
        
        while self.running:
            # Process job queue
            if self.job_queue:
                # Sort queue by priority
                self.job_queue.sort(key=lambda jid: -self.jobs[jid].priority)
                
                for job_id in self.job_queue[:]:
                    job = self.jobs.get(job_id)
                    if job and job.status == JobStatus.PENDING:
                        if self.schedule_job(job_id):
                            self.job_queue.remove(job_id)
            
            # Small delay
            await asyncio.sleep(1)

    def stop_scheduler(self):
        """Stop job scheduler"""
        self.running = False

    def get_system_status(self) -> Dict:
        """Get overall system status"""
        total_jobs = len(self.jobs)
        running_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.RUNNING])
        completed_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.COMPLETED])
        failed_jobs = len([j for j in self.jobs.values() if j.status == JobStatus.FAILED])
        
        total_gpus = sum(c.total_gpus for c in self.clusters.values())
        available_gpus = sum(c.available_gpus for c in self.clusters.values())
        
        return {
            'jobs': {
                'total': total_jobs,
                'running': running_jobs,
                'completed': completed_jobs,
                'failed': failed_jobs,
                'queued': len(self.job_queue)
            },
            'clusters': {
                'total': len(self.clusters),
                'available': len([c for c in self.clusters.values() if c.status == ClusterStatus.AVAILABLE]),
                'busy': len([c for c in self.clusters.values() if c.status == ClusterStatus.BUSY])
            },
            'gpus': {
                'total': total_gpus,
                'available': available_gpus,
                'utilized': total_gpus - available_gpus
            }
        }


class TrainingControlPlane:
    """High-level training control plane"""

    def __init__(self):
        self.controller = TrainingController()
        self.scheduler_task = None

    def initialize(self):
        """Initialize control plane"""
        # Register default clusters (placeholder)
        self.controller.register_cluster(
            cluster_id="cluster-1",
            name="Primary Training Cluster",
            total_gpus=64,
            gpu_type="A100",
            gpu_memory_gb=80,
            location="us-east-1"
        )
        
        logger.info("Training control plane initialized")

    async def start(self):
        """Start control plane"""
        self.scheduler_task = asyncio.create_task(self.controller.run_scheduler())
        logger.info("Training control plane started")

    async def stop(self):
        """Stop control plane"""
        self.controller.stop_scheduler()
        if self.scheduler_task:
            self.scheduler_task.cancel()
        logger.info("Training control plane stopped")

    def submit_training_job(
        self,
        name: str,
        model_config: Dict,
        dataset_id: str,
        cluster_id: str,
        priority: int = 5
    ) -> str:
        """Submit a new training job"""
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        self.controller.create_job(
            job_id=job_id,
            name=name,
            model_config=model_config,
            dataset_id=dataset_id,
            cluster_id=cluster_id,
            priority=priority
        )
        
        return job_id

    def get_dashboard_data(self) -> Dict:
        """Get data for admin dashboard"""
        return {
            'system_status': self.controller.get_system_status(),
            'jobs': self.controller.list_jobs(),
            'clusters': self.controller.list_clusters()
        }


def main():
    """Example usage"""
    control_plane = TrainingControlPlane()
    control_plane.initialize()
    
    # Submit a job
    job_id = control_plane.submit_training_job(
        name="Fivoria-100B Pretraining",
        model_config={
            'layers': 80,
            'hidden_dim': 12288,
            'world_size': 64
        },
        dataset_id="fivoria-corpus-v1",
        cluster_id="cluster-1",
        priority=10
    )
    
    print(f"Submitted job: {job_id}")
    print(f"System status: {control_plane.get_dashboard_data()}")


if __name__ == "__main__":
    main()
