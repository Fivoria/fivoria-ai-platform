"""
Fivoria AI Test Suite
Comprehensive testing for all components
"""

import unittest
import torch
import numpy as np
from datetime import datetime

# Import components to test
import sys
sys.path.append('.')

from model_platform.architecture.config import ModelConfig, get_100M_config
from model_platform.architecture.transformer import FivoriaTransformer
from model_platform.training.trainer import Trainer, create_optimizer
from data_platform.tokenization.tokenizer import FivoriaTokenizer, TokenizerConfig
from knowledge_layer.rag.retrieval import RAGSystem, Document
from knowledge_layer.tools.tool_framework import ToolRegistry, CalculatorTool
from knowledge_layer.memory.memory_system import MemorySystem
from security.auth import SecurityManager, Role
from observability.metrics import MetricsRegistry


class TestTokenizer(unittest.TestCase):
    """Test tokenizer functionality"""
    
    def setUp(self):
        self.config = TokenizerConfig(vocab_size=10000)
        self.tokenizer = FivoriaTokenizer(self.config)
    
    def test_encode_decode(self):
        """Test encoding and decoding"""
        text = "Hello, world!"
        tokens = self.tokenizer.encode(text)
        decoded = self.tokenizer.decode(tokens)
        self.assertIn("Hello", decoded)
    
    def test_code_tokenization(self):
        """Test code tokenization"""
        code = "def hello(): print('Hi')"
        tokens = self.tokenizer.tokenize_code(code)
        self.assertGreater(len(tokens), 0)
    
    def test_math_tokenization(self):
        """Test math tokenization"""
        math_expr = "E = mc^2"
        tokens = self.tokenizer.tokenize_math(math_expr)
        self.assertGreater(len(tokens), 0)


class TestModelArchitecture(unittest.TestCase):
    """Test model architecture"""
    
    def setUp(self):
        self.config = get_100M_config()
        self.model = FivoriaTransformer(self.config)
    
    def test_model_creation(self):
        """Test model creation"""
        self.assertIsNotNone(self.model)
        params = sum(p.numel() for p in self.model.parameters())
        self.assertGreater(params, 0)
    
    def test_forward_pass(self):
        """Test forward pass"""
        batch_size = 2
        seq_len = 64
        input_ids = torch.randint(0, self.config.vocab_size, (batch_size, seq_len))
        
        logits, _ = self.model(input_ids)
        self.assertEqual(logits.shape, (batch_size, seq_len, self.config.vocab_size))
    
    def test_parameter_estimation(self):
        """Test parameter estimation"""
        params = self.config.estimate_parameters()
        self.assertGreater(params, 0)
    
    def test_memory_estimation(self):
        """Test memory estimation"""
        memory = self.config.estimate_memory()
        self.assertIn("weights_gb", memory)
        self.assertIn("total_training_gb", memory)


