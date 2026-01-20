#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                      ClipStash Core Plugin Architecture                        ║
║                         Enhanced Plugin System v2.0                            ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Core plugin architecture for ClipStash including:
- ClipMetadata: Enriched metadata for clips
- Enhanced ClipItem: Backward-compatible clip with metadata
- PluginPriority: Priority levels for plugin execution
- ClipStashPlugin: Abstract base class for plugins
- PluginManager: Plugin lifecycle and execution management
- ContextProvider: System context detection

Author: Logan Smith / Team Brain (Metaphy LLC)
License: MIT
"""

import asyncio
import hashlib
import logging
import platform
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# CLIP METADATA
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ClipMetadata:
    """Metadata for enhanced clipboard items."""
    
    enrichments: Dict[str, Any] = field(default_factory=dict)
    predictions: Dict[str, Any] = field(default_factory=dict)
    security_flags: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ClipMetadata':
        """Create from dictionary."""
        return cls(
            enrichments=data.get('enrichments', {}),
            predictions=data.get('predictions', {}),
            security_flags=data.get('security_flags', []),
            relationships=data.get('relationships', []),
            tags=data.get('tags', []),
            confidence_scores=data.get('confidence_scores', {})
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCED CLIP ITEM
# ═══════════════════════════════════════════════════════════════════════════════

class ClipItem:
    """
    Enhanced clipboard item with metadata support.
    Maintains backward compatibility with original ClipItem format.
    """
    
    def __init__(self, content: str, timestamp: str = None, pinned: bool = False):
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()
        self.pinned = pinned
        self.hash = hashlib.md5(content.encode()).hexdigest()[:8]
        self.metadata = ClipMetadata()
        self._processed_by: List[str] = []
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.
        Includes metadata for enhanced version, but maintains backward compatibility.
        """
        base_dict = {
            "content": self.content,
            "timestamp": self.timestamp,
            "pinned": self.pinned,
            "hash": self.hash
        }
        
        # Add enhanced fields only if they contain data
        if (self.metadata.enrichments or self.metadata.predictions or 
            self.metadata.security_flags or self.metadata.relationships or 
            self.metadata.tags or self.metadata.confidence_scores):
            base_dict["metadata"] = self.metadata.to_dict()
        
        if self._processed_by:
            base_dict["processed_by"] = self._processed_by
        
        return base_dict
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ClipItem':
        """
        Create from dictionary.
        Supports both original and enhanced formats.
        """
        item = cls(
            content=data["content"],
            timestamp=data.get("timestamp"),
            pinned=data.get("pinned", False)
        )
        item.hash = data.get("hash", item.hash)
        
        # Load enhanced fields if present
        if "metadata" in data:
            item.metadata = ClipMetadata.from_dict(data["metadata"])
        
        if "processed_by" in data:
            item._processed_by = data["processed_by"]
        
        return item
    
    def preview(self, max_len: int = 80) -> str:
        """Get a preview of the content."""
        text = self.content.replace('\n', ' ').replace('\r', '').strip()
        if len(text) > max_len:
            return text[:max_len] + "..."
        return text
    
    def formatted_time(self) -> str:
        """Get human-readable timestamp."""
        try:
            dt = datetime.fromisoformat(self.timestamp)
            now = datetime.now()
            diff = now - dt
            
            if diff.days == 0:
                if diff.seconds < 60:
                    return "Just now"
                elif diff.seconds < 3600:
                    mins = diff.seconds // 60
                    return f"{mins}m ago"
                else:
                    hours = diff.seconds // 3600
                    return f"{hours}h ago"
            elif diff.days == 1:
                return "Yesterday"
            elif diff.days < 7:
                return f"{diff.days}d ago"
            else:
                return dt.strftime("%b %d")
        except:
            return ""


# ═══════════════════════════════════════════════════════════════════════════════
# PLUGIN PRIORITY
# ═══════════════════════════════════════════════════════════════════════════════

class PluginPriority(IntEnum):
    """Plugin execution priority levels."""
    CRITICAL = 1  # Security, validation - runs FIRST
    HIGH = 2      # Enrichment, predictions
    MEDIUM = 3    # Analytics, logging
    LOW = 4       # Background tasks


