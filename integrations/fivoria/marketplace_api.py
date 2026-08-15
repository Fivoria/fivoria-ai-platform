"""
Fivoria Marketplace Integration
Enhanced version with advanced features, caching, analytics, and real-time updates
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


class GigCategory(Enum):
    """Gig categories"""
    WEB_DEVELOPMENT = "web_development"
    LOGO_DESIGN = "logo_design"
    GRAPHIC_DESIGN = "graphic_design"
    WRITING = "writing"
    TRANSLATION = "translation"
    VIDEO_EDITING = "video_editing"
    SEO = "seo"
    DIGITAL_MARKETING = "digital_marketing"
    MOBILE_APPS = "mobile_apps"
    DATA_ENTRY = "data_entry"


@dataclass
class Gig:
    """Enhanced Fivoria gig representation"""
    gig_id: str
    title: str
    description: str
    seller_id: str
    seller_name: str
    seller_rating: float
    seller_level: str
    price: float
    currency: str
    category: GigCategory
    tags: List[str]
    delivery_time: int  # days
    total_orders: int
    on_time_delivery: float
    response_time: float  # hours
    location: str
    languages: List[str]
    portfolio_items: List[str]
    reviews_count: int
    avg_rating: float
    # Enhanced fields
    featured: bool = False
    verified: bool = False
    pro_seller: bool = False
    last_updated: datetime = field(default_factory=datetime.now)
    availability_status: str = "available"  # available, busy, offline
    response_rate: float = 0.0
    cancellation_rate: float = 0.0
    portfolio_count: int = 0
    skills: List[str] = field(default_factory=list)
    education: List[Dict] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    languages_spoken: List[Dict] = field(default_factory=list)  # {'language': 'English', 'level': 'native'}
    work_history: List[Dict] = field(default_factory=list)


@dataclass
class SearchFilter:
    """Search filters for gigs"""
    category: Optional[GigCategory] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_rating: Optional[float] = None
    max_delivery_time: Optional[int] = None
    location: Optional[str] = None
    language: Optional[str] = None
    seller_level: Optional[str] = None
    tags: List[str] = None


class FivoriaMarketplaceAPI:
    """Enhanced API client for Fivoria marketplace with caching and analytics"""

    def __init__(self, base_url: str = "https://api.fivoria.com", api_key: str = None, cache_ttl: int = 300):
        self.base_url = base_url
        self.api_key = api_key
        self.cache_ttl = cache_ttl  # Cache time-to-live in seconds
        self.session = None
        self.cache: Dict[str, Tuple[Any, datetime]] = {}  # Response cache
        self.analytics = defaultdict(int)  # Usage analytics
        self.rate_limit_remaining = 1000
        self.rate_limit_reset = datetime.now() + timedelta(hours=1)

    async def _get_session(self):
        """Get or create HTTP session"""
        if self.session is None:
            import aiohttp
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def search_gigs(
        self,
        query: str,
        filters: SearchFilter = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Gig]:
        """Search for gigs with enhanced features"""
        # Check cache first
        cache_key = self._generate_cache_key("search", query, filters, limit, offset)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            self.analytics['cache_hits'] += 1
            return cached_result

        session = await self._get_session()

        params = {
            'q': query,
            'limit': limit,
            'offset': offset
        }

        if filters:
            if filters.category:
                params['category'] = filters.category.value
            if filters.min_price is not None:
                params['min_price'] = filters.min_price
            if filters.max_price is not None:
                params['max_price'] = filters.max_price
            if filters.min_rating is not None:
                params['min_rating'] = filters.min_rating
            if filters.max_delivery_time is not None:
                params['max_delivery_time'] = filters.max_delivery_time
            if filters.location:
                params['location'] = filters.location
            if filters.language:
                params['language'] = filters.language
            if filters.seller_level:
                params['seller_level'] = filters.seller_level
            if filters.tags:
                params['tags'] = ','.join(filters.tags)
            # Enhanced filters
            if filters.featured_only:
                params['featured'] = 'true'
            if filters.verified_only:
                params['verified'] = 'true'
            if filters.pro_sellers_only:
                params['pro'] = 'true'
            if filters.min_orders is not None:
                params['min_orders'] = filters.min_orders
            if filters.min_response_rate is not None:
                params['min_response_rate'] = filters.min_response_rate
            if filters.max_cancellation_rate is not None:
                params['max_cancellation_rate'] = filters.max_cancellation_rate
            if filters.availability_status:
                params['availability'] = filters.availability_status
            if filters.skills:
                params['skills'] = ','.join(filters.skills)
            if filters.languages_spoken:
                params['languages'] = ','.join(filters.languages_spoken)
            params['sort_by'] = filters.sort_by
            params['sort_order'] = filters.sort_order

        try:
            # Check rate limit
            if self.rate_limit_remaining <= 0:
                await self._wait_for_rate_limit_reset()

            async with session.get(f"{self.base_url}/v1/gigs/search", params=params) as response:
                self.analytics['api_calls'] += 1
                
                # Update rate limit from headers
                self._update_rate_limit(response.headers)

                if response.status == 200:
                    data = await response.json()
                    gigs = [self._parse_gig(gig_data) for gig_data in data.get('gigs', [])]
                    
                    # Cache the result
                    self._set_cache(cache_key, gigs)
                    
                    return gigs
                elif response.status == 429:
                    # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Retry after {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    return await self.search_gigs(query, filters, limit, offset)
                else:
                    logger.error(f"Search failed: {response.status}")
                    self.analytics['errors'] += 1
                    return []
        except Exception as e:
            logger.error(f"Search error: {e}")
            self.analytics['errors'] += 1
            return []

    def _generate_cache_key(self, operation: str, *args) -> str:
        """Generate cache key from parameters"""
        key_str = f"{operation}:" + ":".join(str(arg) for arg in args)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return value
            else:
                del self.cache[key]
        return None

    def _set_cache(self, key: str, value: Any):
        """Set value in cache with current timestamp"""
        self.cache[key] = (value, datetime.now())

    def _update_rate_limit(self, headers: Dict):
        """Update rate limit from response headers"""
        if 'X-RateLimit-Remaining' in headers:
            self.rate_limit_remaining = int(headers['X-RateLimit-Remaining'])
        if 'X-RateLimit-Reset' in headers:
            self.rate_limit_reset = datetime.fromtimestamp(int(headers['X-RateLimit-Reset']))

    async def _wait_for_rate_limit_reset(self):
        """Wait for rate limit to reset"""
        now = datetime.now()
        if self.rate_limit_reset > now:
            wait_seconds = (self.rate_limit_reset - now).total_seconds()
            logger.info(f"Rate limit reached. Waiting {wait_seconds} seconds")
            await asyncio.sleep(wait_seconds)
            self.rate_limit_remaining = 1000

    async def get_gig(self, gig_id: str) -> Optional[Gig]:
        """Get gig details by ID"""
        session = await self._get_session()

        try:
            async with session.get(f"{self.base_url}/v1/gigs/{gig_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_gig(data)
                else:
                    logger.error(f"Get gig failed: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Get gig error: {e}")
            return None

    async def get_seller_gigs(self, seller_id: str, limit: int = 20) -> List[Gig]:
        """Get all gigs from a seller"""
        session = await self._get_session()

        try:
            async with session.get(f"{self.base_url}/v1/sellers/{seller_id}/gigs", params={'limit': limit}) as response:
                if response.status == 200:
                    data = await response.json()
                    return [self._parse_gig(gig_data) for gig_data in data.get('gigs', [])]
                else:
                    logger.error(f"Get seller gigs failed: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Get seller gigs error: {e}")
            return []

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get available categories"""
        session = await self._get_session()

        try:
            async with session.get(f"{self.base_url}/v1/categories") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('categories', [])
                else:
                    logger.error(f"Get categories failed: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Get categories error: {e}")
            return []

    def _parse_gig(self, data: Dict) -> Gig:
        """Parse gig data from API response with enhanced fields"""
        return Gig(
            gig_id=data['id'],
            title=data['title'],
            description=data['description'],
            seller_id=data['seller']['id'],
            seller_name=data['seller']['name'],
            seller_rating=data['seller'].get('rating', 0.0),
            seller_level=data['seller'].get('level', 'new'),
            price=data['price']['amount'],
            currency=data['price']['currency'],
            category=GigCategory(data['category']),
            tags=data.get('tags', []),
            delivery_time=data.get('delivery_time', 7),
            total_orders=data.get('total_orders', 0),
            on_time_delivery=data.get('on_time_delivery', 0.0),
            response_time=data.get('response_time', 24.0),
            location=data.get('location', ''),
            languages=data.get('languages', ['en']),
            portfolio_items=data.get('portfolio_items', []),
            reviews_count=data.get('reviews_count', 0),
            avg_rating=data.get('avg_rating', 0.0),
            # Enhanced fields
            featured=data.get('featured', False),
            verified=data.get('verified', False),
            pro_seller=data.get('pro_seller', False),
            last_updated=datetime.fromisoformat(data.get('last_updated', datetime.now().isoformat())),
            availability_status=data.get('availability_status', 'available'),
            response_rate=data.get('response_rate', 0.0),
            cancellation_rate=data.get('cancellation_rate', 0.0),
            portfolio_count=data.get('portfolio_count', 0),
            skills=data.get('skills', []),
            education=data.get('education', []),
            certifications=data.get('certifications', []),
            languages_spoken=data.get('languages_spoken', []),
            work_history=data.get('work_history', [])
        )

    async def get_analytics(self) -> Dict[str, Any]:
        """Get API usage analytics"""
        return {
            'api_calls': self.analytics['api_calls'],
            'cache_hits': self.analytics['cache_hits'],
            'cache_misses': self.analytics['api_calls'] - self.analytics['cache_hits'],
            'errors': self.analytics['errors'],
            'cache_size': len(self.cache),
            'rate_limit_remaining': self.rate_limit_remaining,
            'rate_limit_reset': self.rate_limit_reset.isoformat()
        }

    def clear_cache(self):
        """Clear the cache"""
        self.cache.clear()
        logger.info("Cache cleared")


