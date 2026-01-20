#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                      🗂️ ClipStash Enhanced v2.0.0                             ║
║              Universal Clipboard History Manager with AI Plugins              ║
║                         Metaphy LLC - 2025/2026                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

ClipStash Enhanced with AI Plugin System:
- All features from original ClipStash
- 10 AI-powered plugins for enhanced functionality
- Plugin management UI
- Backward compatible with original version

Author: Logan Smith / Team Brain (Metaphy LLC)
License: MIT
Repository: https://github.com/DonkRonk17/ClipStash
"""

import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Optional

# GUI imports
try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import QTimer
except ImportError:
    print("❌ PySide6 not found. Install with: pip install PySide6")
    sys.exit(1)

# Import original ClipStash window
try:
    from clipstash import ClipStashWindow
except ImportError:
    print("❌ Could not import original ClipStash. Ensure clipstash.py is in the same directory.")
    sys.exit(1)

# Import plugin system
from clipstash_core import PluginManager, ContextProvider
from enhanced_history_manager import EnhancedHistoryManager

# Import all plugins
from plugins import (
    SecurityMonitorPlugin,
    ContentEnricherPlugin,
    PastePredictorPlugin,
    ResearchAssistantPlugin,
    SyncAgentPlugin,
    WorkflowTriggerPlugin,
    KnowledgeGraphPlugin,
    CollaborativeClipboardPlugin,
    SmartTemplatesPlugin,
    APIWrapperPlugin,
)

# Configuration
CONFIG_DIR = Path.home() / '.clipstash' / 'config'
CONFIG_FILE = CONFIG_DIR / 'plugins.json'

# Setup logging
LOG_DIR = Path.home() / '.clipstash'
LOG_FILE = LOG_DIR / 'clipstash_enhanced.log'
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_plugin_config() -> dict:
    """Load plugin configuration from file."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading plugin config: {e}")
    
    # Load default config
    default_config_path = Path(__file__).parent / 'config' / 'plugins.json'
    if default_config_path.exists():
        try:
            with open(default_config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading default config: {e}")
    
    return {}


def initialize_plugins(plugin_manager: PluginManager, config: dict):
    """
    Initialize and load all plugins.
    
    Args:
        plugin_manager: Plugin manager instance
        config: Plugin configuration dictionary
    """
    # Define all available plugins
    plugin_classes = [
        SecurityMonitorPlugin,
        ContentEnricherPlugin,
        PastePredictorPlugin,
        ResearchAssistantPlugin,
        SyncAgentPlugin,
        WorkflowTriggerPlugin,
        KnowledgeGraphPlugin,
        CollaborativeClipboardPlugin,
        SmartTemplatesPlugin,
        APIWrapperPlugin,
    ]
    
    loaded_count = 0
    failed_count = 0
    
    for plugin_class in plugin_classes:
        plugin_name = plugin_class.__name__.replace('Plugin', '')
        plugin_config = config.get(plugin_name, {})
        
        try:
            # Create plugin instance
            plugin = plugin_class(plugin_config.get('config', {}))
            
            # Load plugin
            success = plugin_manager.load_plugin(plugin)
            
            if success:
                # Apply enabled state from config
                if not plugin_config.get('enabled', True):
                    plugin.disable()
                
                loaded_count += 1
                logger.info(f"✓ Loaded plugin: {plugin_name}")
            else:
                failed_count += 1
                logger.warning(f"✗ Failed to load plugin: {plugin_name}")
        
        except Exception as e:
            failed_count += 1
            logger.error(f"✗ Error loading plugin {plugin_name}: {e}")
    
    logger.info(f"Plugin loading complete: {loaded_count} loaded, {failed_count} failed")


class EnhancedClipStashApp:
    """
    Enhanced ClipStash application with plugin system.
    Uses original ClipStashWindow with enhanced history manager.
    """
    
    def __init__(self):
        """Initialize the enhanced application."""
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("ClipStash Enhanced")
        
        # Initialize plugin system
        logger.info("Initializing ClipStash Enhanced v2.0.0")
        
        # Load configuration
        self.config = load_plugin_config()
        
        # Create plugin manager
        self.plugin_manager = PluginManager(timeout=5.0)
        
        # Initialize plugins
        initialize_plugins(self.plugin_manager, self.config)
        
        # Create enhanced history manager
        self.history_manager = EnhancedHistoryManager(self.plugin_manager)
        
        # Create main window (using original UI)
        self.window = ClipStashWindow()
        
        # Replace the history manager with our enhanced version
        self.window.history = self.history_manager
        
        # Update window title
        self.window.setWindowTitle("ClipStash Enhanced v2.0.0")
        
        # Add plugin menu
        self._add_plugin_menu()
        
        logger.info("ClipStash Enhanced initialized successfully")
    
    def _add_plugin_menu(self):
        """Add plugin management menu to main window."""
        try:
            # Add plugins menu if menubar exists
            if hasattr(self.window, 'menuBar'):
                menu_bar = self.window.menuBar()
                
                plugins_menu = menu_bar.addMenu("&Plugins")
                
                # Add plugin settings action
                settings_action = plugins_menu.addAction("Plugin &Settings")
                settings_action.triggered.connect(self._show_plugin_settings)
                
                plugins_menu.addSeparator()
                
                # Add action to show plugin status
                status_action = plugins_menu.addAction("Plugin &Status")
                status_action.triggered.connect(self._show_plugin_status)
        except Exception as e:
            logger.warning(f"Could not add plugin menu: {e}")
    
    def _show_plugin_settings(self):
        """Show plugin settings dialog."""
        try:
            from ui import show_plugin_settings
            show_plugin_settings(self.plugin_manager, self.window)
        except Exception as e:
            logger.error(f"Error showing plugin settings: {e}")
            QMessageBox.warning(
                self.window,
                "Plugin Settings",
                f"Could not open plugin settings: {e}"
            )
    
    def _show_plugin_status(self):
        """Show plugin status information."""
        plugins = self.plugin_manager.get_all_plugins()
        
        status_lines = [
            "=== Plugin Status ===",
            f"Total plugins: {len(plugins)}",
            ""
        ]
        
        for plugin in plugins:
            status = "✓ Enabled" if plugin.enabled else "✗ Disabled"
            status_lines.append(f"{plugin.name} v{plugin.version} - {status}")
        
        # Add history stats
        stats = self.history_manager.get_stats()
        status_lines.extend([
            "",
            "=== History Statistics ===",
            f"Total clips: {stats['total']}",
            f"Pinned clips: {stats['pinned']}",
            f"Enriched clips: {stats['enriched']}",
            f"Flagged clips: {stats['flagged']}",
            f"Tagged clips: {stats['tagged']}",
            f"Active plugins: {stats['plugins_active']}"
        ])
        
        status_text = "\n".join(status_lines)
        
        QMessageBox.information(
            self.window,
            "Plugin Status",
            status_text
        )
    
    def run(self) -> int:
        """
        Run the application.
        
        Returns:
            Exit code
        """
        try:
            self.window.show()
            exit_code = self.app.exec()
            
            # Cleanup
            logger.info("Shutting down ClipStash Enhanced")
            self.plugin_manager.shutdown_all()
            
            return exit_code
        
        except Exception as e:
            logger.error(f"Application error: {e}")
            return 1


def main():
    """Main entry point."""
    try:
        app = EnhancedClipStashApp()
        sys.exit(app.run())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
