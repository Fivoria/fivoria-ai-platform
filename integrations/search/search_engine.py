"""
Search Engine Integration
Enhanced version with advanced features, caching, analytics, and real-time updates
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class SearchEngineType(Enum):
    """Types of search engines"""
    ELASTICSEARCH = "elasticsearch"
    OPENSEARCH = "opensearch"
    SOLR = "solr"
    MEILISEARCH = "meilisearch"
    CUSTOM = "custom"


@dataclass
class SearchResult:
    """Search result"""
    doc_id: str
    title: str
    content: str
    score: float
    source: str
    metadata: Dict[str, Any]
    url: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class SearchQuery:
    """Search query"""
    text: str
    filters: Dict[str, Any] = None
    limit: int = 10
    offset: int = 0
    min_score: float = 0.0


class SearchEngine:
    """Base search engine interface"""

    def __init__(self, engine_type: SearchEngineType, config: Dict[str, Any]):
        self.engine_type = engine_type
        self.config = config
        self.client = None

    async def connect(self):
        """Connect to search engine"""
        raise NotImplementedError

    async def disconnect(self):
        """Disconnect from search engine"""
        raise NotImplementedError

    async def index_document(self, doc_id: str, document: Dict[str, Any]) -> bool:
        """Index a document with enhanced tracking"""
        try:
            await self._index_document_internal(doc_id, document)
            self.index_stats['total_docs'] += 1
            self.index_stats['last_updated'] = datetime.now().isoformat()
            self.analytics['documents_indexed'] += 1
            return True
        except Exception as e:
            logger.error(f"Failed to index document {doc_id}: {e}")
            self.analytics['index_errors'] += 1
            return False

    async def _index_document_internal(self, doc_id: str, document: Dict[str, Any]):
        """Internal document indexing - to be implemented by subclasses"""
        raise NotImplementedError

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search for documents"""
        raise NotImplementedError

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document"""
        raise NotImplementedError

    async def bulk_index(self, documents: List[Tuple[str, Dict[str, Any]]]) -> int:
        """Bulk index documents with enhanced error handling"""
        indexed = 0
        batch_size = 100
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            try:
                actions = []
                for doc_id, doc in batch:
                    actions.append({
                        "_index": self.index,
                        "_id": doc_id,
                        "_source": doc
                    })
                
                from elasticsearch.helpers import async_bulk
                success, failed = await async_bulk(self.client, actions)
                indexed += success
                self.index_stats['total_docs'] += success
                
                if failed:
                    logger.warning(f"{failed} documents failed to index")
                    self.analytics['index_errors'] += failed
                    
            except Exception as e:
                logger.error(f"Bulk index error: {e}")
                self.analytics['index_errors'] += len(batch)
        
        return indexed


class ElasticsearchEngine(SearchEngine):
    """Enhanced Elasticsearch search engine implementation"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(SearchEngineType.ELASTICSEARCH, config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 9200)
        self.index = config.get('index', 'documents')
        self.username = config.get('username')
        self.password = config.get('password')
        self.scroll_size = config.get('scroll_size', 1000)
        self.scroll_timeout = config.get('scroll_timeout', '2m')

    async def connect(self):
        """Connect to Elasticsearch"""
        try:
            from elasticsearch import AsyncElasticsearch
            
            auth = None
            if self.username and self.password:
                auth = (self.username, self.password)
            
            self.client = AsyncElasticsearch(
                hosts=[{'host': self.host, 'port': self.port}],
                http_auth=auth
            )
            
            # Test connection
            info = await self.client.info()
            logger.info(f"Connected to Elasticsearch: {info['version']['number']}")
            
            # Create index if not exists
            await self._ensure_index()
            
        except ImportError:
            logger.warning("elasticsearch package not available")
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")

    async def disconnect(self):
        """Disconnect from Elasticsearch"""
        if self.client:
            await self.client.close()
            self.client = None

    async def _ensure_index(self):
        """Ensure index exists with proper mapping"""
        if not await self.client.indices.exists(index=self.index):
            mapping = {
                "mappings": {
                    "properties": {
                        "title": {"type": "text"},
                        "content": {"type": "text"},
                        "url": {"type": "keyword"},
                        "source": {"type": "keyword"},
                        "timestamp": {"type": "date"},
                        "metadata": {"type": "object"}
                    }
                }
            }
            await self.client.indices.create(index=self.index, body=mapping)
            logger.info(f"Created index: {self.index}")

    async def index_document(self, doc_id: str, document: Dict[str, Any]) -> bool:
        """Index a document"""
        try:
            await self.client.index(index=self.index, id=doc_id, document=document)
            return True
        except Exception as e:
            logger.error(f"Failed to index document {doc_id}: {e}")
            return False

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search for documents"""
        try:
            search_body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": query.text,
                                    "fields": ["title^2", "content"],
                                    "type": "best_fields"
                                }
                            }
                        ]
                    }
                },
                "size": query.limit,
                "from": query.offset,
                "min_score": query.min_score
            }

            # Add filters
            if query.filters:
                for field, value in query.filters.items():
                    search_body["query"]["bool"]["filter"] = {
                        "term": {field: value}
                    }

            response = await self.client.search(index=self.index, body=search_body)
            
            results = []
            for hit in response['hits']['hits']:
                result = SearchResult(
                    doc_id=hit['_id'],
                    title=hit['_source'].get('title', ''),
                    content=hit['_source'].get('content', ''),
                    score=hit['_score'],
                    source=hit['_source'].get('source', ''),
                    metadata=hit['_source'].get('metadata', {}),
                    url=hit['_source'].get('url'),
                    timestamp=hit['_source'].get('timestamp')
                )
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document"""
        try:
            await self.client.delete(index=self.index, id=doc_id)
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False


