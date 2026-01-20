# ClipStash Enhanced v2.0.0 - AI Plugin System

## 🚀 Overview

ClipStash Enhanced is a comprehensive AI-powered clipboard management system built on top of the original ClipStash. It features a plugin architecture that enables advanced functionality through 10 specialized AI plugins.

## 🏗️ Architecture

### Core Components

```
ClipStash Enhanced
├── clipstash_core.py         # Core plugin architecture
├── enhanced_history_manager.py # Enhanced clipboard history
├── clipstash_enhanced.py      # Main application entry point
├── plugins/                   # Plugin directory
│   ├── security_monitor.py    # CRITICAL: Security scanning
│   ├── content_enricher.py    # HIGH: Content analysis
│   ├── paste_predictor.py     # HIGH: ML paste prediction
│   ├── research_assistant.py  # HIGH: Academic paper search
│   ├── sync_agent.py          # MEDIUM: Cross-device sync
│   ├── workflow_trigger.py    # MEDIUM: Automation triggers
│   ├── knowledge_graph.py     # MEDIUM: NLP & relationships
│   ├── collaborative.py       # LOW: Shared clipboards
│   ├── smart_templates.py     # LOW: Template detection
│   └── api_wrapper.py         # LOW: API execution
├── ui/                        # UI components
│   └── plugin_settings.py     # Plugin configuration dialog
├── config/                    # Configuration
│   └── plugins.json           # Plugin settings
└── tests/                     # Test suite
```

### Plugin System

The plugin system is built on a priority-based execution model:

1. **CRITICAL (Priority 1)**: Security and validation - runs FIRST
2. **HIGH (Priority 2)**: Enrichment and predictions
3. **MEDIUM (Priority 3)**: Analytics and automation
4. **LOW (Priority 4)**: Background tasks

#### Plugin Lifecycle

```python
# 1. Plugin loads and initializes
await plugin.initialize()

# 2. Process clipboard items
processed_clip = await plugin.process_clip(clip, context)

# 3. Handle paste events (optional)
result = await plugin.on_paste(clip, context)

# 4. Enhance search results (optional)
results = await plugin.on_search(query, results)

# 5. Cleanup on shutdown
await plugin.shutdown()
```

### Data Flow

```
Clipboard → EnhancedHistoryManager
                ↓
         PluginManager (Priority Order)
                ↓
    [CRITICAL] SecurityMonitor
                ↓
    [HIGH] ContentEnricher
                ↓
    [HIGH] PastePredictor
                ↓
    ... (other plugins)
                ↓
    ClipItem (with enriched metadata)
                ↓
         Save to History
```

## 🎯 Key Features

### Metadata System

Each clipboard item has rich metadata:

```python
ClipItem
├── content: str              # Original clipboard content
├── timestamp: str            # ISO format timestamp
├── pinned: bool             # Pin status
├── hash: str                # Content hash (8 chars)
└── metadata: ClipMetadata
    ├── enrichments: dict    # Plugin enrichment data
    ├── predictions: dict    # ML predictions
    ├── security_flags: list # Security issues
    ├── relationships: list  # Related clips
    ├── tags: list          # Content tags
    └── confidence_scores: dict # Prediction confidence
```

### Context-Aware Processing

Plugins receive context information:

```python
{
    "active_app": "VSCode",
    "time_of_day": "14:30:15",
    "day_of_week": "Monday",
    "timestamp": "2024-01-15T14:30:15",
    "platform": "Linux",
    "platform_version": "5.15.0",
    "python_version": "3.10.0"
}
```

## 🔧 Configuration

### Plugin Configuration

Edit `~/.clipstash/config/plugins.json`:

```json
{
  "SecurityMonitor": {
    "enabled": true,
    "config": {
      "block_sensitive": false,
      "warn_on_paste": true,
      "min_risk_score": 0.3
    }
  },
  "ContentEnricher": {
    "enabled": true,
    "config": {
      "enrich_urls": true,
      "enrich_code": true,
      "fetch_timeout": 3.0
    }
  }
}
```

### Via UI

1. Launch ClipStash Enhanced
2. Menu → Plugins → Plugin Settings
3. Configure each plugin in its tab
4. Click Save to persist changes

