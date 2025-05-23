#!/usr/bin/env python3
"""
Startup script for BMAD MCP Server in stdio mode.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bmad_mcp_server.main import main

if __name__ == "__main__":
    # Force stdio mode
    sys.argv = [sys.argv[0], "--mode", "stdio"]
    asyncio.run(main())
