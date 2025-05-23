"""
BMAD MCP Server - Expose BMAD methodology as standardized tools for AI systems.

This package provides a Model Context Protocol (MCP) server that bridges the
BMAD (Breakthrough Method of Agile AI-driven Development) methodology with
AI systems through standardized tools and workflows.
"""

__version__ = "1.0.0"
__author__ = "BMAD Project"
__email__ = "info@bmadcode.com"

from .server import BMadMCPServer

__all__ = ["BMadMCPServer"]
