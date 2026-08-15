"""
Data Parser Module
Parses raw data from various formats into structured text
"""

import re
import html
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging
from abc import ABC, abstractmethod

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

logger = logging.getLogger(__name__)


class DocumentFormat(Enum):
    """Supported document formats"""
    HTML = "html"
    PDF = "pdf"
    TXT = "txt"
    JSON = "json"
    MARKDOWN = "md"
    XML = "xml"
    CODE = "code"


@dataclass
class ParsedDocument:
    """Parsed document structure"""
    source_id: str
    title: Optional[str]
    content: str
    metadata: Dict[str, Any]
    sections: List[Dict[str, str]]
    language: Optional[str]
    format: DocumentFormat
    word_count: int
    char_count: int

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'source_id': self.source_id,
            'title': self.title,
            'content': self.content,
            'metadata': self.metadata,
            'sections': self.sections,
            'language': self.language,
            'format': self.format.value,
            'word_count': self.word_count,
            'char_count': self.char_count
        }


class BaseParser(ABC):
    """Base parser class"""

    @abstractmethod
    def parse(self, filepath: Path, source_id: str) -> ParsedDocument:
        """Parse document from file"""
        pass

    def _count_words(self, text: str) -> int:
        """Count words in text"""
        return len(text.split())

    def _count_chars(self, text: str) -> int:
        """Count characters in text"""
        return len(text)


class HTMLParser(BaseParser):
    """Parser for HTML documents"""

    def __init__(self):
        if not BS4_AVAILABLE:
            logger.warning("BeautifulSoup not available, HTML parsing limited")

    def parse(self, filepath: Path, source_id: str) -> ParsedDocument:
        """Parse HTML document"""
        html_content = filepath.read_text(encoding='utf-8', errors='ignore')

        if BS4_AVAILABLE:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title = None
            if soup.title:
                title = soup.title.get_text().strip()

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Extract main content
            content = soup.get_text(separator=' ', strip=True)
            content = re.sub(r'\s+', ' ', content)

            # Extract sections
            sections = []
            for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                section_text = header.get_text().strip()
                next_sibling = header.find_next_sibling()
                section_content = ""
                while next_sibling and next_sibling.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    section_content += next_sibling.get_text(separator=' ', strip=True) + " "
                    next_sibling = next_sibling.find_next_sibling()
                
                if section_content.strip():
                    sections.append({
                        'heading': section_text,
                        'content': section_content.strip()
                    })

        else:
            # Fallback without BeautifulSoup
            title = None
            content = re.sub(r'<[^>]+>', ' ', html_content)
            content = html.unescape(content)
            content = re.sub(r'\s+', ' ', content).strip()
            sections = []

        return ParsedDocument(
            source_id=source_id,
            title=title,
            content=content,
            metadata={'filepath': str(filepath)},
            sections=sections,
            language=None,
            format=DocumentFormat.HTML,
            word_count=self._count_words(content),
            char_count=self._count_chars(content)
        )


class TextParser(BaseParser):
    """Parser for plain text documents"""

    def parse(self, filepath: Path, source_id: str) -> ParsedDocument:
        """Parse plain text document"""
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        
        # Try to extract title from first line
        lines = content.split('\n')
        title = lines[0].strip() if lines else None
        
        # Remove title from content if it's the first line
        if title and len(lines) > 1:
            content = '\n'.join(lines[1:]).strip()
        
        content = re.sub(r'\s+', ' ', content)

        return ParsedDocument(
            source_id=source_id,
            title=title,
            content=content,
            metadata={'filepath': str(filepath)},
            sections=[],
            language=None,
            format=DocumentFormat.TXT,
            word_count=self._count_words(content),
            char_count=self._count_chars(content)
        )


class PDFParser(BaseParser):
    """Parser for PDF documents"""

    def __init__(self):
        if not PDF_AVAILABLE:
            logger.warning("pdfplumber not available, PDF parsing disabled")

    def parse(self, filepath: Path, source_id: str) -> ParsedDocument:
        """Parse PDF document"""
        if not PDF_AVAILABLE:
            raise ImportError("pdfplumber is required for PDF parsing")

        content_parts = []
        sections = []
        title = None

        with pdfplumber.open(filepath) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    content_parts.append(text)
                    
                    # Try to detect headers
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and len(line) < 100 and line.isupper():
                            sections.append({
                                'heading': line,
                                'page': page_num + 1
                            })

        content = '\n'.join(content_parts)
        content = re.sub(r'\s+', ' ', content)

        # Try to extract title from first section
        if sections:
            title = sections[0]['heading']

        return ParsedDocument(
            source_id=source_id,
            title=title,
            content=content,
            metadata={'filepath': str(filepath), 'pages': len(content_parts)},
            sections=sections,
            language=None,
            format=DocumentFormat.PDF,
            word_count=self._count_words(content),
            char_count=self._count_chars(content)
        )


