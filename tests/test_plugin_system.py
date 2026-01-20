#!/usr/bin/env python3
"""
Test Suite for ClipStash Core Plugin Architecture
"""

import pytest
import asyncio
from datetime import datetime

from clipstash_core import (
    ClipMetadata, ClipItem, PluginPriority,
    ClipStashPlugin, PluginManager, ContextProvider
)


class TestClipMetadata:
    """Test ClipMetadata class."""
    
    def test_default_initialization(self):
        """Test default metadata initialization."""
        metadata = ClipMetadata()
        assert metadata.enrichments == {}
        assert metadata.predictions == {}
        assert metadata.security_flags == []
        assert metadata.relationships == []
        assert metadata.tags == []
        assert metadata.confidence_scores == {}
    
    def test_to_dict(self):
        """Test metadata serialization to dict."""
        metadata = ClipMetadata(
            enrichments={'test': 'value'},
            security_flags=['api_key']
        )
        data = metadata.to_dict()
        assert data['enrichments'] == {'test': 'value'}
        assert data['security_flags'] == ['api_key']
    
    def test_from_dict(self):
        """Test metadata deserialization from dict."""
        data = {
            'enrichments': {'content_type': 'code'},
            'tags': ['python', 'code']
        }
        metadata = ClipMetadata.from_dict(data)
        assert metadata.enrichments == {'content_type': 'code'}
        assert metadata.tags == ['python', 'code']


class TestClipItem:
    """Test ClipItem class."""
    
    def test_basic_creation(self):
        """Test basic clip creation."""
        clip = ClipItem("test content")
        assert clip.content == "test content"
        assert clip.pinned == False
        assert len(clip.hash) == 8
        assert isinstance(clip.metadata, ClipMetadata)
    
    def test_clip_hash(self):
        """Test clip hash generation."""
        clip1 = ClipItem("same content")
        clip2 = ClipItem("same content")
        clip3 = ClipItem("different content")
        
        assert clip1.hash == clip2.hash
        assert clip1.hash != clip3.hash
    
    def test_to_dict(self):
        """Test clip serialization."""
        clip = ClipItem("test", pinned=True)
        clip.metadata.tags.append('test')
        
        data = clip.to_dict()
        assert data['content'] == 'test'
        assert data['pinned'] == True
        assert 'metadata' in data
        assert data['metadata']['tags'] == ['test']
    
    def test_from_dict(self):
        """Test clip deserialization."""
        data = {
            'content': 'restored content',
            'timestamp': '2024-01-01T12:00:00',
            'pinned': True,
            'hash': '12345678',
            'metadata': {
                'tags': ['restored']
            }
        }
        
        clip = ClipItem.from_dict(data)
        assert clip.content == 'restored content'
        assert clip.pinned == True
        assert clip.hash == '12345678'
        assert clip.metadata.tags == ['restored']
    
    def test_preview(self):
        """Test content preview generation."""
        clip = ClipItem("a" * 100)
        preview = clip.preview(50)
        assert len(preview) <= 53  # 50 + "..."
        assert preview.endswith("...")
    
    def test_formatted_time(self):
        """Test formatted time display."""
        clip = ClipItem("test")
        formatted = clip.formatted_time()
        assert formatted == "Just now" or "ago" in formatted


class TestPluginPriority:
    """Test PluginPriority enum."""
    
    def test_priority_values(self):
        """Test priority ordering."""
        assert PluginPriority.CRITICAL < PluginPriority.HIGH
        assert PluginPriority.HIGH < PluginPriority.MEDIUM
        assert PluginPriority.MEDIUM < PluginPriority.LOW


class DummyPlugin(ClipStashPlugin):
    """Dummy plugin for testing."""
    
    def __init__(self, config=None):
        super().__init__(config)
        self._name = "DummyPlugin"
        self._priority = PluginPriority.MEDIUM
        self.init_called = False
        self.process_called = False
        self.shutdown_called = False
    
    async def initialize(self) -> bool:
        self.init_called = True
        return True
    
    async def process_clip(self, clip, context):
        self.process_called = True
        clip.metadata.tags.append('dummy')
        return clip
    
    async def shutdown(self):
        self.shutdown_called = True


