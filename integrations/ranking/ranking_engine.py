"""
Ranking Engine
Ranks and sorts results based on multiple factors
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RankingStrategy(Enum):
    """Ranking strategies"""
    RELEVANCE = "relevance"
    QUALITY = "quality"
    RECENCY = "recency"
    POPULARITY = "popularity"
    CUSTOM = "custom"
    HYBRID = "hybrid"


@dataclass
class RankingFactor:
    """A ranking factor with weight"""
    name: str
    weight: float
    scorer: Callable[[Any], float]
    normalize: bool = True


class RankingEngine:
    """Enhanced generic ranking engine with ML support and real-time learning"""

    def __init__(self, enable_ml: bool = False):
        self.factors: List[RankingFactor] = []
        self.strategy = RankingStrategy.HYBRID
        self.enable_ml = enable_ml
        self.ml_model = None
        self.feature_history = []  # Track features for online learning
        self.feedback_history = []  # Track user feedback
        self.performance_metrics = defaultdict(float)
        self.last_updated = datetime.now()

    def add_factor(self, name: str, weight: float, scorer: Callable, normalize: bool = True):
        """Add a ranking factor"""
        factor = RankingFactor(name=name, weight=weight, scorer=scorer, normalize=normalize)
        self.factors.append(factor)
        logger.info(f"Added ranking factor: {name} (weight: {weight})")

    def set_strategy(self, strategy: RankingStrategy):
        """Set ranking strategy"""
        self.strategy = strategy

    def rank(self, items: List[Any], context: Dict = None) -> List[Tuple[Any, float]]:
        """Rank items based on factors with enhanced scoring"""
        if not self.factors:
            logger.warning("No ranking factors defined")
            return [(item, 0.0) for item in items]

        scored_items = []
        start_time = datetime.now()

        for item in items:
            total_score = 0.0
            factor_scores = {}
            feature_vector = []

            for factor in self.factors:
                if not factor.enabled:
                    continue
                    
                try:
                    score = factor.scorer(item)
                    
                    if factor.normalize:
                        # Normalize score to 0-1 range
                        score = self._normalize_score(score, factor.name)
                    
                    factor_scores[factor.name] = score
                    total_score += factor.weight * score
                    feature_vector.append(score)
                    
                except Exception as e:
                    logger.error(f"Error scoring factor {factor.name}: {e}")
                    factor_scores[factor.name] = 0.0
                    feature_vector.append(0.0)

            # Apply ML model if enabled
            if self.enable_ml and self.ml_model is not None:
                try:
                    ml_score = self._apply_ml_model(feature_vector)
                    total_score = 0.7 * total_score + 0.3 * ml_score  # Blend with rule-based score
                except Exception as e:
                    logger.error(f"ML model error: {e}")

            scored_items.append((item, total_score, factor_scores, feature_vector))

        # Sort by total score descending
        scored_items.sort(key=lambda x: x[1], reverse=True)

        # Track performance
        duration = (datetime.now() - start_time).total_seconds()
        self.performance_metrics['total_rankings'] += 1
        self.performance_metrics['avg_duration'] = (self.performance_metrics['avg_duration'] * (self.performance_metrics['total_rankings'] - 1) + duration) / self.performance_metrics['total_rankings']
        self.last_updated = datetime.now()

        # Store feature history for online learning
        if self.enable_ml:
            for item, score, factor_scores, feature_vector in scored_items:
                self.feature_history.append({
                    'features': feature_vector,
                    'score': score,
                    'timestamp': datetime.now()
                })
                # Keep only last 10000 samples
                if len(self.feature_history) > 10000:
                    self.feature_history = self.feature_history[-10000:]

        return [(item, score) for item, score, _, _ in scored_items]

    def _normalize_score(self, score: float, factor_name: str) -> float:
        """Normalize score to 0-1 range with adaptive normalization"""
        # Use sigmoid normalization for robustness
        import math
        return 1 / (1 + math.exp(-score))

    def _apply_ml_model(self, feature_vector: List[float]) -> float:
        """Apply ML model for scoring"""
        if self.ml_model is None:
            return 0.5
        
        # Placeholder for ML model inference
        # In production, would use trained model (XGBoost, LightGBM, Neural Network)
        try:
            import numpy as np
            features = np.array(feature_vector).reshape(1, -1)
            prediction = self.ml_model.predict(features)[0]
            return float(prediction)
        except:
            return 0.5

    def train_ml_model(self, training_data: List[Dict], labels: List[int]):
        """Train ML ranking model"""
        if not self.enable_ml:
            logger.warning("ML ranking not enabled")
            return

        try:
            import numpy as np
            from sklearn.ensemble import GradientBoostingRegressor
            from sklearn.preprocessing import StandardScaler

            # Extract features
            X = np.array([item['features'] for item in training_data])
            y = np.array(labels)

            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Train model
            model = GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=42)
            model.fit(X_scaled, y)

            self.ml_model = model
            self.scaler = scaler
            logger.info("ML ranking model trained successfully")

        except ImportError:
            logger.warning("scikit-learn not available for ML ranking")
        except Exception as e:
            logger.error(f"ML model training failed: {e}")

    def record_feedback(self, item_id: str, user_rating: float):
        """Record user feedback for online learning"""
        self.feedback_history.append({
            'item_id': item_id,
            'rating': user_rating,
            'timestamp': datetime.now()
        })
        
        # Keep only last 1000 feedback entries
        if len(self.feedback_history) > 1000:
            self.feedback_history = self.feedback_history[-1000:]

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get ranking performance metrics"""
        return {
            'total_rankings': self.performance_metrics['total_rankings'],
            'avg_duration': self.performance_metrics['avg_duration'],
            'factors_enabled': sum(1 for f in self.factors if f.enabled),
            'total_factors': len(self.factors),
            'ml_enabled': self.enable_ml,
            'ml_model_trained': self.ml_model is not None,
            'feedback_count': len(self.feedback_history),
            'feature_history_size': len(self.feature_history),
            'last_updated': self.last_updated.isoformat()
        }

    def get_top_n(self, items: List[Any], n: int, context: Dict = None) -> List[Any]:
        """Get top N ranked items"""
        ranked = self.rank(items, context)
        return [item for item, score in ranked[:n]]


