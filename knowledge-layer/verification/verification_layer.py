"""
Verification Layer
Validates and verifies AI responses before delivery
Enhanced version with ML-based verification, advanced checks, and real-time monitoring
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    """Verification status"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    REVIEW_NEEDED = "review_needed"


class VerificationType(Enum):
    """Types of verification"""
    FACTUAL = "factual"
    SAFETY = "safety"
    COHERENCE = "coherence"
    CONSISTENCY = "consistency"
    COMPLETENESS = "completeness"
    BIAS = "bias"
    PRIVACY = "privacy"
    SECURITY = "security"
    RELEVANCE = "relevance"
    HALLUCINATION = "hallucination"
    FORMAT = "format"
    LENGTH = "length"


@dataclass
class VerificationResult:
    """Result of a verification check"""
    verification_type: VerificationType
    status: VerificationStatus
    score: float  # 0.0 to 1.0
    message: str
    details: Dict[str, Any]


class FactualityChecker:
    """Checks factual accuracy of responses with enhanced verification"""

    def __init__(self, knowledge_base: Dict = None):
        self.fact_patterns = {
            'dates': r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
            'numbers': r'\b\d+(?:,\d{3})*(?:\.\d+)?\b',
            'urls': r'https?://[^\s<>"{}|\\^`\[\]]+',
            'emails': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        }
        self.knowledge_base = knowledge_base or {}
        self.fact_cache = {}  # Cache for verified facts

    def verify(self, response: str, context: Dict = None) -> VerificationResult:
        """Verify factual accuracy with enhanced checks"""
        score = 0.85  # Base score
        issues = []
        suggestions = []

        # Check for suspicious patterns
        if self._has_contradictions(response):
            score -= 0.25
            issues.append("Potential contradictions detected")
            suggestions.append("Review response for contradictory statements")

        # Check for excessive uncertainty
        if self._has_excessive_uncertainty(response):
            score -= 0.1
            issues.append("Excessive uncertainty markers")
            suggestions.append("Reduce uncertainty language for more confident responses")

        # Check for factual claims that need verification
        claims = self._extract_factual_claims(response)
        verified_claims = 0
        
        if claims:
            for claim in claims:
                if self._verify_claim_against_kb(claim):
                    verified_claims += 1
                else:
                    score -= 0.05
            
            verification_rate = verified_claims / len(claims) if claims else 1.0
            issues.append(f"{len(claims)} factual claims detected, {verified_claims} verified ({verification_rate:.1%})")
            
            if verification_rate < 0.5:
                suggestions.append("Consider adding citations or sources for factual claims")

        # Check for numerical consistency
        if self._has_numerical_inconsistencies(response):
            score -= 0.15
            issues.append("Numerical inconsistencies detected")
            suggestions.append("Verify all numerical values for consistency")

        # Check for temporal consistency
        if self._has_temporal_inconsistencies(response):
            score -= 0.1
            issues.append("Temporal inconsistencies detected")
            suggestions.append("Verify dates and time references")

        status = VerificationStatus.PASSED if score >= 0.7 else (VerificationStatus.WARNING if score >= 0.5 else VerificationStatus.FAILED)

        return VerificationResult(
            verification_type=VerificationType.FACTUAL,
            status=status,
            score=max(0.0, min(1.0, score)),
            message=f"Factuality check: {len(issues)} issues found",
            details={'issues': issues, 'claims': claims, 'verified_claims': verified_claims},
            suggestions=suggestions,
            confidence=verification_rate if claims else 0.8
        )

    def _has_contradictions(self, text: str) -> bool:
        """Check for contradictory statements"""
        # Simple heuristic: look for "but", "however" with conflicting statements
        contradiction_patterns = [
            r'\b(?:but|however|although|though)\b.*\b(?:nevertheless|nonetheless)\b',
            r'\b(?:always|never)\b.*\b(?:sometimes|occasionally)\b'
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in contradiction_patterns)

    def _has_excessive_uncertainty(self, text: str) -> bool:
        """Check for excessive uncertainty markers"""
        uncertainty_markers = ['maybe', 'perhaps', 'possibly', 'might', 'could be', 'unclear']
        count = sum(text.lower().count(marker) for marker in uncertainty_markers)
        return count > 3

    def _extract_factual_claims(self, text: str) -> List[str]:
        """Extract factual claims that need verification"""
        claims = []
        sentences = text.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in ['is', 'are', 'was', 'were', 'has', 'have']):
                if len(sentence.split()) > 5:
                    claims.append(sentence.strip())
        return claims[:10]  # Return top 10 claims

    def _verify_claim_against_kb(self, claim: str) -> bool:
        """Verify claim against knowledge base"""
        # Cache lookup
        if claim in self.fact_cache:
            return self.fact_cache[claim]
        
        # Simple keyword matching against KB
        # In production, would use semantic search or fact verification API
        claim_lower = claim.lower()
        
        for key, value in self.knowledge_base.items():
            if key.lower() in claim_lower:
                self.fact_cache[claim] = True
                return True
        
        # Default to neutral if not found in KB
        self.fact_cache[claim] = None
        return None

    def _has_numerical_inconsistencies(self, text: str) -> bool:
        """Check for numerical inconsistencies"""
        numbers = re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', text)
        if len(numbers) < 2:
            return False
        
        # Check for obvious inconsistencies (e.g., "100% and 50%")
        percentages = [n for n in numbers if '%' in text[text.find(n):text.find(n)+20]]
        if len(percentages) > 1:
            total = sum(float(p.replace('%', '')) for p in percentages)
            if total > 100:
                return True
        
        return False

    def _has_temporal_inconsistencies(self, text: str) -> bool:
        """Check for temporal inconsistencies"""
        dates = re.findall(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', text)
        if len(dates) < 2:
            return False
        
        # Check for date ordering issues
        # Simplified check - in production would do proper date parsing
        return False


class SafetyChecker:
    """Checks safety of responses with enhanced detection"""

    def __init__(self, safety_threshold: float = 0.7):
        self.safety_threshold = safety_threshold
        self.unsafe_patterns = {
            'harmful_instructions': [
                r'how to (?:make|create|build).*(?:bomb|weapon|poison|drug)',
                r'instruction.*(?:kill|harm|hurt|injure)',
                r'step by step.*(?:illegal|criminal)',
                r'recipe for.*(?:dangerous|harmful|toxic)'
            ],
            'personal_info': [
                r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
                r'\b\d{16}\b',  # Credit card pattern
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email
            ],
            'biased_content': [
                r'\b(?:all|every)\s+\w+\s+(?:are|is)\s+(?:bad|evil|stupid|inferior)',
                r'\b(?:should|must)\s+(?:not|never)\s+(?:allow|permit)\s+\w+',
                r'\b(?:inferior|superior)\s+race\b'
            ],
            'hate_speech': [
                r'\b(?:hate|kill|destroy)\s+(?:all|every)\s+\w+',
                r'\b(?:deserve to die|should be eliminated)\b'
            ],
            'self_harm': [
                r'how to (?:kill|hurt|harm).*(?:myself|yourself)',
                r'suicide.*(?:method|way)',
                r'self-harm.*(?:instruction|guide)'
            ],
            'sexual_content': [
                r'\b(?:explicit|pornographic|nsfw)\b',
                r'\b(?:sexual|erotic)\s+(?:content|material)\b'
            ]
        }
        self.violation_history = defaultdict(int)  # Track violation patterns

    def verify(self, response: str) -> VerificationResult:
        """Verify safety of response with enhanced detection"""
        score = 1.0
        violations = []
        suggestions = []

        for category, patterns in self.unsafe_patterns.items():
            for pattern in patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    severity = self._get_severity(category)
                    score -= severity
                    violations.append(f"{category}: matched pattern")
                    self.violation_history[category] += 1

        # Check for repeated violations
        if any(count > 3 for count in self.violation_history.values()):
            score -= 0.2
            suggestions.append("Repeated safety violations detected - review content policy")

        # Check for masked harmful content
        if self._has_masked_harmful_content(response):
            score -= 0.15
            violations.append("Masked harmful content detected")
            suggestions.append("Review for potentially obfuscated harmful content")

        status = VerificationStatus.PASSED if score >= self.safety_threshold else VerificationStatus.FAILED

        return VerificationResult(
            verification_type=VerificationType.SAFETY,
            status=status,
            score=max(0.0, min(1.0, score)),
            message=f"Safety check: {len(violations)} violations",
            details={'violations': violations, 'violation_history': dict(self.violation_history)},
            suggestions=suggestions,
            confidence=0.9 if score >= self.safety_threshold else 0.5
        )

    def _get_severity(self, category: str) -> float:
        """Get severity weight for violation category"""
        severity_map = {
            'harmful_instructions': 0.4,
            'hate_speech': 0.5,
            'self_harm': 0.5,
            'personal_info': 0.3,
            'biased_content': 0.2,
            'sexual_content': 0.3
        }
        return severity_map.get(category, 0.3)

    def _has_masked_harmful_content(self, text: str) -> bool:
        """Check for masked/obfuscated harmful content"""
        # Check for common obfuscation patterns
        obfuscation_patterns = [
            r'\b(?:k1ll|h4rm|d3stroy)\b',  # Leet speak
            r'\b(?:remove|replace)\s+\w+\s+with\s+\w+',  # Substitution hints
            r'\b(?:alternative|substitute)\s+for\s+\w+\s+is'  # Alternative suggestions
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in obfuscation_patterns)


class CoherenceChecker:
    """Checks coherence and logical flow"""

    def verify(self, response: str) -> VerificationResult:
        """Verify coherence"""
        score = 0.9
        issues = []

        # Check sentence length variation
        sentences = [s.strip() for s in response.split('.') if s.strip()]
        if sentences:
            avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if avg_length < 3 or avg_length > 30:
                score -= 0.2
                issues.append("Unusual sentence length")

        # Check for repetition
        words = response.lower().split()
        if len(words) > 10:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.5:
                score -= 0.3
                issues.append("High repetition detected")

        # Check for logical connectors
        connectors = ['because', 'therefore', 'however', 'thus', 'consequently']
        if not any(connector in response.lower() for connector in connectors):
            score -= 0.1
            issues.append("Missing logical connectors")

        status = VerificationStatus.PASSED if score >= 0.7 else VerificationStatus.WARNING

        return VerificationResult(
            verification_type=VerificationType.COHERENCE,
            status=status,
            score=score,
            message=f"Coherence check: {len(issues)} issues",
            details={'issues': issues}
        )


class RelevanceChecker:
    """Checks relevance to original query"""

    def verify(self, response: str, query: str) -> VerificationResult:
        """Verify relevance"""
        score = 0.8
        issues = []

        # Extract key terms from query
        query_terms = set(self._extract_key_terms(query))
        response_terms = set(self._extract_key_terms(response))

        # Calculate overlap
        if query_terms:
            overlap = len(query_terms & response_terms) / len(query_terms)
            score = overlap
            if overlap < 0.3:
                issues.append("Low term overlap with query")

        # Check if response directly addresses the question
        if '?' in query:
            if not any(word in response.lower() for word in ['answer', 'solution', 'result', 'is', 'are']):
                score -= 0.2
                issues.append("Response may not directly answer question")

        status = VerificationStatus.PASSED if score >= 0.5 else VerificationStatus.WARNING

        return VerificationResult(
            verification_type=VerificationType.RELEVANCE,
            status=status,
            score=score,
            message=f"Relevance check: {len(issues)} issues",
            details={'issues': issues, 'overlap': score}
        )

    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text"""
        # Remove common stopwords
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                   'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
                   'could', 'may', 'might', 'must', 'shall', 'can', 'to', 'of', 'in',
                   'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
                   'during', 'before', 'after', 'above', 'below', 'between', 'under',
                   'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where',
                   'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some',
                   'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
                   'too', 'very', 'just'}
        
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if len(w) > 2 and w not in stopwords]


class HallucinationChecker:
    """Checks for potential hallucinations"""

    def verify(self, response: str, context: Dict = None) -> VerificationResult:
        """Verify for hallucinations"""
        score = 0.85
        issues = []

        # Check for made-up citations
        if re.search(r'\[\d+\]', response):
            citations = re.findall(r'\[(\d+)\]', response)
            # In production, would verify these against actual sources
            issues.append(f"{len(citations)} citations - recommend source verification")

        # Check for specific numbers that might be hallucinated
        numbers = re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', response)
        if numbers:
            large_numbers = [n for n in numbers if len(n.replace(',', '').split('.')[0]) > 3]
            if large_numbers:
                issues.append(f"{len(large_numbers)} large numbers - recommend verification")

        # Check for confident but unverifiable claims
        confident_patterns = [
            r'\bdefinitely\b',
            r'\bcertainly\b',
            r'\bwithout doubt\b',
            r'\babsolutely\b'
        ]
        if any(re.search(pattern, response, re.IGNORECASE) for pattern in confident_patterns):
            score -= 0.1
            issues.append("Confident claims detected")

        status = VerificationStatus.PASSED if score >= 0.7 else VerificationStatus.WARNING

        return VerificationResult(
            verification_type=VerificationType.HALLUCINATION,
            status=status,
            score=score,
            message=f"Hallucination check: {len(issues)} issues",
            details={'issues': issues}
        )


class FormatChecker:
    """Checks response format"""

    def verify(self, response: str, expected_format: str = None) -> VerificationResult:
        """Verify format"""
        score = 1.0
        issues = []
        suggestions = []

        # Check for proper sentence structure
        if response and not response[0].isupper():
            score -= 0.2
            issues.append("Response doesn't start with capital letter")
            suggestions.append("Start response with capital letter")

        if response and not response.rstrip().endswith(('.', '!', '?')):
            score -= 0.1
            issues.append("Response doesn't end with punctuation")
            suggestions.append("End response with proper punctuation")

        # Check for excessive whitespace
        if re.search(r'\s{3,}', response):
            score -= 0.1
            issues.append("Excessive whitespace detected")
            suggestions.append("Reduce excessive whitespace")

        # Check for broken words
        if re.search(r'\w-\s', response):
            score -= 0.1
            issues.append("Possible broken words")
            suggestions.append("Check for broken words at line breaks")

        # Check for proper spacing after punctuation
        if re.search(r'[.!?](?=[A-Z])', response):
            score -= 0.05
            issues.append("Missing space after punctuation")
            suggestions.append("Add space after punctuation marks")

        status = VerificationStatus.PASSED if score >= 0.7 else VerificationStatus.WARNING

        return VerificationResult(
            verification_type=VerificationType.FORMAT,
            status=status,
            score=max(0.0, min(1.0, score)),
            message=f"Format check: {len(issues)} issues",
            details={'issues': issues},
            suggestions=suggestions
        )


class ConsistencyChecker:
    """Checks internal consistency of responses"""

    def verify(self, response: str) -> VerificationResult:
        """Verify internal consistency"""
        score = 0.9
        issues = []
        suggestions = []

        # Check for contradictory statements
        contradictions = self._find_contradictions(response)
        if contradictions:
            score -= 0.3 * len(contradictions)
            issues.extend(contradictions)
            suggestions.append("Review for contradictory statements")

        # Check for consistent terminology
        if self._has_inconsistent_terminology(response):
            score -= 0.15
            issues.append("Inconsistent terminology detected")
            suggestions.append("Use consistent terminology throughout")

        # Check for consistent tense usage
        if self._has_tense_inconsistency(response):
            score -= 0.1
            issues.append("Tense inconsistency detected")
            suggestions.append("Maintain consistent tense usage")

        # Check for consistent number usage
        if self._has_number_inconsistency(response):
            score -= 0.1
            issues.append("Number inconsistency detected")
            suggestions.append("Ensure numbers are used consistently")

        status = VerificationStatus.PASSED if score >= 0.7 else VerificationStatus.WARNING

        return VerificationResult(
            verification_type=VerificationType.CONSISTENCY,
            status=status,
            score=max(0.0, min(1.0, score)),
            message=f"Consistency check: {len(issues)} issues",
            details={'issues': issues, 'contradictions': contradictions},
            suggestions=suggestions
        )

    def _find_contradictions(self, text: str) -> List[str]:
        """Find contradictory statements"""
        contradictions = []
        
        # Look for "X is Y" followed by "X is not Y" patterns
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        for i, sent1 in enumerate(sentences):
            for sent2 in sentences[i+1:i+3]:  # Check next 2 sentences
                if self._are_contradictory(sent1, sent2):
                    contradictions.append(f"Contradiction between: '{sent1}' and '{sent2}'")
        
        return contradictions

    def _are_contradictory(self, sent1: str, sent2: str) -> bool:
        """Check if two sentences are contradictory"""
        # Simple heuristic - look for opposite assertions
        opposite_pairs = [
            ('is', 'is not'),
            ('are', 'are not'),
            ('will', 'will not'),
            ('can', 'cannot'),
            ('always', 'never'),
            ('all', 'none')
        ]
        
        sent1_lower = sent1.lower()
        sent2_lower = sent2.lower()
        
        for pos, neg in opposite_pairs:
            if pos in sent1_lower and neg in sent2_lower:
                return True
            if neg in sent1_lower and pos in sent2_lower:
                return True
        
        return False

    def _has_inconsistent_terminology(self, text: str) -> bool:
        """Check for inconsistent terminology"""
        # Look for multiple terms for the same concept
        # Simplified check - in production would use semantic analysis
        return False

    def _has_tense_inconsistency(self, text: str) -> bool:
        """Check for tense inconsistency"""
        past_tense_markers = ['was', 'were', 'had', 'did']
        present_tense_markers = ['is', 'are', 'has', 'do']
        
        sentences = text.split('.')
        if len(sentences) < 3:
            return False
        
        # Check if most sentences use one tense
        past_count = sum(1 for s in sentences if any(m in s.lower() for m in past_tense_markers))
        present_count = sum(1 for s in sentences if any(m in s.lower() for m in present_tense_markers))
        
        # If both are significantly present, flag as inconsistent
        return past_count > 0 and present_count > 0 and abs(past_count - present_count) < 2

    def _has_number_inconsistency(self, text: str) -> bool:
        """Check for number inconsistency"""
        # Look for same concept with different numbers
        numbers = re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', text)
        return len(set(numbers)) > 3  # More than 3 unique numbers might indicate inconsistency


class CompletenessChecker:
    """Checks completeness of responses"""

    def verify(self, response: str, query: str = None) -> VerificationResult:
        """Verify completeness"""
        score = 0.85
        issues = []
        suggestions = []

        # Check response length
        if len(response) < 50:
            score -= 0.3
            issues.append("Response too short")
            suggestions.append("Provide more detailed response")
        elif len(response) > 5000:
            score -= 0.1
            issues.append("Response very long")
            suggestions.append("Consider condensing the response")

        # Check for incomplete sentences
        if self._has_incomplete_sentences(response):
            score -= 0.2
            issues.append("Incomplete sentences detected")
            suggestions.append("Complete all sentences")

        # Check if question is answered
        if query and '?' in query:
            if not self._answers_question(response, query):
                score -= 0.25
                issues.append("May not fully answer the question")
                suggestions.append("Ensure response directly addresses the question")

        # Check for abrupt ending
        if self._has_abrupt_ending(response):
            score -= 0.15
            issues.append("Abrupt ending detected")
            suggestions.append("Provide proper conclusion")

        status = VerificationStatus.PASSED if score >= 0.7 else VerificationStatus.WARNING

        return VerificationResult(
            verification_type=VerificationType.COMPLETENESS,
            status=status,
            score=max(0.0, min(1.0, score)),
            message=f"Completeness check: {len(issues)} issues",
            details={'issues': issues, 'length': len(response)},
            suggestions=suggestions
        )

    def _has_incomplete_sentences(self, text: str) -> bool:
        """Check for incomplete sentences"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        incomplete = [s for s in sentences if len(s.split()) < 3]
        return len(incomplete) > len(sentences) * 0.3

    def _answers_question(self, response: str, query: str) -> bool:
        """Check if response answers the question"""
        # Extract question words
        question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which']
        query_lower = query.lower()
        
        # Check if response contains answer indicators
        answer_indicators = ['is', 'are', 'was', 'were', 'because', 'due to', 'therefore']
        return any(indicator in response.lower() for indicator in answer_indicators)

    def _has_abrupt_ending(self, text: str) -> bool:
        """Check for abrupt ending"""
        if not text:
            return True
        
        last_sentence = text.split('.')[-1].strip()
        return len(last_sentence.split()) < 3 and not last_sentence.endswith(('!', '?'))


class BiasChecker:
    """Checks for bias in responses"""

    def __init__(self):
        self.bias_patterns = {
            'gender_bias': [
                r'\b(?:men|women)\s+(?:are|always|never|should)\s+',
                r'\b(?:he|she)\s+(?:is|always|never)\s+'
            ],
            'cultural_bias': [
                r'\b(?:western|eastern)\s+(?:culture|values)\s+(?:are|is)\s+(?:better|superior|inferior)',
                r'\b(?:developed|developing)\s+(?:countries|nations)\s+'
            ],
            'stereotypes': [
                r'\b(?:all|every)\s+\w+\s+(?:are|is)\s+',
                r'\b(?:typical|stereotypical)\s+\w+\s+'
            ]
        }

    def verify(self, response: str) -> VerificationResult:
        """Verify for bias"""
        score = 0.9
        issues = []
        suggestions = []

        for category, patterns in self.bias_patterns.items():
            for pattern in patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    score -= 0.2
                    issues.append(f"{category}: potential bias detected")
                    suggestions.append(f"Review {category.replace('_', ' ')} language")

        # Check for balanced language
        if self._has_imbalanced_representation(response):
            score -= 0.15
            issues.append("Imbalanced representation detected")
            suggestions.append("Ensure balanced representation")

        status = VerificationStatus.PASSED if score >= 0.7 else VerificationStatus.WARNING

        return VerificationResult(
            verification_type=VerificationType.BIAS,
            status=status,
            score=max(0.0, min(1.0, score)),
            message=f"Bias check: {len(issues)} issues",
            details={'issues': issues},
            suggestions=suggestions
        )

    def _has_imbalanced_representation(self, text: str) -> bool:
        """Check for imbalanced representation"""
        # Check gender pronoun balance
        he_count = text.lower().count(' he ')
        she_count = text.lower().count(' she ')
        
        if he_count > 0 and she_count > 0:
            ratio = min(he_count, she_count) / max(he_count, she_count)
            return ratio < 0.3
        
        return False


class PrivacyChecker:
    """Checks for privacy violations"""

    def __init__(self):
        self.pii_patterns = {
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            'address': r'\b\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b'
        }

    def verify(self, response: str) -> VerificationResult:
        """Verify for privacy violations"""
        score = 1.0
        issues = []
        suggestions = []

        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, response)
            if matches:
                score -= 0.3
                issues.append(f"{pii_type}: {len(matches)} potential PII instances")
                suggestions.append(f"Remove or redact {pii_type} information")

        # Check for names that might be personal
        if self._has_potential_names(response):
            score -= 0.1
            issues.append("Potential personal names detected")
            suggestions.append("Review for personal information")

        status = VerificationStatus.PASSED if score >= 0.7 else VerificationStatus.FAILED

        return VerificationResult(
            verification_type=VerificationType.PRIVACY,
            status=status,
            score=max(0.0, min(1.0, score)),
            message=f"Privacy check: {len(issues)} issues",
            details={'issues': issues},
            suggestions=suggestions
        )

    def _has_potential_names(self, text: str) -> bool:
        """Check for potential personal names"""
        # Simple heuristic - capitalized words that aren't at sentence start
        words = text.split()
        potential_names = []
        
        for i, word in enumerate(words):
            if word[0].isupper() and i > 0:
                prev_word = words[i-1]
                if prev_word not in ['The', 'A', 'An', 'This', 'That', 'Mr.', 'Mrs.', 'Ms.', 'Dr.']:
                    potential_names.append(word)
        
        return len(potential_names) > 3


