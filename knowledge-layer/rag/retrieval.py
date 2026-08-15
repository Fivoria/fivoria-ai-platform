"""
Fivoria AI RAG System
Retrieval-Augmented Generation implementation
"""

import torch
import torch.nn as nn
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class Document:
    """Document for RAG"""
    id: str
    text: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None


@dataclass
class RetrievalResult:
    """Result of retrieval"""
    document: Document
    score: float
    rank: int


class EmbeddingModel(nn.Module):
    """
    Embedding model for document and query encoding
    """
    
    def __init__(self, embedding_dim: int = 768):
        super().__init__()
        self.embedding_dim = embedding_dim
        # In production, this would be a trained embedding model
        # For demo, use a simple projection
        self.projection = nn.Linear(768, embedding_dim)
    
    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        """
        Generate embeddings
        
        Args:
            input_ids: Input token IDs [batch, seq_len]
        
        Returns:
            Embeddings [batch, embedding_dim]
        """
        # Simplified - in production would use actual embedding model
        batch_size, seq_len = input_ids.shape
        # Placeholder: random embeddings
        embeddings = torch.randn(batch_size, 768, device=input_ids.device)
        embeddings = self.projection(embeddings)
        
        # Mean pooling
        embeddings = embeddings.mean(dim=1)
        
        return embeddings


class VectorStore:
    """
    Vector database for storing and retrieving embeddings
    """
    
    def __init__(self, embedding_dim: int = 768):
        self.embedding_dim = embedding_dim
        self.documents: List[Document] = []
        self.embeddings: np.ndarray = np.zeros((0, embedding_dim))
    
    def add_documents(self, documents: List[Document]):
        """
        Add documents to the vector store
        
        Args:
            documents: List of documents with embeddings
        """
        for doc in documents:
            if doc.embedding is not None:
                self.documents.append(doc)
                if len(self.embeddings) == 0:
                    self.embeddings = doc.embedding.reshape(1, -1)
                else:
                    self.embeddings = np.vstack([self.embeddings, doc.embedding])
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        score_threshold: float = 0.0
    ) -> List[RetrievalResult]:
        """
        Search for similar documents
        
        Args:
            query_embedding: Query embedding
            top_k: Number of results to return
            score_threshold: Minimum score threshold
        
        Returns:
            List of retrieval results
        """
        if len(self.documents) == 0:
            return []
        
        # Calculate cosine similarity
        similarities = np.dot(self.embeddings, query_embedding)
        norms = np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        similarities = similarities / (norms + 1e-8)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Create results
        results = []
        for rank, idx in enumerate(top_indices):
            score = similarities[idx]
            if score >= score_threshold:
                results.append(RetrievalResult(
                    document=self.documents[idx],
                    score=float(score),
                    rank=rank + 1
                ))
        
        return results
    
    def delete_document(self, document_id: str):
        """Delete a document by ID"""
        self.documents = [doc for doc in self.documents if doc.id != document_id]
        # Rebuild embeddings (inefficient, for demo only)
        if self.documents:
            self.embeddings = np.vstack([doc.embedding for doc in self.documents if doc.embedding is not None])
        else:
            self.embeddings = np.zeros((0, self.embedding_dim))


