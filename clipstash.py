#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           🗂️ ClipStash v1.0.0                                 ║
║                    Universal Clipboard History Manager                         ║
║                         Metaphy LLC - 2025/2026                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

A lightweight, cross-platform clipboard history manager that:
- Saves your clipboard history automatically
- Lets you search through past clips
- Pin important items to keep them forever
- Works on Windows, Mac, and Linux
- Beautiful dark-themed UI

Author: Logan Smith / Team Brain (Metaphy LLC)
License: MIT
Repository: https://github.com/DonkRonk17/ClipStash
"""

import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

# GUI imports
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QListWidget, QListWidgetItem, QLineEdit, QPushButton, QLabel,
        QSystemTrayIcon, QMenu, QTextEdit, QSplitter, QFrame, QMessageBox,
        QCheckBox, QStatusBar
    )
    from PySide6.QtCore import Qt, QTimer, Signal, QThread
    from PySide6.QtGui import QIcon, QFont, QColor, QAction, QClipboard
except ImportError:
    print("❌ PySide6 not found. Install with: pip install PySide6")
    sys.exit(1)

# Cross-platform clipboard
try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

APP_NAME = "ClipStash"
APP_VERSION = "1.0.0"
MAX_HISTORY = 500  # Maximum clips to keep
POLL_INTERVAL = 500  # Check clipboard every 500ms
DATA_DIR = Path.home() / ".clipstash"
HISTORY_FILE = DATA_DIR / "history.json"

# ═══════════════════════════════════════════════════════════════════════════════
# DARK THEME STYLESHEET
# ═══════════════════════════════════════════════════════════════════════════════

DARK_THEME = """
QMainWindow, QWidget {
    background-color: #1a1a2e;
    color: #eaeaea;
    font-family: 'Segoe UI', 'SF Pro Display', sans-serif;
}

QListWidget {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 8px;
    padding: 5px;
    font-size: 13px;
}

QListWidget::item {
    background-color: #1a1a2e;
    border: 1px solid #0f3460;
    border-radius: 6px;
    margin: 3px;
    padding: 10px;
}

QListWidget::item:hover {
    background-color: #0f3460;
    border-color: #e94560;
}

QListWidget::item:selected {
    background-color: #e94560;
    border-color: #e94560;
    color: white;
}

QLineEdit {
    background-color: #16213e;
    border: 2px solid #0f3460;
    border-radius: 8px;
    padding: 10px 15px;
    font-size: 14px;
    color: #eaeaea;
}

QLineEdit:focus {
    border-color: #e94560;
}

QLineEdit::placeholder {
    color: #6b7280;
}

QPushButton {
    background-color: #e94560;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #ff6b6b;
}

QPushButton:pressed {
    background-color: #c73e54;
}

QPushButton#secondary {
    background-color: #0f3460;
}

QPushButton#secondary:hover {
    background-color: #16213e;
    border: 1px solid #e94560;
}

QTextEdit {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 8px;
    padding: 10px;
    font-size: 13px;
    color: #eaeaea;
    font-family: 'Consolas', 'Monaco', monospace;
}

QLabel {
    color: #eaeaea;
}

QLabel#title {
    font-size: 24px;
    font-weight: bold;
    color: #e94560;
}

QLabel#subtitle {
    font-size: 12px;
    color: #6b7280;
}

QStatusBar {
    background-color: #0f3460;
    color: #6b7280;
    border-top: 1px solid #16213e;
}

QFrame#separator {
    background-color: #0f3460;
}

QCheckBox {
    color: #eaeaea;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #0f3460;
    background-color: #16213e;
}

QCheckBox::indicator:checked {
    background-color: #e94560;
    border-color: #e94560;
}

QMenu {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 8px;
    padding: 5px;
}