class FivoriaSearchEngine:
    """Search engine for Fivoria marketplace with ranking"""

    def __init__(self, api: FivoriaMarketplaceAPI):
        self.api = api

    async def search(
        self,
        query: str,
        filters: SearchFilter = None,
        ranking_weights: Dict[str, float] = None
    ) -> List[Gig]:
        """Search and rank gigs"""
        # Get raw results from API
        gigs = await self.api.search_gigs(query, filters)

        if not gigs:
            return []

        # Apply ranking
        ranked_gigs = self._rank_gigs(gigs, query, ranking_weights)

        return ranked_gigs

    def _rank_gigs(
        self,
        gigs: List[Gig],
        query: str,
        weights: Dict[str, float] = None
    ) -> List[Gig]:
        """Rank gigs by relevance and quality"""
        if weights is None:
            weights = {
                'rating': 0.3,
                'orders': 0.2,
                'price': 0.15,
                'delivery_time': 0.1,
                'response_time': 0.1,
                'text_relevance': 0.15
            }

        scored_gigs = []

        for gig in gigs:
            score = self._calculate_score(gig, query, weights)
            scored_gigs.append((gig, score))

        # Sort by score descending
        scored_gigs.sort(key=lambda x: x[1], reverse=True)

        return [gig for gig, score in scored_gigs]

    def _calculate_score(self, gig: Gig, query: str, weights: Dict[str, float]) -> float:
        """Calculate ranking score for a gig"""
        score = 0.0

        # Rating score (normalized 0-1)
        rating_score = gig.avg_rating / 5.0
        score += weights['rating'] * rating_score

        # Orders score (log scale)
        import math
        orders_score = min(math.log(gig.total_orders + 1) / 10, 1.0)
        score += weights['orders'] * orders_score

        # Price score (lower is better, normalized)
        # Assume max reasonable price is 1000
        price_score = max(0, 1 - (gig.price / 1000))
        score += weights['price'] * price_score

        # Delivery time score (faster is better)
        # Assume max reasonable delivery is 30 days
        delivery_score = max(0, 1 - (gig.delivery_time / 30))
        score += weights['delivery_time'] * delivery_score

        # Response time score (faster is better)
        # Assume max reasonable response is 48 hours
        response_score = max(0, 1 - (gig.response_time / 48))
        score += weights['response_time'] * response_score

        # Text relevance score
        relevance_score = self._calculate_text_relevance(gig, query)
        score += weights['text_relevance'] * relevance_score

        return score

    def _calculate_text_relevance(self, gig: Gig, query: str) -> float:
        """Calculate text relevance score"""
        query_terms = set(query.lower().split())
        
        # Search in title
        title_terms = set(gig.title.lower().split())
        title_match = len(query_terms & title_terms) / max(len(query_terms), 1)
        
        # Search in description
        desc_terms = set(gig.description.lower().split())
        desc_match = len(query_terms & desc_terms) / max(len(query_terms), 1)
        
        # Search in tags
        tag_terms = set(tag.lower() for tag in gig.tags)
        tag_match = len(query_terms & tag_terms) / max(len(query_terms), 1)

        # Weight title higher
        return 0.5 * title_match + 0.3 * desc_match + 0.2 * tag_match

    async def get_recommendations(
        self,
        gig_id: str,
        limit: int = 5
    ) -> List[Gig]:
        """Get similar gig recommendations"""
        gig = await self.api.get_gig(gig_id)
        if not gig:
            return []

        # Search for similar gigs in same category
        filters = SearchFilter(category=gig.category, max_price=gig.price * 1.5)
        similar = await self.api.search_gigs(gig.title, filters, limit=limit + 1)

        # Remove the original gig
        similar = [g for g in similar if g.gig_id != gig_id]

        return similar[:limit]


