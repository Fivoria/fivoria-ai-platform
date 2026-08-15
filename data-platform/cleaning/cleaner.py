"""
Data Cleaning Module
Cleans and normalizes parsed documents
"""

import re
import unicodedata
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class CleaningStats:
    """Statistics for cleaning process"""
    original_chars: int
    cleaned_chars: int
    removed_chars: int
    removed_lines: int
    normalized_chars: int
    fixed_encoding: int


class TextCleaner:
    """Cleans and normalizes text data"""

    def __init__(self):
        # Common boilerplate patterns to remove
        self.boilerplate_patterns = [
            r'Cookie Policy',
            r'Privacy Policy',
            r'Terms of Service',
            r'All rights reserved',
            r'Copyright © \d{4}',
            r'Click here',
            r'Read more',
            r'Subscribe to our newsletter',
            r'Follow us on',
            r'Share this article',
        ]

        # Spam patterns
        self.spam_patterns = [
            r'Click here to claim your prize',
            r'You have been selected',
            r'Limited time offer',
            r'Act now',
            r'Buy now',
            r'Free money',
            r'Winner',
        ]

    def clean(self, text: str) -> tuple[str, CleaningStats]:
        """Clean text and return cleaned text with stats"""
        original_chars = len(text)
        original_lines = len(text.split('\n'))
        
        cleaned = text
        
        # Step 1: Normalize unicode
        cleaned = self._normalize_unicode(cleaned)
        normalized_chars = original_chars - len(cleaned)
        
        # Step 2: Remove control characters
        cleaned = self._remove_control_chars(cleaned)
        
        # Step 3: Normalize whitespace
        cleaned = self._normalize_whitespace(cleaned)
        
        # Step 4: Remove boilerplate
        cleaned = self._remove_boilerplate(cleaned)
        
        # Step 5: Remove spam patterns
        cleaned = self._remove_spam(cleaned)
        
        # Step 6: Fix encoding issues
        cleaned = self._fix_encoding(cleaned)
        fixed_encoding = len(cleaned) - (original_chars - normalized_chars)
        
        # Step 7: Remove empty lines
        lines = [line for line in cleaned.split('\n') if line.strip()]
        cleaned = '\n'.join(lines)
        removed_lines = original_lines - len(lines)
        
        cleaned_chars = len(cleaned)
        removed_chars = original_chars - cleaned_chars
        
        stats = CleaningStats(
            original_chars=original_chars,
            cleaned_chars=cleaned_chars,
            removed_chars=removed_chars,
            removed_lines=removed_lines,
            normalized_chars=normalized_chars,
            fixed_encoding=fixed_encoding
        )
        
        return cleaned, stats

    def _normalize_unicode(self, text: str) -> str:
        """Normalize unicode characters"""
        # Normalize to NFC form
        return unicodedata.normalize('NFC', text)

    def _remove_control_chars(self, text: str) -> str:
        """Remove control characters except newlines and tabs"""
        # Keep \n, \t, \r
        return ''.join(char for char in text if unicodedata.category(char)[0] != 'C' or char in '\n\t\r')

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace"""
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        # Replace multiple newlines with double newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        return '\n'.join(lines)

    def _remove_boilerplate(self, text: str) -> str:
        """Remove boilerplate content"""
        for pattern in self.boilerplate_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        return text

    def _remove_spam(self, text: str) -> str:
        """Remove spam patterns"""
        for pattern in self.spam_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        return text

    def _fix_encoding(self, text: str) -> str:
        """Fix common encoding issues"""
        # Fix mojibake (encoding mismatches)
        # This is a simple implementation
        fixes = {
            'â€™': "'",
            'â€œ': '"',
            'â€\x9d': '"',
            'â€"': '—',
            'â€¦': '…',
            'Ã©': 'é',
            'Ã ': 'à',
            'Ã¹': 'ù',
            'Ã¨': 'è',
            'Ãª': 'ê',
            'Ã®': 'î',
            'Ã´': 'ô',
        }
        
        for wrong, correct in fixes.items():
            text = text.replace(wrong, correct)
        
        return text

    def remove_html_tags(self, text: str) -> str:
        """Remove HTML tags"""
        return re.sub(r'<[^>]+>', '', text)

    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)

    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.findall(email_pattern, text)

    def remove_urls(self, text: str) -> str:
        """Remove URLs from text"""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.sub(url_pattern, '', text)

    def remove_emails(self, text: str) -> str:
        """Remove email addresses"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.sub(email_pattern, '', text)


