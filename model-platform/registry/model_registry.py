"""
Fivoria AI Model Registry
Model versioning and lifecycle management
"""

import json
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import os


class ModelStatus(Enum):
    """Model lifecycle status"""
    DEVELOPMENT = "development"
    TRAINING = "training"
    EVALUATION = "evaluation"
    APPROVED = "approved"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"


class ModelArchitecture(Enum):
    """Model architecture types"""
    DENSE_TRANSFORMER = "dense_transformer"
    MOE_TRANSFORMER = "moe_transformer"
    HYBRID = "hybrid"


@dataclass
class ModelConfig:
    """Model configuration"""
    num_layers: int
    hidden_dim: int
    num_attention_heads: int
    num_kv_heads: int
    ffn_dim: int
    vocab_size: int
    max_seq_len: int
    architecture: ModelArchitecture
    num_experts: Optional[int] = None
    top_k_experts: Optional[int] = None


@dataclass
class ModelVersion:
    """Model version metadata"""
    id: str
    model_id: str
    version: str
    config: ModelConfig
    parameter_count: int
    tokenizer_version: str
    dataset_version: str
    training_run_id: str
    checkpoint_path: str
    status: ModelStatus
    evaluation_scores: Dict[str, float]
    safety_score: float
    created_at: datetime
    updated_at: datetime
    deployment_id: Optional[str] = None


@dataclass
class TrainingRun:
    """Training run metadata"""
    id: str
    model_version_id: str
    dataset_version_id: str
    gpu_cluster_id: str
    config: Dict[str, Any]
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    training_steps: int
    consumed_tokens: int
    final_loss: float
    checkpoint_path: str
    git_commit: str


