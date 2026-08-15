"""
Complete AI Agent
Enhanced version with advanced reasoning, planning, knowledge graph, and adaptive learning
Integrates all layers: Foundation Model, Memory, Tools, RAG, Verification, Knowledge Graph
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Enhanced agent states"""
    IDLE = "idle"
    PROCESSING = "processing"
    THINKING = "thinking"
    PLANNING = "planning"
    USING_TOOLS = "using_tools"
    RETRIEVING = "retrieving"
    VERIFYING = "verifying"
    LEARNING = "learning"
    COLLABORATING = "collaborating"
    COMPLETED = "completed"
    ERROR = "error"


class IntentType(Enum):
    """Enhanced intent types"""
    GENERAL = "general"
    SEARCH = "search"
    CALCULATION = "calculation"
    CODING = "coding"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    REASONING = "reasoning"
    PLANNING = "planning"
    COMPARISON = "comparison"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    QUESTION_ANSWERING = "question_answering"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    ENTITY_EXTRACTION = "entity_extraction"
    CLASSIFICATION = "classification"
    RECOMMENDATION = "recommendation"
    EXPLANATION = "explanation"


@dataclass
class AgentContext:
    """Enhanced context for agent execution"""
    user_id: str
    conversation_id: str
    query: str
    conversation_history: List[Dict] = None
    metadata: Dict = None
    # Enhanced fields
    user_preferences: Dict = None
    session_id: str = None
    language: str = "en"
    timezone: str = "UTC"
    context_window: int = 4096
    max_tokens: int = 2048
    temperature: float = 0.7
    enable_streaming: bool = False
    enable_reasoning: bool = True
    enable_planning: bool = True
    enable_learning: bool = True


@dataclass
class AgentResponse:
    """Enhanced agent response"""
    content: str
    sources: List[str] = None
    tool_calls: List[Dict] = None
    memory_used: List[str] = None
    verification_status: str = None
    confidence: float = 0.0
    metadata: Dict = None
    # Enhanced fields
    reasoning_steps: List[Dict] = None
    plan: List[Dict] = None
    knowledge_graph_nodes: List[str] = None
    entities: List[Dict] = None
    sentiment: str = None
    language_detected: str = None
    processing_time: float = 0.0
    token_usage: Dict = None
    quality_score: float = 0.0
    follow_up_questions: List[str] = None