class JSONParser(BaseParser):
    """Parser for JSON documents"""

    def parse(self, filepath: Path, source_id: str) -> ParsedDocument:
        """Parse JSON document"""
        data = json.loads(filepath.read_text(encoding='utf-8'))
        
        # Try to extract text content from JSON
        content = json.dumps(data, indent=2, ensure_ascii=False)
        title = data.get('title', data.get('name', None))

        return ParsedDocument(
            source_id=source_id,
            title=title,
            content=content,
            metadata={'filepath': str(filepath), 'keys': list(data.keys()) if isinstance(data, dict) else []},
            sections=[],
            language=None,
            format=DocumentFormat.JSON,
            word_count=self._count_words(content),
            char_count=self._count_chars(content)
        )


class CodeParser(BaseParser):
    """Parser for code files"""

    def parse(self, filepath: Path, source_id: str) -> ParsedDocument:
        """Parse code file"""
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        
        # Extract title from filename
        title = filepath.stem

        # Remove comments for cleaner content (simple implementation)
        # This is language-specific and would need extension
        content_lines = []
        for line in content.split('\n'):
            stripped = line.strip()
            # Skip single-line comments (basic)
            if not stripped.startswith('#') and not stripped.startswith('//'):
                content_lines.append(line)
        
        clean_content = '\n'.join(content_lines)

        return ParsedDocument(
            source_id=source_id,
            title=title,
            content=clean_content,
            metadata={
                'filepath': str(filepath),
                'extension': filepath.suffix,
                'language': self._detect_language(filepath.suffix)
            },
            sections=[],
            language=self._detect_language(filepath.suffix),
            format=DocumentFormat.CODE,
            word_count=self._count_words(clean_content),
            char_count=self._count_chars(clean_content)
        )

    def _detect_language(self, extension: str) -> Optional[str]:
        """Detect programming language from extension"""
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.sh': 'shell',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml'
        }
        return language_map.get(extension.lower())


class ParserRegistry:
    """Registry for document parsers"""

    def __init__(self):
        self.parsers: Dict[DocumentFormat, BaseParser] = {}
        self._register_default_parsers()

    def _register_default_parsers(self):
        """Register default parsers"""
        self.parsers[DocumentFormat.HTML] = HTMLParser()
        self.parsers[DocumentFormat.TXT] = TextParser()
        self.parsers[DocumentFormat.PDF] = PDFParser()
        self.parsers[DocumentFormat.JSON] = JSONParser()
        self.parsers[DocumentFormat.CODE] = CodeParser()

    def register_parser(self, format: DocumentFormat, parser: BaseParser):
        """Register a custom parser"""
        self.parsers[format] = parser

    def get_parser(self, format: DocumentFormat) -> BaseParser:
        """Get parser for format"""
        if format not in self.parsers:
            raise ValueError(f"No parser registered for {format}")
        return self.parsers[format]

    def detect_format(self, filepath: Path) -> DocumentFormat:
        """Detect document format from file extension"""
        extension = filepath.suffix.lower()
        
        format_map = {
            '.html': DocumentFormat.HTML,
            '.htm': DocumentFormat.HTML,
            '.pdf': DocumentFormat.PDF,
           ('.txt', '.text'): DocumentFormat.TXT,
            '.json': DocumentFormat.JSON,
            '.md': DocumentFormat.MARKDOWN,
            '.xml': DocumentFormat.XML,
        }
        
        # Code extensions
        code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', 
                          '.rb', '.php', '.swift', '.kt', '.scala', '.sh', '.sql'}
        
        if extension in code_extensions:
            return DocumentFormat.CODE
        
        for ext, fmt in format_map.items():
            if isinstance(ext, tuple):
                if extension in ext:
                    return fmt
            elif extension == ext:
                return fmt
        
        # Default to text
        return DocumentFormat.TXT

    def parse(self, filepath: Path, source_id: str) -> ParsedDocument:
        """Parse document using appropriate parser"""
        format = self.detect_format(filepath)
        parser = self.get_parser(format)
        return parser.parse(filepath, source_id)

    def parse_batch(self, filepaths: List[Path], source_ids: List[str]) -> List[ParsedDocument]:
        """Parse multiple documents"""
        documents = []
        for filepath, source_id in zip(filepaths, source_ids):
            try:
                doc = self.parse(filepath, source_id)
                documents.append(doc)
            except Exception as e:
                logger.error(f"Failed to parse {filepath}: {e}")
                documents.append(None)
        return documents


def main():
    """Example usage"""
    parser_registry = ParserRegistry()
    
    # Example parsing
    test_file = Path("./test.html")
    if test_file.exists():
        doc = parser_registry.parse(test_file, "test-001")
        print(f"Parsed: {doc.title}")
        print(f"Word count: {doc.word_count}")


if __name__ == "__main__":
    main()