class Deduplicator:
    """Removes duplicate and near-duplicate content"""

    def __init__(self, min_similarity: float = 0.95):
        self.min_similarity = min_similarity
        self.seen_hashes: Set[str] = set()
        self.seen_documents: List[Dict] = []

    def _compute_hash(self, text: str) -> str:
        """Compute hash of normalized text"""
        import hashlib
        normalized = ' '.join(text.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute similarity between two texts (simple implementation)"""
        # This is a basic implementation
        # For production, use MinHash, SimHash, or similar
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0

    def is_duplicate(self, text: str) -> bool:
        """Check if text is duplicate of seen content"""
        doc_hash = self._compute_hash(text)
        
        if doc_hash in self.seen_hashes:
            return True
        
        # Check near-duplicates
        for doc in self.seen_documents:
            similarity = self._compute_similarity(text, doc['content'])
            if similarity >= self.min_similarity:
                return True
        
        return False

    def add_document(self, text: str, metadata: Dict = None):
        """Add document to seen documents"""
        doc_hash = self._compute_hash(text)
        self.seen_hashes.add(doc_hash)
        self.seen_documents.append({
            'content': text,
            'hash': doc_hash,
            'metadata': metadata or {}
        })

    def deduplicate_batch(self, documents: List[Dict]) -> List[Dict]:
        """Deduplicate a batch of documents"""
        unique_documents = []
        
        for doc in documents:
            text = doc.get('content', '')
            
            if not self.is_duplicate(text):
                self.add_document(text, doc.get('metadata'))
                unique_documents.append(doc)
            else:
                logger.info(f"Removed duplicate: {doc.get('source_id', 'unknown')}")
        
        return unique_documents

    def get_stats(self) -> Dict:
        """Get deduplication statistics"""
        return {
            'total_seen': len(self.seen_documents),
            'unique_hashes': len(self.seen_hashes)
        }


class QualityFilter:
    """Filters documents based on quality metrics"""

    def __init__(self):
        self.min_word_count = 50
        self.max_word_count = 100000
        self.min_avg_word_length = 3
        self.max_avg_word_length = 15
        self.min_sentence_count = 3

    def check_quality(self, text: str) -> tuple[bool, Dict]:
        """Check if text meets quality standards"""
        metrics = self._compute_metrics(text)
        passed = self._evaluate_metrics(metrics)
        return passed, metrics

    def _compute_metrics(self, text: str) -> Dict:
        """Compute quality metrics"""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        word_count = len(words)
        sentence_count = len(sentences)
        
        if word_count > 0:
            avg_word_length = sum(len(word) for word in words) / word_count
        else:
            avg_word_length = 0
        
        if sentence_count > 0:
            avg_sentence_length = word_count / sentence_count
        else:
            avg_sentence_length = 0
        
        # Check for gibberish (high repetition)
        unique_words = len(set(words.lower() for word in words))
        diversity = unique_words / word_count if word_count > 0 else 0
        
        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'avg_word_length': avg_word_length,
            'avg_sentence_length': avg_sentence_length,
            'vocabulary_diversity': diversity,
            'char_count': len(text)
        }

    def _evaluate_metrics(self, metrics: Dict) -> bool:
        """Evaluate if metrics meet quality standards"""
        if metrics['word_count'] < self.min_word_count:
            return False
        
        if metrics['word_count'] > self.max_word_count:
            return False
        
        if metrics['avg_word_length'] < self.min_avg_word_length:
            return False
        
        if metrics['avg_word_length'] > self.max_avg_word_length:
            return False
        
        if metrics['sentence_count'] < self.min_sentence_count:
            return False
        
        if metrics['vocabulary_diversity'] < 0.3:  # Too repetitive
            return False
        
        return True

    def filter_batch(self, documents: List[Dict]) -> tuple[List[Dict], List[Dict]]:
        """Filter documents by quality"""
        passed = []
        failed = []
        
        for doc in documents:
            text = doc.get('content', '')
            passed_check, metrics = self.check_quality(text)
            
            if passed_check:
                passed.append({**doc, 'quality_metrics': metrics})
            else:
                failed.append({**doc, 'quality_metrics': metrics, 'rejection_reason': 'low_quality'})
                logger.info(f"Filtered low quality: {doc.get('source_id', 'unknown')}")
        
        return passed, failed


class DataPipeline:
    """Complete data cleaning pipeline"""

    def __init__(self):
        self.cleaner = TextCleaner()
        self.deduplicator = Deduplicator()
        self.quality_filter = QualityFilter()

    def process(self, text: str) -> tuple[str, Dict]:
        """Process text through complete pipeline"""
        # Clean
        cleaned_text, cleaning_stats = self.cleaner.clean(text)
        
        # Check quality
        passed_quality, quality_metrics = self.quality_filter.check_quality(cleaned_text)
        
        if not passed_quality:
            logger.warning("Text failed quality check")
            return "", {'status': 'failed', 'reason': 'quality'}
        
        # Check duplicate
        if self.deduplicator.is_duplicate(cleaned_text):
            logger.warning("Text is duplicate")
            return "", {'status': 'failed', 'reason': 'duplicate'}
        
        # Add to deduplicator
        self.deduplicator.add_document(cleaned_text)
        
        return cleaned_text, {
            'status': 'success',
            'cleaning_stats': cleaning_stats.__dict__,
            'quality_metrics': quality_metrics
        }

    def process_batch(self, documents: List[Dict]) -> tuple[List[Dict], List[Dict]]:
        """Process batch of documents"""
        processed = []
        failed = []
        
        for doc in documents:
            text = doc.get('content', '')
            cleaned, result = self.process(text)
            
            if result['status'] == 'success':
                processed.append({**doc, 'content': cleaned, 'processing_stats': result})
            else:
                failed.append({**doc, 'processing_result': result})
        
        return processed, failed


def main():
    """Example usage"""
    pipeline = DataPipeline()
    
    test_text = """
    This is a test document with some text.
    It has multiple sentences.
    And some more content here.
    """
    
    cleaned, stats = pipeline.process(test_text)
    print(f"Cleaned: {cleaned[:100]}...")
    print(f"Stats: {stats}")


if __name__ == "__main__":
    main()
