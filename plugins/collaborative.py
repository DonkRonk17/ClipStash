#!/usr/bin/env python3
"""
Collaborative Clipboard Plugin - Collaborative Clipboard
Priority: LOW

Provides collaborative clipboard functionality:
- Shared clipboard spaces
- User authentication
- Permission system (read/write/admin)
- Real-time activity feed
- WebSocket server for real-time updates
- Notifications
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from clipstash_core import ClipStashPlugin, ClipItem, PluginPriority

logger = logging.getLogger(__name__)


class CollaborativeClipboardPlugin(ClipStashPlugin):
    """
    Enables collaborative clipboard sharing with teams.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._name = "CollaborativeClipboard"
        self._priority = PluginPriority.LOW
        self._version = "1.0.0"
        
        # Configuration
        self.server_url = config.get('server_url', 'ws://localhost:8766') if config else 'ws://localhost:8766'
        self.username = config.get('username', 'anonymous') if config else 'anonymous'
        self.auth_token = config.get('auth_token') if config else None
        self.auto_share = config.get('auto_share', False) if config else False
        self.default_space = config.get('default_space', 'personal') if config else 'personal'
        
        # State
        self.spaces: Dict[str, Dict[str, Any]] = {}
        self.active_space = self.default_space
        self.activity_feed: List[Dict[str, Any]] = []
        self.ws_connection = None
    
    async def initialize(self) -> bool:
        """Initialize collaborative clipboard."""
        # Initialize default space
        self.spaces[self.default_space] = {
            'name': self.default_space,
            'owner': self.username,
            'members': [self.username],
            'permissions': {self.username: 'admin'},
            'clips': [],
            'created': datetime.now().isoformat()
        }
        
        logger.info(f"{self.name} initialized (user: {self.username})")
        return True
    
    async def process_clip(self, clip: ClipItem, context: Dict[str, Any]) -> ClipItem:
        """
        Process clip for collaborative sharing.
        
        Args:
            clip: Clipboard item
            context: Current context
        
        Returns:
            Clip with collaboration metadata
        """
        # Mark clip with collaboration info
        clip.metadata.enrichments['collaboration'] = {
            'owner': self.username,
            'space': self.active_space,
            'shared': self.auto_share,
            'timestamp': datetime.now().isoformat()
        }
        
        # Auto-share if enabled
        if self.auto_share:
            await self._share_to_space(clip, self.active_space)
        
        return clip
    
    async def _share_to_space(self, clip: ClipItem, space_name: str):
        """
        Share clip to a collaborative space.
        
        Args:
            clip: Clip to share
            space_name: Target space
        """
        if space_name not in self.spaces:
            logger.warning(f"Space not found: {space_name}")
            return
        
        space = self.spaces[space_name]
        
        # Check permissions
        user_permission = space['permissions'].get(self.username, 'none')
        if user_permission not in ['write', 'admin']:
            logger.warning(f"No write permission for space: {space_name}")
            return
        
        # Add to space
        space['clips'].append({
            'clip_hash': clip.hash,
            'content_preview': clip.preview(100),
            'owner': self.username,
            'timestamp': datetime.now().isoformat()
        })
        
        # Add to activity feed
        self._add_activity({
            'type': 'clip_shared',
            'user': self.username,
            'space': space_name,
            'clip_hash': clip.hash,
            'timestamp': datetime.now().isoformat()
        })
        
        # Broadcast to other members (in real implementation)
        # await self._broadcast_update(space_name, 'clip_added', clip)
        
        logger.info(f"Shared clip to space: {space_name}")
    
    def create_space(self, name: str, members: Optional[List[str]] = None) -> bool:
        """
        Create a new collaborative space.
        
        Args:
            name: Space name
            members: Initial members
        
        Returns:
            True if created successfully
        """
        if name in self.spaces:
            logger.warning(f"Space already exists: {name}")
            return False
        
        self.spaces[name] = {
            'name': name,
            'owner': self.username,
            'members': [self.username] + (members or []),
            'permissions': {self.username: 'admin'},
            'clips': [],
            'created': datetime.now().isoformat()
        }
        
        # Set permissions for members
        for member in (members or []):
            self.spaces[name]['permissions'][member] = 'write'
        
        self._add_activity({
            'type': 'space_created',
            'user': self.username,
            'space': name,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Created space: {name} with {len(members or [])} members")
        return True
    
    def add_member(self, space_name: str, username: str, permission: str = 'read') -> bool:
        """
        Add member to space.
        
        Args:
            space_name: Space name
            username: User to add
            permission: Permission level (read/write/admin)
        
        Returns:
            True if added successfully
        """
        if space_name not in self.spaces:
            logger.warning(f"Space not found: {space_name}")
            return False
        
        space = self.spaces[space_name]
        
        # Check if current user is admin
        if space['permissions'].get(self.username) != 'admin':
            logger.warning(f"No admin permission for space: {space_name}")
            return False
        
        # Add member
        if username not in space['members']:
            space['members'].append(username)
        
        space['permissions'][username] = permission
        
        self._add_activity({
            'type': 'member_added',
            'user': self.username,
            'space': space_name,
            'new_member': username,
            'permission': permission,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Added {username} to space {space_name} with {permission} permission")
        return True
    
    def remove_member(self, space_name: str, username: str) -> bool:
        """
        Remove member from space.
        
        Args:
            space_name: Space name
            username: User to remove
        
        Returns:
            True if removed successfully
        """
        if space_name not in self.spaces:
            logger.warning(f"Space not found: {space_name}")
            return False
        
        space = self.spaces[space_name]
        
        # Check if current user is admin
        if space['permissions'].get(self.username) != 'admin':
            logger.warning(f"No admin permission for space: {space_name}")
            return False
        
        # Can't remove owner
        if username == space['owner']:
            logger.warning("Cannot remove space owner")
            return False
        
        # Remove member
        if username in space['members']:
            space['members'].remove(username)
        
        if username in space['permissions']:
            del space['permissions'][username]
        
        self._add_activity({
            'type': 'member_removed',
            'user': self.username,
            'space': space_name,
            'removed_member': username,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Removed {username} from space {space_name}")
        return True
    
    def switch_space(self, space_name: str) -> bool:
        """
        Switch active space.
        
        Args:
            space_name: Space to switch to
        
        Returns:
            True if switched successfully
        """
        if space_name not in self.spaces:
            logger.warning(f"Space not found: {space_name}")
            return False
        
        space = self.spaces[space_name]
        
        # Check if user is member
        if self.username not in space['members']:
            logger.warning(f"Not a member of space: {space_name}")
            return False
        
        self.active_space = space_name
        logger.info(f"Switched to space: {space_name}")
        return True
    
    def _add_activity(self, activity: Dict[str, Any]):
        """Add activity to feed."""
        self.activity_feed.append(activity)
        
        # Keep feed manageable
        if len(self.activity_feed) > 100:
            self.activity_feed = self.activity_feed[-100:]
    
    def get_activity_feed(self, space_name: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get activity feed.
        
        Args:
            space_name: Filter by space (None for all)
            limit: Maximum activities to return
        
        Returns:
            List of activities
        """
        activities = self.activity_feed
        
        # Filter by space if specified
        if space_name:
            activities = [a for a in activities if a.get('space') == space_name]
        
        # Return latest activities
        return activities[-limit:]
    
    def get_space_info(self, space_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a space."""
        return self.spaces.get(space_name)
    
    def list_spaces(self) -> List[str]:
        """List all spaces user is member of."""
        return [
            name for name, space in self.spaces.items()
            if self.username in space['members']
        ]
    
    async def shutdown(self):
        """Cleanup on shutdown."""
        if self.ws_connection:
            try:
                await self.ws_connection.close()
            except:
                pass
        
        logger.info(f"{self.name} shutdown")
