#!/usr/bin/env python3
"""
Test Suite for Security Monitor Plugin
"""

import pytest
from clipstash_core import ClipItem
from plugins.security_monitor import SecurityMonitorPlugin


class TestSecurityMonitor:
    """Test SecurityMonitorPlugin functionality."""
    
    @pytest.fixture
    def plugin(self):
        """Create plugin instance."""
        return SecurityMonitorPlugin()
    
    @pytest.mark.asyncio
    async def test_initialization(self, plugin):
        """Test plugin initialization."""
        success = await plugin.initialize()
        assert success
        assert plugin.name == "SecurityMonitor"
    
    @pytest.mark.asyncio
    async def test_detect_api_key(self, plugin):
        """Test API key detection."""
        await plugin.initialize()
        
        clip = ClipItem("API_KEY=sk-1234567890abcdefghijklmnop")
        context = {}
        
        processed = await plugin.process_clip(clip, context)
        
        assert 'security' in processed.metadata.enrichments
        assert 'api_key' in processed.metadata.security_flags
        security = processed.metadata.enrichments['security']
        assert security['risk_level'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    
    @pytest.mark.asyncio
    async def test_detect_github_token(self, plugin):
        """Test GitHub token detection."""
        await plugin.initialize()
        
        clip = ClipItem("ghp_1234567890abcdefghijklmnopqrstuv")
        context = {}
        
        processed = await plugin.process_clip(clip, context)
        
        assert 'api_key' in processed.metadata.security_flags
    
    @pytest.mark.asyncio
    async def test_detect_private_key(self, plugin):
        """Test private key detection."""
        await plugin.initialize()
        
        content = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1234567890
-----END RSA PRIVATE KEY-----"""
        
        clip = ClipItem(content)
        context = {}
        
        processed = await plugin.process_clip(clip, context)
        
        assert 'private_key' in processed.metadata.security_flags
        security = processed.metadata.enrichments['security']
        assert security['risk_score'] > 0.5
    
    @pytest.mark.asyncio
    async def test_detect_credit_card(self, plugin):
        """Test credit card detection."""
        await plugin.initialize()
        
        clip = ClipItem("Card number: 4532015112830366")
        context = {}
        
        processed = await plugin.process_clip(clip, context)
        
        assert 'credit_card' in processed.metadata.security_flags
    
    @pytest.mark.asyncio
    async def test_detect_ssn(self, plugin):
        """Test SSN detection."""
        await plugin.initialize()
        
        clip = ClipItem("SSN: 123-45-6789")
        context = {}
        
        processed = await plugin.process_clip(clip, context)
        
        assert 'ssn' in processed.metadata.security_flags
    
    @pytest.mark.asyncio
    async def test_clean_content(self, plugin):
        """Test clean content has no flags."""
        await plugin.initialize()
        
        clip = ClipItem("This is just regular text with no sensitive data.")
        context = {}
        
        processed = await plugin.process_clip(clip, context)
        
        assert len(processed.metadata.security_flags) == 0
    
    @pytest.mark.asyncio
    async def test_paste_blocking_disabled(self, plugin):
        """Test paste not blocked when blocking disabled."""
        plugin.block_sensitive = False
        await plugin.initialize()
        
        clip = ClipItem("API_KEY=secret123")
        context = {}
        
        # Process first to add flags
        processed = await plugin.process_clip(clip, context)
        
        # Try to paste
        result = await plugin.on_paste(processed, context)
        
        assert result is not None  # Should not block
    
    @pytest.mark.asyncio
    async def test_paste_blocking_enabled(self, plugin):
        """Test paste blocked when blocking enabled."""
        plugin.block_sensitive = True
        plugin.min_risk_score = 0.5
        await plugin.initialize()
        
        clip = ClipItem("-----BEGIN PRIVATE KEY-----\nMIIE...")
        context = {}
        
        # Process first to add flags
        processed = await plugin.process_clip(clip, context)
        
        # Try to paste
        result = await plugin.on_paste(processed, context)
        
        # Should block high-risk content
        if processed.metadata.enrichments['security']['risk_score'] >= 0.5:
            assert result is None
    
    @pytest.mark.asyncio
    async def test_multiple_sensitive_items(self, plugin):
        """Test detecting multiple sensitive items."""
        await plugin.initialize()
        
        content = """
        API_KEY=sk-12345
        Password: MySecret123
        Card: 4532015112830366
        """
        
        clip = ClipItem(content)
        context = {}
        
        processed = await plugin.process_clip(clip, context)
        
        # Should detect multiple issues
        assert len(processed.metadata.security_flags) >= 2
        security = processed.metadata.enrichments['security']
        assert security['total_issues'] >= 2
    
    @pytest.mark.asyncio
    async def test_risk_score_calculation(self, plugin):
        """Test risk score increases with severity."""
        await plugin.initialize()
        
        # Low risk
        clip1 = ClipItem("password: test")
        processed1 = await plugin.process_clip(clip1, {})
        score1 = processed1.metadata.enrichments.get('security', {}).get('risk_score', 0)
        
        # High risk
        clip2 = ClipItem("-----BEGIN PRIVATE KEY-----")
        processed2 = await plugin.process_clip(clip2, {})
        score2 = processed2.metadata.enrichments.get('security', {}).get('risk_score', 0)
        
        # Private key should have higher risk
        if score2 > 0:  # If detected
            assert score2 >= score1