class TestTraining(unittest.TestCase):
    """Test training components"""
    
    def setUp(self):
        self.config = get_100M_config()
        self.model = FivoriaTransformer(self.config)
        self.optimizer = create_optimizer(self.model, self.config)
    
    def test_optimizer_creation(self):
        """Test optimizer creation"""
        self.assertIsNotNone(self.optimizer)
    
    def test_checkpoint_manager(self):
        """Test checkpoint manager"""
        from model_platform.training.trainer import CheckpointManager
        manager = CheckpointManager("./test_checkpoints", max_checkpoints=3)
        self.assertIsNotNone(manager)
    
    def test_training_step(self):
        """Test single training step"""
        batch = {
            "input_ids": torch.randint(0, self.config.vocab_size, (2, 32)),
            "labels": torch.randint(0, self.config.vocab_size, (2, 32))
        }
        
        # Forward pass
        logits, _ = self.model(batch["input_ids"])
        
        # Calculate loss
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = batch["labels"][..., 1:].contiguous()
        loss_fn = torch.nn.CrossEntropyLoss(ignore_index=-100)
        loss = loss_fn(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
        
        self.assertIsNotNone(loss)


class TestRAG(unittest.TestCase):
    """Test RAG system"""
    
    def setUp(self):
        self.rag = RAGSystem()
    
    def test_add_documents(self):
        """Test adding documents"""
        docs = [
            Document(
                id="doc1",
                text="Test document",
                metadata={"source": "test"}
            )
        ]
        docs[0].embedding = np.random.randn(768)
        self.rag.add_documents(docs)
        self.assertEqual(len(self.rag.vector_store.documents), 1)
    
    def test_retrieval(self):
        """Test document retrieval"""
        docs = [
            Document(
                id="doc1",
                text="Test document about AI",
                metadata={"source": "test"}
            )
        ]
        docs[0].embedding = np.random.randn(768)
        self.rag.add_documents(docs)
        
        query_embedding = np.random.randn(768)
        results = self.rag.retrieve("AI", query_embedding)
        self.assertGreaterEqual(len(results), 0)


class TestTools(unittest.TestCase):
    """Test tool framework"""
    
    def setUp(self):
        self.registry = ToolRegistry()
        self.registry.register(CalculatorTool())
    
    def test_tool_registration(self):
        """Test tool registration"""
        self.assertIn("calculator", self.registry.tools)
    
    def test_tool_execution(self):
        """Test tool execution"""
        import asyncio
        
        async def test():
            result = await self.registry.execute_tool(
                "calculator",
                {"expression": "2 + 2"}
            )
            return result
        
        result = asyncio.run(test())
        self.assertTrue(result.success)


class TestMemory(unittest.TestCase):
    """Test memory system"""
    
    def setUp(self):
        self.memory = MemorySystem()
    
    def test_short_term_memory(self):
        """Test short-term memory"""
        self.memory.add_conversation_message(
            session_id="test",
            user_id=1,
            role="user",
            content="Hello"
        )
        conversation = self.memory.short_term.get_conversation("test")
        self.assertEqual(len(conversation), 1)
    
    def test_long_term_memory(self):
        """Test long-term memory"""
        self.memory.long_term.set_preference(1, "theme", "dark")
        pref = self.memory.long_term.get_preference(1, "theme")
        self.assertEqual(pref, "dark")
    
    def test_semantic_memory(self):
        """Test semantic memory"""
        import numpy as np
        embedding = np.random.randn(768)
        self.memory.add_semantic_memory(1, "Test", embedding)
        self.assertGreater(len(self.memory.semantic.memories), 0)


class TestSecurity(unittest.TestCase):
    """Test security components"""
    
    def setUp(self):
        self.security = SecurityManager("test-secret")
    
    def test_user_registration(self):
        """Test user registration"""
        user = self.security.register_user(
            username="test",
            email="test@test.com",
            password="password",
            role=Role.USER
        )
        self.assertIsNotNone(user)
    
    def test_api_key_generation(self):
        """Test API key generation"""
        user = self.security.register_user(
            username="test",
            email="test@test.com",
            password="password"
        )
        api_key = self.security.create_api_key(user.id, "Test Key")
        self.assertIsNotNone(api_key)
    
    def test_authorization(self):
        """Test authorization"""
        user = self.security.register_user(
            username="test",
            email="test@test.com",
            password="password",
            role=Role.ADMIN
        )
        authorized = self.security.authorize(user.id, security.rbac.Permission.ADMIN)
        self.assertTrue(authorized)


class TestMetrics(unittest.TestCase):
    """Test metrics system"""
    
    def setUp(self):
        self.registry = MetricsRegistry()
    
    def test_counter(self):
        """Test counter metric"""
        counter = self.registry.counter("test_counter")
        counter.inc()
        self.assertEqual(counter.get(), 1.0)
    
    def test_gauge(self):
        """Test gauge metric"""
        gauge = self.registry.gauge("test_gauge")
        gauge.set(42.0)
        self.assertEqual(gauge.get(), 42.0)
    
    def test_histogram(self):
        """Test histogram metric"""
        histogram = self.registry.histogram("test_histogram")
        histogram.observe(1.5)
        self.assertEqual(histogram.get_count(), 1)
    
    def test_metrics_export(self):
        """Test metrics export"""
        counter = self.registry.counter("test_counter")
        counter.inc()
        
        metrics = self.registry.get_all_metrics()
        self.assertGreater(len(metrics), 0)


class TestModelRegistry(unittest.TestCase):
    """Test model registry"""
    
    def setUp(self):
        from model_platform.registry.model_registry import ModelRegistry, ModelArchitecture
        self.registry = ModelRegistry("./test_registry")
    
    def test_model_registration(self):
        """Test model registration"""
        model = self.registry.register_model(
            model_id="test-model",
            name="Test Model",
            description="Test",
            architecture=ModelArchitecture.DENSE_TRANSFORMER
        )
        self.assertIsNotNone(model)
    
    def test_version_registration(self):
        """Test version registration"""
        from model_platform.registry.model_registry import ModelConfig, ModelArchitecture
        from model_platform.architecture.config import get_100M_config
        
        config = get_100M_config()
        
        version = self.registry.register_version(
            model_id="test-model",
            version="v1.0",
            config=ModelConfig(
                num_layers=config.num_layers,
                hidden_dim=config.hidden_dim,
                num_attention_heads=config.num_attention_heads,
                num_kv_heads=config.num_kv_heads,
                ffn_dim=config.ffn_dim,
                vocab_size=config.vocab_size,
                max_seq_len=config.max_seq_len,
                architecture=ModelArchitecture.DENSE_TRANSFORMER
            ),
            parameter_count=100_000_000,
            tokenizer_version="v1.0",
            dataset_version="v1.0",
            training_run_id="test-run",
            checkpoint_path="/test"
        )
        self.assertIsNotNone(version)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTokenizer))
    suite.addTests(loader.loadTestsFromTestCase(TestModelArchitecture))
    suite.addTests(loader.loadTestsFromTestCase(TestTraining))
    suite.addTests(loader.loadTestsFromTestCase(TestRAG))
    suite.addTests(loader.loadTestsFromTestCase(TestTools))
    suite.addTests(loader.loadTestsFromTestCase(TestMemory))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurity))
    suite.addTests(loader.loadTestsFromTestCase(TestMetrics))
    suite.addTests(loader.loadTestsFromTestCase(TestModelRegistry))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    print("Fivoria AI Test Suite")
    print("=" * 50)
    result = run_tests()
    
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
