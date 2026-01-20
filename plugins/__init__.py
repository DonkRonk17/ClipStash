"""
ClipStash Plugin Collection
AI-powered plugins for enhanced clipboard management
"""

from typing import List, Type
from clipstash_core import ClipStashPlugin

# Import all plugins
try:
    from .security_monitor import SecurityMonitorPlugin
except ImportError:
    SecurityMonitorPlugin = None

try:
    from .content_enricher import ContentEnricherPlugin
except ImportError:
    ContentEnricherPlugin = None

try:
    from .paste_predictor import PastePredictorPlugin
except ImportError:
    PastePredictorPlugin = None

try:
    from .research_assistant import ResearchAssistantPlugin
except ImportError:
    ResearchAssistantPlugin = None

try:
    from .sync_agent import SyncAgentPlugin
except ImportError:
    SyncAgentPlugin = None

try:
    from .workflow_trigger import WorkflowTriggerPlugin
except ImportError:
    WorkflowTriggerPlugin = None

try:
    from .knowledge_graph import KnowledgeGraphPlugin
except ImportError:
    KnowledgeGraphPlugin = None

try:
    from .collaborative import CollaborativeClipboardPlugin
except ImportError:
    CollaborativeClipboardPlugin = None

try:
    from .smart_templates import SmartTemplatesPlugin
except ImportError:
    SmartTemplatesPlugin = None

try:
    from .api_wrapper import APIWrapperPlugin
except ImportError:
    APIWrapperPlugin = None


def get_available_plugins() -> List[Type[ClipStashPlugin]]:
    """Get list of all available plugin classes."""
    plugins = []
    
    if SecurityMonitorPlugin:
        plugins.append(SecurityMonitorPlugin)
    if ContentEnricherPlugin:
        plugins.append(ContentEnricherPlugin)
    if PastePredictorPlugin:
        plugins.append(PastePredictorPlugin)
    if ResearchAssistantPlugin:
        plugins.append(ResearchAssistantPlugin)
    if SyncAgentPlugin:
        plugins.append(SyncAgentPlugin)
    if WorkflowTriggerPlugin:
        plugins.append(WorkflowTriggerPlugin)
    if KnowledgeGraphPlugin:
        plugins.append(KnowledgeGraphPlugin)
    if CollaborativeClipboardPlugin:
        plugins.append(CollaborativeClipboardPlugin)
    if SmartTemplatesPlugin:
        plugins.append(SmartTemplatesPlugin)
    if APIWrapperPlugin:
        plugins.append(APIWrapperPlugin)
    
    return plugins


__all__ = [
    'SecurityMonitorPlugin',
    'ContentEnricherPlugin',
    'PastePredictorPlugin',
    'ResearchAssistantPlugin',
    'SyncAgentPlugin',
    'WorkflowTriggerPlugin',
    'KnowledgeGraphPlugin',
    'CollaborativeClipboardPlugin',
    'SmartTemplatesPlugin',
    'APIWrapperPlugin',
    'get_available_plugins'
]