class GigRankingEngine(RankingEngine):
    """Enhanced specialized ranking engine for Fivoria gigs"""

    def __init__(self, enable_ml: bool = True):
        super().__init__(enable_ml=enable_ml)
        self._setup_default_factors()

    def _setup_default_factors(self):
        """Setup enhanced default ranking factors for gigs"""
        # Rating factor
        self.add_factor(
            name="rating",
            weight=0.25,
            scorer=lambda gig: gig.avg_rating / 5.0,
            description="Seller average rating",
            priority=10
        )

        # Orders factor (log scale)
        self.add_factor(
            name="orders",
            weight=0.20,
            scorer=lambda gig: self._log_scale(gig.total_orders),
            description="Total completed orders",
            priority=9
        )

        # Price factor (lower is better)
        self.add_factor(
            name="price",
            weight=0.15,
            scorer=lambda gig: 1 - min(gig.price / 1000, 1.0),
            description="Price competitiveness",
            priority=8
        )

        # Delivery time factor
        self.add_factor(
            name="delivery",
            weight=0.10,
            scorer=lambda gig: 1 - min(gig.delivery_time / 30, 1.0),
            description="Delivery speed",
            priority=7
        )

        # Response time factor
        self.add_factor(
            name="response",
            weight=0.10,
            scorer=lambda gig: 1 - min(gig.response_time / 48, 1.0),
            description="Response time",
            priority=6
        )

        # On-time delivery factor
        self.add_factor(
            name="ontime",
            weight=0.10,
            scorer=lambda gig: gig.on_time_delivery,
            description="On-time delivery rate",
            priority=5
        )

        # Reviews count factor
        self.add_factor(
            name="reviews",
            weight=0.05,
            scorer=lambda gig: self._log_scale(gig.reviews_count),
            description="Number of reviews",
            priority=4
        )

        # Enhanced factors
        self.add_factor(
            name="featured",
            weight=0.08,
            scorer=lambda gig: 1.0 if gig.featured else 0.0,
            description="Featured gig status",
            priority=3
        )

        self.add_factor(
            name="verified",
            weight=0.07,
            scorer=lambda gig: 1.0 if gig.verified else 0.0,
            description="Verified seller status",
            priority=2
        )

        self.add_factor(
            name="pro_seller",
            weight=0.06,
            scorer=lambda gig: 1.0 if gig.pro_seller else 0.0,
            description="Pro seller status",
            priority=1
        )

        self.add_factor(
            name="response_rate",
            weight=0.04,
            scorer=lambda gig: gig.response_rate,
            description="Response rate",
            priority=0
        )

        self.add_factor(
            name="cancellation_rate",
            weight=-0.05,  # Negative weight - lower cancellation is better
            scorer=lambda gig: 1.0 - gig.cancellation_rate,
            description="Cancellation rate (inverted)",
            priority=0
        )

    def _log_scale(self, value: int) -> float:
        """Apply log scale to value"""
        import math
        return min(math.log(value + 1) / 10, 1.0)


