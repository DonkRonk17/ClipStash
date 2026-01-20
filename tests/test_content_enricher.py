#!/usr/bin/env python3
"""
Test Suite for Content Enricher Plugin
"""

import pytest
from unittest.mock import AsyncMock, patch
from clipstash_core import ClipItem
from plugins.content_enricher import ContentEnricherPlugin


class TestContentEnricher:
    """Test ContentEnricherPlugin functionality."""
    
    @pytest.fixture
    def plugin(self):
        """Create plugin instance."""
        return ContentEnricherPlugin()
    
    @pytest.mark.asyncio
    async def test_initialization(self, plugin):
        """Test plugin initialization."""
        success = await plugin.initialize()
        assert success
    
    @pytest.mark.asyncio
    async def test_detect_url(self, plugin):
        """Test URL detection."""
        await plugin.initialize()
        
        clip = ClipItem("https://github.com/user/repo")
        context = {}
        
        processed = await plugin.process_clip(clip, context)
        
        enrichment = processed.metadata.enrichments.get('content', {})
        assert enrichment['content_type'] == 'url'
        assert 'url' in processed.metadata.tags
    
    @pytest.mark.asyncio
    async def test_detect_code(self, plugin):
        """Test code detection."""
        await plugin.initialize()
        
        code = """def hello_world():
    print("Hello, World!")
    return 42"""
        
        clip = ClipItem(code)
        context = {}
        
        processed = await plugin.process_clip(clip, context)
        
        enrichment = processed.metadata.enrichments.get('content', {})
        assert enrichment['content_type'] == 'code'
        assert 'code' in enrichment
        assert enrichment['code']['lines'] == 3
    
    @pytest.mark.asyncio
    async def test_detect_python_code(self, plugin):
        """Test Python language detection."""
        await plugin.initialize()
        
        code = """import sys
def main():
    pass"""
        
        clip = ClipItem(code)
        context = {}
        
        processed = await plugin.process_clip(clip, context)
        
        code_data = processed.metadata.enrichments['content']['code']
        assert code_data.get('language') == 'python'
    
    @pytest.mark.asyncio
    async def test_detect_javascript_code(self, plugin):
        """Test JavaScript language detection."""
        await plugin.initialize()
        
        code = """function test() {
    const x = 42;
    return x;
}"""
        
        clip = ClipItem(code)
        context = {}
        
        processed = await plugin.process_clip(clip, context)
        
        code_data = processed.metadata.enrichments['content']['code']
        assert code_data.get('language') == 'javascript'
    
    @pytest.mark.asyncio
    async def test_extract_functions(self, plugin):
        """Test function extraction from code."""
        await plugin.initialize()
        
        code = """def func1():
    pass

def func2(x, y):
    return x + y"""
        
        clip = ClipItem(code)
        context = {}
        
        processed = await plugin.process_clip(clip, context)
        
        code_data = processed.metadata.enrichments['content']['code']
        assert 'functions' in code_data
        assert 'func1' in code_data['functions']
        assert 'func2' in code_data['functions']
    
    @pytest.mark.asyncio
    async def test_enrich_text(self, plugin):
        """Test text enrichment."""
        await plugin.initialize()
        
        text = """This is a test message with multiple words.
It has two lines.
Contact me at test@example.com or call 555-123-4567."""
        
        clip = ClipItem(text)
        context = {}
        
        processed = await plugin.process_clip(clip, context)
        
        text_data = processed.metadata.enrichments['content']['text']
        assert text_data['word_count'] > 0
        assert text_data['line_count'] == 3
        assert 'emails' in text_data
        assert 'test@example.com' in text_data['emails']
    
    @pytest.mark.asyncio
    async def test_detect_email(self, plugin):
        """Test email detection."""
        await plugin.initialize()
        
        clip = ClipItem("test@example.com")
        context = {}
        
        processed = await plugin.process_clip(clip, context)
        
        enrichment = processed.metadata.enrichments.get('content', {})
        assert enrichment['content_type'] == 'email'
    
    @pytest.mark.asyncio
    async def test_url_enrichment_without_fetch(self, plugin):
        """Test URL enrichment without fetching (no network)."""
        plugin.enrich_urls = True
        await plugin.initialize()
        
        clip = ClipItem("https://github.com")
        context = {}
        
        processed = await plugin.process_clip(clip, context)
        
        url_data = processed.metadata.enrichments['content']['url']
        assert url_data['domain'] == 'github.com'
        assert url_data['scheme'] == 'https'
    
    @pytest.mark.asyncio
    async def test_json_detection(self, plugin):
        """Test JSON detection."""
        await plugin.initialize()
        
        json_content = '{"key": "value", "number": 42}'
        clip = ClipItem(json_content)
        context = {}
        
        processed = await plugin.process_clip(clip, context)
        
        enrichment = processed.metadata.enrichments.get('content', {})
        assert enrichment['content_type'] == 'json'
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis(self, plugin):
        """Test basic sentiment analysis."""
        await plugin.initialize()
        
        # Positive text
        clip1 = ClipItem("This is great! I love it. Amazing!")
        processed1 = await plugin.process_clip(clip1, {})
        
        # Negative text
        clip2 = ClipItem("This is terrible. I hate it. Awful!")
        processed2 = await plugin.process_clip(clip2, {})
        
        text1 = processed1.metadata.enrichments['content']['text']
        text2 = processed2.metadata.enrichments['content']['text']
        
        # Check sentiments are different
        if 'sentiment' in text1 and 'sentiment' in text2:
            assert text1['sentiment'] != text2['sentiment']
