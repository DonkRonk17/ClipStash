<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/47fd28d7-ae80-4557-8233-7e853c737461" />

# 🗂️ ClipStash - Universal Clipboard History Manager

**Never lose a copied item again!** ClipStash is a lightweight, cross-platform clipboard history manager with a beautiful dark-themed UI.

![ClipStash Screenshot](https://img.shields.io/badge/version-1.0.0-e94560?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.8+-blue?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)

## ✨ Features

- **📋 Automatic History** - Saves everything you copy automatically
- **🔍 Instant Search** - Find any clip instantly with fuzzy search
- **📌 Pin Important Items** - Keep critical clips forever
- **🌙 Beautiful Dark Theme** - Easy on the eyes, day or night
- **🖥️ System Tray** - Runs quietly in background
- **💾 Persistent Storage** - History survives restarts
- **🚀 Lightweight** - Uses minimal system resources
- **🌐 Cross-Platform** - Works on Windows, Mac, and Linux

## 🚀 Quick Start

### Option 1: One-Line Install (Recommended)

```bash
pip install PySide6 && python clipstash.py
```

### Option 2: Full Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DonkRonk17/ClipStash.git
   cd ClipStash
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run ClipStash:**
   ```bash
   python clipstash.py
   ```

## 📖 Usage

### Basic Operations

| Action | How |
|--------|-----|
| **Copy to clipboard** | Double-click any item in the list |
| **Preview content** | Single-click to see full content |
| **Pin an item** | Select item → Click "📌 Pin" |
| **Delete an item** | Select item → Click "🗑️ Delete" |
| **Search history** | Type in the search box |
| **Clear history** | Click "Clear History" (keeps pinned items) |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+F` | Focus search box |
| `Enter` | Copy selected item |
| `Delete` | Delete selected item |
| `Escape` | Minimize to tray |

### System Tray

ClipStash runs in your system tray when minimized:
- **Double-click** the tray icon to open
- **Right-click** for menu options
- Close the window to minimize (doesn't quit)

## 🎨 Screenshots

```
╔═══════════════════════════════════════════════════════════════╗
║  🗂️ ClipStash                          42 clips • 3 pinned   ║
╠═══════════════════════════════════════════════════════════════╣
║  🔍 Search your clipboard history...                          ║
╠═══════════════════════════════════════════════════════════════╣
║  ┌──────────────────────┐  ┌─────────────────────────────────┐║
║  │ 📌 Important API key │  │ Preview                         │║
║  │ Just now             │  │                                 │║
║  ├──────────────────────┤  │ sk-abc123...                    │║
║  │ Hello World code...  │  │                                 │║
║  │ 5m ago               │  │                                 │║
║  ├──────────────────────┤  │                                 │║
║  │ Meeting notes from...│  ├─────────────────────────────────┤║
║  │ 2h ago               │  │ [📋 Copy] [📌 Pin] [🗑️ Delete] │║
║  └──────────────────────┘  └─────────────────────────────────┘║
╚═══════════════════════════════════════════════════════════════╝
```

## 📁 Data Storage

ClipStash stores your clipboard history at:

| Platform | Location |
|----------|----------|
| **Windows** | `C:\Users\<you>\.clipstash\history.json` |
| **Mac** | `/Users/<you>/.clipstash/history.json` |
| **Linux** | `/home/<you>/.clipstash/history.json` |

### Configuration

Edit the constants at the top of `clipstash.py`:

```python
MAX_HISTORY = 500      # Maximum clips to keep
POLL_INTERVAL = 500    # Clipboard check interval (ms)
```

## 🔧 Requirements

- Python 3.8 or higher
- PySide6 (Qt6 for Python)

### Installing Python

**Windows:**
```bash
# Download from python.org or use winget:
winget install Python.Python.3.12
```

**Mac:**
```bash
brew install python@3.12
```

**Linux:**
```bash
sudo apt install python3 python3-pip  # Ubuntu/Debian
sudo dnf install python3 python3-pip  # Fedora
```

## 🤔 FAQ

**Q: Does ClipStash see my passwords?**
> ClipStash stores everything you copy locally on your machine. It never sends data anywhere. You can delete sensitive items manually or clear history.

**Q: How do I make it start automatically?**
> **Windows:** Add a shortcut to `shell:startup`
> **Mac:** Add to Login Items in System Preferences
> **Linux:** Add to your desktop environment's autostart

**Q: Can I sync across devices?**
> Not yet, but you can manually copy the history.json file. Cloud sync is planned for v2.0.

**Q: Why PySide6 instead of tkinter?**
> PySide6 provides a modern, native-looking UI with better performance and more features.

## 🛠️ Development

### Project Structure

```
ClipStash/
├── clipstash.py      # Main application
├── requirements.txt  # Python dependencies
├── README.md         # This file
└── LICENSE           # MIT License
```
<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/ca354e9a-5677-4161-990a-4427b3810c2b" />

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Credits

Created by **Logan Smith / Team Brain** at [Metaphy LLC](https://metaphysicsandcomputing.com)

Part of the HMSS (Heavenly Morning Star System) ecosystem.

---

**⭐ Star this repo if ClipStash saves your day!**

[Report Bug](https://github.com/DonkRonk17/ClipStash/issues) • [Request Feature](https://github.com/DonkRonk17/ClipStash/issues)
