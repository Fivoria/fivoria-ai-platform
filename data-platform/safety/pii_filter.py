"""
PII and Safety Filtering Module
Filters personally identifiable information and unsafe content
"""

import re
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PIIType(Enum):
    """Types of PII"""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    URL = "url"
    DATE_OF_BIRTH = "date_of_birth"
    ADDRESS = "address"
    NAME = "name"
    USERNAME = "username"
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"


class SafetyCategory(Enum):
    """Safety categories"""
    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    SELF_HARM = "self_harm"
    SEXUAL = "sexual"
    HARASSMENT = "harassment"
    MALICIOUS = "malicious"
    PII = "pii"
    MEDICAL = "medical"
    FINANCIAL = "financial"


@dataclass
class PIIEntity:
    """Detected PII entity"""
    text: str
    type: PIIType
    start: int
    end: int
    confidence: float


@dataclass
class SafetyViolation:
    """Detected safety violation"""
    text: str
    category: SafetyCategory
    severity: str  # "low", "medium", "high"
    start: int
    end: int
    description: str


class PIIDetector:
    """Detects personally identifiable information"""

    def __init__(self):
        # Email pattern
        self.email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        
        # Phone patterns (various formats)
        self.phone_patterns = [
            r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',  # US format
            r'\+?[0-9]{1,3}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}',  # International
        ]
        
        # SSN pattern
        self.ssn_pattern = r'\d{3}-\d{2}-\d{4}'
        
        # Credit card pattern
        self.credit_card_pattern = r'\b(?:\d[ -]*?){13,16}\b'
        
        # IP address pattern
        self.ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        
        # URL pattern
        self.url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        
        # Date of birth pattern
        self.dob_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # DD-MM-YYYY
        ]
        
        # Address pattern (basic)
        self.address_pattern = r'\d+\s+[A-Za-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Way|Place|Pl)'
        
        # Name patterns (basic - would need NER for production)
        self.name_indicators = ['Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.', 'name:', 'called:']

    def detect(self, text: str) -> List[PIIEntity]:
        """Detect PII in text"""
        entities = []
        
        # Detect emails
        for match in re.finditer(self.email_pattern, text):
            entities.append(PIIEntity(
                text=match.group(),
                type=PIIType.EMAIL,
                start=match.start(),
                end=match.end(),
                confidence=0.95
            ))
        
        # Detect phone numbers
        for pattern in self.phone_patterns:
            for match in re.finditer(pattern, text):
                entities.append(PIIEntity(
                    text=match.group(),
                    type=PIIType.PHONE,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.85
                ))
        
        # Detect SSN
        for match in re.finditer(self.ssn_pattern, text):
            entities.append(PIIEntity(
                text=match.group(),
                type=PIIType.SSN,
                start=match.start(),
                end=match.end(),
                confidence=0.90
            ))
        
        # Detect credit cards
        for match in re.finditer(self.credit_card_pattern, text):
            if self._is_valid_credit_card(match.group()):
                entities.append(PIIEntity(
                    text=match.group(),
                    type=PIIType.CREDIT_CARD,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.80
                ))
        
        # Detect IP addresses
        for match in re.finditer(self.ip_pattern, text):
            if self._is_valid_ip(match.group()):
                entities.append(PIIEntity(
                    text=match.group(),
                    type=PIIType.IP_ADDRESS,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.85
                ))
        
        # Detect URLs
        for match in re.finditer(self.url_pattern, text):
            entities.append(PIIEntity(
                text=match.group(),
                type=PIIType.URL,
                start=match.start(),
                end=match.end(),
                confidence=0.90
            ))
        
        return entities

    def _is_valid_credit_card(self, number: str) -> bool:
        """Basic credit card validation (Luhn algorithm placeholder)"""
        # Remove non-digits
        digits = re.sub(r'\D', '', number)
        # Basic length check
        return 13 <= len(digits) <= 16

    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False

    def redact(self, text: str, entities: List[PIIEntity], replacement: str = "[REDACTED]") -> str:
        """Redact PII from text"""
        if not entities:
            return text
        
        # Sort entities by position (reverse order to avoid index issues)
        sorted_entities = sorted(entities, key=lambda x: x.start, reverse=True)
        
        text_list = list(text)
        for entity in sorted_entities:
            text_list[entity.start:entity.end] = list(replacement)
        
        return ''.join(text_list)