class TestClipStashPlugin:
    """Test ClipStashPlugin base class."""
    
    def test_plugin_properties(self):
        """Test plugin properties."""
        plugin = DummyPlugin()
        assert plugin.name == "DummyPlugin"
        assert plugin.priority == PluginPriority.MEDIUM
        assert plugin.enabled == True
    
    def test_enable_disable(self):
        """Test plugin enable/disable."""
        plugin = DummyPlugin()
        assert plugin.enabled
        
        plugin.disable()
        assert not plugin.enabled
        
        plugin.enable()
        assert plugin.enabled


class TestPluginManager:
    """Test PluginManager class."""
    
    def test_initialization(self):
        """Test plugin manager initialization."""
        manager = PluginManager(timeout=10.0)
        assert manager.timeout == 10.0
        assert len(manager.plugins) == 0
    
    def test_load_plugin(self):
        """Test loading a plugin."""
        manager = PluginManager()
        plugin = DummyPlugin()
        
        success = manager.load_plugin(plugin)
        assert success
        assert plugin.init_called
        assert plugin._initialized
        assert plugin in manager.plugins
    
    def test_unload_plugin(self):
        """Test unloading a plugin."""
        manager = PluginManager()
        plugin = DummyPlugin()
        
        manager.load_plugin(plugin)
        success = manager.unload_plugin("DummyPlugin")
        
        assert success
        assert plugin.shutdown_called
        assert plugin not in manager.plugins
    
    def test_process_clip(self):
        """Test clip processing through plugins."""
        manager = PluginManager()
        plugin = DummyPlugin()
        manager.load_plugin(plugin)
        
        clip = ClipItem("test")
        context = {}
        
        processed = manager.process_clip(clip, context)
        
        assert plugin.process_called
        assert 'dummy' in processed.metadata.tags
        assert 'DummyPlugin' in processed._processed_by
    
    def test_plugin_priority_sorting(self):
        """Test plugins are sorted by priority."""
        manager = PluginManager()
        
        plugin1 = DummyPlugin()
        plugin1._priority = PluginPriority.LOW
        
        plugin2 = DummyPlugin()
        plugin2._priority = PluginPriority.CRITICAL
        plugin2._name = "CriticalPlugin"
        
        manager.load_plugin(plugin1)
        manager.load_plugin(plugin2)
        
        # Critical should be first
        assert manager.plugins[0].name == "CriticalPlugin"
        assert manager.plugins[1].name == "DummyPlugin"


class TestContextProvider:
    """Test ContextProvider class."""
    
    def test_get_context(self):
        """Test context retrieval."""
        context = ContextProvider.get_context()
        
        assert 'active_app' in context
        assert 'time_of_day' in context
        assert 'day_of_week' in context
        assert 'timestamp' in context
        assert 'platform' in context
    
    def test_context_types(self):
        """Test context value types."""
        context = ContextProvider.get_context()
        
        assert isinstance(context['active_app'], str)
        assert isinstance(context['time_of_day'], str)
        assert isinstance(context['platform'], str)


@pytest.mark.asyncio
async def test_async_plugin_processing():
    """Test asynchronous plugin processing."""
    manager = PluginManager()
    plugin = DummyPlugin()
    manager.load_plugin(plugin)
    
    clip = ClipItem("async test")
    context = {}
    
    processed = await manager.process_clip_async(clip, context)
    
    assert 'dummy' in processed.metadata.tags
    assert plugin.process_called


def test_plugin_failure_isolation():
    """Test that plugin failures don't crash the system."""
    
    class FailingPlugin(ClipStashPlugin):
        async def initialize(self):
            return True
        
        async def process_clip(self, clip, context):
            raise Exception("Plugin failed!")
    
    manager = PluginManager()
    failing_plugin = FailingPlugin()
    working_plugin = DummyPlugin()
    
    manager.load_plugin(failing_plugin)
    manager.load_plugin(working_plugin)
    
    clip = ClipItem("test")
    context = {}
    
    # Should not raise exception
    processed = manager.process_clip(clip, context)
    
    # Working plugin should still process
    assert working_plugin.process_called
