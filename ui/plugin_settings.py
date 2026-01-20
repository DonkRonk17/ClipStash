#!/usr/bin/env python3
"""
Plugin Settings Dialog - UI for configuring plugins

Provides tabbed interface for plugin management:
- Enable/disable toggles
- Plugin-specific settings
- Save/load from config file
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List

try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
        QPushButton, QLabel, QCheckBox, QSpinBox, QLineEdit,
        QFormLayout, QGroupBox, QScrollArea, QWidget, QTextEdit
    )
    from PySide6.QtCore import Qt
except ImportError:
    print("PySide6 not available - UI components disabled")
    QDialog = object

from clipstash_core import PluginManager, ClipStashPlugin

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / '.clipstash' / 'config'
CONFIG_FILE = CONFIG_DIR / 'plugins.json'


class PluginSettingsDialog(QDialog):
    """
    Dialog for managing plugin settings.
    """
    
    def __init__(self, plugin_manager: PluginManager, parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        self.config = self._load_config()
        self.setting_widgets = {}
        
        self.setWindowTitle("Plugin Settings")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self._setup_ui()
        self._load_current_settings()
    
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout()
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Create tab for each plugin
        for plugin in self.plugin_manager.get_all_plugins():
            tab = self._create_plugin_tab(plugin)
            self.tabs.addTab(tab, plugin.name)
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._save_settings)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._apply_settings)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.apply_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _create_plugin_tab(self, plugin: ClipStashPlugin) -> QWidget:
        """
        Create settings tab for a plugin.
        
        Args:
            plugin: Plugin to create tab for
        
        Returns:
            Widget for the tab
        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        container = QWidget()
        layout = QVBoxLayout()
        
        # Plugin info
        info_group = QGroupBox("Plugin Information")
        info_layout = QFormLayout()
        info_layout.addRow("Name:", QLabel(plugin.name))
        info_layout.addRow("Version:", QLabel(plugin.version))
        info_layout.addRow("Priority:", QLabel(plugin.priority.name))
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Enable/disable
        enabled_group = QGroupBox("Status")
        enabled_layout = QHBoxLayout()
        
        enabled_checkbox = QCheckBox("Enable Plugin")
        enabled_checkbox.setChecked(plugin.enabled)
        self.setting_widgets[f"{plugin.name}_enabled"] = enabled_checkbox
        
        enabled_layout.addWidget(enabled_checkbox)
        enabled_layout.addStretch()
        enabled_group.setLayout(enabled_layout)
        layout.addWidget(enabled_group)
        
        # Plugin-specific settings
        settings_group = QGroupBox("Settings")
        settings_layout = QFormLayout()
        
        # Get plugin-specific settings
        plugin_settings = self._get_plugin_settings(plugin)
        
        for key, value in plugin_settings.items():
            widget = self._create_setting_widget(key, value)
            if widget:
                self.setting_widgets[f"{plugin.name}_{key}"] = widget
                settings_layout.addRow(key.replace('_', ' ').title() + ":", widget)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Custom UI from plugin
        custom_ui = plugin.get_settings_ui()
        if custom_ui:
            custom_group = QGroupBox("Advanced Settings")
            custom_layout = QVBoxLayout()
            custom_layout.addWidget(custom_ui)
            custom_group.setLayout(custom_layout)
            layout.addWidget(custom_group)
        
        layout.addStretch()
        container.setLayout(layout)
        scroll.setWidget(container)
        
        return scroll
    
    def _get_plugin_settings(self, plugin: ClipStashPlugin) -> Dict[str, Any]:
        """Get current settings for a plugin."""
        # Return plugin's config
        return plugin.config
    
    def _create_setting_widget(self, key: str, value: Any) -> QWidget:
        """
        Create appropriate widget for a setting value.
        
        Args:
            key: Setting key
            value: Setting value
        
        Returns:
            Widget for the setting
        """
        if isinstance(value, bool):
            widget = QCheckBox()
            widget.setChecked(value)
            return widget
        
        elif isinstance(value, int):
            widget = QSpinBox()
            widget.setMinimum(0)
            widget.setMaximum(10000)
            widget.setValue(value)
            return widget
        
        elif isinstance(value, float):
            widget = QLineEdit()
            widget.setText(str(value))
            return widget
        
        elif isinstance(value, str):
            if len(value) > 50:
                widget = QTextEdit()
                widget.setPlainText(value)
                widget.setMaximumHeight(100)
            else:
                widget = QLineEdit()
                widget.setText(value)
            return widget
        
        elif isinstance(value, list):
            widget = QTextEdit()
            widget.setPlainText('\n'.join(str(v) for v in value))
            widget.setMaximumHeight(100)
            return widget
        
        else:
            widget = QLineEdit()
            widget.setText(str(value))
            return widget
    
    def _load_current_settings(self):
        """Load current settings into widgets."""
        # Settings are already loaded from config and applied to plugins
        pass
    
    def _save_settings(self):
        """Save settings and close dialog."""
        self._apply_settings()
        self._write_config()
        self.accept()
    
    def _apply_settings(self):
        """Apply settings to plugins without closing."""
        for plugin in self.plugin_manager.get_all_plugins():
            # Apply enabled status
            enabled_key = f"{plugin.name}_enabled"
            if enabled_key in self.setting_widgets:
                enabled = self.setting_widgets[enabled_key].isChecked()
                if enabled:
                    plugin.enable()
                else:
                    plugin.disable()
            
            # Apply other settings
            for setting_key, widget in self.setting_widgets.items():
                if not setting_key.startswith(f"{plugin.name}_"):
                    continue
                
                key = setting_key.replace(f"{plugin.name}_", "")
                if key == "enabled":
                    continue
                
                # Get value from widget
                value = self._get_widget_value(widget)
                
                # Update plugin config
                if key in plugin.config:
                    plugin.config[key] = value
        
        logger.info("Applied plugin settings")
    
    def _get_widget_value(self, widget: QWidget) -> Any:
        """Extract value from widget."""
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QSpinBox):
            return widget.value()
        elif isinstance(widget, QLineEdit):
            text = widget.text()
            # Try to parse as number
            try:
                if '.' in text:
                    return float(text)
                else:
                    return int(text)
            except ValueError:
                return text
        elif isinstance(widget, QTextEdit):
            return widget.toPlainText()
        else:
            return None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load plugin configuration from file."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading plugin config: {e}")
        return {}
    
    def _write_config(self):
        """Write plugin configuration to file."""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            
            config = {}
            for plugin in self.plugin_manager.get_all_plugins():
                config[plugin.name] = {
                    'enabled': plugin.enabled,
                    'config': plugin.config
                }
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Saved plugin config to {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Error saving plugin config: {e}")


def show_plugin_settings(plugin_manager: PluginManager, parent=None):
    """
    Show plugin settings dialog.
    
    Args:
        plugin_manager: Plugin manager instance
        parent: Parent widget
    
    Returns:
        True if settings were saved, False if cancelled
    """
    dialog = PluginSettingsDialog(plugin_manager, parent)
    return dialog.exec() == QDialog.DialogCode.Accepted
