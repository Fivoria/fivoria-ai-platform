"""
Fivoria AI Memory System
Multi-layer memory management for AI agents
"""

import json
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import numpy as np


class MemoryType(Enum):
    """Memory layer types"""
    SHORT_TERM = "short_term"  # Current conversation
    LONG_TERM = "long_term"  # User preferences/context
    SEMANTIC = "semantic"  # Vector embeddings
    FACTUAL = "factual"  # Structured database
    EPISODIC = "episodic"  # Important interaction summaries


class MemoryPriority(Enum):
    """Memory priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Memory:
    """Memory entry"""
    id: str
    user_id: int
    memory_type: MemoryType
    content: str
    metadata: Dict[str, Any]
    priority: MemoryPriority = MemoryPriority.MEDIUM
    embedding: Optional[np.ndarray] = None
    created_at: datetime = None
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.last_accessed is None:
            self.last_accessed = datetime.utcnow()


class ShortTermMemory:
    """
    Short-term memory for current conversation
    """
    
    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self.conversations: Dict[str, List[Dict]] = {}
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to conversation"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        message = {
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.conversations[session_id].append(message)
        
        # Trim if exceeds max turns
        if len(self.conversations[session_id]) > self.max_turns:
            self.conversations[session_id] = self.conversations[session_id][-self.max_turns:]
    
    def get_conversation(self, session_id: str) -> List[Dict]:
        """Get conversation history"""
        return self.conversations.get(session_id, [])
    
    def clear_conversation(self, session_id: str):
        """Clear conversation"""
        if session_id in self.conversations:
            del self.conversations[session_id]
    
    def get_context(self, session_id: str, max_tokens: int = 4096) -> str:
        """Get conversation context within token limit"""
        messages = self.get_conversation(session_id)
        context_parts = []
        total_tokens = 0
        
        for msg in reversed(messages):
            msg_text = f"{msg['role']}: {msg['content']}"
            msg_tokens = len(msg_text.split())
            
            if total_tokens + msg_tokens > max_tokens:
                break
            
            context_parts.insert(0, msg_text)
            total_tokens += msg_tokens
        
        return "\n".join(context_parts)


class LongTermMemory:
    """
    Long-term memory for user preferences and persistent context
    """
    
    def __init__(self):
        self.user_profiles: Dict[int, Dict] = {}
        self.preferences: Dict[int, Dict] = {}
    
    def set_user_profile(self, user_id: int, profile: Dict):
        """Set user profile"""
        self.user_profiles[user_id] = {
            **profile,
            "updated_at": datetime.utcnow().isoformat()
        }
    
    def get_user_profile(self, user_id: int) -> Optional[Dict]:
        """Get user profile"""
        return self.user_profiles.get(user_id)
    
    def set_preference(self, user_id: int, key: str, value: Any):
        """Set user preference"""
        if user_id not in self.preferences:
            self.preferences[user_id] = {}
        
        self.preferences[user_id][key] = {
            "value": value,
            "updated_at": datetime.utcnow().isoformat()
        }
    
    def get_preference(self, user_id: int, key: str) -> Optional[Any]:
        """Get user preference"""
        if user_id in self.preferences and key in self.preferences[user_id]:
            return self.preferences[user_id][key]["value"]
        return None
    
    def get_all_preferences(self, user_id: int) -> Dict:
        """Get all user preferences"""
        return self.preferences.get(user_id, {})


class SemanticMemory:
    """
    Semantic memory using vector embeddings
    """
    
    def __init__(self, embedding_dim: int = 768):
        self.embedding_dim = embedding_dim
        self.memories: List[Memory] = []
        self.index: Dict[str, int] = {}  # memory_id -> index
    
    def add_memory(self, memory: Memory):
        """Add memory with embedding"""
        memory.id = self._generate_id(memory.content)
        self.memories.append(memory)
        self.index[memory.id] = len(self.memories) - 1
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        user_id: Optional[int] = None,
        min_similarity: float = 0.0
    ) -> List[Memory]:
        """Search memories by semantic similarity"""
        if not self.memories:
            return []
        
        similarities = []
        for memory in self.memories:
            # Filter by user if specified
            if user_id is not None and memory.user_id != user_id:
                continue
            
            # Calculate cosine similarity
            if memory.embedding is not None:
                similarity = np.dot(query_embedding, memory.embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(memory.embedding) + 1e-8
                )
                if similarity >= min_similarity:
                    similarities.append((memory, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k
        return [mem for mem, _ in similarities[:top_k]]
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get memory by ID"""
        if memory_id in self.index:
            return self.memories[self.index[memory_id]]
        return None
    
    def delete_memory(self, memory_id: str):
        """Delete memory by ID"""
        if memory_id in self.index:
            idx = self.index[memory_id]
            del self.memories[idx]
            del self.index[memory_id]
            # Rebuild index
            self.index = {mem.id: i for i, mem in enumerate(self.memories)}
    
    def cleanup_expired(self):
        """Remove expired memories"""
        now = datetime.utcnow()
        self.memories = [
            mem for mem in self.memories
            if mem.expires_at is None or mem.expires_at > now
        ]
        self.index = {mem.id: i for i, mem in enumerate(self.memories)}
    
    def _generate_id(self, content: str) -> str:
        """Generate unique ID for memory"""
        hash_input = f"{content}_{datetime.utcnow().timestamp()}"
        return hashlib.md5(hash_input.encode()).hexdigest()