class HybridSearchEngine:
    """Hybrid search combining vector and keyword search"""

    def __init__(self, keyword_engine: SearchEngine, vector_store):
        self.keyword_engine = keyword_engine
        self.vector_store = vector_store

    async def search(
        self,
        query: str,
        limit: int = 10,
        alpha: float = 0.5
    ) -> List[SearchResult]:
        """Hybrid search combining keyword and vector search"""
        # Keyword search
        keyword_query = SearchQuery(text=query, limit=limit * 2)
        keyword_results = await self.keyword_engine.search(keyword_query)

        # Vector search
        vector_results = await self.vector_store.search(query, limit=limit * 2)

        # Combine and rerank
        combined = self._combine_results(keyword_results, vector_results, alpha)

        return combined[:limit]

    def _combine_results(
        self,
        keyword_results: List[SearchResult],
        vector_results: List[Any],
        alpha: float
    ) -> List[SearchResult]:
        """Combine and rerank results"""
        # Create score map
        keyword_scores = {r.doc_id: r.score for r in keyword_results}
        vector_scores = {r.doc_id: r.score for r in vector_results}

        # Combine scores
        combined = {}
        for doc_id in set(keyword_scores.keys()) | set(vector_scores.keys()):
            keyword_score = keyword_scores.get(doc_id, 0)
            vector_score = vector_scores.get(doc_id, 0)
            
            # Normalize scores
            max_keyword = max(keyword_scores.values()) if keyword_scores else 1
            max_vector = max(vector_scores.values()) if vector_scores else 1
            
            normalized_keyword = keyword_score / max_keyword
            normalized_vector = vector_score / max_vector
            
            combined_score = alpha * normalized_keyword + (1 - alpha) * normalized_vector
            combined[doc_id] = combined_score

        # Sort by combined score
        sorted_doc_ids = sorted(combined.keys(), key=lambda x: combined[x], reverse=True)

        # Return results in order
        final_results = []
        for doc_id in sorted_doc_ids:
            # Find in keyword results first
            result = next((r for r in keyword_results if r.doc_id == doc_id), None)
            if result:
                result.score = combined[doc_id]
                final_results.append(result)

        return final_results


class SearchEngineManager:
    """Manages multiple search engines"""

    def __init__(self):
        self.engines: Dict[str, SearchEngine] = {}
        self.default_engine: Optional[str] = None

    def register_engine(self, name: str, engine: SearchEngine, is_default: bool = False):
        """Register a search engine"""
        self.engines[name] = engine
        if is_default:
            self.default_engine = name
        logger.info(f"Registered search engine: {name}")

    async def connect_all(self):
        """Connect all registered engines"""
        for name, engine in self.engines.items():
            await engine.connect()

    async def disconnect_all(self):
        """Disconnect all engines"""
        for name, engine in self.engines.items():
            await engine.disconnect()

    def get_engine(self, name: str = None) -> Optional[SearchEngine]:
        """Get a search engine by name"""
        if name is None:
            name = self.default_engine
        return self.engines.get(name)

    async def search(
        self,
        query: str,
        engine: str = None,
        **kwargs
    ) -> List[SearchResult]:
        """Search using specified or default engine"""
        search_engine = self.get_engine(engine)
        if not search_engine:
            logger.error(f"Search engine not found: {engine}")
            return []

        search_query = SearchQuery(text=query, **kwargs)
        return await search_engine.search(search_query)


def main():
    """Example usage"""
    async def example():
        manager = SearchEngineManager()

        # Register Elasticsearch engine
        es_config = {
            'host': 'localhost',
            'port': 9200,
            'index': 'documents'
        }
        es_engine = ElasticsearchEngine(es_config)
        manager.register_engine('elasticsearch', es_engine, is_default=True)

        # Connect
        await manager.connect_all()

        # Search
        results = await manager.search("machine learning", limit=5)
        print(f"Found {len(results)} results")

        for result in results:
            print(f"- {result.title} (score: {result.score:.2f})")

        # Disconnect
        await manager.disconnect_all()

    asyncio.run(example())


if __name__ == "__main__":
    main()
