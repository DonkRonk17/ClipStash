#!/usr/bin/env python3
"""
Smart Templates Plugin - AI-Powered Templates
Priority: LOW

Detects and creates templates from clipboard patterns:
- Detects template-worthy patterns (emails, code, meeting notes, bug reports)
- Extracts templates from repeated structures
- Uses regex and pattern matching
- Variable placeholders ({{name}}, {{date}}, etc.)
- Template suggestion engine
"""

import re
import logging
from collections import defaultdict
from typing import Dict, Any, Optional, List

from clipstash_core import ClipStashPlugin, ClipItem, PluginPriority

logger = logging.getLogger(__name__)


class SmartTemplatesPlugin(ClipStashPlugin):
    """
    Learns and suggests templates from clipboard patterns.
    """
    
    # Template types and their patterns
    TEMPLATE_TYPES = {
        'email': {
            'patterns': [r'(?i)^(dear|hi|hello)', r'(?i)(regards|sincerely|thanks|best)\s*,'],
            'variables': ['recipient', 'sender', 'subject'],
        },
        'code': {
            'patterns': [r'^\s*(def|function|class)', r'^\s*(import|from|using|package)'],
            'variables': ['name', 'params', 'type'],
        },
        'meeting_notes': {
            'patterns': [r'(?i)(meeting|agenda|attendees|action items)', r'\d{1,2}:\d{2}\s*(am|pm)?'],
            'variables': ['date', 'attendees', 'topic'],
        },
        'bug_report': {
            'patterns': [r'(?i)(bug|issue|error|problem)', r'(?i)(steps to reproduce|expected|actual)'],
            'variables': ['title', 'description', 'steps'],
        },
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._name = "SmartTemplates"
        self._priority = PluginPriority.LOW
        self._version = "1.0.0"
        
        # Configuration
        self.min_pattern_count = config.get('min_pattern_count', 3) if config else 3
        self.similarity_threshold = config.get('similarity_threshold', 0.6) if config else 0.6
        self.auto_suggest = config.get('auto_suggest', True) if config else True
        
        # State
        self.templates: Dict[str, Dict[str, Any]] = {}
        self.pattern_counts: Dict[str, int] = defaultdict(int)
        self.clip_structures: List[Dict[str, Any]] = []
    
    async def initialize(self) -> bool:
        """Initialize smart templates."""
        logger.info(f"{self.name} initialized")
        return True
    
    async def process_clip(self, clip: ClipItem, context: Dict[str, Any]) -> ClipItem:
        """
        Detect template patterns and suggest templates.
        
        Args:
            clip: Clipboard item
            context: Current context
        
        Returns:
            Clip with template suggestions
        """
        content = clip.content
        
        # Detect template type
        template_type = self._detect_template_type(content)
        
        if template_type:
            # Extract structure
            structure = self._extract_structure(content, template_type)
            
            # Store structure for pattern learning
            self.clip_structures.append({
                'type': template_type,
                'structure': structure,
                'content': content,
                'hash': clip.hash
            })
            
            # Check for similar patterns
            similar_structures = self._find_similar_structures(structure, template_type)
            
            if len(similar_structures) >= self.min_pattern_count:
                # Create template
                template = self._create_template(similar_structures, template_type)
                
                if template:
                    template_id = f"{template_type}_{len(self.templates)}"
                    self.templates[template_id] = template
                    
                    clip.metadata.enrichments['template'] = {
                        'type': template_type,
                        'template_id': template_id,
                        'suggestion': template.get('content'),
                        'variables': template.get('variables', [])
                    }
                    
                    logger.info(f"Created template: {template_id}")
            
            # Suggest existing templates
            elif self.auto_suggest:
                suggested = self._suggest_template(content, template_type)
                if suggested:
                    clip.metadata.enrichments['template_suggestion'] = suggested
        
        return clip
    
    def _detect_template_type(self, content: str) -> Optional[str]:
        """
        Detect template type from content.
        
        Args:
            content: Content to analyze
        
        Returns:
            Template type or None
        """
        scores = {}
        
        for template_type, config in self.TEMPLATE_TYPES.items():
            score = 0
            for pattern in config['patterns']:
                if re.search(pattern, content, re.MULTILINE):
                    score += 1
            
            if score > 0:
                scores[template_type] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return None
    
    def _extract_structure(self, content: str, template_type: str) -> Dict[str, Any]:
        """
        Extract structural elements from content.
        
        Args:
            content: Content to analyze
            template_type: Type of template
        
        Returns:
            Structure dictionary
        """
        structure = {
            'type': template_type,
            'lines': content.count('\n') + 1,
            'length': len(content),
        }
        
        if template_type == 'email':
            structure.update(self._extract_email_structure(content))
        elif template_type == 'code':
            structure.update(self._extract_code_structure(content))
        elif template_type == 'meeting_notes':
            structure.update(self._extract_meeting_structure(content))
        elif template_type == 'bug_report':
            structure.update(self._extract_bug_report_structure(content))
        
        return structure
    
    def _extract_email_structure(self, content: str) -> Dict[str, Any]:
        """Extract email structure."""
        structure = {}
        
        # Greeting
        greeting_match = re.search(r'(?i)^(dear|hi|hello)\s+(\w+)', content.strip())
        if greeting_match:
            structure['greeting_type'] = greeting_match.group(1).lower()
            structure['has_recipient'] = True
        
        # Closing
        closing_match = re.search(r'(?i)(regards|sincerely|thanks|best)\s*,', content)
        if closing_match:
            structure['closing_type'] = closing_match.group(1).lower()
        
        # Paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        structure['paragraph_count'] = len(paragraphs)
        
        return structure
    
    def _extract_code_structure(self, content: str) -> Dict[str, Any]:
        """Extract code structure."""
        structure = {}
        
        # Function/method count
        functions = len(re.findall(r'^\s*(def|function)\s+\w+', content, re.MULTILINE))
        structure['function_count'] = functions
        
        # Class count
        classes = len(re.findall(r'^\s*class\s+\w+', content, re.MULTILINE))
        structure['class_count'] = classes
        
        # Import count
        imports = len(re.findall(r'^\s*(import|from|using|package)', content, re.MULTILINE))
        structure['import_count'] = imports
        
        return structure
    
    def _extract_meeting_structure(self, content: str) -> Dict[str, Any]:
        """Extract meeting notes structure."""
        structure = {}
        
        # Has date
        structure['has_date'] = bool(re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', content))
        
        # Has time
        structure['has_time'] = bool(re.search(r'\d{1,2}:\d{2}', content))
        
        # Has attendees section
        structure['has_attendees'] = bool(re.search(r'(?i)attendees?:', content))
        
        # Has action items
        structure['has_action_items'] = bool(re.search(r'(?i)action items?:', content))
        
        # Bullet points
        bullets = len(re.findall(r'^\s*[-*•]\s+', content, re.MULTILINE))
        structure['bullet_count'] = bullets
        
        return structure
    
    def _extract_bug_report_structure(self, content: str) -> Dict[str, Any]:
        """Extract bug report structure."""
        structure = {}
        
        # Has title/summary
        structure['has_title'] = bool(re.search(r'(?i)(title|summary):', content))
        
        # Has steps to reproduce
        structure['has_steps'] = bool(re.search(r'(?i)steps? to reproduce', content))
        
        # Has expected/actual
        structure['has_expected'] = bool(re.search(r'(?i)expected', content))
        structure['has_actual'] = bool(re.search(r'(?i)actual', content))
        
        # Has environment info
        structure['has_environment'] = bool(re.search(r'(?i)environment|version|browser|os', content))
        
        return structure
    
    def _find_similar_structures(self, structure: Dict[str, Any], template_type: str) -> List[Dict[str, Any]]:
        """Find similar structures in history."""
        similar = []
        
        for stored in self.clip_structures:
            if stored['type'] != template_type:
                continue
            
            # Calculate similarity
            similarity = self._calculate_structure_similarity(structure, stored['structure'])
            
            if similarity >= self.similarity_threshold:
                similar.append(stored)
        
        return similar
    
    def _calculate_structure_similarity(self, struct1: Dict[str, Any], struct2: Dict[str, Any]) -> float:
        """Calculate similarity between structures."""
        matching_keys = 0
        total_keys = 0
        
        all_keys = set(struct1.keys()) | set(struct2.keys())
        
        for key in all_keys:
            if key in ['type', 'lines', 'length']:
                continue
            
            total_keys += 1
            
            val1 = struct1.get(key)
            val2 = struct2.get(key)
            
            if val1 == val2:
                matching_keys += 1
            elif isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # Numeric similarity
                if val1 and val2:
                    diff = abs(val1 - val2) / max(val1, val2)
                    if diff < 0.5:
                        matching_keys += 0.5
        
        return matching_keys / total_keys if total_keys > 0 else 0.0
    
    def _create_template(self, similar_structures: List[Dict[str, Any]], template_type: str) -> Optional[Dict[str, Any]]:
        """Create template from similar structures."""
        if not similar_structures:
            return None
        
        # Use first structure as base
        base_content = similar_structures[0]['content']
        
        # Extract common parts and create placeholders
        template_content = self._extract_common_template(base_content, template_type)
        
        # Get variables
        variables = self.TEMPLATE_TYPES[template_type]['variables']
        
        return {
            'type': template_type,
            'content': template_content,
            'variables': variables,
            'usage_count': len(similar_structures),
            'created': len(self.templates)
        }
    
    def _extract_common_template(self, content: str, template_type: str) -> str:
        """Extract template with placeholders from content."""
        template = content
        
        # Replace common variable patterns with placeholders
        if template_type == 'email':
            # Replace names after greeting
            template = re.sub(r'(?i)(dear|hi|hello)\s+\w+', r'\1 {{recipient}}', template)
            # Replace signature
            template = re.sub(r'(?i)(regards|sincerely|thanks|best)\s*,\s*\w+', r'\1,\n{{sender}}', template)
        
        elif template_type == 'code':
            # Replace function names
            template = re.sub(r'(def|function)\s+\w+', r'\1 {{function_name}}', template)
            # Replace class names
            template = re.sub(r'class\s+\w+', r'class {{class_name}}', template)
        
        elif template_type == 'meeting_notes':
            # Replace dates
            template = re.sub(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', '{{date}}', template)
            # Replace times
            template = re.sub(r'\d{1,2}:\d{2}\s*(am|pm)?', '{{time}}', template)
        
        elif template_type == 'bug_report':
            # Keep structure, add placeholders in common places
            template = re.sub(r'(?i)(title|summary):\s*.+', r'\1: {{title}}', template)
        
        return template
    
    def _suggest_template(self, content: str, template_type: str) -> Optional[Dict[str, Any]]:
        """Suggest existing template for content."""
        for template_id, template in self.templates.items():
            if template['type'] == template_type:
                return {
                    'template_id': template_id,
                    'type': template_type,
                    'content': template['content'],
                    'variables': template['variables']
                }
        
        return None
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template by ID."""
        return self.templates.get(template_id)
    
    def list_templates(self, template_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all templates, optionally filtered by type."""
        templates = []
        
        for template_id, template in self.templates.items():
            if template_type is None or template['type'] == template_type:
                templates.append({
                    'id': template_id,
                    **template
                })
        
        return templates
    
    async def shutdown(self):
        """Cleanup on shutdown."""
        logger.info(f"{self.name} shutdown - created {len(self.templates)} templates")
