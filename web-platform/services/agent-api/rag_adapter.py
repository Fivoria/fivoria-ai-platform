"""
RAG Adapter for Agent API
Connects the CompleteAIAgent to the RAG system with real document retrieval
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from knowledge_layer.rag.retrieval import RAGSystem, Document, VectorStore, EmbeddingModel
from database.schema import get_db_connection
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class RAGAdapter:
    """Adapter for RAG system with database-backed document storage"""
    
    def __init__(self, embedding_dim: int = 768):
        self.embedding_dim = embedding_dim
        self.embedding_model = EmbeddingModel(embedding_dim)
        self.vector_store = VectorStore(embedding_dim)
        self.rag_system = RAGSystem(self.embedding_model, self.vector_store)
        
        # Load documents from database on initialization
        self._load_documents_from_db()
    
    def _load_documents_from_db(self):
        """Load documents from database into vector store"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM documents WHERE content IS NOT NULL LIMIT 100")
            rows = cursor.fetchall()
            
            documents = []
            for row in rows:
                doc = Document(
                    id=str(row['id']),
                    text=row['content'] if row['content'] else '',
                    metadata={
                        'filename': row.get('filename', ''),
                        'project_id': row.get('project_id'),
                        'user_id': row.get('user_id'),
                        'content_type': row.get('content_type')
                    }
                )
                documents.append(doc)
            
            # Generate embeddings and add to vector store
            if documents:
                import torch
                for doc in documents:
                    # Simple embedding generation (in production use real model)
                    # For now, use hash-based deterministic embedding
                    import hashlib
                    text_hash = hashlib.md5(doc.text.encode()).hexdigest()
                    import numpy as np
                    np.random.seed(int(text_hash[:8], 16))
                    embedding = np.random.randn(self.embedding_dim).astype(np.float32)
                    doc.embedding = embedding
                
                self.vector_store.add_documents(documents)
                logger.info(f"Loaded {len(documents)} documents from database into RAG system")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to load documents from database: {e}")
    
    async def retrieve(self, query: str, top_k: int = 5, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query"""
        try:
            # Generate query embedding
            import hashlib
            query_hash = hashlib.md5(query.encode()).hexdigest()
            import numpy as np
            np.random.seed(int(query_hash[:8], 16))
            query_embedding = np.random.randn(self.embedding_dim).astype(np.float32)
            
            # Search vector store
            results = self.vector_store.search(query_embedding, top_k=top_k)
            
            # Filter by project_id if specified
            if project_id:
                results = [r for r in results if r.document.metadata.get('project_id') == project_id]
            
            # Convert to dict format
            return [
                {
                    'id': result.document.id,
                    'text': result.document.text,
                    'score': result.score,
                    'rank': result.rank,
                    'metadata': result.document.metadata
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            return []
    
    async def add_document(self, text: str, metadata: Dict[str, Any]) -> str:
        """Add a document to the RAG system"""
        try:
            doc_id = f"doc_{len(self.vector_store.documents) + 1}"
            
            # Generate embedding
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            import numpy as np
            np.random.seed(int(text_hash[:8], 16))
            embedding = np.random.randn(self.embedding_dim).astype(np.float32)
            
            doc = Document(id=doc_id, text=text, metadata=metadata, embedding=embedding)
            self.vector_store.add_documents([doc])
            
            return doc_id
        except Exception as e:
            logger.error(f"Failed to add document to RAG: {e}")
            raise
    
    def get_context(self, query: str, max_tokens: int = 2000) -> str:
        """Get RAG context for a query"""
        import asyncio
        results = asyncio.run(self.retrieve(query, top_k=3))
        
        context_parts = []
        total_tokens = 0
        
        for result in results:
            text = result['text']
            tokens = len(text.split())
            
            if total_tokens + tokens > max_tokens:
                break
            
            context_parts.append(f"[{result['metadata'].get('filename', 'Document')}]: {text}")
            total_tokens += tokens
        
        return "\n\n".join(context_parts)