class DocumentRankingEngine(RankingEngine):
    """Specialized ranking engine for documents"""

    def __init__(self):
        super().__init__()
        self._setup_default_factors()

    def _setup_default_factors(self):
        """Setup default ranking factors for documents"""
        # Relevance score
        self.add_factor(
            name="relevance",
            weight=0.40,
            scorer=lambda doc: doc.get('score', 0.0)
        )

        # Recency factor
        self.add_factor(
            name="recency",
            weight=0.20,
            scorer=lambda doc: self._recency_score(doc.get('timestamp'))
        )

        # Authority factor
        self.add_factor(
            name="authority",
            weight=0.20,
            scorer=lambda doc: doc.get('authority', 0.5)
        )

        # Length factor (prefer moderate length)
        self.add_factor(
            name="length",
            weight=0.10,
            scorer=lambda doc: self._length_score(doc.get('content', ''))
        )

        # Source quality
        self.add_factor(
            name="source_quality",
            weight=0.10,
            scorer=lambda doc: doc.get('source_quality', 0.5)
        )

    def _recency_score(self, timestamp: str) -> float:
        """Calculate recency score"""
        if not timestamp:
            return 0.5
        
        from datetime import datetime
        try:
            doc_date = datetime.fromisoformat(timestamp)
            days_old = (datetime.now() - doc_date).days
            # Decay over 365 days
            return max(0, 1 - days_old / 365)
        except:
            return 0.5

    def _length_score(self, content: str) -> float:
        """Calculate length score (prefer moderate length)"""
        length = len(content)
        # Ideal range: 500-5000 characters
        if 500 <= length <= 5000:
            return 1.0
        elif length < 500:
            return length / 500
        else:
            return max(0, 1 - (length - 5000) / 10000)