class FactualMemory:
    """
    Factual memory for structured data storage
    """
    
    def __init__(self):
        self.facts: Dict[int, List[Dict]] = {}  # user_id -> facts
    
    def add_fact(self, user_id: int, fact_type: str, fact_data: Dict):
        """Add structured fact"""
        if user_id not in self.facts:
            self.facts[user_id] = []
        
        fact = {
            "type": fact_type,
            "data": fact_data,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        self.facts[user_id].append(fact)
    
    def get_facts(self, user_id: int, fact_type: Optional[str] = None) -> List[Dict]:
        """Get facts for user"""
        if user_id not in self.facts:
            return []
        
        if fact_type is None:
            return self.facts[user_id]
        
        return [f for f in self.facts[user_id] if f["type"] == fact_type]
    
    def update_fact(self, user_id: int, fact_type: str, fact_data: Dict):
        """Update existing fact"""
        if user_id not in self.facts:
            self.add_fact(user_id, fact_type, fact_data)
            return
        
        # Find and update existing fact of this type
        for fact in self.facts[user_id]:
            if fact["type"] == fact_type:
                fact["data"] = fact_data
                fact["updated_at"] = datetime.utcnow().isoformat()
                return
        
        # If not found, add new
        self.add_fact(user_id, fact_type, fact_data)
    
    def delete_fact(self, user_id: int, fact_type: str):
        """Delete fact by type"""
        if user_id in self.facts:
            self.facts[user_id] = [f for f in self.facts[user_id] if f["type"] != fact_type]


class EpisodicMemory:
    """
    Episodic memory for important interaction summaries
    """
    
    def __init__(self):
        self.episodes: Dict[int, List[Dict]] = {}  # user_id -> episodes
    
    def add_episode(
        self,
        user_id: int,
        summary: str,
        importance: float,
        metadata: Optional[Dict] = None
    ):
        """Add episodic memory"""
        if user_id not in self.episodes:
            self.episodes[user_id] = []
        
        episode = {
            "summary": summary,
            "importance": importance,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.episodes[user_id].append(episode)
        
        # Keep only top 100 episodes per user
        if len(self.episodes[user_id]) > 100:
            self.episodes[user_id].sort(key=lambda x: x["importance"], reverse=True)
            self.episodes[user_id] = self.episodes[user_id][:100]
    
    def get_episodes(self, user_id: int, min_importance: float = 0.5) -> List[Dict]:
        """Get episodes above importance threshold"""
        if user_id not in self.episodes:
            return []
        
        return [
            ep for ep in self.episodes[user_id]
            if ep["importance"] >= min_importance
        ]
    
    def get_recent_episodes(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get recent episodes"""
        if user_id not in self.episodes:
            return []
        
        return self.episodes[user_id][-limit:]


class MemorySystem:
    """
    Complete memory system managing all memory layers
    """
    
    def __init__(self, embedding_dim: int = 768):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()
        self.semantic = SemanticMemory(embedding_dim)
        self.factual = FactualMemory()
        self.episodic = EpisodicMemory()
    
    def add_conversation_message(
        self,
        session_id: str,
        user_id: int,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """Add message to short-term conversation"""
        self.short_term.add_message(session_id, role, content, metadata)
    
    def add_semantic_memory(
        self,
        user_id: int,
        content: str,
        embedding: np.ndarray,
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        expires_in_hours: Optional[int] = None
    ):
        """Add semantic memory"""
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        memory = Memory(
            id="",  # Will be generated
            user_id=user_id,
            memory_type=MemoryType.SEMANTIC,
            content=content,
            metadata={},
            priority=priority,
            embedding=embedding,
            expires_at=expires_at
        )
        
        self.semantic.add_memory(memory)
    
    def get_relevant_context(
        self,
        session_id: str,
        user_id: int,
        query_embedding: Optional[np.ndarray] = None,
        max_tokens: int = 8192
    ) -> Dict[str, Any]:
        """
        Get comprehensive context from all memory layers
        
        Args:
            session_id: Current session ID
            user_id: User ID
            query_embedding: Query embedding for semantic search
            max_tokens: Maximum tokens for context
        
        Returns:
            Context dictionary
        """
        context = {
            "conversation": "",
            "user_profile": None,
            "preferences": {},
            "semantic_memories": [],
            "facts": [],
            "episodes": []
        }
        
        # Short-term conversation
        context["conversation"] = self.short_term.get_context(session_id, max_tokens // 4)
        
        # Long-term profile
        context["user_profile"] = self.long_term.get_user_profile(user_id)
        context["preferences"] = self.long_term.get_all_preferences(user_id)
        
        # Semantic memories
        if query_embedding is not None:
            semantic_memories = self.semantic.search(query_embedding, top_k=5, user_id=user_id)
            context["semantic_memories"] = [mem.content for mem in semantic_memories]
        
        # Factual memories
        context["facts"] = self.factual.get_facts(user_id)
        
        # Episodic memories
        context["episodes"] = self.episodic.get_recent_episodes(user_id, limit=3)
        
        return context
    
    def cleanup_expired_memories(self):
        """Clean up expired memories across all layers"""
        self.semantic.cleanup_expired()
    
    def clear_user_data(self, user_id: int):
        """Clear all data for a user (GDPR compliance)"""
        # Clear semantic memories
        self.semantic.memories = [m for m in self.semantic.memories if m.user_id != user_id]
        self.semantic.index = {mem.id: i for i, mem in enumerate(self.semantic.memories)}
        
        # Clear factual memories
        if user_id in self.factual.facts:
            del self.factual.facts[user_id]
        
        # Clear episodic memories
        if user_id in self.episodic.episodes:
            del self.episodic.episodes[user_id]
        
        # Clear long-term preferences
        if user_id in self.long_term.preferences:
            del self.long_term.preferences[user_id]
        
        if user_id in self.long_term.user_profiles:
            del self.long_term.user_profiles[user_id]


if __name__ == "__main__":
    # Demo: Memory system
    memory_system = MemorySystem()
    
    # Add conversation
    memory_system.add_conversation_message(
        session_id="session-1",
        user_id=1,
        role="user",
        content="Hello, I'm looking for a React developer"
    )
    
    # Add semantic memory
    import numpy as np
    embedding = np.random.randn(768)
    memory_system.add_semantic_memory(
        user_id=1,
        content="User prefers React developers with 5+ years experience",
        embedding=embedding
    )
    
    # Add factual memory
    memory_system.factual.add_fact(
        user_id=1,
        fact_type="skill_preference",
        fact_data={"primary_skill": "React", "min_experience": 5}
    )
    
    # Add episodic memory
    memory_system.episodic.add_episode(
        user_id=1,
        summary="User successfully hired a React developer last month",
        importance=0.8
    )
    
    # Get context
    context = memory_system.get_relevant_context(
        session_id="session-1",
        user_id=1,
        query_embedding=embedding
    )
    
    print("Context retrieved:")
    print(f"Conversation: {context['conversation']}")
    print(f"Semantic memories: {len(context['semantic_memories'])}")
    print(f"Facts: {len(context['facts'])}")
    print(f"Episodes: {len(context['episodes'])}")