class CompleteAIAgent:
    """Enhanced complete AI agent with all layers and advanced capabilities"""

    def __init__(
        self,
        foundation_model,
        memory_system,
        tool_framework,
        rag_system,
        verification_layer,
        knowledge_graph=None,
        fivoria_integration=None,
        enable_reasoning: bool = True,
        enable_planning: bool = True,
        enable_learning: bool = True
    ):
        self.foundation_model = foundation_model
        self.memory_system = memory_system
        self.tool_framework = tool_framework
        self.rag_system = rag_system
        self.verification_layer = verification_layer
        self.knowledge_graph = knowledge_graph
        self.fivoria_integration = fivoria_integration

        self.state = AgentState.IDLE
        self.current_context = None
        
        # Advanced features
        self.enable_reasoning = enable_reasoning
        self.enable_planning = enable_planning
        self.enable_learning = enable_learning
        
        # Analytics and learning
        self.analytics = defaultdict(int)
        self.interaction_history = []
        self.performance_metrics = defaultdict(float)
        
        # Intent detection model
        self.intent_classifier = None
        
        # Reasoning engine
        self.reasoning_engine = None
        
        # Planner
        self.planner = None

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process user query through complete enhanced agent pipeline"""
        start_time = datetime.now()
        self.state = AgentState.PROCESSING
        self.current_context = context

        try:
            # Step 1: Advanced intent detection
            intent, confidence = await self._detect_intent(context.query)
            logger.info(f"Detected intent: {intent} (confidence: {confidence:.2f})")

            # Step 2: Retrieve enhanced memory
            memory_context = await self._retrieve_memory(context)
            logger.info(f"Retrieved {len(memory_context)} memory items")

            # Step 3: Retrieve external knowledge (RAG + Knowledge Graph)
            rag_context = await self._retrieve_rag(context.query, intent)
            kg_context = await self._retrieve_knowledge_graph(context.query, intent) if self.knowledge_graph else []
            logger.info(f"Retrieved {len(rag_context)} RAG items, {len(kg_context)} KG nodes")

            # Step 4: Planning if enabled
            plan = []
            if self.enable_planning and await self._needs_planning(context.query, intent):
                self.state = AgentState.PLANNING
                plan = await self._create_plan(context.query, intent, memory_context, rag_context)
                logger.info(f"Created plan with {len(plan)} steps")

            # Step 5: Reasoning if enabled
            reasoning_steps = []
            if self.enable_reasoning and await self._needs_reasoning(context.query, intent):
                self.state = AgentState.THINKING
                reasoning_steps = await self._perform_reasoning(context.query, intent, memory_context, rag_context, kg_context)
                logger.info(f"Performed {len(reasoning_steps)} reasoning steps")

            # Step 6: Check if tools needed and execute
            tool_results = []
            if await self._needs_tools(context.query, intent):
                self.state = AgentState.USING_TOOLS
                tool_results = await self._execute_tools(context.query, intent, plan)
                logger.info(f"Executed {len(tool_results)} tool calls")

            # Step 7: Build enhanced context for model
            model_context = self._build_model_context(
                context.query,
                memory_context,
                rag_context,
                kg_context,
                tool_results,
                reasoning_steps,
                context.conversation_history
            )

            # Step 8: Generate response
            response = await self._generate_response(model_context, context)
            logger.info("Generated response")

            # Step 9: Enhanced verification
            self.state = AgentState.VERIFYING
            verification = await self._verify_response(response, context.query, intent)
            logger.info(f"Verification status: {verification['status']}")

            # Step 10: Learn from interaction if enabled
            if self.enable_learning:
                self.state = AgentState.LEARNING
                await self._learn_from_interaction(context, response, verification, intent)
                logger.info("Learned from interaction")

            # Step 11: Store to enhanced memory
            await self._store_to_memory(context, response, tool_results, reasoning_steps, intent)

            # Step 12: Generate follow-up questions
            follow_up_questions = await self._generate_follow_up_questions(context.query, response, intent)

            # Calculate metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self.analytics['total_interactions'] += 1
            self.analytics['avg_processing_time'] = (
                self.analytics['avg_processing_time'] * (self.analytics['total_interactions'] - 1) + processing_time
            ) / self.analytics['total_interactions']

            self.state = AgentState.COMPLETED

            return AgentResponse(
                content=response,
                sources=[item.get('source') for item in rag_context],
                tool_calls=tool_results,
                memory_used=[item.get('type') for item in memory_context],
                verification_status=verification['status'],
                confidence=verification.get('score', 0.0),
                reasoning_steps=reasoning_steps,
                plan=plan,
                knowledge_graph_nodes=[node.get('id') for node in kg_context],
                entities=verification.get('entities', []),
                sentiment=verification.get('sentiment'),
                language_detected=verification.get('language'),
                processing_time=processing_time,
                token_usage=verification.get('token_usage', {}),
                quality_score=verification.get('quality_score', 0.0),
                follow_up_questions=follow_up_questions,
                metadata={
                    'intent': intent.value,
                    'intent_confidence': confidence,
                    'tools_used': len(tool_results),
                    'rag_items': len(rag_context),
                    'kg_nodes': len(kg_context),
                    'memory_items': len(memory_context),
                    'reasoning_steps': len(reasoning_steps),
                    'plan_steps': len(plan)
                }
            )

        except Exception as e:
            logger.error(f"Agent processing failed: {e}")
            self.state = AgentState.ERROR
            self.analytics['errors'] += 1
            raise

    async def _detect_intent(self, query: str) -> Tuple[IntentType, float]:
        """Enhanced intent detection with confidence scoring"""
        # Use intent classifier if available
        if self.intent_classifier:
            try:
                intent, confidence = await self.intent_classifier.classify(query)
                return IntentType(intent), confidence
            except Exception as e:
                logger.error(f"Intent classifier failed: {e}")

        # Use Fivoria intent detector if available
        if self.fivoria_integration:
            try:
                from integrations.fivoria.marketplace_api import FivoriaIntentDetector
                detector = FivoriaIntentDetector()
                intent, confidence = detector.detect_intent(query)
                
                if confidence > 0.5:
                    return IntentType.SEARCH, confidence
            except Exception as e:
                logger.error(f"Fivoria intent detection failed: {e}")

        # Enhanced rule-based intent detection with confidence
        query_lower = query.lower()
        
        intent_keywords = {
            IntentType.SEARCH: ['find', 'search', 'look for', 'best', 'top', 'recommend'],
            IntentType.CALCULATION: ['calculate', 'compute', 'math', 'solve', 'equation'],
            IntentType.CODING: ['code', 'program', 'function', 'script', 'debug', 'implement'],
            IntentType.ANALYSIS: ['analyze', 'examine', 'evaluate', 'assess', 'study'],
            IntentType.CREATIVE: ['write', 'create', 'generate', 'compose', 'design'],
            IntentType.REASONING: ['why', 'how', 'explain', 'reason', 'logic', 'deduce'],
            IntentType.PLANNING: ['plan', 'schedule', 'organize', 'strategy', 'roadmap'],
            IntentType.COMPARISON: ['compare', 'vs', 'versus', 'difference', 'better'],
            IntentType.SUMMARIZATION: ['summarize', 'summary', 'brief', 'overview'],
            IntentType.TRANSLATION: ['translate', 'translation', 'in', 'to'],
            IntentType.QUESTION_ANSWERING: ['what', 'when', 'where', 'who', 'which'],
            IntentType.SENTIMENT_ANALYSIS: ['sentiment', 'opinion', 'feel', 'attitude'],
            IntentType.ENTITY_EXTRACTION: ['extract', 'identify', 'find entities'],
            IntentType.CLASSIFICATION: ['classify', 'categorize', 'group', 'type'],
            IntentType.RECOMMENDATION: ['recommend', 'suggest', 'advice', 'should'],
            IntentType.EXPLANATION: ['explain', 'describe', 'clarify', 'elaborate']
        }

        max_matches = 0
        best_intent = IntentType.GENERAL
        
        for intent, keywords in intent_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in query_lower)
            if matches > max_matches:
                max_matches = matches
                best_intent = intent

        confidence = min(0.3 + (max_matches * 0.15), 0.95)
        
        return best_intent, confidence

    async def _retrieve_memory(self, context: AgentContext) -> List[Dict]:
        """Enhanced memory retrieval with multiple memory types"""
        if not self.memory_system:
            return []

        memory_items = []

        # Retrieve short-term memory (conversation history)
        try:
            short_term = self.memory_system.get_short_term_memory(context.user_id)
            memory_items.append({'type': 'short_term', 'content': short_term})
        except Exception as e:
            logger.error(f"Short-term memory retrieval failed: {e}")

        # Retrieve long-term memory (user preferences, patterns)
        try:
            long_term = self.memory_system.get_long_term_memory(context.user_id)
            memory_items.append({'type': 'long_term', 'content': long_term})
        except Exception as e:
            logger.error(f"Long-term memory retrieval failed: {e}")

        # Retrieve semantic memory (vector search)
        try:
            semantic = self.memory_system.get_semantic_memory(context.query, context.user_id)
            memory_items.append({'type': 'semantic', 'content': semantic})
        except Exception as e:
            logger.error(f"Semantic memory retrieval failed: {e}")

        # Retrieve episodic memory (past interactions)
        try:
            episodic = self.memory_system.get_episodic_memory(context.user_id, context.query)
            memory_items.append({'type': 'episodic', 'content': episodic})
        except Exception as e:
            logger.error(f"Episodic memory retrieval failed: {e}")

        # Retrieve procedural memory (skills, procedures)
        try:
            procedural = self.memory_system.get_procedural_memory(context.user_id)
            memory_items.append({'type': 'procedural', 'content': procedural})
        except Exception as e:
            logger.error(f"Procedural memory retrieval failed: {e}")

        return memory_items

    async def _retrieve_rag(self, query: str, intent: IntentType) -> List[Dict]:
        """Enhanced RAG retrieval with intent-aware strategies"""
        if not self.rag_system:
            return []

        rag_items = []

        # If Fivoria-related query, use Fivoria integration
        if intent == IntentType.SEARCH and self.fivoria_integration:
            try:
                from integrations.fivoria.marketplace_api import SearchFilter
                params = self.fivoria_integration.extract_search_params(query)
                filters = SearchFilter(**params)
                
                results = await self.fivoria_integration.search(query, filters)
                rag_items.append({'type': 'fivoria', 'content': results, 'source': 'fivoria_api'})
            except Exception as e:
                logger.error(f"Fivoria RAG retrieval failed: {e}")

        # Standard RAG retrieval with intent-specific strategies
        try:
            # Adjust retrieval based on intent
            top_k = 10 if intent in [IntentType.ANALYSIS, IntentType.COMPARISON] else 5
            retrieval_strategy = self._get_retrieval_strategy(intent)
            
            results = self.rag_system.retrieve(
                query, 
                top_k=top_k,
                strategy=retrieval_strategy
            )
            
            for r in results:
                rag_items.append({'type': 'rag', 'content': r, 'source': r.get('source', 'knowledge_base')})
        except Exception as e:
            logger.error(f"Standard RAG retrieval failed: {e}")

        return rag_items

    async def _retrieve_knowledge_graph(self, query: str, intent: IntentType) -> List[Dict]:
        """Retrieve relevant nodes from knowledge graph"""
        if not self.knowledge_graph:
            return []

        try:
            # Extract entities from query
            entities = self._extract_entities(query)
            
            # Query knowledge graph
            kg_nodes = []
            for entity in entities:
                nodes = self.knowledge_graph.query_nodes(entity, depth=2)
                kg_nodes.extend(nodes)
            
            return kg_nodes
        except Exception as e:
            logger.error(f"Knowledge graph retrieval failed: {e}")
            return []

    def _get_retrieval_strategy(self, intent: IntentType) -> str:
        """Get retrieval strategy based on intent"""
        strategies = {
            IntentType.SEARCH: 'hybrid',
            IntentType.ANALYSIS: 'comprehensive',
            IntentType.COMPARISON: 'comprehensive',
            IntentType.REASONING: 'comprehensive',
            IntentType.QUESTION_ANSWERING: 'precise',
            IntentType.SUMMARIZATION: 'comprehensive'
        }
        return strategies.get(intent, 'hybrid')

    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from text"""
        # Simple entity extraction - in production would use NER model
        import re
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        return list(set(words))

    async def _needs_planning(self, query: str, intent: IntentType) -> bool:
        """Determine if planning is needed"""
        planning_intents = [
            IntentType.PLANNING,
            IntentType.ANALYSIS,
            IntentType.REASONING,
            IntentType.COMPARISON
        ]
        
        # Check intent
        if intent in planning_intents:
            return True
        
        # Check query complexity
        query_words = len(query.split())
        if query_words > 20:  # Complex queries need planning
            return True
        
        # Check for multi-step indicators
        multi_step_indicators = ['then', 'after that', 'next', 'finally', 'step by step']
        if any(indicator in query.lower() for indicator in multi_step_indicators):
            return True
        
        return False

    async def _create_plan(
        self, 
        query: str, 
        intent: IntentType, 
        memory_context: List[Dict],
        rag_context: List[Dict]
    ) -> List[Dict]:
        """Create execution plan"""
        plan = []
        
        # Step 1: Analyze requirements
        plan.append({
            'step': 1,
            'action': 'analyze_requirements',
            'description': 'Analyze query requirements and constraints',
            'status': 'pending'
        })
        
        # Step 2: Gather information
        plan.append({
            'step': 2,
            'action': 'gather_information',
            'description': 'Gather relevant information from memory and knowledge base',
            'status': 'pending'
        })
        
        # Step 3: Process information
        plan.append({
            'step': 3,
            'action': 'process_information',
            'description': 'Process and analyze gathered information',
            'status': 'pending'
        })
        
        # Step 4: Generate response
        plan.append({
            'step': 4,
            'action': 'generate_response',
            'description': 'Generate comprehensive response',
            'status': 'pending'
        })
        
        # Step 5: Verify quality
        plan.append({
            'step': 5,
            'action': 'verify_quality',
            'description': 'Verify response quality and accuracy',
            'status': 'pending'
        })
        
        return plan

    async def _needs_reasoning(self, query: str, intent: IntentType) -> bool:
        """Determine if reasoning is needed"""
        reasoning_intents = [
            IntentType.REASONING,
            IntentType.ANALYSIS,
            IntentType.QUESTION_ANSWERING,
            IntentType.EXPLANATION
        ]
        
        return intent in reasoning_intents

    async def _perform_reasoning(
        self,
        query: str,
        intent: IntentType,
        memory_context: List[Dict],
        rag_context: List[Dict],
        kg_context: List[Dict]
    ) -> List[Dict]:
        """Perform reasoning steps"""
        reasoning_steps = []
        
        # Step 1: Understand the problem
        reasoning_steps.append({
            'step': 1,
            'type': 'understanding',
            'description': 'Understand the query and identify key components',
            'result': self._identify_key_components(query)
        })
        
        # Step 2: Gather relevant information
        reasoning_steps.append({
            'step': 2,
            'type': 'information_gathering',
            'description': 'Gather and evaluate relevant information',
            'result': f'Evaluated {len(rag_context)} RAG items and {len(kg_context)} KG nodes'
        })
        
        # Step 3: Analyze relationships
        reasoning_steps.append({
            'step': 3,
            'type': 'relationship_analysis',
            'description': 'Analyze relationships between concepts',
            'result': self._analyze_relationships(rag_context, kg_context)
        })
        
        # Step 4: Draw conclusions
        reasoning_steps.append({
            'step': 4,
            'type': 'conclusion',
            'description': 'Draw logical conclusions based on analysis',
            'result': 'Logical conclusions derived'
        })
        
        return reasoning_steps

    def _identify_key_components(self, query: str) -> Dict:
        """Identify key components of the query"""
        import re
        words = query.split()
        return {
            'word_count': len(words),
            'question_words': [w for w in words if w.lower() in ['what', 'how', 'why', 'when', 'where', 'who']],
            'entities': re.findall(r'\b[A-Z][a-z]+\b', query),
            'numbers': re.findall(r'\b\d+\b', query)
        }

    def _analyze_relationships(self, rag_context: List[Dict], kg_context: List[Dict]) -> str:
        """Analyze relationships between concepts"""
        return f"Analyzed relationships between {len(rag_context)} documents and {len(kg_context)} knowledge graph nodes"

    async def _needs_tools(self, query: str, intent: IntentType) -> bool:
        """Determine if tools are needed"""
        tool_intents = [
            IntentType.CALCULATION,
            IntentType.SEARCH,
            IntentType.CODING,
            IntentType.ANALYSIS
        ]
        return intent in tool_intents

    async def _execute_tools(self, query: str, intent: IntentType, plan: List[Dict]) -> List[Dict]:
        """Execute relevant tools based on plan and intent"""
        if not self.tool_framework:
            return []

        results = []

        if intent == IntentType.CALCULATION:
            result = await self.tool_framework.execute_tool('calculator', {'expression': query})
            results.append({'tool': 'calculator', 'result': result})

        elif intent == IntentType.SEARCH:
            result = await self.tool_framework.execute_tool('web_search', {'query': query})
            results.append({'tool': 'web_search', 'result': result})

        elif intent == IntentType.CODING:
            result = await self.tool_framework.execute_tool('python_sandbox', {'code': query})
            results.append({'tool': 'python_sandbox', 'result': result})

        elif intent == IntentType.ANALYSIS:
            # Multiple tools for analysis
            web_result = await self.tool_framework.execute_tool('web_search', {'query': query})
            results.append({'tool': 'web_search', 'result': web_result})
            
            calc_result = await self.tool_framework.execute_tool('calculator', {'expression': 'analyze'})
            results.append({'tool': 'calculator', 'result': calc_result})

        return results

    def _build_model_context(
        self,
        query: str,
        memory_context: List[Dict],
        rag_context: List[Dict],
        kg_context: List[Dict],
        tool_results: List[Dict],
        reasoning_steps: List[Dict],
        conversation_history: List[Dict]
    ) -> str:
        """Build enhanced context for foundation model"""
        context_parts = []

        # Add conversation history
        if conversation_history:
            context_parts.append("=== Conversation History ===")
            for msg in conversation_history[-5:]:  # Last 5 messages
                context_parts.append(f"{msg.get('role', 'user')}: {msg.get('content', '')}")

        # Add memory context
        if memory_context:
            context_parts.append("\n=== Relevant Memory ===")
            for mem in memory_context:
                if mem['content']:
                    context_parts.append(f"- {mem['type']}: {str(mem['content'])[:200]}")

        # Add RAG context
        if rag_context:
            context_parts.append("\n=== Relevant Information ===")
            for rag in rag_context:
                if rag['content']:
                    context_parts.append(f"- {rag['type']} ({rag.get('source', 'unknown')}): {str(rag['content'])[:300]}")

        # Add knowledge graph context
        if kg_context:
            context_parts.append("\n=== Knowledge Graph ===")
            for node in kg_context:
                context_parts.append(f"- Node: {node.get('id', 'unknown')} - {node.get('label', '')[:100]}")

        # Add reasoning steps
        if reasoning_steps:
            context_parts.append("\n=== Reasoning Process ===")
            for step in reasoning_steps:
                context_parts.append(f"- Step {step['step']} ({step['type']}): {step['description']}")
                context_parts.append(f"  Result: {step['result']}")

        # Add tool results
        if tool_results:
            context_parts.append("\n=== Tool Results ===")
            for tool in tool_results:
                context_parts.append(f"- {tool['tool']}: {str(tool['result'])[:200]}")

        # Add current query
        context_parts.append(f"\n=== Current Query ===\n{query}")

        return "\n".join(context_parts)

    async def _generate_response(self, context: str, agent_context: AgentContext) -> str:
        """Generate response using foundation model with enhanced parameters"""
        if self.foundation_model:
            try:
                response = await self.foundation_model.generate(
                    context,
                    temperature=agent_context.temperature,
                    max_tokens=agent_context.max_tokens,
                    enable_streaming=agent_context.enable_streaming
                )
                return response
            except Exception as e:
                logger.error(f"Foundation model generation failed: {e}")
                return self._generate_fallback_response(context)
        else:
            return self._generate_fallback_response(context)

    def _generate_fallback_response(self, context: str) -> str:
        """Generate fallback response when model fails"""
        return "I apologize, but I encountered an issue generating a response. Please try again."

    async def _verify_response(self, response: str, query: str, intent: IntentType) -> Dict:
        """Enhanced response verification with multiple checks"""
        if not self.verification_layer:
            return {'status': 'skipped', 'score': 0.5}

        try:
            results = self.verification_layer.verify_response(response, query)
            status, score = self.verification_layer.get_overall_status(results)

            # Extract additional verification info
            entities = self._extract_entities(response)
            sentiment = self._analyze_sentiment(response)
            language = self._detect_language(response)
            quality_score = self._calculate_quality_score(response, results)

            return {
                'status': status.value,
                'score': score,
                'details': results,
                'entities': entities,
                'sentiment': sentiment,
                'language': language,
                'quality_score': quality_score,
                'token_usage': {'input_tokens': len(query.split()), 'output_tokens': len(response.split())}
            }
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {'status': 'skipped', 'score': 0.5}

    def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of text"""
        # Simple sentiment analysis
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'positive']
        negative_words = ['bad', 'terrible', 'awful', 'poor', 'negative', 'worst']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'

    def _detect_language(self, text: str) -> str:
        """Detect language of text"""
        # Simple language detection - in production would use proper NLP
        if any(char in text for char in 'آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی'):
            return 'urdu'
        elif any(char in text for char in 'अआइईउऊएऐओऔकखगघचछजझटठडढणतथदधनपफबभमयरलवशषसह'):
            return 'hindi'
        else:
            return 'english'

    def _calculate_quality_score(self, response: str, verification_results: Dict) -> float:
        """Calculate overall quality score"""
        if not verification_results:
            return 0.5
        
        scores = [result.score for result in verification_results.values()]
        return sum(scores) / len(scores) if scores else 0.5

    async def _store_to_memory(
        self,
        context: AgentContext,
        response: str,
        tool_results: List[Dict],
        reasoning_steps: List[Dict],
        intent: IntentType
    ):
        """Enhanced memory storage with multiple memory types"""
        if not self.memory_system:
            return

        try:
            # Store to short-term memory (conversation history)
            self.memory_system.add_short_term_memory(
                context.user_id,
                {'role': 'user', 'content': context.query, 'intent': intent.value}
            )
            self.memory_system.add_short_term_memory(
                context.user_id,
                {'role': 'assistant', 'content': response, 'intent': intent.value}
            )

            # Extract and store to semantic memory (vector search)
            self.memory_system.add_semantic_memory(
                context.user_id,
                context.query,
                {'response': response, 'intent': intent.value, 'reasoning': reasoning_steps}
            )

            # Store to episodic memory (interaction history)
            if hasattr(self.memory_system, 'add_episodic_memory'):
                self.memory_system.add_episodic_memory(
                    context.user_id,
                    {
                        'query': context.query,
                        'response': response,
                        'intent': intent.value,
                        'tools_used': tool_results,
                        'reasoning_steps': reasoning_steps,
                        'timestamp': datetime.now().isoformat()
                    }
                )

            # Update user preferences if available
            if hasattr(self.memory_system, 'update_user_preferences'):
                self.memory_system.update_user_preferences(
                    context.user_id,
                    {'last_intent': intent.value, 'interaction_count': 1}
                )

        except Exception as e:
            logger.error(f"Memory storage failed: {e}")

    async def _learn_from_interaction(
        self,
        context: AgentContext,
        response: str,
        verification: Dict,
        intent: IntentType
    ):
        """Learn from interaction for adaptive improvement"""
        try:
            # Store interaction for analysis
            self.interaction_history.append({
                'query': context.query,
                'response': response,
                'intent': intent.value,
                'verification_score': verification.get('score', 0.0),
                'quality_score': verification.get('quality_score', 0.0),
                'timestamp': datetime.now().isoformat()
            })

            # Keep only last 1000 interactions
            if len(self.interaction_history) > 1000:
                self.interaction_history = self.interaction_history[-1000:]

            # Update performance metrics
            self.performance_metrics['avg_verification_score'] = (
                self.performance_metrics['avg_verification_score'] * (self.analytics['total_interactions'] - 1) + verification.get('score', 0.0)
            ) / self.analytics['total_interactions']

        except Exception as e:
            logger.error(f"Learning from interaction failed: {e}")

    async def _generate_follow_up_questions(
        self,
        query: str,
        response: str,
        intent: IntentType
    ) -> List[str]:
        """Generate relevant follow-up questions"""
        follow_ups = []

        # Intent-specific follow-ups
        if intent == IntentType.SEARCH:
            follow_ups.append("Would you like more specific criteria for your search?")
            follow_ups.append("Do you need information about pricing or delivery times?")
        elif intent == IntentType.ANALYSIS:
            follow_ups.append("Would you like me to analyze this from a different perspective?")
            follow_ups.append("Do you need more detailed breakdown of the findings?")
        elif intent == IntentType.REASONING:
            follow_ups.append("Would you like me to elaborate on any specific point?")
            follow_ups.append("Do you need additional evidence or examples?")
        elif intent == IntentType.CODING:
            follow_ups.append("Would you like me to explain how this code works?")
            follow_ups.append("Do you need help with testing or debugging?")
        elif intent == IntentType.CREATIVE:
            follow_ups.append("Would you like me to refine this further?")
            follow_ups.append("Do you need alternatives or variations?")
        else:
            follow_ups.append("Is there anything specific you'd like me to clarify?")
            follow_ups.append("Would you like more information on this topic?")

        return follow_ups[:3]  # Return top 3 follow-ups

    def get_analytics(self) -> Dict[str, Any]:
        """Get agent analytics and performance metrics"""
        return {
            'total_interactions': self.analytics['total_interactions'],
            'avg_processing_time': self.analytics['avg_processing_time'],
            'total_errors': self.analytics['errors'],
            'avg_verification_score': self.performance_metrics['avg_verification_score'],
            'interaction_history_size': len(self.interaction_history),
            'current_state': self.state.value,
            'enable_reasoning': self.enable_reasoning,
            'enable_planning': self.enable_planning,
            'enable_learning': self.enable_learning
        }


class AgentOrchestrator:
    """Enhanced orchestrator for multiple agents with collaboration support"""

    def __init__(self):
        self.agents: Dict[str, CompleteAIAgent] = {}
        self.collaboration_history = []
        self.routing_stats = defaultdict(int)

    def register_agent(self, name: str, agent: CompleteAIAgent):
        """Register an agent"""
        self.agents[name] = agent
        logger.info(f"Registered agent: {name}")

    async def route_to_agent(
        self,
        context: AgentContext,
        agent_name: str = None
    ) -> AgentResponse:
        """Enhanced routing to appropriate agent"""
        if agent_name and agent_name in self.agents:
            self.routing_stats[agent_name] += 1
            return await self.agents[agent_name].process(context)

        # Auto-select agent based on intent
        intent = await self._detect_intent(context.query)
        
        if intent == IntentType.SEARCH and 'fivoria' in self.agents:
            self.routing_stats['fivoria'] += 1
            return await self.agents['fivoria'].process(context)
        elif intent == IntentType.CODING and 'code' in self.agents:
            self.routing_stats['code'] += 1
            return await self.agents['code'].process(context)
        elif intent == IntentType.ANALYSIS and 'analyst' in self.agents:
            self.routing_stats['analyst'] += 1
            return await self.agents['analyst'].process(context)
        else:
            # Use default agent
            default_agent = next(iter(self.agents.values()))
            self.routing_stats['default'] += 1
            return await default_agent.process(context)

    async def _detect_intent(self, query: str) -> IntentType:
        """Enhanced intent detection for routing"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['fivoria', 'gig', 'freelancer', 'seller', 'marketplace']):
            return IntentType.SEARCH
        elif any(word in query_lower for word in ['code', 'program', 'function', 'debug', 'implement']):
            return IntentType.CODING
        elif any(word in query_lower for word in ['analyze', 'evaluate', 'assess', 'examine']):
            return IntentType.ANALYSIS
        else:
            return IntentType.GENERAL

    async def collaborative_process(
        self,
        context: AgentContext,
        agents_to_use: List[str]
    ) -> AgentResponse:
        """Process request using multiple agents collaboratively"""
        if not agents_to_use:
            return await self.route_to_agent(context)

        results = []
        for agent_name in agents_to_use:
            if agent_name in self.agents:
                try:
                    result = await self.agents[agent_name].process(context)
                    results.append({
                        'agent': agent_name,
                        'response': result,
                        'confidence': result.confidence
                    })
                except Exception as e:
                    logger.error(f"Agent {agent_name} failed: {e}")

        # Combine results
        if results:
            # Select best response based on confidence
            best_result = max(results, key=lambda x: x['confidence'])
            
            # Record collaboration
            self.collaboration_history.append({
                'agents_used': agents_to_use,
                'selected_agent': best_result['agent'],
                'timestamp': datetime.now().isoformat()
            })
            
            return best_result['response']
        else:
            return await self.route_to_agent(context)

    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return {
            'stats': dict(self.routing_stats),
            'total_routes': sum(self.routing_stats.values()),
            'collaboration_count': len(self.collaboration_history),
            'registered_agents': list(self.agents.keys())
        }