class SafetyFilter:
    """Filters unsafe content"""

    def __init__(self):
        # Hate speech patterns (basic - production would use ML models)
        self.hate_speech_patterns = [
            r'\b(hate|kill|destroy|eliminate)\s+(all|every)\s+(?:people|group|race|religion)\b',
            r'\b(inferior|superior)\s+(race|ethnicity|religion)\b',
        ]
        
        # Violence patterns
        self.violence_patterns = [
            r'\b(kill|murder|torture|assault|attack)\b',
            r'\b(bomb|explosive|weapon|gun|knife)\b',
        ]
        
        # Self-harm patterns
        self.self_harm_patterns = [
            r'\b(suicide|kill myself|end my life|hurt myself)\b',
            r'\b(depressed|hopeless|worthless)\s+(?:to live|life)\b',
        ]
        
        # Sexual content patterns
        self.sexual_patterns = [
            r'\b(pornography|explicit|nsfw)\b',
        ]
        
        # Malicious patterns
        self.malicious_patterns = [
            r'\b(hack|exploit|vulnerability|malware|virus|trojan)\b',
            r'\b(phishing|scam|fraud)\b',
        ]
        
        # Medical information patterns
        self.medical_patterns = [
            r'\b(prescription|medication|diagnosis|treatment)\s+(?:for|of)\b',
            r'\b(patient\s+(?:id|name|record))\b',
        ]
        
        # Financial information patterns
        self.financial_patterns = [
            r'\b(account\s+(?:number|balance))\b',
            r'\b(routing\s+number)\b',
            r'\b(bank\s+account)\b',
        ]

    def detect(self, text: str) -> List[SafetyViolation]:
        """Detect safety violations"""
        violations = []
        
        # Check hate speech
        for pattern in self.hate_speech_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                violations.append(SafetyViolation(
                    text=match.group(),
                    category=SafetyCategory.HATE_SPEECH,
                    severity="high",
                    start=match.start(),
                    end=match.end(),
                    description="Hate speech detected"
                ))
        
        # Check violence
        for pattern in self.violence_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                violations.append(SafetyViolation(
                    text=match.group(),
                    category=SafetyCategory.VIOLENCE,
                    severity="medium",
                    start=match.start(),
                    end=match.end(),
                    description="Violence reference detected"
                ))
        
        # Check self-harm
        for pattern in self.self_harm_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                violations.append(SafetyViolation(
                    text=match.group(),
                    category=SafetyCategory.SELF_HARM,
                    severity="high",
                    start=match.start(),
                    end=match.end(),
                    description="Self-harm reference detected"
                ))
        
        # Check sexual content
        for pattern in self.sexual_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                violations.append(SafetyViolation(
                    text=match.group(),
                    category=SafetyCategory.SEXUAL,
                    severity="medium",
                    start=match.start(),
                    end=match.end(),
                    description="Sexual content detected"
                ))
        
        # Check malicious content
        for pattern in self.malicious_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                violations.append(SafetyViolation(
                    text=match.group(),
                    category=SafetyCategory.MALICIOUS,
                    severity="medium",
                    start=match.start(),
                    end=match.end(),
                    description="Malicious content detected"
                ))
        
        # Check medical information
        for pattern in self.medical_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                violations.append(SafetyViolation(
                    text=match.group(),
                    category=SafetyCategory.MEDICAL,
                    severity="low",
                    start=match.start(),
                    end=match.end(),
                    description="Medical information detected"
                ))
        
        # Check financial information
        for pattern in self.financial_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                violations.append(SafetyViolation(
                    text=match.group(),
                    category=SafetyCategory.FINANCIAL,
                    severity="low",
                    start=match.start(),
                    end=match.end(),
                    description="Financial information detected"
                ))
        
        return violations

    def filter(self, text: str, max_severity: str = "medium") -> Tuple[bool, List[SafetyViolation]]:
        """Filter text based on safety violations"""
        violations = self.detect(text)
        
        severity_order = {"low": 0, "medium": 1, "high": 2}
        max_severity_level = severity_order.get(max_severity, 1)
        
        for violation in violations:
            if severity_order.get(violation.severity, 0) >= max_severity_level:
                return False, violations
        
        return True, violations


class SafetyPipeline:
    """Complete safety and PII filtering pipeline"""

    def __init__(self):
        self.pii_detector = PIIDetector()
        self.safety_filter = SafetyFilter()

    def process(self, text: str, redact_pii: bool = True, safety_level: str = "medium") -> Dict:
        """Process text through safety pipeline"""
        result = {
            'original_text': text,
            'passed': True,
            'redacted_text': text,
            'pii_entities': [],
            'safety_violations': [],
            'reason': None
        }
        
        # Detect PII
        pii_entities = self.pii_detector.detect(text)
        result['pii_entities'] = [e.__dict__ for e in pii_entities]
        
        # Redact PII if requested
        if redact_pii and pii_entities:
            result['redacted_text'] = self.pii_detector.redact(text, pii_entities)
        
        # Check safety
        passed, violations = self.safety_filter.filter(result['redacted_text'], safety_level)
        result['safety_violations'] = [v.__dict__ for v in violations]
        result['passed'] = passed
        
        if not passed:
            result['reason'] = "safety_violation"
        
        return result

    def process_batch(self, texts: List[str], **kwargs) -> List[Dict]:
        """Process batch of texts"""
        return [self.process(text, **kwargs) for text in texts]


def main():
    """Example usage"""
    pipeline = SafetyPipeline()
    
    test_text = """
    Contact me at john.doe@example.com or call 555-123-4567.
    My SSN is 123-45-6789.
    """
    
    result = pipeline.process(test_text)
    print(f"Passed: {result['passed']}")
    print(f"PII entities: {len(result['pii_entities'])}")
    print(f"Redacted: {result['redacted_text'][:100]}...")


if __name__ == "__main__":
    main()