QMenu::item {
    padding: 8px 20px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #e94560;
}
"""

# ═══════════════════════════════════════════════════════════════════════════════
# CLIPBOARD MONITOR THREAD
# ═══════════════════════════════════════════════════════════════════════════════

class ClipboardMonitor(QThread):
    """Background thread that monitors clipboard changes."""
    
    clip_changed = Signal(str)  # Emits new clipboard content
    
    def __init__(self, clipboard: QClipboard):
        super().__init__()
        self.clipboard = clipboard
        self.running = True
        self.last_content = ""
        
    def run(self):
        """Poll clipboard for changes."""
        while self.running:
            try:
                current = self.clipboard.text()
                if current and current != self.last_content:
                    self.last_content = current
                    self.clip_changed.emit(current)
            except Exception:
                pass
            self.msleep(POLL_INTERVAL)
    
    def stop(self):
        self.running = False
        self.wait()

# ═══════════════════════════════════════════════════════════════════════════════
# CLIP ITEM DATA
# ═══════════════════════════════════════════════════════════════════════════════

class ClipItem:
    """Represents a single clipboard item."""
    
    def __init__(self, content: str, timestamp: str = None, pinned: bool = False):
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()
        self.pinned = pinned
        self.hash = hashlib.md5(content.encode()).hexdigest()[:8]
    
    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "timestamp": self.timestamp,
            "pinned": self.pinned,
            "hash": self.hash
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ClipItem':
        item = cls(
            content=data["content"],
            timestamp=data.get("timestamp"),
            pinned=data.get("pinned", False)
        )
        item.hash = data.get("hash", item.hash)
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
# HISTORY MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class HistoryManager:
    """Manages clipboard history persistence."""
    
    def __init__(self):
        self.items: List[ClipItem] = []
        self._ensure_data_dir()
        self.load()
    
    def _ensure_data_dir(self):
        """Create data directory if needed."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    def load(self):
        """Load history from disk."""
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.items = [ClipItem.from_dict(d) for d in data]
            except Exception as e:
                print(f"⚠️ Failed to load history: {e}")
                self.items = []
    
    def save(self):
        """Save history to disk."""
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump([item.to_dict() for item in self.items], f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save history: {e}")
    
    def add(self, content: str) -> Optional[ClipItem]:
        """Add new clip to history."""
        if not content or not content.strip():
            return None
        
        # Check for duplicates
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        for i, item in enumerate(self.items):
            if item.hash == content_hash:
                # Move to top instead of adding duplicate
                self.items.pop(i)
                break
        
        # Create new item
        item = ClipItem(content)
        self.items.insert(0, item)
        
        # Enforce max history (keep pinned items)
        self._trim_history()
        self.save()
        return item
    
    def _trim_history(self):
        """Remove old items if over limit."""
        pinned = [i for i in self.items if i.pinned]
        unpinned = [i for i in self.items if not i.pinned]
        
        if len(unpinned) > MAX_HISTORY:
            unpinned = unpinned[:MAX_HISTORY]
        
        self.items = pinned + unpinned
    
    def delete(self, item: ClipItem):
        """Delete an item from history."""
        self.items = [i for i in self.items if i.hash != item.hash]
        self.save()
    
    def toggle_pin(self, item: ClipItem):
        """Toggle pin status of an item."""
        for i in self.items:
            if i.hash == item.hash:
                i.pinned = not i.pinned
                break
        self.save()
    
    def search(self, query: str) -> List[ClipItem]:
        """Search history for matching items."""
        if not query:
            return self.items
        
        query = query.lower()
        return [i for i in self.items if query in i.content.lower()]
    
    def clear_unpinned(self):
        """Clear all unpinned items."""
        self.items = [i for i in self.items if i.pinned]
        self.save()

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════════════

class ClipStashWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.history = HistoryManager()
        self.clipboard = QApplication.clipboard()
        self.current_item: Optional[ClipItem] = None
        
        self._setup_ui()
        self._setup_tray()
        self._start_monitor()
        self._refresh_list()
    
    def _setup_ui(self):
        """Build the user interface."""
        self.setWindowTitle(f"{APP_NAME} - Clipboard History")
        self.setMinimumSize(700, 500)
        self.resize(900, 650)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 10)
        layout.setSpacing(15)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("🗂️ ClipStash")
        title.setObjectName("title")
        header.addWidget(title)
        
        header.addStretch()
        
        # Stats label
        self.stats_label = QLabel()
        self.stats_label.setObjectName("subtitle")
        header.addWidget(self.stats_label)
        
        layout.addLayout(header)
        
        # Search bar
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search your clipboard history...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        
        clear_btn = QPushButton("Clear History")
        clear_btn.setObjectName("secondary")
        clear_btn.clicked.connect(self._clear_history)
        search_layout.addWidget(clear_btn)
        
        layout.addLayout(search_layout)
        
        # Main content (splitter)
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: History list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_selected)
        self.list_widget.itemDoubleClicked.connect(self._copy_item)
        left_layout.addWidget(self.list_widget)
        
        splitter.addWidget(left_panel)
        
        # Right: Preview panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        preview_label = QLabel("Preview")
        preview_label.setObjectName("subtitle")
        right_layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Select a clip to preview...")
        right_layout.addWidget(self.preview_text)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.clicked.connect(self._copy_selected)
        btn_layout.addWidget(self.copy_btn)
        
        self.pin_btn = QPushButton("📌 Pin")
        self.pin_btn.setObjectName("secondary")
        self.pin_btn.clicked.connect(self._pin_selected)
        btn_layout.addWidget(self.pin_btn)
        
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setObjectName("secondary")
        self.delete_btn.clicked.connect(self._delete_selected)
        btn_layout.addWidget(self.delete_btn)
        
        right_layout.addLayout(btn_layout)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 300])
        
        layout.addWidget(splitter)
        
        # Status bar
        self.statusBar().showMessage("Monitoring clipboard...")
        
        # Apply theme
        self.setStyleSheet(DARK_THEME)
    
    def _setup_tray(self):
        """Setup system tray icon."""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show ClipStash", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)
        
        # Show tray icon
        self.tray_icon.show()
    
    def _tray_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()
    
    def _start_monitor(self):
        """Start clipboard monitoring."""
        self.monitor = ClipboardMonitor(self.clipboard)
        self.monitor.clip_changed.connect(self._on_clip_changed)
        self.monitor.start()
    
    def _on_clip_changed(self, content: str):
        """Handle new clipboard content."""
        item = self.history.add(content)
        if item:
            self._refresh_list()
            self.statusBar().showMessage(f"Saved: {item.preview(40)}", 3000)
    
    def _refresh_list(self, items: List[ClipItem] = None):
        """Refresh the history list."""
        self.list_widget.clear()
        
        items = items if items is not None else self.history.items
        
        for item in items:
            prefix = "📌 " if item.pinned else ""
            text = f"{prefix}{item.preview(60)}\n{item.formatted_time()}"
            
            list_item = QListWidgetItem(text)
            list_item.setData(Qt.UserRole, item)
            
            if item.pinned:
                list_item.setForeground(QColor("#e94560"))
            
            self.list_widget.addItem(list_item)
        
        # Update stats
        total = len(self.history.items)
        pinned = sum(1 for i in self.history.items if i.pinned)
        self.stats_label.setText(f"{total} clips • {pinned} pinned")
    
    def _on_search(self, query: str):
        """Handle search input."""
        results = self.history.search(query)
        self._refresh_list(results)
    
    def _on_item_selected(self, list_item: QListWidgetItem):
        """Handle item selection."""
        self.current_item = list_item.data(Qt.UserRole)
        if self.current_item:
            self.preview_text.setText(self.current_item.content)
            self.pin_btn.setText("📌 Unpin" if self.current_item.pinned else "📌 Pin")
    
    def _copy_item(self, list_item: QListWidgetItem):
        """Copy item on double-click."""
        item = list_item.data(Qt.UserRole)
        if item:
            self.clipboard.setText(item.content)
            self.statusBar().showMessage("Copied to clipboard!", 2000)
    
    def _copy_selected(self):
        """Copy currently selected item."""
        if self.current_item:
            self.clipboard.setText(self.current_item.content)
            self.statusBar().showMessage("Copied to clipboard!", 2000)
    
    def _pin_selected(self):
        """Toggle pin on selected item."""
        if self.current_item:
            self.history.toggle_pin(self.current_item)
            self._refresh_list()
            self.pin_btn.setText("📌 Unpin" if self.current_item.pinned else "📌 Pin")
    
    def _delete_selected(self):
        """Delete selected item."""
        if self.current_item:
            self.history.delete(self.current_item)
            self.current_item = None
            self.preview_text.clear()
            self._refresh_list()
    
    def _clear_history(self):
        """Clear all unpinned history."""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Clear all unpinned clipboard history?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.history.clear_unpinned()
            self._refresh_list()
            self.statusBar().showMessage("History cleared (pinned items kept)", 3000)
    
    def closeEvent(self, event):
        """Handle window close - minimize to tray."""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "ClipStash",
            "Running in background. Double-click tray icon to open.",
            QSystemTrayIcon.Information,
            2000
        )
    
    def quit_app(self):
        """Properly quit the application."""
        self.monitor.stop()
        self.history.save()
        QApplication.quit()

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point."""
    print(f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           🗂️ ClipStash v{APP_VERSION}                                 ║
║                    Universal Clipboard History Manager                         ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray
    
    # Create and show window
    window = ClipStashWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
