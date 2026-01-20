#!/usr/bin/env python3
"""
API Wrapper Plugin - Autonomous API Wrapper
Priority: LOW

Detects and executes API-executable content:
- JSON validation and pretty-printing
- URL → HTTP request execution
- SQL query execution (sandboxed)
- File path → read contents
- Coordinates → reverse geocode
- GraphQL execution
- Sandboxing and rate limiting
"""

import json
import logging
import re
from typing import Dict, Any, Optional

from clipstash_core import ClipStashPlugin, ClipItem, PluginPriority

logger = logging.getLogger(__name__)


class APIWrapperPlugin(ClipStashPlugin):
    """
    Automatically executes API-related clipboard content.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._name = "APIWrapper"
        self._priority = PluginPriority.LOW
        self._version = "1.0.0"
        
        # Configuration
        self.auto_execute = config.get('auto_execute', False) if config else False
        self.safe_mode = config.get('safe_mode', True) if config else True
        self.max_requests_per_minute = config.get('max_requests_per_minute', 10) if config else 10
        self.allowed_domains = config.get('allowed_domains', ['*']) if config else ['*']
        
        # State
        self.request_count = 0
        self.last_reset_time = None
    
    async def initialize(self) -> bool:
        """Initialize API wrapper."""
        from datetime import datetime
        self.last_reset_time = datetime.now()
        logger.info(f"{self.name} initialized (auto_execute={self.auto_execute})")
        return True
    
    async def process_clip(self, clip: ClipItem, context: Dict[str, Any]) -> ClipItem:
        """
        Detect and optionally execute API content.
        
        Args:
            clip: Clipboard item
            context: Current context
        
        Returns:
            Clip with API execution results
        """
        content = clip.content.strip()
        
        # Check rate limit
        if not self._check_rate_limit():
            logger.warning("Rate limit exceeded")
            return clip
        
        # Detect content type and execute
        executed = False
        
        # JSON validation/pretty-print
        if self._is_json(content):
            result = await self._handle_json(content)
            if result:
                clip.metadata.enrichments['api'] = result
                executed = True
        
        # HTTP request
        elif self._is_url(content):
            result = await self._handle_http_request(content)
            if result:
                clip.metadata.enrichments['api'] = result
                executed = True
        
        # SQL query
        elif self._is_sql(content):
            result = await self._handle_sql(content)
            if result:
                clip.metadata.enrichments['api'] = result
                executed = True
        
        # File path
        elif self._is_file_path(content):
            result = await self._handle_file_path(content)
            if result:
                clip.metadata.enrichments['api'] = result
                executed = True
        
        # Coordinates
        elif self._is_coordinates(content):
            result = await self._handle_coordinates(content)
            if result:
                clip.metadata.enrichments['api'] = result
                executed = True
        
        # GraphQL
        elif self._is_graphql(content):
            result = await self._handle_graphql(content)
            if result:
                clip.metadata.enrichments['api'] = result
                executed = True
        
        if executed:
            self.request_count += 1
            clip.metadata.tags.append('api-executed')
        
        return clip
    
    def _check_rate_limit(self) -> bool:
        """Check if within rate limit."""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        # Reset counter every minute
        if (now - self.last_reset_time) > timedelta(minutes=1):
            self.request_count = 0
            self.last_reset_time = now
        
        return self.request_count < self.max_requests_per_minute
    
    def _is_json(self, content: str) -> bool:
        """Check if content is JSON."""
        try:
            json.loads(content)
            return True
        except:
            return False
    
    async def _handle_json(self, content: str) -> Optional[Dict[str, Any]]:
        """Validate and pretty-print JSON."""
        try:
            data = json.loads(content)
            pretty = json.dumps(data, indent=2, sort_keys=True)
            
            return {
                'type': 'json',
                'valid': True,
                'pretty_printed': pretty,
                'keys': list(data.keys()) if isinstance(data, dict) else None,
                'length': len(data) if isinstance(data, (dict, list)) else None
            }
        except Exception as e:
            return {
                'type': 'json',
                'valid': False,
                'error': str(e)
            }
    
    def _is_url(self, content: str) -> bool:
        """Check if content is a URL."""
        from urllib.parse import urlparse
        try:
            result = urlparse(content)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except:
            return False
    
    async def _handle_http_request(self, url: str) -> Optional[Dict[str, Any]]:
        """Execute HTTP request."""
        if not self.auto_execute:
            return {
                'type': 'http_request',
                'url': url,
                'executed': False,
                'message': 'Auto-execute disabled. Set auto_execute=True to execute.'
            }
        
        # Check domain whitelist
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        if '*' not in self.allowed_domains and domain not in self.allowed_domains:
            return {
                'type': 'http_request',
                'url': url,
                'executed': False,
                'message': f'Domain {domain} not in allowed list'
            }
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5.0)) as response:
                    status = response.status
                    headers = dict(response.headers)
                    
                    # Get content based on type
                    content_type = headers.get('Content-Type', '')
                    
                    if 'application/json' in content_type:
                        content = await response.json()
                    else:
                        content = await response.text()
                        content = content[:500]  # Limit size
                    
                    return {
                        'type': 'http_request',
                        'url': url,
                        'executed': True,
                        'status': status,
                        'content_type': content_type,
                        'response': content
                    }
        
        except ImportError:
            logger.debug("aiohttp not available")
            return None
        except Exception as e:
            return {
                'type': 'http_request',
                'url': url,
                'executed': False,
                'error': str(e)
            }
    
    def _is_sql(self, content: str) -> bool:
        """Check if content is SQL query."""
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
        content_upper = content.upper()
        return any(keyword in content_upper for keyword in sql_keywords)
    
    async def _handle_sql(self, sql: str) -> Optional[Dict[str, Any]]:
        """Handle SQL query (sandboxed)."""
        # Only allow SELECT in safe mode
        if self.safe_mode and not sql.strip().upper().startswith('SELECT'):
            return {
                'type': 'sql',
                'executed': False,
                'message': 'Only SELECT queries allowed in safe mode'
            }
        
        return {
            'type': 'sql',
            'query': sql,
            'executed': False,
            'message': 'SQL execution not implemented (requires database connection)'
        }
    
    def _is_file_path(self, content: str) -> bool:
        """Check if content is a file path."""
        # Simple heuristic: contains / or \ and file extension
        return (('/' in content or '\\' in content) and 
                re.search(r'\.\w{2,4}$', content))
    
    async def _handle_file_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Read file contents."""
        if not self.auto_execute:
            return {
                'type': 'file_read',
                'path': path,
                'executed': False,
                'message': 'Auto-execute disabled'
            }
        
        try:
            from pathlib import Path
            
            file_path = Path(path.strip())
            
            if not file_path.exists():
                return {
                    'type': 'file_read',
                    'path': path,
                    'executed': False,
                    'error': 'File not found'
                }
            
            # Safety check: don't read very large files
            if file_path.stat().st_size > 1024 * 100:  # 100KB
                return {
                    'type': 'file_read',
                    'path': path,
                    'executed': False,
                    'error': 'File too large (>100KB)'
                }
            
            # Read content
            content = file_path.read_text(encoding='utf-8')
            
            return {
                'type': 'file_read',
                'path': path,
                'executed': True,
                'size': file_path.stat().st_size,
                'content': content[:500]  # Limit preview
            }
        
        except Exception as e:
            return {
                'type': 'file_read',
                'path': path,
                'executed': False,
                'error': str(e)
            }
    
    def _is_coordinates(self, content: str) -> bool:
        """Check if content is coordinates."""
        # Matches patterns like: 40.7128, -74.0060
        pattern = r'^-?\d+\.?\d*,\s*-?\d+\.?\d*$'
        return re.match(pattern, content.strip()) is not None
    
    async def _handle_coordinates(self, coords: str) -> Optional[Dict[str, Any]]:
        """Reverse geocode coordinates."""
        try:
            lat, lon = [float(x.strip()) for x in coords.split(',')]
            
            # Basic validation
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                return {
                    'type': 'coordinates',
                    'executed': False,
                    'error': 'Invalid coordinates'
                }
            
            return {
                'type': 'coordinates',
                'latitude': lat,
                'longitude': lon,
                'executed': False,
                'message': 'Reverse geocoding not implemented (requires geocoding API)'
            }
        
        except Exception as e:
            return {
                'type': 'coordinates',
                'executed': False,
                'error': str(e)
            }
    
    def _is_graphql(self, content: str) -> bool:
        """Check if content is GraphQL query."""
        graphql_keywords = ['query', 'mutation', 'subscription']
        content_lower = content.lower()
        return any(f'{keyword} ' in content_lower or f'{keyword}' + '{' in content_lower 
                   for keyword in graphql_keywords)
    
    async def _handle_graphql(self, query: str) -> Optional[Dict[str, Any]]:
        """Handle GraphQL query."""
        return {
            'type': 'graphql',
            'query': query,
            'executed': False,
            'message': 'GraphQL execution not implemented (requires endpoint configuration)'
        }
    
    async def shutdown(self):
        """Cleanup on shutdown."""
        logger.info(f"{self.name} shutdown - executed {self.request_count} requests")