class ModelRegistry:
    """
    Central model registry for versioning and lifecycle management
    """
    
    def __init__(self, storage_path: str = "./model_registry"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        
        self.models: Dict[str, Dict] = {}
        self.versions: Dict[str, ModelVersion] = {}
        self.training_runs: Dict[str, TrainingRun] = {}
        
        self._load_from_disk()
    
    def register_model(
        self,
        model_id: str,
        name: str,
        description: str,
        architecture: ModelArchitecture
    ) -> Dict:
        """Register a new model"""
        model = {
            "id": model_id,
            "name": name,
            "description": description,
            "architecture": architecture.value,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        self.models[model_id] = model
        self._save_to_disk()
        
        return model
    
    def register_version(
        self,
        model_id: str,
        version: str,
        config: ModelConfig,
        parameter_count: int,
        tokenizer_version: str,
        dataset_version: str,
        training_run_id: str,
        checkpoint_path: str
    ) -> ModelVersion:
        """Register a new model version"""
        version_id = f"{model_id}-{version}"
        
        model_version = ModelVersion(
            id=version_id,
            model_id=model_id,
            version=version,
            config=config,
            parameter_count=parameter_count,
            tokenizer_version=tokenizer_version,
            dataset_version=dataset_version,
            training_run_id=training_run_id,
            checkpoint_path=checkpoint_path,
            status=ModelStatus.DEVELOPMENT,
            evaluation_scores={},
            safety_score=0.0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.versions[version_id] = model_version
        self._save_to_disk()
        
        return model_version
    
    def register_training_run(
        self,
        model_version_id: str,
        dataset_version_id: str,
        gpu_cluster_id: str,
        config: Dict[str, Any],
        git_commit: str
    ) -> TrainingRun:
        """Register a training run"""
        run_id = f"train-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        training_run = TrainingRun(
            id=run_id,
            model_version_id=model_version_id,
            dataset_version_id=dataset_version_id,
            gpu_cluster_id=gpu_cluster_id,
            config=config,
            status="running",
            start_time=datetime.utcnow(),
            end_time=None,
            training_steps=0,
            consumed_tokens=0,
            final_loss=0.0,
            checkpoint_path="",
            git_commit=git_commit
        )
        
        self.training_runs[run_id] = training_run
        self._save_to_disk()
        
        return training_run
    
    def update_training_run(
        self,
        run_id: str,
        status: Optional[str] = None,
        training_steps: Optional[int] = None,
        consumed_tokens: Optional[int] = None,
        final_loss: Optional[float] = None,
        checkpoint_path: Optional[str] = None,
        end_time: Optional[datetime] = None
    ):
        """Update training run"""
        if run_id not in self.training_runs:
            raise ValueError(f"Training run {run_id} not found")
        
        run = self.training_runs[run_id]
        
        if status is not None:
            run.status = status
        if training_steps is not None:
            run.training_steps = training_steps
        if consumed_tokens is not None:
            run.consumed_tokens = consumed_tokens
        if final_loss is not None:
            run.final_loss = final_loss
        if checkpoint_path is not None:
            run.checkpoint_path = checkpoint_path
        if end_time is not None:
            run.end_time = end_time
        
        self._save_to_disk()
    
    def update_version_status(
        self,
        version_id: str,
        status: ModelStatus,
        evaluation_scores: Optional[Dict[str, float]] = None,
        safety_score: Optional[float] = None,
        deployment_id: Optional[str] = None
    ):
        """Update model version status"""
        if version_id not in self.versions:
            raise ValueError(f"Version {version_id} not found")
        
        version = self.versions[version_id]
        version.status = status
        version.updated_at = datetime.utcnow()
        
        if evaluation_scores is not None:
            version.evaluation_scores = evaluation_scores
        if safety_score is not None:
            version.safety_score = safety_score
        if deployment_id is not None:
            version.deployment_id = deployment_id
        
        self._save_to_disk()
    
    def get_model(self, model_id: str) -> Optional[Dict]:
        """Get model by ID"""
        return self.models.get(model_id)
    
    def get_version(self, version_id: str) -> Optional[ModelVersion]:
        """Get version by ID"""
        return self.versions.get(version_id)
    
    def get_versions(self, model_id: str) -> List[ModelVersion]:
        """Get all versions for a model"""
        return [
            v for v in self.versions.values()
            if v.model_id == model_id
        ]
    
    def get_latest_version(self, model_id: str, status: Optional[ModelStatus] = None) -> Optional[ModelVersion]:
        """Get latest version for a model"""
        versions = self.get_versions(model_id)
        
        if status is not None:
            versions = [v for v in versions if v.status == status]
        
        if not versions:
            return None
        
        return max(versions, key=lambda v: v.created_at)
    
    def get_production_version(self, model_id: str) -> Optional[ModelVersion]:
        """Get production version for a model"""
        return self.get_latest_version(model_id, ModelStatus.PRODUCTION)
    
    def get_training_run(self, run_id: str) -> Optional[TrainingRun]:
        """Get training run by ID"""
        return self.training_runs.get(run_id)
    
    def list_models(self) -> List[Dict]:
        """List all models"""
        return list(self.models.values())
    
    def list_versions(self, status: Optional[ModelStatus] = None) -> List[ModelVersion]:
        """List all versions"""
        versions = list(self.versions.values())
        
        if status is not None:
            versions = [v for v in versions if v.status == status]
        
        return versions
    
    def promote_to_staging(self, version_id: str):
        """Promote version to staging"""
        self.update_version_status(version_id, ModelStatus.STAGING)
    
    def promote_to_production(self, version_id: str):
        """Promote version to production"""
        # Demote current production version
        model_id = self.versions[version_id].model_id
        current_prod = self.get_production_version(model_id)
        if current_prod:
            self.update_version_status(current_prod.id, ModelStatus.STAGING)
        
        # Promote new version
        self.update_version_status(version_id, ModelStatus.PRODUCTION)
    
    def deprecate_version(self, version_id: str):
        """Deprecate a version"""
        self.update_version_status(version_id, ModelStatus.DEPRECATED)
    
    def calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def verify_checkpoint(self, checkpoint_path: str, expected_checksum: str) -> bool:
        """Verify checkpoint integrity"""
        actual_checksum = self.calculate_checksum(checkpoint_path)
        return actual_checksum == expected_checksum
    
    def _save_to_disk(self):
        """Save registry to disk"""
        # Save models
        with open(os.path.join(self.storage_path, "models.json"), "w") as f:
            json.dump(self.models, f, indent=2, default=str)
        
        # Save versions
        with open(os.path.join(self.storage_path, "versions.json"), "w") as f:
            versions_data = {}
            for vid, version in self.versions.items():
                versions_data[vid] = {
                    **asdict(version),
                    "config": asdict(version.config),
                    "status": version.status.value
                }
            json.dump(versions_data, f, indent=2, default=str)
        
        # Save training runs
        with open(os.path.join(self.storage_path, "training_runs.json"), "w") as f:
            runs_data = {}
            for rid, run in self.training_runs.items():
                runs_data[rid] = asdict(run)
            json.dump(runs_data, f, indent=2, default=str)
    
    def _load_from_disk(self):
        """Load registry from disk"""
        # Load models
        models_path = os.path.join(self.storage_path, "models.json")
        if os.path.exists(models_path):
            with open(models_path, "r") as f:
                self.models = json.load(f)
        
        # Load versions
        versions_path = os.path.join(self.storage_path, "versions.json")
        if os.path.exists(versions_path):
            with open(versions_path, "r") as f:
                versions_data = json.load(f)
                for vid, vdata in versions_data.items():
                    config = ModelConfig(**vdata["config"])
                    vdata["config"] = config
                    vdata["status"] = ModelStatus(vdata["status"])
                    vdata["created_at"] = datetime.fromisoformat(vdata["created_at"])
                    vdata["updated_at"] = datetime.fromisoformat(vdata["updated_at"])
                    self.versions[vid] = ModelVersion(**vdata)
        
        # Load training runs
        runs_path = os.path.join(self.storage_path, "training_runs.json")
        if os.path.exists(runs_path):
            with open(runs_path, "r") as f:
                runs_data = json.load(f)
                for rid, rdata in runs_data.items():
                    rdata["start_time"] = datetime.fromisoformat(rdata["start_time"])
                    if rdata["end_time"]:
                        rdata["end_time"] = datetime.fromisoformat(rdata["end_time"])
                    self.training_runs[rid] = TrainingRun(**rdata)


if __name__ == "__main__":
    # Demo: Model registry
    registry = ModelRegistry()
    
    # Register model
    model = registry.register_model(
        model_id="fivoria-100b",
        name="Fivoria 100B",
        description="100B parameter foundation model",
        architecture=ModelArchitecture.DENSE_TRANSFORMER
    )
    
    print(f"Registered model: {model['name']}")
    
    # Register version
    config = ModelConfig(
        num_layers=96,
        hidden_dim=12288,
        num_attention_heads=96,
        num_kv_heads=8,
        ffn_dim=49152,
        vocab_size=100000,
        max_seq_len=32768,
        architecture=ModelArchitecture.DENSE_TRANSFORMER
    )
    
    version = registry.register_version(
        model_id="fivoria-100b",
        version="v1.0",
        config=config,
        parameter_count=100_000_000_000,
        tokenizer_version="v1.0",
        dataset_version="corpus-v1.0",
        training_run_id="train-20240101-000000",
        checkpoint_path="/checkpoints/fivoria-100b-v1.0"
    )
    
    print(f"Registered version: {version.id}")
    
    # Register training run
    training_run = registry.register_training_run(
        model_version_id=version.id,
        dataset_version_id="corpus-v1.0",
        gpu_cluster_id="cluster-1",
        config={"batch_size": 4, "learning_rate": 0.0001},
        git_commit="abc123def456"
    )
    
    print(f"Registered training run: {training_run.id}")
    
    # Update training run
    registry.update_training_run(
        training_run.id,
        status="completed",
        training_steps=100000,
        consumed_tokens=100_000_000_000,
        final_loss=1.5
    )
    
    # Update version with evaluation scores
    registry.update_version_status(
        version.id,
        ModelStatus.APPROVED,
        evaluation_scores={"MMLU": 0.75, "GSM8K": 0.65},
        safety_score=0.95
    )
    
    # Promote to production
    registry.promote_to_production(version.id)
    
    print(f"Production version: {registry.get_production_version('fivoria-100b').id}")
