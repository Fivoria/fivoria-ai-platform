"""
Model Gateway Adapter
Adapts the Model Gateway for use with CompleteAIAgent
"""

import asyncio
from typing import Dict, List, Optional, Any
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from inference.gateway import InferenceEngine


class ModelGatewayAdapter:
    """Adapter for Model Gateway to work with CompleteAIAgent"""
    
    def __init__(self, model: str = "fivoria-base"):
        self.model = model
        self.inference_engine = InferenceEngine()
    
    async def generate(
        self,
        context: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        enable_streaming: bool = False,
        **kwargs
    ) -> str:
        """Generate response using Model Gateway"""
        try:
            # Parse context to extract messages
            messages = self._parse_context(context)
            
            # Add system message if not present
            if not any(msg.get('role') == 'system' for msg in messages):
                messages.insert(0, {
                    'role': 'system',
                    'content': 'You are a helpful AI assistant. Provide clear, accurate, and helpful responses.'
                })
            
            # Generate response
            result = await self.inference_engine.generate(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return result.get('content', '')
            
        except Exception as e:
            print(f"Model Gateway generation failed: {e}")
            return "I apologize, but I encountered an issue generating a response. Please try again."
    
    def _parse_context(self, context: str) -> List[Dict[str, str]]:
        """Parse context string into message format"""
        messages = []
        lines = context.split('\n')
        
        current_role = 'user'
        current_content = []
        
        for line in lines:
            if line.startswith('==='):
                # Section header, skip
                continue
            elif line.startswith('- '):
                # List item, add to current content
                current_content.append(line)
            elif ':' in line and not line.startswith(' '):
                # Might be role: content format
                parts = line.split(':', 1)
                if len(parts) == 2 and parts[0].strip().lower() in ['user', 'assistant', 'system']:
                    # Save previous message
                    if current_content:
                        messages.append({
                            'role': current_role,
                            'content': '\n'.join(current_content)
                        })
                    # Start new message
                    current_role = parts[0].strip().lower()
                    current_content = [parts[1].strip()]
                else:
                    current_content.append(line)
            else:
                current_content.append(line)
        
        # Add last message
        if current_content:
            messages.append({
                'role': current_role,
                'content': '\n'.join(current_content)
            })
        
        # If no messages parsed, treat entire context as user message
        if not messages:
            messages.append({
                'role': 'user',
                'content': context
            })
        
        return messages
    
    async def close(self):
        """Close inference engine connections"""
        await self.inference_engine.close()
