"""Pytest configuration for all tests"""

import sys
import os
from pathlib import Path

# Add agent_service to path so relative imports work
agent_service_path = Path(__file__).parent.parent / "agent_service"
if str(agent_service_path) not in sys.path:
    sys.path.insert(0, str(agent_service_path))
