"""Add the project root to sys.path so tests can import agent, tools, rag, etc."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
