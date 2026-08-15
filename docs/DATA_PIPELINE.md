# Fivoria AI Data Pipeline Documentation

## Overview

The Fivoria AI data pipeline is a comprehensive system for collecting, cleaning, and preparing training data for the foundation model. It ensures data quality, legal compliance, and provenance tracking.

## Architecture

```
DATA SOURCES
    ↓
COLLECTORS
    ↓
RAW DATA LAKE
    ↓
PARSERS
    ↓
CLEANING
    ↓
DEDUPLICATION
    ↓
QUALITY FILTERING
    ↓
SAFETY/PII FILTERING
    ↓
DATASET REGISTRY
    ↓
TOKENIZATION
    ↓
TRAINING SHARDS
```

## Components

### 1. Data Collectors (`data-platform/collectors/`)

**Purpose**: Collect data from various sources with provenance tracking.

**Key Features**:
- Web scraping with robots.txt compliance
- Dataset downloading
- Code repository collection
- License and permission tracking
- Checksum verification

**Usage**:
```python
from data_platform.collectors.collector import CollectorRegistry, DataSource, DataSourceType, LicenseType

registry = CollectorRegistry(Path("./data/raw"))

source = DataSource(
    source_id="example-001",
    source_type=DataSourceType.WEBSITE,
    url="https://example.com",
    provider="Example Provider",
    license_type=LicenseType.CC_BY,
    acquisition_date=datetime.now(),
    permission_status="allowed",
    allowed_uses=["training", "research"],
    restrictions=["commercial"],
    checksum="",
    version="1.0",
    metadata={}
)

filepath = await registry.collect(source)
```

### 2. Data Parsers (`data-platform/parsers/`)

**Purpose**: Parse raw data from various formats into structured text.

**Supported Formats**:
- HTML
- PDF
- Plain text
- JSON
- Code files (Python, JavaScript, etc.)

**Usage**:
```python
from data_platform.parsers.parser import ParserRegistry

parser_registry = ParserRegistry()
doc = parser_registry.parse(filepath, source_id)
```

### 3. Data Cleaning (`data-platform/cleaning/`)

**Purpose**: Clean and normalize text data.

**Features**:
- Unicode normalization
- Control character removal
- Whitespace normalization
- Boilerplate removal
- Spam detection
- Encoding fix

**Usage**:
```python
from data_platform.cleaning.cleaner import DataPipeline

pipeline = DataPipeline()
cleaned, stats = pipeline.process(text)
```

### 4. Deduplication (`data-platform/cleaning/`)

**Purpose**: Remove duplicate and near-duplicate content.

**Features**:
- Exact duplicate detection
- Near-duplicate detection
- Hash-based comparison
- Similarity scoring

**Usage**:
```python
from data_platform.cleaning.cleaner import Deduplicator

deduplicator = Deduplicator(min_similarity=0.95)
unique_docs = deduplicator.deduplicate_batch(documents)
```

### 5. Quality Filtering (`data-platform/cleaning/`)

**Purpose**: Filter documents based on quality metrics.

**Metrics**:
- Word count
- Sentence count
- Average word length
- Vocabulary diversity
- Readability

**Usage**:
```python
from data_platform.cleaning.cleaner import QualityFilter

filter = QualityFilter()
passed, failed = filter.filter_batch(documents)
```

### 6. PII and Safety Filtering (`data-platform/safety/`)

**Purpose**: Remove PII and unsafe content.

**PII Detection**:
- Email addresses
- Phone numbers
- SSN
- Credit card numbers
- IP addresses
- URLs

**Safety Categories**:
- Hate speech
- Violence
- Self-harm
- Sexual content
- Malicious content

**Usage**:
```python
from data_platform.safety.pii_filter import SafetyPipeline

pipeline = SafetyPipeline()
result = pipeline.process(text, redact_pii=True, safety_level="medium")
```

### 7. Dataset Registry (`data-platform/registry/`)

**Purpose**: Manage dataset versioning and metadata.

**Features**:
- Version control
- Provenance tracking
- License compliance
- Checksum verification
- Lifecycle management

