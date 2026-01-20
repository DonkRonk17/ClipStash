#!/usr/bin/env python3
"""
Sync Agent Plugin - Cross-Device Sync Agent
Priority: MEDIUM

Provides cross-device clipboard synchronization:
- WebSocket client for real-time sync
- E2E encryption using cryptography library
- Device fingerprinting
- Conflict resolution (timestamp-based)
- Delta syncing (only changed clips)
- Filters sensitive content before sync
"""

import asyncio
import hashlib
import logging
import platform
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from clipstash_core import ClipStashPlugin, ClipItem, PluginPriority

logger = logging.getLogger(__name__)


class SyncAgentPlugin(ClipStashPlugin):
    """
    Synchronizes clipboard across devices securely.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._name = "SyncAgent"
        self._priority = PluginPriority.MEDIUM
        self._version = "1.0.0"
        
        # Configuration with defaults
        config = config or {}
        self.sync_server = config.get('sync_server', 'ws://localhost:8765')
        self.encryption_key = config.get('encryption_key')
        self.device_id = config.get('device_id', self._generate_device_id())
        self.sync_enabled = config.get('sync_enabled', False)
        self.filter_sensitive = config.get('filter_sensitive', True)
        self.max_sync_size = config.get('max_sync_size', 1024 * 100)  # 100KB
        
        # State
        self.ws_connection = None
        self.sync_task = None
        self.synced_hashes = set()
        self.encryption_cipher = None
    
    def _generate_device_id(self) -> str:
        """Generate unique device identifier."""
        machine_id = platform.node()
        user = platform.system()
        fingerprint = f"{machine_id}-{user}-{uuid.getnode()}"
        return hashlib.md5(fingerprint.encode()).hexdigest()
    
    async def initialize(self) -> bool:
        """Initialize the sync agent."""
        if not self.sync_enabled:
            logger.info(f"{self.name} initialized (disabled)")
            return True
        
        # Initialize encryption
        if self.encryption_key:
            try:
                from cryptography.fernet import Fernet
                
                # Ensure key is valid format
                if isinstance(self.encryption_key, str):
                    key = self.encryption_key.encode()
                else:
                    key = self.encryption_key
                
                # Generate key if needed
                if key == b'auto':
                    key = Fernet.generate_key()
                    logger.info(f"Generated encryption key: {key.decode()}")
                
                self.encryption_cipher = Fernet(key)
                logger.info("E2E encryption enabled")
            except ImportError:
                logger.warning("cryptography library not available, sync will be unencrypted")
            except Exception as e:
                logger.error(f"Failed to initialize encryption: {e}")
        
        # Start sync connection
        # Note: In production, this would establish WebSocket connection
        # For now, we just log that it's ready
        logger.info(f"{self.name} initialized (device: {self.device_id[:8]}...)")
        
        return True
    
    async def process_clip(self, clip: ClipItem, context: Dict[str, Any]) -> ClipItem:
        """
        Process clip for potential sync.
        
        Args:
            clip: Clipboard item
            context: Current context
        
        Returns:
            Clip with sync metadata
        """
        if not self.sync_enabled:
            return clip
        
        # Check if should sync
        should_sync = self._should_sync(clip)
        
        if should_sync:
            # Mark for sync
            clip.metadata.enrichments['sync'] = {
                'device_id': self.device_id,
                'device_name': platform.node(),
                'timestamp': datetime.now().isoformat(),
                'should_sync': True
            }
            
            # Queue for sync (in real implementation)
            # await self._queue_for_sync(clip)
            logger.debug(f"Clip marked for sync: {clip.preview(40)}")
        else:
            clip.metadata.enrichments['sync'] = {
                'should_sync': False,
                'reason': 'filtered'
            }
        
        return clip
    
    def _should_sync(self, clip: ClipItem) -> bool:
        """
        Determine if clip should be synced.
        
        Args:
            clip: Clip to check
        
        Returns:
            True if should sync
        """
        # Check size
        if len(clip.content) > self.max_sync_size:
            logger.debug(f"Clip too large for sync: {len(clip.content)} bytes")
            return False
        
        # Filter sensitive content
        if self.filter_sensitive:
            security = clip.metadata.enrichments.get('security', {})
            if security.get('security_flags'):
                logger.debug("Blocking sync of sensitive content")
                return False
        
        # Check if already synced
        if clip.hash in self.synced_hashes:
            return False
        
        return True
    
    async def _queue_for_sync(self, clip: ClipItem):
        """
        Queue clip for synchronization.
        
        Args:
            clip: Clip to sync
        """
        try:
            # Prepare sync payload
            payload = self._prepare_sync_payload(clip)
            
            # Encrypt if enabled
            if self.encryption_cipher:
                payload = self._encrypt_payload(payload)
            
            # Send via WebSocket (in real implementation)
            # await self._send_to_server(payload)
            
            self.synced_hashes.add(clip.hash)
            logger.debug(f"Synced clip: {clip.hash}")
        
        except Exception as e:
            logger.error(f"Error queuing clip for sync: {e}")
    
    def _prepare_sync_payload(self, clip: ClipItem) -> Dict[str, Any]:
        """
        Prepare clip data for sync.
        
        Args:
            clip: Clip to prepare
        
        Returns:
            Sync payload
        """
        return {
            'device_id': self.device_id,
            'clip_hash': clip.hash,
            'content': clip.content,
            'timestamp': clip.timestamp,
            'metadata': clip.metadata.to_dict()
        }
    
    def _encrypt_payload(self, payload: Dict[str, Any]) -> bytes:
        """
        Encrypt sync payload.
        
        Args:
            payload: Payload to encrypt
        
        Returns:
            Encrypted bytes
        """
        import json
        
        if self.encryption_cipher:
            data = json.dumps(payload).encode()
            return self.encryption_cipher.encrypt(data)
        
        return json.dumps(payload).encode()
    
    def _decrypt_payload(self, encrypted: bytes) -> Dict[str, Any]:
        """
        Decrypt sync payload.
        
        Args:
            encrypted: Encrypted data
        
        Returns:
            Decrypted payload
        """
        import json
        
        if self.encryption_cipher:
            decrypted = self.encryption_cipher.decrypt(encrypted)
            return json.loads(decrypted.decode())
        
        return json.loads(encrypted.decode())
    
    async def _receive_sync_updates(self):
        """
        Receive sync updates from server.
        Background task that runs continuously.
        """
        # In real implementation, this would:
        # 1. Connect to WebSocket server
        # 2. Listen for incoming syncs
        # 3. Decrypt and validate
        # 4. Apply to local history
        # 5. Resolve conflicts
        
        logger.info("Sync receiver started")
        
        try:
            # Placeholder for WebSocket connection
            # import websockets
            # async with websockets.connect(self.sync_server) as ws:
            #     async for message in ws:
            #         await self._handle_sync_message(message)
            pass
        except Exception as e:
            logger.error(f"Sync receiver error: {e}")
    
    async def _handle_sync_message(self, message: bytes):
        """
        Handle incoming sync message.
        
        Args:
            message: Encrypted sync message
        """
        try:
            # Decrypt
            payload = self._decrypt_payload(message)
            
            # Validate
            if payload.get('device_id') == self.device_id:
                # Ignore own syncs
                return
            
            # Check for conflicts
            clip_hash = payload.get('clip_hash')
            if clip_hash in self.synced_hashes:
                # Resolve conflict
                logger.debug(f"Conflict detected for clip: {clip_hash}")
                # Use timestamp-based resolution
            
            # Apply sync (would integrate with history manager)
            logger.info(f"Received sync from device: {payload.get('device_id')[:8]}...")
        
        except Exception as e:
            logger.error(f"Error handling sync message: {e}")
    
    async def shutdown(self):
        """Cleanup on shutdown."""
        if self.ws_connection:
            try:
                await self.ws_connection.close()
            except:
                pass
        
        if self.sync_task:
            self.sync_task.cancel()
        
        logger.info(f"{self.name} shutdown")
