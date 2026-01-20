#!/usr/bin/env python3
"""
Content Enricher Plugin - Content Enrichment Pipeline
Priority: HIGH

Enriches clipboard content with metadata:
- Content type detection
- URL enrichment (title, description, OpenGraph metadata)
- Code enrichment (language detection, line count, function extraction)
- Text enrichment (word count, email/phone/address detection, sentiment)
- Image enrichment (EXIF data)
"""

import re
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from clipstash_core import ClipStashPlugin, ClipItem, PluginPriority

logger = logging.getLogger(__name__)


class ContentEnricherPlugin(ClipStashPlugin):
    """
    Enriches clipboard content with contextual metadata.
    """
    
    # Code language detection patterns
    LANGUAGE_PATTERNS = {
        'python': [r'^\s*def\s+\w+\s*\(', r'^\s*class\s+\w+', r'^\s*import\s+\w+', r'^\s*from\s+\w+\s+import'],
        'javascript': [r'^\s*function\s+\w+\s*\(', r'^\s*const\s+\w+\s*=', r'^\s*let\s+\w+\s*=', r'^\s*var\s+\w+\s*='],
        'java': [r'^\s*public\s+class', r'^\s*private\s+\w+\s+\w+', r'^\s*@\w+'],
        'cpp': [r'^\s*#include\s*<', r'^\s*using\s+namespace', r'^\s*std::'],
        'go': [r'^\s*package\s+\w+', r'^\s*func\s+\w+\s*\(', r'^\s*import\s+\('],
        'rust': [r'^\s*fn\s+\w+\s*\(', r'^\s*use\s+\w+', r'^\s*pub\s+fn'],
        'sql': [r'^\s*SELECT\s+', r'^\s*INSERT\s+INTO', r'^\s*UPDATE\s+', r'^\s*DELETE\s+FROM'],
        'json': [r'^\s*\{.*\}\s*$', r'^\s*\[.*\]\s*$'],
        'xml': [r'^\s*<\?xml', r'^\s*<\w+.*>'],
        'html': [r'^\s*<!DOCTYPE', r'^\s*<html', r'^\s*<div'],
        'css': [r'^\s*\.\w+\s*\{', r'^\s*#\w+\s*\{', r'^\s*@media'],
        'shell': [r'^\s*#!/bin/(bash|sh)', r'^\s*sudo\s+', r'^\s*apt(-get)?\s+'],
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._name = "ContentEnricher"
        self._priority = PluginPriority.HIGH
        self._version = "1.0.0"
        
        # Configuration
        self.enrich_urls = config.get('enrich_urls', True) if config else True
        self.enrich_code = config.get('enrich_code', True) if config else True
        self.enrich_text = config.get('enrich_text', True) if config else True
        self.fetch_timeout = config.get('fetch_timeout', 3.0) if config else 3.0
    
    async def initialize(self) -> bool:
        """Initialize the content enricher."""
        logger.info(f"{self.name} initialized")
        return True
    
    async def process_clip(self, clip: ClipItem, context: Dict[str, Any]) -> ClipItem:
        """
        Enrich clipboard content with metadata.
        
        Args:
            clip: Clipboard item to enrich
            context: Current context
        
        Returns:
            Enriched clip
        """
        content = clip.content
        content_type = self._detect_content_type(content)
        
        enrichment = {
            'content_type': content_type,
            'length': len(content),
        }
        
        # Type-specific enrichment
        if content_type == 'url' and self.enrich_urls:
            url_data = await self._enrich_url(content)
            enrichment['url'] = url_data
        
        elif content_type == 'code' and self.enrich_code:
            code_data = self._enrich_code(content)
            enrichment['code'] = code_data
        
        elif content_type == 'text' and self.enrich_text:
            text_data = self._enrich_text(content)
            enrichment['text'] = text_data
        
        elif content_type == 'email':
            email_data = self._enrich_email(content)
            enrichment['email'] = email_data
        
        # Add to clip metadata
        clip.metadata.enrichments['content'] = enrichment
        
        # Add content type tag
        if content_type:
            if content_type not in clip.metadata.tags:
                clip.metadata.tags.append(content_type)
        
        logger.debug(f"Enriched {content_type} content ({len(content)} chars)")
        
        return clip
    
    def _detect_content_type(self, content: str) -> str:
        """
        Detect content type.
        
        Args:
            content: Content to analyze
        
        Returns:
            Content type string
        """
        content_stripped = content.strip()
        
        # URL detection
        if self._is_url(content_stripped):
            return 'url'
        
        # Email detection
        if self._is_email(content_stripped):
            return 'email'
        
        # Code detection (multiple lines or code patterns)
        if '\n' in content_stripped or any(
            re.search(pattern, content_stripped, re.MULTILINE | re.IGNORECASE)
            for patterns in self.LANGUAGE_PATTERNS.values()
            for pattern in patterns
        ):
            return 'code'
        
        # JSON detection
        if content_stripped.startswith(('{', '[')) and content_stripped.endswith(('}', ']')):
            try:
                import json
                json.loads(content_stripped)
                return 'json'
            except:
                pass
        
        # Default to text
        return 'text'
    
    def _is_url(self, content: str) -> bool:
        """Check if content is a URL."""
        try:
            result = urlparse(content)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https', 'ftp']
        except:
            return False
    
    def _is_email(self, content: str) -> bool:
        """Check if content is an email address."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, content.strip()) is not None
    
    async def _enrich_url(self, url: str) -> Dict[str, Any]:
        """
        Enrich URL with metadata.
        Fetches title, description, and OpenGraph metadata.
        
        Args:
            url: URL to enrich
        
        Returns:
            URL metadata dictionary
        """
        data = {
            'url': url,
            'domain': urlparse(url).netloc,
            'scheme': urlparse(url).scheme,
        }
        
        # Try to fetch metadata
        try:
            import aiohttp
            import asyncio
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.fetch_timeout)) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Parse metadata
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Title
                        title_tag = soup.find('title')
                        if title_tag:
                            data['title'] = title_tag.text.strip()
                        
                        # Description
                        desc_tag = soup.find('meta', attrs={'name': 'description'})
                        if desc_tag and desc_tag.get('content'):
                            data['description'] = desc_tag.get('content').strip()
                        
                        # OpenGraph metadata
                        og_data = {}
                        for og_tag in soup.find_all('meta', property=re.compile(r'^og:')):
                            prop = og_tag.get('property', '').replace('og:', '')
                            content = og_tag.get('content', '')
                            if prop and content:
                                og_data[prop] = content
                        
                        if og_data:
                            data['opengraph'] = og_data
                        
                        logger.debug(f"Fetched URL metadata: {data.get('title', 'No title')}")
        
        except ImportError:
            logger.debug("aiohttp or beautifulsoup4 not available for URL enrichment")
        except Exception as e:
            logger.debug(f"Could not fetch URL metadata: {e}")
        
        return data
    
    def _enrich_code(self, content: str) -> Dict[str, Any]:
        """
        Enrich code with metadata.
        
        Args:
            content: Code content
        
        Returns:
            Code metadata dictionary
        """
        data = {
            'lines': content.count('\n') + 1,
            'chars': len(content),
        }
        
        # Detect language
        language = self._detect_language(content)
        if language:
            data['language'] = language
        
        # Extract functions/classes
        functions = self._extract_functions(content)
        if functions:
            data['functions'] = functions
        
        classes = self._extract_classes(content)
        if classes:
            data['classes'] = classes
        
        # Count comments
        comment_lines = len([line for line in content.split('\n') if line.strip().startswith(('#', '//', '/*', '*'))])
        data['comment_lines'] = comment_lines
        
        return data
    
    def _detect_language(self, content: str) -> Optional[str]:
        """Detect programming language."""
        scores = {}
        
        for language, patterns in self.LANGUAGE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                    score += 1
            if score > 0:
                scores[language] = score
        
        if scores:
            return max(scores, key=scores.get)
        return None
    
    def _extract_functions(self, content: str) -> list:
        """Extract function names from code."""
        functions = []
        
        # Python functions
        for match in re.finditer(r'^\s*def\s+(\w+)\s*\(', content, re.MULTILINE):
            functions.append(match.group(1))
        
        # JavaScript/TypeScript functions
        for match in re.finditer(r'^\s*(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\()', content, re.MULTILINE):
            func_name = match.group(1) or match.group(2)
            if func_name:
                functions.append(func_name)
        
        # Java/C++/C# methods
        for match in re.finditer(r'^\s*(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\(', content, re.MULTILINE):
            functions.append(match.group(1))
        
        return functions[:10]  # Limit to first 10
    
    def _extract_classes(self, content: str) -> list:
        """Extract class names from code."""
        classes = []
        
        # Python/Java/C++ classes
        for match in re.finditer(r'^\s*(?:public\s+)?class\s+(\w+)', content, re.MULTILINE):
            classes.append(match.group(1))
        
        return classes[:10]  # Limit to first 10
    
    def _enrich_text(self, content: str) -> Dict[str, Any]:
        """
        Enrich plain text with metadata.
        
        Args:
            content: Text content
        
        Returns:
            Text metadata dictionary
        """
        data = {
            'word_count': len(content.split()),
            'line_count': content.count('\n') + 1,
            'char_count': len(content),
        }
        
        # Extract emails
        emails = re.findall(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', content)
        if emails:
            data['emails'] = list(set(emails))[:5]  # Unique, limit to 5
        
        # Extract phone numbers
        phones = re.findall(r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', content)
        if phones:
            data['phones'] = list(set(phones))[:5]
        
        # Basic sentiment (simple heuristic)
        sentiment = self._analyze_sentiment(content)
        if sentiment:
            data['sentiment'] = sentiment
        
        return data
    
    def _analyze_sentiment(self, text: str) -> Optional[str]:
        """Simple sentiment analysis using keyword heuristics."""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'happy', 'best']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'worst', 'sad', 'angry', 'disappointed']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        elif positive_count > 0 or negative_count > 0:
            return 'neutral'
        
        return None
    
    def _enrich_email(self, content: str) -> Dict[str, Any]:
        """Enrich email address."""
        return {
            'email': content.strip(),
            'domain': content.split('@')[1] if '@' in content else None
        }
    
    async def shutdown(self):
        """Cleanup on shutdown."""
        logger.info(f"{self.name} shutdown")
