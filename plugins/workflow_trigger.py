#!/usr/bin/env python3
"""
Workflow Trigger Plugin - Workflow Automation Trigger
Priority: MEDIUM

Automated workflow triggers based on clipboard content:
- Pattern-based triggers with rule engine
- Built-in triggers:
  * Error messages → Stack Overflow search
  * GitHub URL → fetch repository details
  * Address → geocode and weather
  * AWS resource → describe resource
  * Email → draft reply
- Extensible trigger system
"""

import re
import logging
from typing import Dict, Any, Optional, List, Callable

from clipstash_core import ClipStashPlugin, ClipItem, PluginPriority

logger = logging.getLogger(__name__)


class WorkflowTriggerPlugin(ClipStashPlugin):
    """
    Triggers automated workflows based on clipboard content patterns.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._name = "WorkflowTrigger"
        self._priority = PluginPriority.MEDIUM
        self._version = "1.0.0"
        
        # Configuration
        self.enabled_triggers = config.get('enabled_triggers', [
            'error_search', 'github_info', 'address_info', 'aws_resource', 'email_draft'
        ]) if config else ['error_search', 'github_info', 'address_info', 'aws_resource', 'email_draft']
        
        # Trigger registry
        self.triggers: Dict[str, Callable] = {}
        self._register_builtin_triggers()
    
    def _register_builtin_triggers(self):
        """Register built-in workflow triggers."""
        self.triggers['error_search'] = self._trigger_error_search
        self.triggers['github_info'] = self._trigger_github_info
        self.triggers['address_info'] = self._trigger_address_info
        self.triggers['aws_resource'] = self._trigger_aws_resource
        self.triggers['email_draft'] = self._trigger_email_draft
    
    async def initialize(self) -> bool:
        """Initialize the workflow trigger."""
        logger.info(f"{self.name} initialized with {len(self.enabled_triggers)} triggers")
        return True
    
    async def process_clip(self, clip: ClipItem, context: Dict[str, Any]) -> ClipItem:
        """
        Check for workflow triggers and execute.
        
        Args:
            clip: Clipboard item
            context: Current context
        
        Returns:
            Clip with workflow results
        """
        workflows_triggered = []
        
        # Check each enabled trigger
        for trigger_name in self.enabled_triggers:
            trigger_func = self.triggers.get(trigger_name)
            if trigger_func:
                result = await trigger_func(clip, context)
                if result:
                    workflows_triggered.append({
                        'trigger': trigger_name,
                        'result': result
                    })
                    logger.info(f"Workflow triggered: {trigger_name}")
        
        if workflows_triggered:
            clip.metadata.enrichments['workflows'] = {
                'triggered': workflows_triggered,
                'count': len(workflows_triggered)
            }
            clip.metadata.tags.append('workflow')
        
        return clip
    
    async def _trigger_error_search(self, clip: ClipItem, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Detect error messages and search Stack Overflow.
        
        Args:
            clip: Clipboard item
            context: Current context
        
        Returns:
            Search results or None
        """
        content = clip.content
        
        # Detect error patterns
        error_patterns = [
            r'(?i)(error|exception|traceback|stack trace)',
            r'(?i)(failed|failure|error code)',
            r'(?i)(syntax error|type error|value error|runtime error)',
            r'line \d+',
            r'at [\w\.]+\(\)',
        ]
        
        error_score = sum(1 for pattern in error_patterns if re.search(pattern, content))
        
        if error_score >= 2:  # At least 2 error indicators
            # Extract error message
            error_lines = [line for line in content.split('\n') if 'error' in line.lower() or 'exception' in line.lower()]
            query = error_lines[0] if error_lines else content[:100]
            
            # Generate Stack Overflow search URL
            import urllib.parse
            search_url = f"https://stackoverflow.com/search?q={urllib.parse.quote(query)}"
            
            return {
                'type': 'error_search',
                'query': query,
                'search_url': search_url,
                'description': 'Detected error message, search on Stack Overflow'
            }
        
        return None
    
    async def _trigger_github_info(self, clip: ClipItem, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Detect GitHub URLs and fetch repository info.
        
        Args:
            clip: Clipboard item
            context: Current context
        
        Returns:
            Repository info or None
        """
        content = clip.content.strip()
        
        # Match GitHub repository URL
        github_pattern = r'https?://github\.com/([^/]+)/([^/\s]+)'
        match = re.search(github_pattern, content)
        
        if match:
            owner, repo = match.groups()
            repo = repo.rstrip('/')
            
            # Fetch repository details
            try:
                import aiohttp
                
                api_url = f"https://api.github.com/repos/{owner}/{repo}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=3.0)) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            return {
                                'type': 'github_info',
                                'owner': owner,
                                'repo': repo,
                                'description': data.get('description'),
                                'stars': data.get('stargazers_count'),
                                'language': data.get('language'),
                                'url': data.get('html_url'),
                                'updated': data.get('updated_at'),
                            }
            except ImportError:
                logger.debug("aiohttp not available for GitHub API")
            except Exception as e:
                logger.debug(f"Error fetching GitHub info: {e}")
            
            # Return basic info even if API fails
            return {
                'type': 'github_info',
                'owner': owner,
                'repo': repo,
                'url': f"https://github.com/{owner}/{repo}"
            }
        
        return None
    
    async def _trigger_address_info(self, clip: ClipItem, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Detect addresses and provide geocoding/weather.
        
        Args:
            clip: Clipboard item
            context: Current context
        
        Returns:
            Address info or None
        """
        content = clip.content
        
        # Simple address detection (US addresses)
        address_pattern = r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Way),?\s+[\w\s]+,?\s+[A-Z]{2}\s+\d{5}'
        
        match = re.search(address_pattern, content, re.IGNORECASE)
        
        if match:
            address = match.group(0)
            
            return {
                'type': 'address_info',
                'address': address,
                'description': 'Detected address, can geocode or get weather',
                'actions': ['geocode', 'weather', 'map']
            }
        
        return None
    
    async def _trigger_aws_resource(self, clip: ClipItem, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Detect AWS resource identifiers.
        
        Args:
            clip: Clipboard item
            context: Current context
        
        Returns:
            AWS resource info or None
        """
        content = clip.content
        
        # AWS resource patterns
        aws_patterns = {
            'instance': r'i-[a-f0-9]{8,17}',
            'security_group': r'sg-[a-f0-9]{8,17}',
            'vpc': r'vpc-[a-f0-9]{8,17}',
            'subnet': r'subnet-[a-f0-9]{8,17}',
            's3_bucket': r's3://[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]',
            'lambda': r'arn:aws:lambda:[a-z0-9-]+:\d+:function:[a-zA-Z0-9-_]+',
            'arn': r'arn:aws:[a-z0-9-]+:[a-z0-9-]*:\d*:[a-zA-Z0-9-_/]+',
        }
        
        for resource_type, pattern in aws_patterns.items():
            match = re.search(pattern, content)
            if match:
                resource_id = match.group(0)
                
                return {
                    'type': 'aws_resource',
                    'resource_type': resource_type,
                    'resource_id': resource_id,
                    'description': f'Detected AWS {resource_type}',
                    'actions': ['describe', 'console_link']
                }
        
        return None
    
    async def _trigger_email_draft(self, clip: ClipItem, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Detect email content and draft reply.
        
        Args:
            clip: Clipboard item
            context: Current context
        
        Returns:
            Draft info or None
        """
        content = clip.content
        
        # Detect email structure
        has_greeting = bool(re.search(r'(?i)^(hi|hello|dear|hey)\s+\w+', content.strip()))
        has_signature = bool(re.search(r'(?i)(best regards|sincerely|thanks|regards|cheers)\s*,?\s*$', content.strip(), re.MULTILINE))
        has_email_header = bool(re.search(r'(?i)^(from|to|subject|date):', content, re.MULTILINE))
        
        if (has_greeting and has_signature) or has_email_header:
            # Extract key elements
            subject_match = re.search(r'(?i)^subject:\s*(.+)$', content, re.MULTILINE)
            subject = subject_match.group(1) if subject_match else None
            
            return {
                'type': 'email_draft',
                'detected_subject': subject,
                'description': 'Detected email content',
                'actions': ['draft_reply', 'summarize']
            }
        
        return None
    
    async def shutdown(self):
        """Cleanup on shutdown."""
        logger.info(f"{self.name} shutdown")
