"""
Dataset Registry Module
Manages dataset versioning, provenance, and metadata
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DatasetStatus(Enum):
    """Dataset lifecycle status"""
    CREATING = "creating"
    READY = "ready"
    VALIDATING = "validating"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class DatasetType(Enum):
    """Types of datasets"""
    PRETRAINING = "pretraining"
    INSTRUCTION_TUNING = "instruction_tuning"
    PREFERENCE = "preference"
    SAFETY = "safety"
    REASONING = "reasoning"
    CODING = "coding"
    MATH = "math"
    MULTILINGUAL = "multilingual"
    EVALUATION = "evaluation"
    CUSTOM = "custom"


@dataclass
class DatasetVersion:
    """Dataset version metadata"""
    dataset_id: str
    version: str
    name: str
    description: str
    dataset_type: DatasetType
    status: DatasetStatus
    created_at: datetime
    created_by: str
    parent_version: Optional[str]
    sources: List[str]  # Source IDs
    total_documents: int
    total_tokens: int
    total_size_bytes: int
    checksum: str
    languages: List[str]
    license_compliance: str
    safety_score: float
    quality_score: float
    metadata: Dict[str, Any]
    storage_path: str
    sharding_info: Dict[str, Any]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['dataset_type'] = self.dataset_type.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'DatasetVersion':
        """Create from dictionary"""
        data['dataset_type'] = DatasetType(data['dataset_type'])
        data['status'] = DatasetStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


class DatasetRegistry:
    """Registry for managing datasets"""

    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self.registry_path.mkdir(parents=True, exist_ok=True)
        self.datasets_file = self.registry_path / "datasets.json"
        self.datasets: Dict[str, Dict[str, DatasetVersion]] = {}
        self._load()

    def _load(self):
        """Load datasets from storage"""
        if self.datasets_file.exists():
            with open(self.datasets_file, 'r') as f:
                data = json.load(f)
                for dataset_id, versions in data.items():
                    self.datasets[dataset_id] = {}
                    for version_str, version_data in versions.items():
                        self.datasets[dataset_id][version_str] = DatasetVersion.from_dict(version_data)

    def _save(self):
        """Save datasets to storage"""
        data = {}
        for dataset_id, versions in self.datasets.items():
            data[dataset_id] = {}
            for version_str, version in versions.items():
                data[dataset_id][version_str] = version.to_dict()
        
        with open(self.datasets_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _calculate_checksum(self, filepath: Path) -> str:
        """Calculate checksum of dataset files"""
        hash_sha256 = hashlib.sha256()
        
        if filepath.is_file():
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
        elif filepath.is_dir():
            for file_path in sorted(filepath.rglob('*')):
                if file_path.is_file():
                    with open(file_path, 'rb') as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()

    def create_dataset(
        self,
        dataset_id: str,
        name: str,
        description: str,
        dataset_type: DatasetType,
        created_by: str,
        storage_path: str,
        sources: List[str] = None,
        parent_version: str = None,
        metadata: Dict = None
    ) -> DatasetVersion:
        """Create a new dataset version"""
        if dataset_id not in self.datasets:
            self.datasets[dataset_id] = {}
        
        # Generate version number
        existing_versions = list(self.datasets[dataset_id].keys())
        if not existing_versions:
            version = "1.0.0"
        else:
            # Simple increment - in production use semantic versioning
            last_version = existing_versions[-1]
            parts = last_version.split('.')
            parts[-1] = str(int(parts[-1]) + 1)
            version = '.'.join(parts)
        
        # Calculate checksum
        storage = Path(storage_path)
        checksum = self._calculate_checksum(storage)
        
        # Count documents and estimate tokens (placeholder)
        total_documents = 0
        total_tokens = 0
        total_size = 0
        
        if storage.exists():
            if storage.is_file():
                total_size = storage.stat().st_size
                total_documents = 1
                # Rough token estimate: 4 chars per token
                total_tokens = total_size // 4
            elif storage.is_dir():
                for file_path in storage.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                        total_documents += 1
                total_tokens = total_size // 4
        
        dataset = DatasetVersion(
            dataset_id=dataset_id,
            version=version,
            name=name,
            description=description,
            dataset_type=dataset_type,
            status=DatasetStatus.CREATING,
            created_at=datetime.now(),
            created_by=created_by,
            parent_version=parent_version,
            sources=sources or [],
            total_documents=total_documents,
            total_tokens=total_tokens,
            total_size_bytes=total_size,
            checksum=checksum,
            languages=[],
            license_compliance="pending",
            safety_score=0.0,
            quality_score=0.0,
            metadata=metadata or {},
            storage_path=storage_path,
            sharding_info={}
        )
        
        self.datasets[dataset_id][version] = dataset
        self._save()
        
        return dataset

    def get_dataset(self, dataset_id: str, version: str = None) -> Optional[DatasetVersion]:
        """Get dataset by ID and version"""
        if dataset_id not in self.datasets:
            return None
        
        if version is None:
            # Return latest version
            versions = list(self.datasets[dataset_id].keys())
            if not versions:
                return None
            version = versions[-1]
        
        return self.datasets[dataset_id].get(version)

    def update_dataset(
        self,
        dataset_id: str,
        version: str,
        **updates
    ) -> Optional[DatasetVersion]:
        """Update dataset metadata"""
        dataset = self.get_dataset(dataset_id, version)
        if not dataset:
            return None
        
        for key, value in updates.items():
            if hasattr(dataset, key):
                setattr(dataset, key, value)
        
        self._save()
        return dataset

    def set_status(self, dataset_id: str, version: str, status: DatasetStatus) -> bool:
        """Set dataset status"""
        dataset = self.get_dataset(dataset_id, version)
        if not dataset:
            return False
        
        dataset.status = status
        self._save()
        return True

    def list_datasets(self, dataset_type: DatasetType = None, status: DatasetStatus = None) -> List[DatasetVersion]:
        """List datasets with optional filters"""
        results = []
        
        for dataset_id, versions in self.datasets.items():
            for version, dataset in versions.items():
                if dataset_type and dataset.dataset_type != dataset_type:
                    continue
                if status and dataset.status != status:
                    continue
                results.append(dataset)
        
        return results

    def get_lineage(self, dataset_id: str, version: str) -> List[DatasetVersion]:
        """Get dataset lineage (parent versions)"""
        lineage = []
        current = self.get_dataset(dataset_id, version)
        
        while current and current.parent_version:
            lineage.append(current)
            parent_dataset_id, parent_version = self._parse_version_reference(current.parent_version)
            current = self.get_dataset(parent_dataset_id, parent_version)
        
        if current:
            lineage.append(current)
        
        return list(reversed(lineage))

    def _parse_version_reference(self, reference: str) -> tuple[str, str]:
        """Parse version reference string"""
        if ':' in reference:
            return reference.split(':', 1)
        return reference, None

    def delete_dataset(self, dataset_id: str, version: str = None) -> bool:
        """Delete dataset version"""
        if dataset_id not in self.datasets:
            return False
        
        if version:
            if version in self.datasets[dataset_id]:
                del self.datasets[dataset_id][version]
                self._save()
                return True
            return False
        else:
            del self.datasets[dataset_id]
            self._save()
            return True

    def search(self, query: str) -> List[DatasetVersion]:
        """Search datasets by name or description"""
        results = []
        query_lower = query.lower()
        
        for dataset_id, versions in self.datasets.items():
            for version, dataset in versions.items():
                if (query_lower in dataset.name.lower() or 
                    query_lower in dataset.description.lower()):
                    results.append(dataset)
        
        return results

    def get_statistics(self) -> Dict:
        """Get registry statistics"""
        total_datasets = len(self.datasets)
        total_versions = sum(len(versions) for versions in self.datasets.values())
        
        status_counts = {}
        type_counts = {}
        
        for dataset_id, versions in self.datasets.items():
            for version, dataset in versions.items():
                status_counts[dataset.status.value] = status_counts.get(dataset.status.value, 0) + 1
                type_counts[dataset.dataset_type.value] = type_counts.get(dataset.dataset_type.value, 0) + 1
        
        return {
            'total_datasets': total_datasets,
            'total_versions': total_versions,
            'status_distribution': status_counts,
            'type_distribution': type_counts
        }


def main():
    """Example usage"""
    registry = DatasetRegistry(Path("./data/registry"))
    
    # Create a dataset
    dataset = registry.create_dataset(
        dataset_id="fivoria-pretrain-v1",
        name="Fivoria Pretraining Dataset v1",
        description="Initial pretraining dataset for Fivoria AI",
        dataset_type=DatasetType.PRETRAINING,
        created_by="system",
        storage_path="./data/datasets/pretrain-v1",
        sources=["source-001", "source-002"]
    )
    
    print(f"Created dataset: {dataset.dataset_id} v{dataset.version}")
    
    # Update status
    registry.set_status("fivoria-pretrain-v1", "1.0.0", DatasetStatus.READY)
    
    # Get statistics
    stats = registry.get_statistics()
    print(f"Registry stats: {stats}")


if __name__ == "__main__":
    main()
