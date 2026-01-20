#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                      Enhanced History Manager                                  ║
║              Extends HistoryManager with Plugin Support                        ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Enhanced clipboard history manager that integrates with the plugin system
while maintaining backward compatibility with the original HistoryManager.

Author: Logan Smith / Team Brain (Metaphy LLC)
License: MIT
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from clipstash_core import (
    ClipItem, ClipMetadata, PluginManager, ContextProvider
)

# Configuration
DATA_DIR = Path.home() / ".clipstash"
HISTORY_FILE = DATA_DIR / "history.json"
MAX_HISTORY = 500
PLUGIN_TIMEOUT = 5.0  # Maximum time for plugin processing

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCED HISTORY MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class EnhancedHistoryManager:
    """
    Enhanced clipboard history manager with plugin support.
    Extends original HistoryManager functionality while maintaining
    backward compatibility with the original data format.
    """
    
    def __init__(self, plugin_manager: Optional[PluginManager] = None):
        """
        Initialize enhanced history manager.
        
        Args:
            plugin_manager: Optional plugin manager for clip processing
        """
        self.items: List[ClipItem] = []
        self.plugin_manager = plugin_manager or PluginManager(timeout=PLUGIN_TIMEOUT)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._ensure_data_dir()
        self.load()
        logger.info("EnhancedHistoryManager initialized")
    
    def _ensure_data_dir(self):
        """Create data directory if needed."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    def load(self):
        """
        Load history from disk.
        Supports both original and enhanced formats.
        """
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.items = [ClipItem.from_dict(d) for d in data]
                logger.info(f"Loaded {len(self.items)} clips from history")
            except Exception as e:
                logger.error(f"Failed to load history: {e}")
                self.items = []
        else:
            logger.info("No existing history file found")
    
    def save(self):
        """
        Save history to disk.
        Maintains backward compatibility - old version can still read basic data.
        """
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump([item.to_dict() for item in self.items], f, indent=2)
            logger.debug(f"Saved {len(self.items)} clips to history")
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
    
    def add(self, content: str) -> Optional[ClipItem]:
        """
        Add new clip to history with plugin processing.
        
        Args:
            content: Clipboard content to add
        
        Returns:
            The created clip item or None if invalid
        """
        if not content or not content.strip():
            return None
        
        # Check for duplicates
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        for i, item in enumerate(self.items):
            if item.hash == content_hash:
                # Move to top instead of adding duplicate
                self.items.pop(i)
                logger.debug(f"Moving duplicate clip to top: {item.preview(40)}")
                break
        
        # Create new item
        item = ClipItem(content)
        
        # Process through plugins
        if self.plugin_manager:
            try:
                context = ContextProvider.get_context()
                item = self.plugin_manager.process_clip(item, context)
                logger.debug(f"Clip processed by {len(item._processed_by)} plugins")
            except Exception as e:
                logger.error(f"Error processing clip through plugins: {e}")
        
        # Add to history
        self.items.insert(0, item)
        
        # Enforce max history (keep pinned items)
        self._trim_history()
        self.save()
        
        return item
    
    def _trim_history(self):
        """Remove old items if over limit, keeping pinned items."""
        pinned = [i for i in self.items if i.pinned]
        unpinned = [i for i in self.items if not i.pinned]
        
        if len(unpinned) > MAX_HISTORY:
            unpinned = unpinned[:MAX_HISTORY]
            logger.debug(f"Trimmed history to {MAX_HISTORY} unpinned items")
        
        self.items = pinned + unpinned
    
    def delete(self, item: ClipItem):
        """
        Delete an item from history.
        
        Args:
            item: ClipItem to delete
        """
        self.items = [i for i in self.items if i.hash != item.hash]
        self.save()
        logger.debug(f"Deleted clip: {item.preview(40)}")
    
    def toggle_pin(self, item: ClipItem):
        """
        Toggle pin status of an item.
        
        Args:
            item: ClipItem to toggle
        """
        for i in self.items:
            if i.hash == item.hash:
                i.pinned = not i.pinned
                logger.debug(f"Toggled pin for clip: {i.preview(40)} -> {i.pinned}")
                break
        self.save()
    
    def search(self, query: str) -> List[ClipItem]:
        """
        Search history for matching items.
        
        Args:
            query: Search query string
        
        Returns:
            List of matching ClipItems
        """
        if not query:
            return self.items
        
        query = query.lower()
        results = [i for i in self.items if query in i.content.lower()]
        
        # Allow plugins to modify search results
        if self.plugin_manager:
            try:
                if self._loop is None:
                    try:
                        self._loop = asyncio.get_event_loop()
                    except RuntimeError:
                        self._loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(self._loop)
                
                # Run search hooks for all plugins
                for plugin in self.plugin_manager.get_all_plugins():
                    if plugin.enabled:
                        try:
                            results = self._loop.run_until_complete(
                                plugin.on_search(query, results)
                            )
                        except Exception as e:
                            logger.error(f"Error in plugin {plugin.name} search: {e}")
            except Exception as e:
                logger.error(f"Error running plugin search hooks: {e}")
        
        logger.debug(f"Search '{query}' returned {len(results)} results")
        return results
    
    async def search_async(self, query: str) -> List[ClipItem]:
        """
        Asynchronous search with plugin hooks.
        
        Args:
            query: Search query string
        
        Returns:
            List of matching ClipItems
        """
        if not query:
            return self.items
        
        query = query.lower()
        results = [i for i in self.items if query in i.content.lower()]
        
        # Allow plugins to modify search results
        if self.plugin_manager:
            for plugin in self.plugin_manager.get_all_plugins():
                if plugin.enabled:
                    try:
                        results = await plugin.on_search(query, results)
                    except Exception as e:
                        logger.error(f"Error in plugin {plugin.name} search: {e}")
        
        return results
    
    def clear_unpinned(self):
        """Clear all unpinned items."""
        before_count = len(self.items)
        self.items = [i for i in self.items if i.pinned]
        after_count = len(self.items)
        self.save()
        logger.info(f"Cleared {before_count - after_count} unpinned items")
    
    def on_paste(self, item: ClipItem) -> Optional[ClipItem]:
        """
        Handle paste event through plugins.
        Plugins can modify or block the paste.
        
        Args:
            item: ClipItem being pasted
        
        Returns:
            Modified clip or None to block paste
        """
        if self.plugin_manager:
            try:
                context = ContextProvider.get_context()
                result = self.plugin_manager.on_paste(item, context)
                if result is None:
                    logger.warning(f"Paste blocked for clip: {item.preview(40)}")
                return result
            except Exception as e:
                logger.error(f"Error in paste hooks: {e}")
                return item
        return item
    
    def get_stats(self) -> dict:
        """
        Get statistics about the clipboard history.
        
        Returns:
            Dictionary with history statistics
        """
        total = len(self.items)
        pinned = sum(1 for i in self.items if i.pinned)
        
        # Count clips with metadata
        enriched = sum(1 for i in self.items if i.metadata.enrichments)
        flagged = sum(1 for i in self.items if i.metadata.security_flags)
        tagged = sum(1 for i in self.items if i.metadata.tags)
        
        # Count by processed plugins
        plugins_used = set()
        for item in self.items:
            plugins_used.update(item._processed_by)
        
        return {
            "total": total,
            "pinned": pinned,
            "enriched": enriched,
            "flagged": flagged,
            "tagged": tagged,
            "plugins_active": len(plugins_used),
            "plugins_list": list(plugins_used)
        }


# ═══════════════════════════════════════════════════════════════════════════════
# BACKWARD COMPATIBLE ALIAS
# ═══════════════════════════════════════════════════════════════════════════════

# For backward compatibility, can be imported as HistoryManager
HistoryManager = EnhancedHistoryManager


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    'EnhancedHistoryManager',
    'HistoryManager'
]
