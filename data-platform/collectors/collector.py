"""
Data Collector Module
Collects data from various sources with provenance tracking
"""

import asyncio
import aiohttp
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Types of data sources"""
    WEBSITE = "website"
    DATASET = "dataset"
    BOOK = "book"
    CODE_REPOSITORY = "code_repository"
    SCIENTIFIC_PAPER = "scientific_paper"
    DOCUMENT = "document"
    API = "api"
    CUSTOM = "custom"


class LicenseType(Enum):
    """License types for data sources"""
    PUBLIC_DOMAIN = "public_domain"
    MIT = "mit"
    APACHE_2_0 = "apache_2_0"
    GPL_3_0 = "gpl_3_0"
    CC_BY = "cc_by"
    CC_BY_SA = "cc_by_sa"
    CC_BY_NC = "cc_by_nc"
    CC0 = "cc0"
    COMMERCIAL_LICENSE = "commercial_license"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


@dataclass
class DataSource:
    """Data source metadata"""
    source_id: str
    source_type: DataSourceType
    url: Optional[str]
    provider: str
    license_type: LicenseType
    license_url: Optional[str]
    acquisition_date: datetime
    permission_status: str  # "allowed", "pending", "denied"
    allowed_uses: List[str]
    restrictions: List[str]
    jurisdiction: Optional[str]
    checksum: str
    version: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['source_type'] = self.source_type.value
        data['license_type'] = self.license_type.value
        data['acquisition_date'] = self.acquisition_date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'DataSource':
        """Create from dictionary"""
        data['source_type'] = DataSourceType(data['source_type'])
        data['license_type'] = LicenseType(data['license_type'])
        data['acquisition_date'] = datetime.fromisoformat(data['acquisition_date'])
        return cls(**data)


class BaseCollector:
    """Base class for data collectors"""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def collect(self, source: DataSource) -> Path:
        """Collect data from source"""
        raise NotImplementedError

    def _calculate_checksum(self, data: bytes) -> str:
        """Calculate SHA256 checksum"""
        return hashlib.sha256(data).hexdigest()

    def _save_raw_data(self, source_id: str, data: bytes, extension: str = ".raw") -> Path:
        """Save raw data to storage"""
        filename = f"{source_id}{extension}"
        filepath = self.storage_path / filename
        filepath.write_bytes(data)
        return filepath


class WebCollector(BaseCollector):
    """Collector for web data"""

    def __init__(self, storage_path: Path, user_agent: str = "Fivoria-DataCollector/1.0"):
        super().__init__(storage_path)
        self.user_agent = user_agent
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            headers = {"User-Agent": self.user_agent}
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def collect(self, source: DataSource) -> Path:
        """Collect data from URL"""
        if not source.url:
            raise ValueError("URL is required for web collection")

        session = await self._get_session()

        try:
            async with session.get(source.url, timeout=aiohttp.ClientTimeout(total=300)) as response:
                response.raise_for_status()
                data = await response.read()

                # Verify checksum if provided
                if source.checksum:
                    calculated_checksum = self._calculate_checksum(data)
                    if calculated_checksum != source.checksum:
                        logger.warning(f"Checksum mismatch for {source.source_id}")

                return self._save_raw_data(source.source_id, data, ".html")

        except Exception as e:
            logger.error(f"Failed to collect from {source.url}: {e}")
            raise

    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()


class DatasetCollector(BaseCollector):
    """Collector for datasets"""

    async def collect(self, source: DataSource) -> Path:
        """Collect dataset from source"""
        # Implementation depends on dataset format
        # This is a placeholder for various dataset formats
        if source.url:
            # Download from URL
            web_collector = WebCollector(self.storage_path)
            return await web_collector.collect(source)
        else:
            # Local dataset
            raise NotImplementedError("Local dataset collection not implemented")


class CodeRepositoryCollector(BaseCollector):
    """Collector for code repositories"""

    async def collect(self, source: DataSource) -> Path:
        """Collect code repository"""
        # This would integrate with git or similar
        # Placeholder implementation
        raise NotImplementedError("Git-based collection not implemented")


class CollectorRegistry:
    """Registry for data collectors"""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.collectors: Dict[DataSourceType, BaseCollector] = {}
        self._register_default_collectors()

    def _register_default_collectors(self):
        """Register default collectors"""
        self.collectors[DataSourceType.WEBSITE] = WebCollector(self.storage_path / "web")
        self.collectors[DataSourceType.DATASET] = DatasetCollector(self.storage_path / "datasets")
        self.collectors[DataSourceType.CODE_REPOSITORY] = CodeRepositoryCollector(self.storage_path / "code")

    def register_collector(self, source_type: DataSourceType, collector: BaseCollector):
        """Register a custom collector"""
        self.collectors[source_type] = collector

    def get_collector(self, source_type: DataSourceType) -> BaseCollector:
        """Get collector for source type"""
        if source_type not in self.collectors:
            raise ValueError(f"No collector registered for {source_type}")
        return self.collectors[source_type]

    async def collect(self, source: DataSource) -> Path:
        """Collect data using appropriate collector"""
        collector = self.get_collector(source.source_type)
        return await collector.collect(source)

    async def collect_batch(self, sources: List[DataSource]) -> Dict[str, Path]:
        """Collect multiple sources in parallel"""
        tasks = [self.collect(source) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for source, result in zip(sources, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to collect {source.source_id}: {result}")
                output[source.source_id] = None
            else:
                output[source.source_id] = result

        return output

    async def cleanup(self):
        """Cleanup resources"""
        for collector in self.collectors.values():
            if hasattr(collector, 'close'):
                await collector.close()


async def main():
    """Example usage"""
    storage_path = Path("./data/raw")
    registry = CollectorRegistry(storage_path)

    # Example source
    source = DataSource(
        source_id="example-001",
        source_type=DataSourceType.WEBSITE,
        url="https://example.com",
        provider="Example Provider",
        license_type=LicenseType.CC_BY,
        license_url="https://creativecommons.org/licenses/by/4.0/",
        acquisition_date=datetime.now(),
        permission_status="allowed",
        allowed_uses=["training", "research"],
        restrictions=["commercial"],
        jurisdiction="US",
        checksum="",
        version="1.0",
        metadata={"description": "Example data source"}
    )

    try:
        filepath = await registry.collect(source)
        print(f"Collected data to: {filepath}")
    finally:
        await registry.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