class FivoriaIntentDetector:
    """Detects user intent for Fivoria-related queries"""

    def __init__(self):
        self.intent_patterns = {
            'search_gig': [
                r'find.*gig',
                r'search.*freelancer',
                r'best.*designer',
                r'best.*developer',
                r'looking for.*',
                r'need.*gig'
            ],
            'get_price': [
                r'how much',
                r'price.*gig',
                r'cost.*service',
                r'budget.*'
            ],
            'compare_sellers': [
                r'compare.*',
                r'better.*seller',
                r'which.*is better'
            ],
            'get_reviews': [
                r'reviews',
                r'rating',
                r'feedback',
                r'what.*people say'
            ],
            'get_delivery': [
                r'delivery.*time',
                r'how long',
                r'when.*deliver',
                r'turnaround'
            ]
        }

    def detect_intent(self, query: str) -> Tuple[str, float]:
        """Detect the primary intent of a query"""
        import re

        scores = {}
        query_lower = query.lower()

        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1
            scores[intent] = score

        if not scores or max(scores.values()) == 0:
            return 'general', 0.0

        best_intent = max(scores, key=scores.get)
        confidence = scores[best_intent] / len(self.intent_patterns[best_intent])

        return best_intent, confidence

    def extract_search_params(self, query: str) -> Dict[str, Any]:
        """Extract search parameters from query"""
        import re

        params = {}

        # Extract price range
        price_match = re.search(r'£(\d+)', query)
        if price_match:
            params['max_price'] = float(price_match.group(1))

        # Extract location
        location_patterns = [
            r'in\s+(\w+)',
            r'from\s+(\w+)'
        ]
        for pattern in location_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                params['location'] = match.group(1)
                break

        # Extract category keywords
        category_keywords = {
            'web developer': GigCategory.WEB_DEVELOPMENT,
            'logo design': GigCategory.LOGO_DESIGN,
            'graphic design': GigCategory.GRAPHIC_DESIGN,
            'writer': GigCategory.WRITING,
            'translator': GigCategory.TRANSLATION,
            'video': GigCategory.VIDEO_EDITING,
            'seo': GigCategory.SEO,
            'marketing': GigCategory.DIGITAL_MARKETING,
            'mobile app': GigCategory.MOBILE_APPS
        }

        for keyword, category in category_keywords.items():
            if keyword in query.lower():
                params['category'] = category
                break

        return params


def main():
    """Example usage"""
    async def example():
        api = FivoriaMarketplaceAPI(api_key="demo_key")
        search_engine = FivoriaSearchEngine(api)
        intent_detector = FivoriaIntentDetector()

        query = "Find best web developers in Pakistan under £500"
        
        # Detect intent
        intent, confidence = intent_detector.detect_intent(query)
        print(f"Intent: {intent} (confidence: {confidence:.2f})")

        # Extract search params
        params = intent_detector.extract_search_params(query)
        print(f"Search params: {params}")

        # Create filters
        filters = SearchFilter(
            category=params.get('category'),
            max_price=params.get('max_price'),
            location=params.get('location')
        )

        # Search
        results = await search_engine.search(query, filters)
        print(f"Found {len(results)} gigs")

        for gig in results[:3]:
            print(f"- {gig.title} by {gig.seller_name} (£{gig.price})")

        await api.close()

    asyncio.run(example())


if __name__ == "__main__":
    main()
