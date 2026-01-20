# ClipStash Plugins Documentation

Complete guide to all available plugins, their functionality, configuration options, and usage examples.

---

## 🔐 Security Monitor (CRITICAL Priority)

**Purpose**: Detects sensitive data in clipboard content and calculates security risk.

### Features

- API key detection (OpenAI, GitHub, AWS, Google, etc.)
- Private key detection (SSH, PGP, OpenSSH)
- Password pattern detection
- Social Security Number detection
- Credit card number detection
- JWT token detection
- Database URL detection
- Bearer token detection
- Risk scoring (0.0 to 1.0)
- Optional paste blocking

### Configuration

```json
{
  "block_sensitive": false,       // Block high-risk pastes
  "warn_on_paste": true,          // Log warnings
  "min_risk_score": 0.3,          // Minimum score to block
  "enabled_patterns": [
    "api_key",
    "private_key",
    "password",
    "ssn",
    "credit_card",
    "jwt_token",
    "database_url",
    "bearer_token"
  ]
}
```

### Example Output

```python
clip.metadata.security_flags = ['api_key', 'password']
clip.metadata.enrichments['security'] = {
    'detections': {
        'api_key': 1,
        'password': 2
    },
    'risk_score': 0.75,
    'privacy_score': 0.25,
    'risk_level': 'HIGH',
    'total_issues': 2
}
```

### Use Cases

- Prevent accidental sharing of API keys
- Alert when copying sensitive credentials
- Audit clipboard usage for compliance
- Block risky paste operations

---

## 📊 Content Enricher (HIGH Priority)

**Purpose**: Enriches clipboard content with contextual metadata and analysis.

### Features

- Content type detection (URL, code, text, JSON, email)
- URL enrichment (title, description, OpenGraph metadata)
- Code analysis (language detection, function extraction, line count)
- Text analysis (word count, email/phone extraction, sentiment)
- JSON validation and pretty-printing
- Multi-language code detection (Python, JavaScript, Java, etc.)

### Configuration

```json
{
  "enrich_urls": true,       // Fetch URL metadata
  "enrich_code": true,       // Analyze code structure
  "enrich_text": true,       // Extract text features
  "fetch_timeout": 3.0       // Network timeout (seconds)
}
```

### Example Output

**For Code:**
```python
clip.metadata.enrichments['content'] = {
    'content_type': 'code',
    'code': {
        'language': 'python',
        'lines': 42,
        'functions': ['main', 'process_data', 'calculate'],
        'classes': ['DataProcessor'],
        'comment_lines': 8
    }
}
```

**For URL:**
```python
clip.metadata.enrichments['content'] = {
    'content_type': 'url',
    'url': {
        'url': 'https://example.com',
        'domain': 'example.com',
        'title': 'Example Domain',
        'description': 'This domain is for examples...',
        'opengraph': {
            'title': 'Example',
            'type': 'website'
        }
    }
}
```

### Use Cases

- Automatically tag clipboard content
- Extract code structure for documentation
- Preview URLs before visiting
- Analyze text for key information

---

## 🎯 Paste Predictor (HIGH Priority)

**Purpose**: Machine learning-based prediction of paste likelihood.

### Features

- Tracks paste patterns by context (time, app, content type)
- Trains RandomForest model on usage history
- Predicts next paste with confidence scores
- Persists model to disk
- Automatic retraining on new data

### Configuration

```json
{
  "model_path": "~/.clipstash/paste_predictor.pkl",
  "min_training_samples": 50,    // Minimum data to train
  "max_predictions": 5,           // Top predictions to show
  "retrain_interval": 100         // Retrain every N pastes
}
```

### Example Output

```python
clip.metadata.predictions['paste_likelihood'] = [
    {
        'type': 'paste_likelihood',
        'confidence': 0.85,
        'timestamp': '2024-01-15T14:30:00'
    }
]
clip.metadata.confidence_scores['paste_prediction'] = 0.85
```

### Use Cases

- Prioritize frequently pasted items
- Smart clipboard organization
- Predict user needs based on context
- Optimize clipboard UI ordering

---

## 📚 Research Assistant (HIGH Priority)

**Purpose**: Finds related academic papers and research for clipboard content.

### Features

- Detects research-worthy content
- Searches arXiv API
- Searches Semantic Scholar API
- Extracts paper metadata (title, authors, abstract)
- Relevance scoring

### Configuration

```json
{
  "auto_search": true,           // Automatically search
  "max_results": 3,              // Papers per search
  "min_relevance_score": 0.3,   // Minimum relevance
  "search_timeout": 5.0          // API timeout (seconds)
}
```

### Example Output