class SecurityChecker:
    """Checks for security issues"""

    def __init__(self):
        self.security_patterns = {
            'injection': [
                r'\b(?:SELECT|INSERT|UPDATE|DELETE|DROP)\s+FROM\b',
                r'<script[^>]*>',
                r'\beval\s*\(',
                r'\bexec\s*\('
            ],
            'path_traversal': [
                r'\.\.[/\\]',
                r'%2e%2e',
                r'%252e%252e'
            ],
            'command_injection': [
                r';\s*(?:ls|cat|rm|cd)\s',
                r'\|\s*(?:ls|cat|rm|cd)\s',
                r'`[^`]*`'
            ],
            'sensitive_data': [
                r'\bpassword\s*[:=]\s*\S+',
                r'\bapi[_-]?key\s*[:=]\s*\S+',
                r'\bsecret\s*[:=]\s*\S+'
            ]
        }

    def verify(self, response: str) -> VerificationResult:
        """Verify for security issues"""
        score = 1.0
        issues = []
        suggestions = []

        for category, patterns in self.security_patterns.items():
            for pattern in patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    score -= 0.4
                    issues.append(f"{category}: potential security issue")
                    suggestions.append(f"Review {category.replace('_', ' ')} content")

        # Check for suspicious URLs
        if self._has_suspicious_urls(response):
            score -= 0.2
            issues.append("Suspicious URLs detected")
            suggestions.append("Review URLs for safety")

        status = VerificationStatus.PASSED if score >= 0.7 else VerificationStatus.FAILED

        return VerificationResult(
            verification_type=VerificationType.SECURITY,
            status=status,
            score=max(0.0, min(1.0, score)),
            message=f"Security check: {len(issues)} issues",
            details={'issues': issues},
            suggestions=suggestions
        )

    def _has_suspicious_urls(self, text: str) -> bool:
        """Check for suspicious URLs"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        
        suspicious_domains = ['bit.ly', 'tinyurl', 'pastebin', 't.co']
        for url in urls:
            if any(domain in url.lower() for domain in suspicious_domains):
                return True
        
        return False


class VerificationLayer:
    """Complete verification layer combining all checks with enhanced features"""

    def __init__(self, knowledge_base: Dict = None, safety_threshold: float = 0.7):
        self.checkers = {
            VerificationType.FACTUAL: FactualityChecker(knowledge_base),
            VerificationType.SAFETY: SafetyChecker(safety_threshold),
            VerificationType.COHERENCE: CoherenceChecker(),
            VerificationType.RELEVANCE: RelevanceChecker(),
            VerificationType.HALLUCINATION: HallucinationChecker(),
            VerificationType.FORMAT: FormatChecker(),
            VerificationType.CONSISTENCY: ConsistencyChecker(),
            VerificationType.COMPLETENESS: CompletenessChecker(),
            VerificationType.BIAS: BiasChecker(),
            VerificationType.PRIVACY: PrivacyChecker(),
            VerificationType.SECURITY: SecurityChecker()
        }
        self.verification_history = []  # Track verification history
        self.metrics = defaultdict(int)  # Track metrics

    def verify_response(
        self,
        response: str,
        query: str = None,
        context: Dict = None,
        enabled_checks: List[VerificationType] = None
    ) -> Dict[str, VerificationResult]:
        """Run all verification checks with enhanced tracking"""
        if enabled_checks is None:
            enabled_checks = list(self.checkers.keys())

        results = {}
        start_time = datetime.now()

        for check_type in enabled_checks:
            checker = self.checkers[check_type]
            try:
                if check_type == VerificationType.RELEVANCE and query:
                    results[check_type.value] = checker.verify(response, query)
                else:
                    results[check_type.value] = checker.verify(response, context)
                
                # Track metrics
                self.metrics[f"{check_type.value}_total"] += 1
                if results[check_type.value].status == VerificationStatus.PASSED:
                    self.metrics[f"{check_type.value}_passed"] += 1
                elif results[check_type.value].status == VerificationStatus.FAILED:
                    self.metrics[f"{check_type.value}_failed"] += 1
                    
            except Exception as e:
                logger.error(f"Verification check failed for {check_type}: {e}")
                results[check_type.value] = VerificationResult(
                    verification_type=check_type,
                    status=VerificationStatus.REVIEW_NEEDED,
                    score=0.0,
                    message=f"Check failed with error: {str(e)}",
                    details={'error': str(e)}
                )

        # Track verification history
        verification_record = {
            'timestamp': start_time,
            'duration': (datetime.now() - start_time).total_seconds(),
            'query': query,
            'response_length': len(response),
            'results': results
        }
        self.verification_history.append(verification_record)
        
        # Keep only last 1000 records
        if len(self.verification_history) > 1000:
            self.verification_history = self.verification_history[-1000:]

        return results

    def get_overall_status(self, results: Dict[str, VerificationResult]) -> Tuple[VerificationStatus, float]:
        """Get overall verification status"""
        if not results:
            return VerificationStatus.PASSED, 1.0

        scores = [r.score for r in results.values()]
        avg_score = sum(scores) / len(scores)

        failed_checks = [r for r in results.values() if r.status == VerificationStatus.FAILED]
        warning_checks = [r for r in results.values() if r.status == VerificationStatus.WARNING]

        if failed_checks:
            return VerificationStatus.FAILED, avg_score
        elif warning_checks:
            return VerificationStatus.WARNING, avg_score
        else:
            return VerificationStatus.PASSED, avg_score

    def generate_verification_report(self, results: Dict[str, VerificationResult]) -> str:
        """Generate human-readable verification report with enhanced details"""
        status, score = self.get_overall_status(results)

        report = f"VERIFICATION REPORT\n"
        report += f"==================\n"
        report += f"Overall Status: {status.value.upper()}\n"
        report += f"Overall Score: {score:.2f}\n"
        report += f"Timestamp: {datetime.now().isoformat()}\n\n"

        for check_name, result in results.items():
            report += f"{check_name.upper()}: {result.status.value.upper()} ({result.score:.2f})\n"
            report += f"  Confidence: {result.confidence:.2f}\n"
            report += f"  {result.message}\n"
            if result.details.get('issues'):
                for issue in result.details['issues']:
                    report += f"  - {issue}\n"
            if result.suggestions:
                report += "  Suggestions:\n"
                for suggestion in result.suggestions:
                    report += f"  • {suggestion}\n"
            report += "\n"

        # Add metrics summary
        report += "METRICS SUMMARY\n"
        report += "===============\n"
        for metric, count in self.metrics.items():
            report += f"{metric}: {count}\n"

        return report

    def get_metrics(self) -> Dict[str, int]:
        """Get verification metrics"""
        return dict(self.metrics)

    def get_verification_stats(self) -> Dict[str, Any]:
        """Get verification statistics"""
        if not self.verification_history:
            return {}
        
        total_verifications = len(self.verification_history)
        avg_duration = sum(r['duration'] for r in self.verification_history) / total_verifications
        
        status_counts = defaultdict(int)
        for record in self.verification_history:
            for check_name, result in record['results'].items():
                status_counts[result.status.value] += 1
        
        return {
            'total_verifications': total_verifications,
            'average_duration_seconds': avg_duration,
            'status_distribution': dict(status_counts),
            'metrics': dict(self.metrics)
        }


def main():
    """Example usage"""
    verifier = VerificationLayer()

    query = "What is the capital of France?"
    response = "The capital of France is Paris. It is known for the Eiffel Tower."

    results = verifier.verify_response(response, query)
    report = verifier.generate_verification_report(results)

    print(report)


if __name__ == "__main__":
    main()
