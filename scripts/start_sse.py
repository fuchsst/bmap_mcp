#!/usr/bin/env python3
"""
Startup script for BMAD MCP Server in SSE mode.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bmad_mcp_server.main import main

if __name__ == "__main__":
    # Force SSE mode with default settings
    sys.argv = [sys.argv[0], "--mode", "sse", "--host", "0.0.0.0", "--port", "8000"]
    asyncio.run(main())