```python
clip.metadata.enrichments['research'] = {
    'relevance_score': 0.8,
    'query': 'machine learning optimization',
    'papers': [
        {
            'title': 'Deep Learning Optimization Techniques',
            'authors': ['Smith, J.', 'Doe, A.'],
            'abstract': 'This paper presents...',
            'url': 'https://arxiv.org/abs/2024.12345',
            'published': '2024-01',
            'source': 'arXiv'
        }
    ],
    'count': 3
}
```

### Use Cases

- Research assistance during literature review
- Automatic citation suggestions
- Find related work for papers
- Discover new publications in your field

---

## 🔄 Sync Agent (MEDIUM Priority)

**Purpose**: Cross-device clipboard synchronization with encryption.

### Features

- WebSocket-based real-time sync
- E2E encryption using Fernet
- Device fingerprinting
- Conflict resolution (timestamp-based)
- Sensitive content filtering
- Delta syncing

### Configuration

```json
{
  "sync_server": "ws://localhost:8765",
  "encryption_key": null,         // Auto-generate or specify
  "device_id": null,              // Auto-generated
  "sync_enabled": false,          // Master toggle
  "filter_sensitive": true,       // Don't sync sensitive data
  "max_sync_size": 102400         // 100KB limit
}
```

### Example Output

```python
clip.metadata.enrichments['sync'] = {
    'device_id': 'abc123...',
    'device_name': 'MyLaptop',
    'timestamp': '2024-01-15T14:30:00',
    'should_sync': True
}
```

### Use Cases

- Sync clipboard between work and home computers
- Share clips across team members
- Backup clipboard history to cloud
- Mobile device integration

---

## ⚡ Workflow Trigger (MEDIUM Priority)

**Purpose**: Automated workflow triggers based on clipboard patterns.

### Features

- Error message → Stack Overflow search
- GitHub URL → Repository details
- Address → Geocoding/weather
- AWS resource → Resource description
- Email → Draft reply suggestions
- Extensible trigger system

### Configuration

```json
{
  "enabled_triggers": [
    "error_search",
    "github_info",
    "address_info",
    "aws_resource",
    "email_draft"
  ]
}
```

### Example Output

```python
clip.metadata.enrichments['workflows'] = {
    'triggered': [
        {
            'trigger': 'error_search',
            'result': {
                'type': 'error_search',
                'query': 'TypeError: cannot concatenate str and int',
                'search_url': 'https://stackoverflow.com/search?q=...',
                'description': 'Detected error message'
            }
        }
    ],
    'count': 1
}
```

### Use Cases

- Instant error message lookup
- Quick GitHub repository insights
- Location-based information retrieval
- Email workflow automation
- AWS resource management

---

## 🧠 Knowledge Graph (MEDIUM Priority)

**Purpose**: Builds knowledge graph with NLP entity extraction and relationships.

### Features

- spaCy entity extraction
- Relationship detection between clips
- NetworkX graph operations
- Semantic similarity using sentence-transformers
- Entity linking and clustering

### Configuration

```json
{
  "min_similarity": 0.5,         // Minimum similarity threshold
  "max_relationships": 10,       // Max related clips
  "use_spacy": true,             // Use spaCy for NLP
  "use_transformers": false      // Use sentence-transformers
}
```

### Example Output

```python
clip.metadata.enrichments['entities'] = [
    {
        'text': 'New York',
        'label': 'GPE',  // Geopolitical Entity
        'start': 15,
        'end': 23
    },
    {
        'text': 'John Smith',
        'label': 'PERSON',
        'start': 0,
        'end': 10
    }
]
```

### Use Cases

- Find related clipboard items
- Build concept maps from clips
- Entity-based search
- Content recommendation
- Research organization

---

## 👥 Collaborative Clipboard (LOW Priority)

**Purpose**: Shared clipboard spaces for teams.

### Features

- Multiple clipboard spaces
- User authentication
- Permission system (read/write/admin)
- Real-time activity feed
- WebSocket notifications
- Space management

### Configuration

```json
{
  "server_url": "ws://localhost:8766",
  "username": "anonymous",
  "auth_token": null,
  "auto_share": false,
  "default_space": "personal"
}
```

### Example Usage

```python
from plugins.collaborative import CollaborativeClipboardPlugin

plugin = CollaborativeClipboardPlugin(config)
await plugin.initialize()

# Create space
plugin.create_space("team-alpha", members=["alice", "bob"])

# Add member
plugin.add_member("team-alpha", "charlie", permission="write")

# Switch to space
plugin.switch_space("team-alpha")

# Get activity
activities = plugin.get_activity_feed("team-alpha", limit=20)
```

### Use Cases