**Usage**:
```python
from data_platform.registry.dataset_registry import DatasetRegistry, DatasetType, DatasetStatus

registry = DatasetRegistry(Path("./data/registry"))

dataset = registry.create_dataset(
    dataset_id="fivoria-pretrain-v1",
    name="Fivoria Pretraining Dataset v1",
    description="Initial pretraining dataset",
    dataset_type=DatasetType.PRETRAINING,
    created_by="system",
    storage_path="./data/datasets/pretrain-v1"
)

registry.set_status("fivoria-pretrain-v1", "1.0.0", DatasetStatus.APPROVED)
```

## Data Flow

### Collection Phase

1. **Source Registration**: Register data sources with license information
2. **Data Collection**: Collect raw data from sources
3. **Provenance Tracking**: Record source metadata and checksums

### Processing Phase

1. **Parsing**: Convert raw data to structured text
2. **Cleaning**: Normalize and clean text
3. **Deduplication**: Remove duplicates
4. **Quality Filtering**: Filter by quality metrics
5. **Safety Filtering**: Remove PII and unsafe content

### Registration Phase

1. **Dataset Creation**: Create dataset version
2. **Metadata Recording**: Record all metadata
3. **Status Management**: Track dataset lifecycle
4. **Storage**: Store processed data

## Best Practices

### Data Collection

- Always verify license compliance
- Respect robots.txt
- Track provenance
- Calculate checksums
- Store raw data before processing

### Data Cleaning

- Preserve original data
- Track cleaning statistics
- Use conservative filtering thresholds
- Validate cleaning results

### Quality Control

- Set appropriate quality thresholds
- Monitor vocabulary diversity
- Check for encoding issues
- Validate language detection

### Safety

- Use multiple safety filters
- Redact PII by default
- Log all safety violations
- Review false positives

## Configuration

### Collector Configuration

```python
# Web collector settings
USER_AGENT = "Fivoria-DataCollector/1.0"
TIMEOUT = 300  # seconds
MAX_RETRIES = 3
```

### Cleaning Configuration

```python
# Quality thresholds
MIN_WORD_COUNT = 50
MAX_WORD_COUNT = 100000
MIN_VOCABULARY_DIVERSITY = 0.3
```

### Safety Configuration

```python
# Safety levels
SAFETY_LEVELS = {
    "low": {"hate_speech": False, "violence": False},
    "medium": {"hate_speech": True, "violence": True},
    "high": {"hate_speech": True, "violence": True, "self_harm": True}
}
```

## Monitoring

### Metrics to Track

- Collection success rate
- Processing throughput
- Quality filter pass rate
- Safety violation rate
- Deduplication rate

### Logging

All components log important events:
- Collection successes/failures
- Processing statistics
- Quality metrics
- Safety violations

## Troubleshooting

### Collection Issues

- **Problem**: Collection fails
- **Solution**: Check URL, network, permissions

### Parsing Issues

- **Problem**: Parser fails
- **Solution**: Check file format, encoding

### Quality Issues

- **Problem**: Too many documents filtered
- **Solution**: Adjust quality thresholds

### Safety Issues

- **Problem**: Too many false positives
- **Solution**: Review safety patterns, adjust thresholds

## Integration

### With Training Pipeline

```python
# Load dataset from registry
registry = DatasetRegistry(Path("./data/registry"))
dataset = registry.get_dataset("fivoria-pretrain-v1")

# Use in training
trainer = Trainer(model, dataset.storage_path)
```

### With Tokenizer

```python
from data_platform.tokenization.tokenizer import FivoriaTokenizer

tokenizer = FivoriaTokenizer()
tokens = tokenizer.encode(text)
```

## Security Considerations

- Encrypt sensitive data at rest
- Use secure connections for collection
- Implement access controls
- Audit data access
- Comply with GDPR/CCPA

## Performance Optimization

- Use parallel processing for collection
- Batch processing for cleaning
- Cache intermediate results
- Use efficient data structures
- Monitor memory usage

## Scaling

### Horizontal Scaling

- Distribute collection across workers
- Use message queues for coordination
- Scale storage independently

### Vertical Scaling

- Increase memory for large documents
- Use faster storage for I/O
- Optimize CPU for processing

## Future Enhancements

- Advanced NER for PII detection
- ML-based quality scoring
- Distributed deduplication
- Real-time processing
- Automated data validation
