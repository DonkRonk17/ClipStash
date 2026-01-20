"""
ClipStash Test Suite

Run tests with: pytest tests/
Run with coverage: pytest --cov=. tests/
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