- Team clipboard sharing
- Collaborative research
- Code snippet libraries
- Documentation workflows
- Remote pair programming

---

## 📝 Smart Templates (LOW Priority)

**Purpose**: Detects and creates templates from repeated patterns.

### Features

- Template type detection (email, code, meeting notes, bug reports)
- Pattern recognition and extraction
- Variable placeholder generation
- Template suggestion engine
- Usage tracking

### Configuration

```json
{
  "min_pattern_count": 3,        // Patterns needed for template
  "similarity_threshold": 0.6,   // Structure similarity
  "auto_suggest": true           // Suggest templates
}
```

### Example Output

```python
clip.metadata.enrichments['template'] = {
    'type': 'email',
    'template_id': 'email_1',
    'suggestion': '''
        Dear {{recipient}},
        
        [email body]
        
        Best regards,
        {{sender}}
    ''',
    'variables': ['recipient', 'sender']
}
```

### Use Cases

- Email template generation
- Code boilerplate creation
- Meeting notes standardization
- Bug report templates
- Reduce repetitive typing

---

## 🔌 API Wrapper (LOW Priority)

**Purpose**: Executes API-related clipboard content automatically.

### Features

- JSON validation and formatting
- HTTP request execution
- SQL query handling (sandboxed)
- File path reading
- Coordinate geocoding
- GraphQL query support
- Rate limiting

### Configuration

```json
{
  "auto_execute": false,          // Auto-run detected APIs
  "safe_mode": true,              // Restrict dangerous operations
  "max_requests_per_minute": 10,
  "allowed_domains": ["*"]        // Domain whitelist
}
```

### Example Output

```python
clip.metadata.enrichments['api'] = {
    'type': 'http_request',
    'url': 'https://api.github.com/users/octocat',
    'executed': True,
    'status': 200,
    'content_type': 'application/json',
    'response': {...}
}
```

### Use Cases

- Quick JSON validation
- API testing from clipboard
- Coordinate lookup
- File content preview
- GraphQL debugging

---

## 🛠️ Plugin Development Guide

### Creating a Custom Plugin

```python
from clipstash_core import ClipStashPlugin, PluginPriority

class MyPlugin(ClipStashPlugin):
    def __init__(self, config=None):
        super().__init__(config)
        self._name = "MyPlugin"
        self._priority = PluginPriority.MEDIUM
        self._version = "1.0.0"
        
        # Custom configuration
        self.my_setting = config.get('my_setting', 'default') if config else 'default'
    
    async def initialize(self) -> bool:
        """Initialize plugin resources."""
        # Setup code here
        logger.info(f"{self.name} initialized")
        return True
    
    async def process_clip(self, clip, context):
        """Process clipboard item."""
        # Add your logic here
        clip.metadata.enrichments['my_plugin'] = {
            'processed': True,
            'data': 'custom data'
        }
        clip.metadata.tags.append('my-tag')
        
        return clip
    
    async def on_paste(self, clip, context):
        """Called before paste (optional)."""
        # Can modify or block paste
        return clip
    
    async def on_search(self, query, results):
        """Enhance search results (optional)."""
        return results
    
    async def shutdown(self):
        """Cleanup on shutdown."""
        logger.info(f"{self.name} shutdown")
```

### Best Practices

1. **Error Handling**: Always wrap risky operations in try-except
2. **Timeouts**: Use timeouts for network operations
3. **Logging**: Log important events and errors
4. **Dependencies**: Make optional dependencies graceful
5. **Performance**: Keep processing fast (<100ms)
6. **Testing**: Write unit tests for your plugin

### Plugin Checklist

- [ ] Implements all required abstract methods
- [ ] Has proper error handling
- [ ] Logs important events
- [ ] Handles missing dependencies gracefully
- [ ] Has unit tests
- [ ] Documented configuration options
- [ ] Performance tested with large clips
- [ ] Thread-safe and async-safe

---

## 📊 Performance Tips

1. **Disable Unused Plugins**: Only enable what you need
2. **Adjust Timeouts**: Reduce network timeouts if needed
3. **Limit Results**: Reduce `max_results` for search plugins
4. **Simple Models**: Use lighter ML models when possible
5. **Cache Results**: Plugins can cache enrichments
6. **Async Operations**: Use async/await properly

## 🐛 Debugging

```bash
# Enable debug logging
export CLIPSTASH_LOG_LEVEL=DEBUG

# Check logs
tail -f ~/.clipstash/clipstash_enhanced.log

# Test single plugin
pytest tests/test_security_monitor.py -v

# Profile performance
python -m cProfile clipstash_enhanced.py
```

---

**Last Updated**: 2025  
**Plugin API Version**: 2.0.0