class LearningToRank:
    """Learning to rank using historical data"""

    def __init__(self):
        self.model = None
        self.feature_names = []

    def train(self, training_data: List[Dict], labels: List[int]):
        """Train ranking model"""
        # Placeholder for ML-based ranking
        # In production, would use XGBoost, LightGBM, or neural ranking models
        logger.info("Training ranking model")
        self.feature_names = list(training_data[0].keys()) if training_data else []

    def predict(self, features: Dict) -> float:
        """Predict ranking score"""
        # Placeholder - would use trained model
        return 0.5

    def rank(self, items: List[Dict]) -> List[Dict]:
        """Rank items using learned model"""
        scored = []
        for item in items:
            score = self.predict(item)
            scored.append((item, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [item for item, score in scored]


class AdaptiveRankingEngine(RankingEngine):
    """Enhanced adaptive ranking engine that adjusts weights based on context and user feedback"""

    def __init__(self, enable_auto_tuning: bool = True):
        super().__init__()
        self.context_weights: Dict[str, Dict[str, float]] = {}
        self.enable_auto_tuning = enable_auto_tuning
        self.user_preferences: Dict[str, Dict[str, float]] = {}  # Per-user preferences
        self.global_preferences: Dict[str, float] = {}  # Global learned preferences
        self.tuning_history = []

    def set_context_weights(self, context: str, weights: Dict[str, float]):
        """Set weights for a specific context"""
        self.context_weights[context] = weights
        logger.info(f"Set weights for context: {context}")

    def rank(self, items: List[Any], context: Dict = None) -> List[Tuple[Any, float]]:
        """Rank items with context-aware and user-aware weights"""
        # Determine context
        context_type = context.get('type', 'default') if context else 'default'
        user_id = context.get('user_id') if context else None

        # Apply context-specific weights if available
        if context_type in self.context_weights:
            original_weights = {f.name: f.weight for f in self.factors}
            
            # Update weights
            for factor in self.factors:
                if factor.name in self.context_weights[context_type]:
                    factor.weight = self.context_weights[context_type][factor.name]

        # Apply user-specific weights if available
        if user_id and user_id in self.user_preferences:
            original_weights = {f.name: f.weight for f in self.factors}
            
            for factor in self.factors:
                if factor.name in self.user_preferences[user_id]:
                    factor.weight = self.user_preferences[user_id][factor.name]

        # Apply global learned preferences
        if self.global_preferences:
            for factor in self.factors:
                if factor.name in self.global_preferences:
                    # Blend with current weight
                    factor.weight = 0.7 * factor.weight + 0.3 * self.global_preferences[factor.name]

        # Rank with adjusted weights
        results = super().rank(items, context)

        # Restore original weights
        if context_type in self.context_weights or (user_id and user_id in self.user_preferences) or self.global_preferences:
            for factor in self.factors:
                if factor.name in original_weights:
                    factor.weight = original_weights[factor.name]

        return results

    def set_context_weights(self, context: str, weights: Dict[str, float]):
        """Set weights for a specific context"""
        self.context_weights[context] = weights
        logger.info(f"Set weights for context: {context}")

    def set_user_preferences(self, user_id: str, preferences: Dict[str, float]):
        """Set ranking preferences for a specific user"""
        self.user_preferences[user_id] = preferences
        logger.info(f"Set preferences for user: {user_id}")

    def learn_from_feedback(self, feedback: List[Dict]):
        """Learn from user feedback to adjust global preferences"""
        if not self.enable_auto_tuning:
            return

        try:
            # Analyze feedback to adjust weights
            factor_adjustments = defaultdict(float)
            
            for fb in feedback:
                if fb.get('satisfied'):
                    # Increase weight of factors that contributed to satisfaction
                    for factor_name in fb.get('important_factors', []):
                        factor_adjustments[factor_name] += 0.01
                else:
                    # Decrease weight of factors that contributed to dissatisfaction
                    for factor_name in fb.get('problematic_factors', []):
                        factor_adjustments[factor_name] -= 0.01

            # Apply adjustments with smoothing
            for factor_name, adjustment in factor_adjustments.items():
                current_weight = self.global_preferences.get(factor_name, 0.5)
                new_weight = max(0.0, min(1.0, current_weight + adjustment))
                self.global_preferences[factor_name] = new_weight

            self.tuning_history.append({
                'adjustments': dict(factor_adjustments),
                'timestamp': datetime.now().isoformat()
            })

            logger.info(f"Learned from {len(feedback)} feedback samples")

        except Exception as e:
            logger.error(f"Learning from feedback failed: {e}")

    def get_tuning_stats(self) -> Dict[str, Any]:
        """Get tuning statistics"""
        return {
            'context_count': len(self.context_weights),
            'user_count': len(self.user_preferences),
            'global_preferences': self.global_preferences,
            'tuning_history_count': len(self.tuning_history),
            'auto_tuning_enabled': self.enable_auto_tuning
        }


def main():
    """Example usage"""
    from integrations.fivoria.marketplace_api import Gig, GigCategory

    # Create gig ranking engine
    ranking_engine = GigRankingEngine()

    # Sample gigs
    gigs = [
        Gig(
            gig_id="1",
            title="Professional Web Development",
            description="Full-stack web development services",
            seller_id="s1",
            seller_name="John Doe",
            seller_rating=4.8,
            seller_level="top_rated",
            price=500,
            currency="GBP",
            category=GigCategory.WEB_DEVELOPMENT,
            tags=["web", "development", "full-stack"],
            delivery_time=7,
            total_orders=150,
            on_time_delivery=0.95,
            response_time=2.0,
            location="UK",
            languages=["en"],
            portfolio_items=[],
            reviews_count=120,
            avg_rating=4.8
        ),
        Gig(
            gig_id="2",
            title="Quick Website Setup",
            description="Basic website setup",
            seller_id="s2",
            seller_name="Jane Smith",
            seller_rating=4.5,
            seller_level="level_2",
            price=200,
            currency="GBP",
            category=GigCategory.WEB_DEVELOPMENT,
            tags=["web", "setup"],
            delivery_time=3,
            total_orders=50,
            on_time_delivery=0.90,
            response_time=5.0,
            location="US",
            languages=["en"],
            portfolio_items=[],
            reviews_count=45,
            avg_rating=4.5
        )
    ]

    # Rank gigs
    ranked = ranking_engine.rank(gigs)

    print("Ranked Gigs:")
    for gig, score in ranked:
        print(f"{gig.title}: {score:.3f}")


if __name__ == "__main__":
    main()