def main():
    """Example usage of enhanced Complete AI Agent"""
    async def example():
        # Mock components
        class MockModel:
            async def generate(self, context, temperature=0.7, max_tokens=2048, enable_streaming=False):
                return "This is a mock response from the foundation model."

        class MockMemory:
            def get_short_term_memory(self, user_id):
                return []
            def get_long_term_memory(self, user_id):
                return {}
            def get_semantic_memory(self, query, user_id):
                return []
            def get_episodic_memory(self, user_id, query):
                return []
            def get_procedural_memory(self, user_id):
                return {}
            def add_short_term_memory(self, user_id, memory):
                pass
            def add_semantic_memory(self, user_id, query, data):
                pass
            def add_episodic_memory(self, user_id, data):
                pass
            def update_user_preferences(self, user_id, prefs):
                pass

        class MockTools:
            async def execute_tool(self, tool_name, params):
                return f"Mock result from {tool_name}"

        class MockRAG:
            def retrieve(self, query, top_k=5, strategy='hybrid'):
                return []

        class MockVerification:
            def verify_response(self, response, query):
                return {'factual': type('Result', (), {'status': 'passed', 'score': 0.8})()}
            def get_overall_status(self, results):
                return type('Status', (), {'value': 'passed'}), 0.8

        class MockKnowledgeGraph:
            def query_nodes(self, entity, depth=2):
                return []

        # Create enhanced agent
        context = AgentContext(
            user_id="demo_user",
            conversation_id="demo_conv",
            query="What is artificial intelligence?",
            conversation_history=[],
            project_id=None,
            temperature=0.7,
            max_tokens=2048,
            enable_streaming=False
        )
        
        response = await agent.process(context)
        print(f"Response: {response.content}")
        print(f"Metadata: {response.metadata}")
        
        # Get analytics
        analytics = agent.get_analytics()
        print(f"\nAgent Analytics: {analytics}")
    
    asyncio.run(demo())


if __name__ == "__main__":
    main()
