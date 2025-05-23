"""
BMAD MCP Server - Core server implementation.

This module provides the main BMadMCPServer class that orchestrates
tool execution and protocol handling for the BMAD methodology.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from .utils.state_manager import StateManager
from .utils.logging import setup_logging
from .crewai_integration.config import CrewAIConfig
from .tools.base import BMadTool

logger = logging.getLogger(__name__)


class BMadMCPServer:
    """
    Core BMAD MCP Server that orchestrates tool execution and protocol handling.
    
    This server exposes BMAD methodology as standardized MCP tools, enabling
    any MCP-compatible AI system to leverage structured project development workflows.
    """
    
    def __init__(self, config_path: Optional[Path] = None, project_root: Optional[Path] = None):
        """
        Initialize the BMAD MCP Server.
        
        Args:
            config_path: Optional path to configuration file
            project_root: Optional project root directory for state management
        """
        self.config = self._load_config(config_path)
        self.project_root = project_root or Path.cwd()
        
        # Initialize components
        self.state_manager = StateManager(project_root=self.project_root)
        self.crewai_config = CrewAIConfig()
        self.mcp = FastMCP("BMAD-Server", version="1.0.0")
        
        # Tool registry
        self.tools: Dict[str, BMadTool] = {}
        
        # Setup logging
        log_level = self.config.get("log_level", "INFO")
        log_file = self.config.get("log_file")
        if log_file:
            log_file = Path(log_file)
        setup_logging(level=log_level, log_file=log_file)
        
        # Register all BMAD tools
        self._register_tools()
        
        logger.info("BMAD MCP Server initialized successfully")
        logger.info(f"Project root: {self.project_root}")
        logger.info(f"Registered {len(self.tools)} BMAD tools")
    
    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """Load server configuration."""
        default_config = {
            "log_level": "INFO",
            "max_concurrent_tools": 5,
            "tool_timeout_seconds": 300,
            "enable_stdio": True,
            "enable_sse": True,
            "sse_host": "localhost",
            "sse_port": 8000
        }
        
        if config_path and config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return default_config
    
    def _register_tools(self) -> None:
        """Register all BMAD tools with the MCP server."""
        # Import tools here to avoid circular imports
        from .tools.planning.project_brief import CreateProjectBriefTool
        from .tools.planning.generate_prd import GeneratePRDTool
        from .tools.planning.validate_requirements import ValidateRequirementsTool
        from .tools.architecture.create_architecture import CreateArchitectureTool
        from .tools.architecture.frontend_architecture import CreateFrontendArchitectureTool
        from .tools.story.create_story import CreateNextStoryTool
        from .tools.story.validate_story import ValidateStoryTool
        from .tools.validation.run_checklist import RunChecklistTool
        from .tools.validation.correct_course import CorrectCourseTool
        
        # Register planning tools
        self._register_tool(CreateProjectBriefTool(self.state_manager))
        self._register_tool(GeneratePRDTool(self.state_manager))
        self._register_tool(ValidateRequirementsTool(self.state_manager))
        
        # Register architecture tools
        self._register_tool(CreateArchitectureTool(self.state_manager))
        self._register_tool(CreateFrontendArchitectureTool(self.state_manager))
        
        # Register story tools
        self._register_tool(CreateNextStoryTool(self.state_manager))
        self._register_tool(ValidateStoryTool(self.state_manager))
        
        # Register validation tools
        self._register_tool(RunChecklistTool(self.state_manager))
        self._register_tool(CorrectCourseTool(self.state_manager))
        
        logger.info(f"Registered {len(self.tools)} BMAD tools")
    
    def _register_tool(self, tool: BMadTool) -> None:
        """Register a single tool with the MCP server."""
        self.tools[tool.name] = tool
        
        # Create MCP tool wrapper
        @self.mcp.tool(
            name=tool.name,
            description=tool.description,
            schema=tool.get_input_schema()
        )
        async def mcp_tool_wrapper(**kwargs):
            try:
                # Validate input
                validated_args = tool.validate_input(kwargs)
                
                # Execute tool
                result = await tool.execute(validated_args)
                
                logger.info(f"Tool {tool.name} executed successfully")
                return result
                
            except Exception as e:
                logger.error(f"Tool {tool.name} execution failed: {e}")
                raise
        
        # Store reference to wrapper for potential cleanup
        setattr(self, f"_tool_wrapper_{tool.name}", mcp_tool_wrapper)
        
        logger.debug(f"Registered tool: {tool.name}")
    
    async def run_stdio(self) -> None:
        """Run the server in stdio mode."""
        logger.info("Starting BMAD MCP Server in stdio mode")
        
        try:
            # FastMCP handles stdio communication
            await self.mcp.run_stdio()
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error in stdio mode: {e}")
            raise
    
    async def run_sse(self, host: str = "localhost", port: int = 8000) -> None:
        """Run the server in Server-Sent Events mode."""
        logger.info(f"Starting BMAD MCP Server in SSE mode on {host}:{port}")
        
        try:
            # FastMCP handles SSE communication
            await self.mcp.run_sse(host=host, port=port)
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error in SSE mode: {e}")
            raise
    
    def get_tool_info(self) -> List[Dict[str, Any]]:
        """Get information about all registered tools."""
        return [tool.get_tool_info() for tool in self.tools.values()]
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information and status."""
        return {
            "name": "BMAD MCP Server",
            "version": "1.0.0",
            "project_root": str(self.project_root),
            "bmad_dir": str(self.state_manager.get_bmad_dir()),
            "registered_tools": len(self.tools),
            "tool_names": list(self.tools.keys()),
            "config": {
                "log_level": self.config.get("log_level"),
                "max_concurrent_tools": self.config.get("max_concurrent_tools"),
                "tool_timeout_seconds": self.config.get("tool_timeout_seconds")
            }
        }
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the server."""
        logger.info("Shutting down BMAD MCP Server")
        
        # Cleanup tasks
        try:
            # Cancel any pending tasks
            tasks = [task for task in asyncio.all_tasks() if not task.done()]
            if tasks:
                logger.info(f"Cancelling {len(tasks)} pending tasks")
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.warning(f"Error during shutdown: {e}")
        
        logger.info("BMAD MCP Server shutdown complete")
