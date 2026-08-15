"""
Fivoria AI Document Processor Worker
Processes uploaded documents for RAG/knowledge engine
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from celery import Celery
from knowledge_layer.rag.rag_engine import RAGEngine
from knowledge_layer.memory.memory_system import MemorySystem
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Celery app
celery_app = Celery(
    'document_processor',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

rag_engine = RAGEngine()
memory_system = MemorySystem()

@celery_app.task(bind=True)
def process_document(self, document_id: str, file_path: str, user_id: int, project_id: str = None):
    """Process document for RAG"""
    try:
        logger.info(f"Processing document {document_id} for user {user_id}")
        
        # Extract content from document
        content = extract_document_content(file_path)
        
        # Chunk the content
        chunks = chunk_content(content)
        
        # Generate embeddings for each chunk
        for i, chunk in enumerate(chunks):
            embedding = rag_engine.generate_embedding(chunk)
            
            # Store in vector database
            rag_engine.add_document(
                document_id=f"{document_id}-chunk-{i}",
                content=chunk,
                embedding=embedding,
                metadata={
                    "user_id": user_id,
                    "project_id": project_id,
                    "chunk_index": i,
                    "source_document": document_id
                }
            )
            
            # Also store in memory system
            memory_system.add_semantic_memory(
                user_id=user_id,
                content=chunk,
                embedding=embedding
            )
        
        logger.info(f"Successfully processed document {document_id}")
        return {"status": "success", "chunks_processed": len(chunks)}
        
    except Exception as e:
        logger.error(f"Failed to process document {document_id}: {str(e)}")
        self.retry(exc=e, countdown=60, max_retries=3)
        return {"status": "failed", "error": str(e)}

def extract_document_content(file_path: str) -> str:
    """Extract text content from document"""
    # TODO: Implement based on file type (PDF, DOCX, TXT, etc.)
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def chunk_content(content: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Chunk content into overlapping segments"""
    chunks = []
    start = 0
    
    while start < len(content):
        end = start + chunk_size
        chunk = content[start:end]
        chunks.append(chunk)
        start = end - overlap
    
    return chunks

if __name__ == "__main__":
    celery_app.start()