## 🚦 Usage

### Basic Usage

```bash
# Run ClipStash Enhanced
python clipstash_enhanced.py
```

### Programmatic Usage

```python
from clipstash_core import PluginManager, ClipItem
from plugins import SecurityMonitorPlugin, ContentEnricherPlugin

# Create plugin manager
manager = PluginManager()

# Load plugins
security = SecurityMonitorPlugin()
enricher = ContentEnricherPlugin()

manager.load_plugin(security)
manager.load_plugin(enricher)

# Process clipboard item
clip = ClipItem("your content here")
context = {"active_app": "Terminal"}

processed = manager.process_clip(clip, context)

# Check results
if processed.metadata.security_flags:
    print(f"Security issues: {processed.metadata.security_flags}")

if 'content' in processed.metadata.enrichments:
    content_type = processed.metadata.enrichments['content']['content_type']
    print(f"Content type: {content_type}")
```

## 🧪 Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Run all tests
pytest tests/

# Run with coverage
pytest --cov=. tests/

# Run specific test file
pytest tests/test_security_monitor.py

# Run with verbose output
pytest -v tests/
```

### Test Coverage

The test suite includes:
- Unit tests for core plugin architecture
- Metadata serialization tests
- Plugin-specific functionality tests
- Integration tests for complete system
- Error handling and recovery tests

## 📦 Dependencies

### Required

```bash
pip install -r requirements.txt  # Basic ClipStash
pip install -r requirements_ai.txt  # AI features
```

### Optional

Some plugins have optional dependencies:
- **spaCy**: NLP entity extraction (KnowledgeGraph)
- **sentence-transformers**: Advanced similarity (KnowledgeGraph)
- **aiohttp**: URL fetching (ContentEnricher, ResearchAssistant)
- **scikit-learn**: ML predictions (PastePredictor)

Without these, plugins will use fallback implementations or be disabled.

## 🔌 Creating Custom Plugins

```python
from clipstash_core import ClipStashPlugin, PluginPriority

class MyCustomPlugin(ClipStashPlugin):
    def __init__(self, config=None):
        super().__init__(config)
        self._name = "MyPlugin"
        self._priority = PluginPriority.MEDIUM
    
    async def initialize(self) -> bool:
        # Setup code here
        return True
    
    async def process_clip(self, clip, context):
        # Process clipboard item
        clip.metadata.tags.append('custom')
        return clip
    
    async def shutdown(self):
        # Cleanup code here
        pass
```

## 🔒 Security Considerations

1. **Sensitive Data**: SecurityMonitor scans for API keys, passwords, etc.
2. **Paste Blocking**: Can block pastes of high-risk content
3. **Sync Encryption**: E2E encryption for cross-device sync
4. **Sandboxing**: API execution runs in safe mode by default
5. **Rate Limiting**: API Wrapper limits requests per minute

## 🐛 Troubleshooting

### Plugin Not Loading

1. Check logs: `~/.clipstash/clipstash_enhanced.log`
2. Verify plugin is enabled in config
3. Check for missing dependencies

### Import Errors

```bash
# Ensure all dependencies installed
pip install -r requirements_ai.txt

# For spaCy models
python -m spacy download en_core_web_sm
```

### Performance Issues

1. Disable unused plugins
2. Reduce `retrain_interval` for PastePredictor
3. Set `use_transformers=false` for KnowledgeGraph
4. Decrease `fetch_timeout` for network plugins

## 📝 Backward Compatibility

ClipStash Enhanced maintains full backward compatibility:
- Original `clipstash.py` continues to work unchanged
- History files are compatible between versions
- Can run both versions side-by-side

## 🤝 Contributing

See [PLUGINS.md](PLUGINS.md) for detailed plugin documentation and development guidelines.

## 📄 License

MIT License - See LICENSE file for details

## 👏 Credits

- **Original ClipStash**: Logan Smith / Team Brain (Metaphy LLC)
- **Plugin System**: AI-powered enhancement architecture
- **Community**: Contributors and testers

---

**Version**: 2.0.0  
**Release Date**: 2025  
**Status**: Production Ready
