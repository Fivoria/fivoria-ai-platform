"""
Memory Adapter
Adapts the Memory System for use with Agent API and database persistence
"""

import sys
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from knowledge_layer.memory.memory_system import (
    ShortTermMemory,
    LongTermMemory,
    SemanticMemory,
    FactualMemory,
    EpisodicMemory,
    Memory,
    MemoryType,
    MemoryPriority
)
from database.schema import get_db_connection


class MemoryAdapter:
    """Adapter for Memory System with database persistence"""
    
    def __init__(self):
        self.short_term = ShortTermMemory(max_turns=20)
        self.long_term = LongTermMemory()
        self.semantic = SemanticMemory(embedding_dim=768)
        self.factual = FactualMemory()
        self.episodic = EpisodicMemory()
    
    # Short-term memory (conversation history)
    def add_short_term_memory(self, user_id: str, message: Dict[str, Any]):
        """Add message to short-term memory"""
        self.short_term.add_message(
            session_id=user_id,
            role=message.get('role', 'user'),
            content=message.get('content', ''),
            metadata=message.get('metadata', {})
        )
    
    def get_short_term_memory(self, user_id: str) -> List[Dict]:
        """Get conversation history from short-term memory"""
        return self.short_term.get_conversation(user_id)
    
    # Long-term memory (user preferences)
    def set_user_profile(self, user_id: str, profile: Dict):
        """Set user profile in long-term memory"""
        self.long_term.set_user_profile(int(user_id), profile)
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile from long-term memory"""
        return self.long_term.get_user_profile(int(user_id))
    
    def set_preference(self, user_id: str, key: str, value: Any):
        """Set user preference"""
        self.long_term.set_preference(int(user_id), key, value)
    
    def get_preference(self, user_id: str, key: str) -> Optional[Any]:
        """Get user preference"""
        return self.long_term.get_preference(int(user_id), key)
    
    def get_all_preferences(self, user_id: str) -> Dict:
        """Get all user preferences"""
        return self.long_term.get_all_preferences(int(user_id))
    
    # Semantic memory (vector search - simplified for now)
    def add_semantic_memory(self, user_id: str, text: str, metadata: Dict):
        """Add semantic memory (simplified version without actual embeddings)"""
        # In production, this would generate embeddings using the model gateway
        # For now, we'll store as factual memory
        self.factual.add_fact(int(user_id), 'semantic', {
            'text': text,
            'metadata': metadata
        })
    
    def get_semantic_memory(self, query: str, user_id: str) -> List[Dict]:
        """Get semantic memory (simplified version)"""
        # In production, this would do vector similarity search
        # For now, return relevant facts
        facts = self.factual.get_facts(int(user_id), 'semantic')
        return [{'content': f['data']['text'], 'metadata': f['data']['metadata']} for f in facts]
    
    # Episodic memory (interaction summaries)
    def add_episodic_memory(self, user_id: str, episode: Dict):
        """Add episodic memory"""
        self.episodic.add_episode(
            user_id=int(user_id),
            summary=episode.get('summary', ''),
            importance=episode.get('importance', 0.5),
            metadata=episode.get('metadata', {})
        )
    
    def get_episodic_memory(self, user_id: str, query: str) -> List[Dict]:
        """Get episodic memory"""
        # Simplified - return all episodes for user
        if int(user_id) in self.episodic.episodes:
            return self.episodic.episodes[int(user_id)]
        return []
    
    # Procedural memory (skills, procedures)
    def get_procedural_memory(self, user_id: str) -> List[Dict]:
        """Get procedural memory (stored as factual memory)"""
        facts = self.factual.get_facts(int(user_id), 'procedural')
        return [{'type': f['type'], 'data': f['data']} for f in facts]
    
    # Database persistence
    async def save_conversation_to_db(self, user_id: str, conversation_id: str, messages: List[Dict]):
        """Save conversation to database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Save each message
            for msg in messages:
                cursor.execute("""
                    INSERT INTO messages (conversation_id, role, content, created_at)
                    VALUES (%s, %s, %s, %s)
                """, (
                    conversation_id,
                    msg.get('role', 'user'),
                    msg.get('content', ''),
                    msg.get('timestamp', datetime.utcnow())
                ))
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Failed to save conversation to database: {e}")
    
    async def load_conversation_from_db(self, conversation_id: str) -> List[Dict]:
        """Load conversation from database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT role, content, created_at
                FROM messages
                WHERE conversation_id = %s
                ORDER BY created_at ASC
            """, (conversation_id,))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'role': row['role'],
                    'content': row['content'],
                    'timestamp': row['created_at'].isoformat() if row['created_at'] else None
                })
            
            cursor.close()
            conn.close()
            return messages
        except Exception as e:
            print(f"Failed to load conversation from database: {e}")
            return []
