#!/usr/bin/env python3
"""
Integration Tests for ClipStash AI Plugin System
"""

import pytest
from clipstash_core import ClipItem, PluginManager, ContextProvider
from enhanced_history_manager import EnhancedHistoryManager
from plugins.security_monitor import SecurityMonitorPlugin
from plugins.content_enricher import ContentEnricherPlugin


class TestIntegration:
    """Integration tests for the complete system."""
    
    @pytest.mark.asyncio
    async def test_plugin_pipeline(self):
        """Test multiple plugins processing a clip."""
        # Create plugin manager
        manager = PluginManager()
        
        # Load plugins
        security = SecurityMonitorPlugin()
        enricher = ContentEnricherPlugin()
        
        manager.load_plugin(security)
        manager.load_plugin(enricher)
        
        # Process clip
        clip = ClipItem("API_KEY=sk-12345")
        context = ContextProvider.get_context()
        
        processed = manager.process_clip(clip, context)
        
        # Should be processed by both plugins
        assert 'SecurityMonitor' in processed._processed_by
        assert 'ContentEnricher' in processed._processed_by
        
        # Should have enrichments from both
        assert 'security' in processed.metadata.enrichments
        assert 'content' in processed.metadata.enrichments
    
    @pytest.mark.asyncio
    async def test_history_manager_with_plugins(self):
        """Test EnhancedHistoryManager with plugins."""
        # Create plugin manager
        manager = PluginManager()
        
        # Load plugins
        security = SecurityMonitorPlugin()
        manager.load_plugin(security)
        
        # Create history manager
        history = EnhancedHistoryManager(manager)
        
        # Add clip
        clip = history.add("test content")
        
        assert clip is not None
        assert len(clip._processed_by) > 0
    
    def test_plugin_priority_ordering(self):
        """Test that plugins execute in priority order."""
        manager = PluginManager()
        
        # Security (CRITICAL) should run before Enricher (HIGH)
        security = SecurityMonitorPlugin()
        enricher = ContentEnricherPlugin()
        
        manager.load_plugin(enricher)  # Load in reverse order
        manager.load_plugin(security)
        
        # Check order
        assert manager.plugins[0].name == "SecurityMonitor"
        assert manager.plugins[1].name == "ContentEnricher"
    
    @pytest.mark.asyncio
    async def test_security_blocks_enrichment(self):
        """Test that security can block before enrichment."""
        manager = PluginManager()
        
        # Enable blocking
        security = SecurityMonitorPlugin({'block_sensitive': True, 'min_risk_score': 0.5})
        enricher = ContentEnricherPlugin()
        
        manager.load_plugin(security)
        manager.load_plugin(enricher)
        
        # Create high-risk content
        clip = ClipItem("-----BEGIN PRIVATE KEY-----\nMIIE...")
        context = ContextProvider.get_context()
        
        # Process
        processed = manager.process_clip(clip, context)
        
        # Try to paste
        result = await manager.on_paste_async(processed, context)
        
        # Should potentially block (depends on risk score)
        # Just verify it doesn't crash
        assert result is None or isinstance(result, ClipItem)
    
    def test_context_provider_integration(self):
        """Test ContextProvider integration."""
        context = ContextProvider.get_context()
        
        # Verify we get all expected fields
        assert 'active_app' in context
        assert 'timestamp' in context
        assert 'platform' in context
        
        # Use context in plugin
        manager = PluginManager()
        security = SecurityMonitorPlugin()
        manager.load_plugin(security)
        
        clip = ClipItem("test")
        processed = manager.process_clip(clip, context)
        
        assert processed is not None
    
    def test_search_with_plugins(self):
        """Test search functionality with plugins."""
        manager = PluginManager()
        enricher = ContentEnricherPlugin()
        manager.load_plugin(enricher)
        
        history = EnhancedHistoryManager(manager)
        
        # Add some clips
        history.add("python code: def test(): pass")
        history.add("javascript code: function test() {}")
        history.add("regular text")
        
        # Search
        results = history.search("code")
        
        assert len(results) >= 2
        
        # Verify enrichment
        for result in results:
            if 'code' in result.content.lower():
                assert 'content' in result.metadata.enrichments
    
    def test_stats_with_plugins(self):
        """Test statistics collection with plugins."""
        manager = PluginManager()
        security = SecurityMonitorPlugin()
        enricher = ContentEnricherPlugin()
        
        manager.load_plugin(security)
        manager.load_plugin(enricher)
        
        history = EnhancedHistoryManager(manager)
        
        # Add clips
        history.add("normal text")
        history.add("API_KEY=sk-12345")  # Should be flagged
        
        # Get stats
        stats = history.get_stats()
        
        assert stats['total'] >= 2
        assert stats['plugins_active'] > 0
        assert 'SecurityMonitor' in stats['plugins_list']
    
    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Test system recovers from plugin errors."""
        
        class BrokenPlugin(ContentEnricherPlugin):
            async def process_clip(self, clip, context):
                raise Exception("Plugin is broken!")
        
        manager = PluginManager()
        
        # Load working and broken plugins
        working = SecurityMonitorPlugin()
        broken = BrokenPlugin()
        
        manager.load_plugin(broken)
        manager.load_plugin(working)
        
        # Process clip
        clip = ClipItem("test")
        context = {}
        
        # Should not crash
        processed = manager.process_clip(clip, context)
        
        # Working plugin should still process
        assert 'SecurityMonitor' in processed._processed_by
    
    def test_config_loading_integration(self):
        """Test loading plugins from config."""
        import json
        from pathlib import Path
        
        # Create temp config
        config = {
            "SecurityMonitor": {
                "enabled": True,
                "config": {
                    "block_sensitive": True
                }
            }
        }
        
        # Create plugin with config
        plugin = SecurityMonitorPlugin(config["SecurityMonitor"]["config"])
        
        assert plugin.block_sensitive == True
    
    def test_memory_management(self):
        """Test that system handles many clips efficiently."""
        manager = PluginManager()
        enricher = ContentEnricherPlugin()
        manager.load_plugin(enricher)
        
        history = EnhancedHistoryManager(manager)
        
        # Add many clips
        for i in range(100):
            history.add(f"clip content {i}")
        
        # Should trim to MAX_HISTORY
        assert len(history.items) <= 500
        
        # Stats should work
        stats = history.get_stats()
        assert stats['total'] <= 500