# ═══════════════════════════════════════════════════════════════════════════════
# PLUGIN BASE CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class ClipStashPlugin(ABC):
    """
    Abstract base class for ClipStash plugins.
    All plugins must inherit from this class and implement required methods.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize plugin with optional configuration.
        
        Args:
            config: Plugin-specific configuration dictionary
        """
        self.config = config or {}
        self._name: Optional[str] = None
        self._version: str = "1.0.0"
        self._priority: PluginPriority = PluginPriority.MEDIUM
        self._enabled: bool = True
        self._initialized: bool = False
    
    @property
    def name(self) -> str:
        """Plugin name."""
        if self._name is None:
            return self.__class__.__name__
        return self._name
    
    @property
    def version(self) -> str:
        """Plugin version."""
        return self._version
    
    @property
    def priority(self) -> PluginPriority:
        """Plugin priority level."""
        return self._priority
    
    @property
    def enabled(self) -> bool:
        """Whether plugin is enabled."""
        return self._enabled
    
    def enable(self):
        """Enable the plugin."""
        self._enabled = True
    
    def disable(self):
        """Disable the plugin."""
        self._enabled = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the plugin.
        Called once when plugin is loaded.
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def process_clip(self, clip: ClipItem, context: Dict[str, Any]) -> ClipItem:
        """
        Process a clipboard item.
        
        Args:
            clip: The clipboard item to process
            context: Current context (active app, time, etc.)
        
        Returns:
            The processed clip item (may be modified)
        """
        pass
    
    async def on_paste(self, clip: ClipItem, context: Dict[str, Any]) -> Optional[ClipItem]:
        """
        Called when user is about to paste a clip.
        Can modify or block the paste.
        
        Args:
            clip: The clip being pasted
            context: Current context
        
        Returns:
            Modified clip, original clip, or None to block paste
        """
        return clip
    
    async def on_search(self, query: str, results: List[ClipItem]) -> List[ClipItem]:
        """
        Called during search operations.
        Can modify search results or rankings.
        
        Args:
            query: Search query string
            results: Current search results
        
        Returns:
            Modified search results
        """
        return results
    
    async def shutdown(self):
        """
        Cleanup when plugin is unloaded.
        Called once when application exits or plugin is disabled.
        """
        pass
    
    def get_settings_ui(self) -> Optional[Any]:
        """
        Get Qt widget for plugin settings.
        Override to provide custom configuration UI.
        
        Returns:
            QWidget for settings or None
        """
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# PLUGIN MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class PluginManager:
    """
    Manages plugin lifecycle and execution.
    Handles loading, unloading, and coordinating plugin execution.
    """
    
    def __init__(self, timeout: float = 5.0):
        """
        Initialize plugin manager.
        
        Args:
            timeout: Maximum time (seconds) for plugin processing
        """
        self.plugins: List[ClipStashPlugin] = []
        self.timeout = timeout
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        logger.info("PluginManager initialized")
    
    def load_plugin(self, plugin: ClipStashPlugin) -> bool:
        """
        Load and initialize a plugin.
        
        Args:
            plugin: Plugin instance to load
        
        Returns:
            True if loaded successfully
        """
        try:
            # Initialize plugin
            if self._loop is None:
                # Create event loop if needed
                try:
                    self._loop = asyncio.get_event_loop()
                except RuntimeError:
                    self._loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self._loop)
            
            # Run initialization
            success = self._loop.run_until_complete(plugin.initialize())
            
            if success:
                plugin._initialized = True
                self.plugins.append(plugin)
                self._sort_plugins()
                logger.info(f"Plugin loaded: {plugin.name} v{plugin.version}")
                return True
            else:
                logger.error(f"Plugin initialization failed: {plugin.name}")
                return False
        except Exception as e:
            logger.error(f"Error loading plugin {plugin.name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin by name.
        
        Args:
            plugin_name: Name of plugin to unload
        
        Returns:
            True if unloaded successfully
        """
        try:
            plugin = next((p for p in self.plugins if p.name == plugin_name), None)
            if plugin is None:
                logger.warning(f"Plugin not found: {plugin_name}")
                return False
            
            # Shutdown plugin
            if self._loop:
                self._loop.run_until_complete(plugin.shutdown())
            
            self.plugins.remove(plugin)
            logger.info(f"Plugin unloaded: {plugin_name}")
            return True
        except Exception as e:
            logger.error(f"Error unloading plugin {plugin_name}: {e}")
            return False
    
    def _sort_plugins(self):
        """Sort plugins by priority."""
        self.plugins.sort(key=lambda p: p.priority)
    
    async def process_clip_async(self, clip: ClipItem, context: Dict[str, Any]) -> ClipItem:
        """
        Process a clip through all enabled plugins asynchronously.
        
        Args:
            clip: Clip to process
            context: Current context
        
        Returns:
            Processed clip
        """
        for plugin in self.plugins:
            if not plugin.enabled or not plugin._initialized:
                continue
            
            try:
                # Process with timeout
                clip = await asyncio.wait_for(
                    plugin.process_clip(clip, context),
                    timeout=self.timeout
                )
                clip._processed_by.append(plugin.name)
            except asyncio.TimeoutError:
                logger.warning(f"Plugin {plugin.name} timed out")
            except Exception as e:
                logger.error(f"Error in plugin {plugin.name}: {e}")
                # Continue with other plugins even if one fails
        
        return clip
    
    def process_clip(self, clip: ClipItem, context: Dict[str, Any]) -> ClipItem:
        """
        Process a clip through all enabled plugins (synchronous wrapper).
        
        Args:
            clip: Clip to process
            context: Current context
        
        Returns:
            Processed clip
        """
        if self._loop is None:
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        
        try:
            return self._loop.run_until_complete(
                self.process_clip_async(clip, context)
            )
        except Exception as e:
            logger.error(f"Error processing clip: {e}")
            return clip
    
    async def on_paste_async(self, clip: ClipItem, context: Dict[str, Any]) -> Optional[ClipItem]:
        """
        Handle paste event through plugins asynchronously.
        
        Args:
            clip: Clip being pasted
            context: Current context
        
        Returns:
            Modified clip or None to block paste
        """
        for plugin in self.plugins:
            if not plugin.enabled or not plugin._initialized:
                continue
            
            try:
                clip = await asyncio.wait_for(
                    plugin.on_paste(clip, context),
                    timeout=self.timeout
                )
                if clip is None:
                    logger.info(f"Paste blocked by plugin: {plugin.name}")
                    return None
            except asyncio.TimeoutError:
                logger.warning(f"Plugin {plugin.name} on_paste timed out")
            except Exception as e:
                logger.error(f"Error in plugin {plugin.name} on_paste: {e}")
        
        return clip
    
    def on_paste(self, clip: ClipItem, context: Dict[str, Any]) -> Optional[ClipItem]:
        """
        Handle paste event (synchronous wrapper).
        
        Args:
            clip: Clip being pasted
            context: Current context
        
        Returns:
            Modified clip or None to block paste
        """
        if self._loop is None:
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        
        try:
            return self._loop.run_until_complete(
                self.on_paste_async(clip, context)
            )
        except Exception as e:
            logger.error(f"Error in on_paste: {e}")
            return clip
    
    def get_plugin(self, name: str) -> Optional[ClipStashPlugin]:
        """Get plugin by name."""
        return next((p for p in self.plugins if p.name == name), None)
    
    def get_all_plugins(self) -> List[ClipStashPlugin]:
        """Get all loaded plugins."""
        return self.plugins.copy()
    
    def shutdown_all(self):
        """Shutdown all plugins."""
        if self._loop:
            for plugin in self.plugins:
                try:
                    self._loop.run_until_complete(plugin.shutdown())
                except Exception as e:
                    logger.error(f"Error shutting down plugin {plugin.name}: {e}")
        self.plugins.clear()
        logger.info("All plugins shut down")


# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXT PROVIDER
# ═══════════════════════════════════════════════════════════════════════════════

class ContextProvider:
    """
    Provides system and application context for plugins.
    Cross-platform context detection.
    """
    
    @staticmethod
    def get_active_app() -> str:
        """
        Detect currently active application.
        Cross-platform implementation.
        
        Returns:
            Active application name or "Unknown"
        """
        system = platform.system()
        
        try:
            if system == "Windows":
                return ContextProvider._get_active_app_windows()
            elif system == "Darwin":  # macOS
                return ContextProvider._get_active_app_macos()
            elif system == "Linux":
                return ContextProvider._get_active_app_linux()
        except Exception as e:
            logger.debug(f"Could not detect active app: {e}")
        
        return "Unknown"
    
    @staticmethod
    def _get_active_app_windows() -> str:
        """Get active app on Windows."""
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            return buff.value if buff.value else "Unknown"
        except:
            return "Unknown"
    
    @staticmethod
    def _get_active_app_macos() -> str:
        """Get active app on macOS."""
        try:
            from AppKit import NSWorkspace
            active_app = NSWorkspace.sharedWorkspace().activeApplication()
            return active_app.get('NSApplicationName', 'Unknown')
        except:
            return "Unknown"
    
    @staticmethod
    def _get_active_app_linux() -> str:
        """Get active app on Linux."""
        try:
            import subprocess
            # Try to get active window using xdotool
            result = subprocess.run(
                ['xdotool', 'getactivewindow', 'getwindowname'],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return "Unknown"
    
    @staticmethod
    def get_context() -> Dict[str, Any]:
        """
        Get comprehensive system context.
        
        Returns:
            Dictionary with context information
        """
        now = datetime.now()
        
        return {
            "active_app": ContextProvider.get_active_app(),
            "time_of_day": now.strftime("%H:%M:%S"),
            "day_of_week": now.strftime("%A"),
            "timestamp": now.isoformat(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": sys.version.split()[0]
        }


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    'ClipMetadata',
    'ClipItem',
    'PluginPriority',
    'ClipStashPlugin',
    'PluginManager',
    'ContextProvider'
]
