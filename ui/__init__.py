"""
UI Module for ClipStash Enhanced
"""

try:
    from .plugin_settings import PluginSettingsDialog, show_plugin_settings
    
    __all__ = ['PluginSettingsDialog', 'show_plugin_settings']
except ImportError:
    # PySide6 not available
    __all__ = []