class BM25Search:
    """
    BM25 keyword search for retrieval
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: List[Document] = []
        self.doc_freqs: Dict[str, int] = {}
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
    
    def add_documents(self, documents: List[Document]):
        """Add documents for BM25 indexing"""
        self.documents.extend(documents)
        
        # Calculate document frequencies
        for doc in documents:
            tokens = doc.text.lower().split()
            self.doc_lengths.append(len(tokens))
            
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1
        
        # Calculate average document length
        if self.doc_lengths:
            self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)
    
    def search(self, query: str, top_k: int = 10) -> List[RetrievalResult]:
        """
        Search using BM25
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of retrieval results
        """
        if not self.documents:
            return []
        
        query_tokens = query.lower().split()
        scores = []
        
        for idx, doc in enumerate(self.documents):
            doc_tokens = doc.text.lower().split()
            doc_length = len(doc_tokens)
            doc_token_counts = {}
            
            for token in doc_tokens:
                doc_token_counts[token] = doc_token_counts.get(token, 0) + 1
            
            score = 0.0
            for token in query_tokens:
                if token in doc_token_counts:
                    tf = doc_token_counts[token]
                    df = self.doc_freqs.get(token, 1)
                    idf = np.log((len(self.documents) - df + 0.5) / (df + 0.5) + 1.0)
                    
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
                    score += idf * (numerator / denominator)
            
            scores.append((idx, score))
        
        # Sort by score and get top-k
        scores.sort(key=lambda x: x[1], reverse=True)
        top_results = scores[:top_k]
        
        results = []
        for rank, (idx, score) in enumerate(top_results):
            results.append(RetrievalResult(
                document=self.documents[idx],
                score=float(score),
                rank=rank + 1
            ))
        
        return results


class HybridSearch:
    """
    Hybrid search combining vector and keyword search
    """
    
    def __init__(self, vector_store: VectorStore, bm25: BM25Search, alpha: float = 0.5):
        self.vector_store = vector_store
        self.bm25 = bm25
        self.alpha = alpha  # Weight for vector search (1-alpha for BM25)
    
    def search(
        self,
        query: str,
        query_embedding: np.ndarray,
        top_k: int = 10
    ) -> List[RetrievalResult]:
        """
        Hybrid search combining vector and BM25
        
        Args:
            query: Text query
            query_embedding: Query embedding
            top_k: Number of results to return
        
        Returns:
            List of retrieval results
        """
        # Get results from both methods
        vector_results = self.vector_store.search(query_embedding, top_k=top_k * 2)
        bm25_results = self.bm25.search(query, top_k=top_k * 2)
        
        # Combine scores
        combined_scores = {}
        
        # Add vector scores
        for result in vector_results:
            doc_id = result.document.id
            combined_scores[doc_id] = self.alpha * result.score
        
        # Add BM25 scores
        for result in bm25_results:
            doc_id = result.document.id
            if doc_id in combined_scores:
                combined_scores[doc_id] += (1 - self.alpha) * result.score
            else:
                combined_scores[doc_id] = (1 - self.alpha) * result.score
        
        # Sort by combined score
        sorted_results = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        # Create final results
        results = []
        doc_map = {doc.id: doc for doc in self.vector_store.documents}
        
        for rank, (doc_id, score) in enumerate(sorted_results):
            if doc_id in doc_map:
                results.append(RetrievalResult(
                    document=doc_map[doc_id],
                    score=float(score),
                    rank=rank + 1
                ))
        
        return results


class Reranker:
    """
    Reranker for improving retrieval results
    """
    
    def __init__(self):
        pass
    
    def rerank(
        self,
        documents: List[Document],
        query: str,
        top_k: int = 10
    ) -> List[RetrievalResult]:
        """
        Rerank documents based on query relevance
        
        Args:
            documents: Documents to rerank
            query: Query text
            top_k: Number of results to return
        
        Returns:
            Reranked results
        """
        # In production, this would use a cross-encoder model
        # For demo, use simple keyword matching as placeholder
        
        query_tokens = set(query.lower().split())
        scores = []
        
        for doc in documents:
            doc_tokens = set(doc.text.lower().split())
            overlap = len(query_tokens.intersection(doc_tokens))
            score = overlap / len(query_tokens) if query_tokens else 0
            scores.append((doc, score))
        
        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for rank, (doc, score) in enumerate(scores[:top_k]):
            results.append(RetrievalResult(
                document=doc,
                score=float(score),
                rank=rank + 1
            ))
        
        return results


class RAGSystem:
    """
    Complete RAG system
    """
    
    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        use_hybrid: bool = True,
        use_reranking: bool = True
    ):
        self.embedding_model = embedding_model or EmbeddingModel()
        self.vector_store = VectorStore(embedding_dim=self.embedding_model.embedding_dim)
        self.bm25 = BM25Search()
        self.use_hybrid = use_hybrid
        self.use_reranking = use_reranking
        
        if use_hybrid:
            self.search = HybridSearch(self.vector_store, self.bm25)
        else:
            self.search = self.vector_store
        
        self.reranker = Reranker() if use_reranking else None
    
    def add_documents(self, documents: List[Document]):
        """Add documents to the RAG system"""
        # Add to vector store
        self.vector_store.add_documents(documents)
        
        # Add to BM25
        self.bm25.add_documents(documents)
    
    def retrieve(
        self,
        query: str,
        query_embedding: Optional[np.ndarray] = None,
        top_k: int = 10
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Query text
            query_embedding: Query embedding (optional, will be generated if not provided)
            top_k: Number of results to return
        
        Returns:
            List of retrieval results
        """
        if query_embedding is None:
            # Generate query embedding
            # In production, would tokenize and run through embedding model
            query_embedding = np.random.randn(self.embedding_model.embedding_dim)
        
        # Search
        if self.use_hybrid:
            results = self.search.search(query, query_embedding, top_k=top_k)
        else:
            results = self.vector_store.search(query_embedding, top_k=top_k)
        
        # Rerank if enabled
        if self.use_reranking and self.reranker:
            documents = [r.document for r in results]
            results = self.reranker.rerank(documents, query, top_k=top_k)
        
        return results
    
    def build_context(
        self,
        query: str,
        max_tokens: int = 4096
    ) -> str:
        """
        Build context from retrieved documents
        
        Args:
            query: Query text
            max_tokens: Maximum tokens in context
        
        Returns:
            Context string
        """
        results = self.retrieve(query, top_k=10)
        
        context_parts = []
        total_tokens = 0
        
        for result in results:
            doc_text = result.document.text
            # Rough token estimation (4 chars per token)
            doc_tokens = len(doc_text) // 4
            
            if total_tokens + doc_tokens > max_tokens:
                break
            
            context_parts.append(f"[Source: {result.document.id}]\n{doc_text}")
            total_tokens += doc_tokens
        
        return "\n\n".join(context_parts)


if __name__ == "__main__":
    # Demo: Create RAG system
    rag = RAGSystem()
    
    # Add sample documents
    documents = [
        Document(
            id="doc1",
            text="Fivoria is a freelance marketplace connecting buyers and sellers.",
            metadata={"source": "about", "category": "general"}
        ),
        Document(
            id="doc2",
            text="React developers on Fivoria typically charge $50-500 per hour.",
            metadata={"source": "pricing", "category": "rates"}
        ),
        Document(
            id="doc3",
            text="Python is a popular programming language for web development and data science.",
            metadata={"source": "tech", "category": "programming"}
        ),
    ]
    
    # Generate dummy embeddings
    for doc in documents:
        doc.embedding = np.random.randn(768)
    
    rag.add_documents(documents)
    
    # Retrieve
    query = "Find React developers"
    results = rag.retrieve(query)
    
    print(f"Query: {query}")
    print(f"Results: {len(results)}")
    for result in results:
        print(f"  {result.rank}. {result.document.text[:50]}... (score: {result.score:.4f})")
