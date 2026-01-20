#!/usr/bin/env python3
"""
Security Monitor Plugin - AI Security Monitor
Priority: CRITICAL

Detects sensitive data in clipboard content including:
- API keys and tokens
- Private keys (SSH, PGP, etc.)
- Passwords
- Social Security Numbers
- Credit card numbers
- Email addresses with passwords

Calculates privacy score and risk level.
Can optionally block pastes of sensitive content.
"""

import re
import logging
from typing import Dict, Any, Optional, List

from clipstash_core import ClipStashPlugin, ClipItem, PluginPriority

logger = logging.getLogger(__name__)


class SecurityMonitorPlugin(ClipStashPlugin):
    """
    Monitors clipboard for sensitive data and security risks.
    """
    
    # Detection patterns
    PATTERNS = {
        'api_key': [
            r'(?i)(api[_-]?key|apikey)\s*[:=]\s*[\'"]?([a-zA-Z0-9_\-]{20,})',
            r'(?i)(access[_-]?token|token)\s*[:=]\s*[\'"]?([a-zA-Z0-9_\-]{20,})',
            r'AKIA[0-9A-Z]{16}',  # AWS Access Key
            r'AIza[0-9A-Za-z\-_]{35}',  # Google API Key
            r'ya29\.[0-9A-Za-z\-_]+',  # Google OAuth
            r'sk-[a-zA-Z0-9]{32,}',  # OpenAI API Key
            r'ghp_[a-zA-Z0-9]{36}',  # GitHub Personal Access Token
            r'glpat-[a-zA-Z0-9\-_]{20,}',  # GitLab Personal Access Token
        ],
        'private_key': [
            r'-----BEGIN (?:RSA |DSA |EC )?PRIVATE KEY-----',
            r'-----BEGIN OPENSSH PRIVATE KEY-----',
            r'-----BEGIN PGP PRIVATE KEY BLOCK-----',
        ],
        'password': [
            r'(?i)(password|passwd|pwd)\s*[:=]\s*[\'"]([^\'"]{8,})[\'"]',
            r'(?i)pass\s*[:=]\s*[\'"]?([^\s\'"]{8,})',
        ],
        'ssn': [
            r'\b\d{3}-\d{2}-\d{4}\b',  # XXX-XX-XXXX
            r'\b\d{9}\b',  # XXXXXXXXX (contextual)
        ],
        'credit_card': [
            r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b',
        ],
        'jwt_token': [
            r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*',
        ],
        'database_url': [
            r'(?i)(mongodb|mysql|postgres|postgresql)://[^\s]+',
        ],
        'bearer_token': [
            r'(?i)bearer\s+[a-zA-Z0-9\-._~+/]+=*',
        ],
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._name = "SecurityMonitor"
        self._priority = PluginPriority.CRITICAL
        self._version = "1.0.0"
        
        # Configuration
        self.block_sensitive = config.get('block_sensitive', False) if config else False
        self.warn_on_paste = config.get('warn_on_paste', True) if config else True
        self.min_risk_score = config.get('min_risk_score', 0.3) if config else 0.3
        self.enabled_patterns = config.get('enabled_patterns', list(self.PATTERNS.keys())) if config else list(self.PATTERNS.keys())
    
    async def initialize(self) -> bool:
        """Initialize the security monitor."""
        logger.info(f"{self.name} initialized (block_sensitive={self.block_sensitive})")
        return True
    
    async def process_clip(self, clip: ClipItem, context: Dict[str, Any]) -> ClipItem:
        """
        Scan clipboard content for sensitive data.
        
        Args:
            clip: Clipboard item to scan
            context: Current context
        
        Returns:
            Clip with security metadata added
        """
        content = clip.content
        flags = []
        detections = {}
        risk_score = 0.0
        
        # Scan for each pattern type
        for pattern_type in self.enabled_patterns:
            if pattern_type not in self.PATTERNS:
                continue
            
            patterns = self.PATTERNS[pattern_type]
            matches = []
            
            for pattern in patterns:
                found = re.findall(pattern, content)
                if found:
                    matches.extend(found)
            
            if matches:
                flags.append(pattern_type)
                detections[pattern_type] = len(matches)
                
                # Calculate risk contribution
                risk_contribution = self._calculate_risk(pattern_type, len(matches))
                risk_score += risk_contribution
        
        # Normalize risk score
        risk_score = min(risk_score, 1.0)
        
        # Calculate privacy score (inverse of risk)
        privacy_score = 1.0 - risk_score
        
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "CRITICAL"
        elif risk_score >= 0.5:
            risk_level = "HIGH"
        elif risk_score >= 0.3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Add metadata
        clip.metadata.security_flags = flags
        clip.metadata.enrichments['security'] = {
            'detections': detections,
            'risk_score': round(risk_score, 3),
            'privacy_score': round(privacy_score, 3),
            'risk_level': risk_level,
            'total_issues': len(flags)
        }
        
        if flags:
            logger.warning(
                f"Security issues detected: {', '.join(flags)} "
                f"(risk={risk_level}, score={risk_score:.2f})"
            )
        
        return clip
    
    def _calculate_risk(self, pattern_type: str, count: int) -> float:
        """
        Calculate risk contribution for a pattern type.
        
        Args:
            pattern_type: Type of pattern detected
            count: Number of matches
        
        Returns:
            Risk score contribution (0.0 to 1.0)
        """
        # Base risk scores by type
        base_risks = {
            'private_key': 0.9,
            'api_key': 0.7,
            'password': 0.8,
            'credit_card': 0.9,
            'ssn': 0.95,
            'jwt_token': 0.6,
            'database_url': 0.7,
            'bearer_token': 0.65,
        }
        
        base_risk = base_risks.get(pattern_type, 0.5)
        
        # Increase risk with multiple occurrences (logarithmic scaling)
        # Factor of 0.1 provides gradual increase: 2 occurrences = 1.07x, 10 occurrences = 1.23x
        import math
        multiplier = 1.0 + (math.log(count) * 0.1)
        
        return min(base_risk * multiplier, 1.0)
    
    async def on_paste(self, clip: ClipItem, context: Dict[str, Any]) -> Optional[ClipItem]:
        """
        Check security before paste.
        Can block paste if content is too risky.
        
        Args:
            clip: Clip being pasted
            context: Current context
        
        Returns:
            Clip or None to block paste
        """
        security = clip.metadata.enrichments.get('security', {})
        risk_score = security.get('risk_score', 0.0)
        
        # Block if risk is too high and blocking is enabled
        if self.block_sensitive and risk_score >= self.min_risk_score:
            logger.warning(
                f"BLOCKED paste: Risk score {risk_score:.2f} >= {self.min_risk_score} "
                f"(flags: {', '.join(clip.metadata.security_flags)})"
            )
            return None
        
        # Log warning if enabled
        if self.warn_on_paste and clip.metadata.security_flags:
            logger.warning(
                f"Pasting sensitive content: {', '.join(clip.metadata.security_flags)}"
            )
        
        return clip
    
    async def shutdown(self):
        """Cleanup on shutdown."""
        logger.info(f"{self.name} shutdown")
