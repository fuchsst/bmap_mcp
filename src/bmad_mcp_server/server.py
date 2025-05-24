"""
BMAD MCP Server - Core server implementation.

This module provides the main BMadMCPServer class that orchestrates
tool execution and protocol handling for the BMAD methodology.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal

from fastmcp import FastMCP
from pydantic import BaseModel

from .utils.state_manager import StateManager
from .utils.logging import setup_logging
from .crewai_integration.config import CrewAIConfig

# Import Pydantic models from tool files
from .tools.planning.project_brief import CreateProjectBriefTool
from .tools.planning.generate_prd import GeneratePRDTool, PRDGenerationRequest
from .tools.planning.validate_requirements import ValidateRequirementsTool, RequirementsValidationRequest
from .tools.architecture.create_architecture import CreateArchitectureTool, ArchitectureRequest, TechPreferences
from .tools.architecture.frontend_architecture import CreateFrontendArchitectureTool, FrontendArchitectureRequest
from .tools.story.create_story import CreateNextStoryTool, CreateStoryRequest, CurrentProgress
from .tools.story.validate_story import ValidateStoryTool, StoryValidationRequest
from .tools.validation.run_checklist import RunChecklistTool, ChecklistRequest, ValidationContext, ChecklistType
from .tools.validation.correct_course import CorrectCourseTool, CorrectCourseRequest, ChangeContext


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
        self.crewai_config = CrewAIConfig() # TODO: Pass LLM configs from server_config to crewai_config
        self.mcp = FastMCP("BMAD-Server", version="1.0.0")
        
        # Setup logging
        log_level = self.config.get("log_level", "INFO")
        log_file = self.config.get("log_file")
        if log_file:
            log_file = Path(log_file)
        setup_logging(level=log_level, log_file=log_file)
        
        # Register all BMAD tools
        self._register_native_tools()
        
        logger.info("BMAD MCP Server initialized successfully")
        logger.info(f"Project root: {self.project_root}")
        # FastMCP handles tool listing, so self.tools might not be needed in the same way
        # logger.info(f"Registered tools via FastMCP decorators") 
    
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

    def _register_native_tools(self) -> None:
        """Register all BMAD tools with FastMCP using explicit function definitions."""

        # --- Planning Tools ---
        @self.mcp.tool()
        async def create_project_brief(
            topic: str,
            target_audience: Optional[str] = "General users",
            constraints: Optional[List[str]] = None, # Handled by Field(default_factory=list) in Pydantic
            scope_level: Literal["minimal", "standard", "comprehensive"] = "standard"
        ) -> Dict[str, Any]:
            """Generate a structured project brief following BMAD methodology."""
            tool_instance = CreateProjectBriefTool(self.state_manager, self.crewai_config)
            # The tool's execute method expects a dict, matching its Pydantic model
            return await tool_instance.execute({
                "topic": topic,
                "target_audience": target_audience,
                "constraints": constraints or [], # Ensure list if None
                "scope_level": scope_level
            })

        @self.mcp.tool()
        async def generate_prd(
            project_brief_content: str, # Renamed from project_brief in original tool schema
            workflow_mode: Literal["incremental", "yolo"] = "incremental",
            technical_depth: Literal["basic", "standard", "detailed"] = "standard",
            include_architecture_prompt: bool = True
        ) -> Dict[str, Any]:
            """Generate comprehensive PRD with epics and user stories from project brief."""
            tool_instance = GeneratePRDTool(self.state_manager, self.crewai_config)
            return await tool_instance.execute({
                "project_brief_content": project_brief_content,
                "workflow_mode": workflow_mode,
                "technical_depth": technical_depth,
                "include_architecture_prompt": include_architecture_prompt
            })

        @self.mcp.tool()
        async def validate_requirements(
            prd_content: str,
            checklist_type: Literal["pm_checklist", "standard", "comprehensive"] = "pm_checklist",
            validation_mode: Literal["strict", "standard", "lenient"] = "standard",
            include_recommendations: bool = True
        ) -> Dict[str, Any]:
            """Validate PRD documents against PM quality checklists."""
            tool_instance = ValidateRequirementsTool(self.state_manager, self.crewai_config)
            return await tool_instance.execute({
                "prd_content": prd_content,
                "checklist_type": checklist_type,
                "validation_mode": validation_mode,
                "include_recommendations": include_recommendations
            })

        # --- Architecture Tools ---
        @self.mcp.tool()
        async def create_architecture(
            prd_content: str,
            tech_preferences: Optional[TechPreferences] = None, # Pydantic model
            architecture_type: Literal["monolith", "modular_monolith", "microservices", "serverless"] = "monolith",
            include_frontend_prompt: bool = True
        ) -> Dict[str, Any]:
            """Generate comprehensive technical architecture from PRD requirements."""
            tool_instance = CreateArchitectureTool(self.state_manager, self.crewai_config)
            # Pass tech_preferences as a dict if not None, else Pydantic model in tool will use default_factory
            tech_prefs_dict = tech_preferences.model_dump() if tech_preferences else {}
            return await tool_instance.execute({
                "prd_content": prd_content,
                "tech_preferences": tech_prefs_dict,
                "architecture_type": architecture_type,
                "include_frontend_prompt": include_frontend_prompt
            })

        @self.mcp.tool()
        async def create_frontend_architecture(
            main_architecture: str,
            ux_specification: Optional[str] = "",
            framework_preference: Optional[Literal["React", "Vue", "Angular", "Svelte", "React Native", "Flutter", ""]] = "",
            component_strategy: Literal["atomic", "modular", "feature-based", "layered"] = "atomic",
            state_management: Optional[Literal["Redux", "Zustand", "Context API", "Vuex", "Pinia", "NgRx", ""]] = ""
        ) -> Dict[str, Any]:
            """Generate frontend-specific architecture specifications."""
            tool_instance = CreateFrontendArchitectureTool(self.state_manager, self.crewai_config)
            return await tool_instance.execute({
                "main_architecture": main_architecture,
                "ux_specification": ux_specification,
                "framework_preference": framework_preference,
                "component_strategy": component_strategy,
                "state_management": state_management
            })

        # --- Story Tools ---
        @self.mcp.tool()
        async def create_next_story(
            prd_content: str,
            architecture_content: str,
            current_progress: Optional[CurrentProgress] = None, # Pydantic model
            story_type: Literal["feature", "bug", "technical", "research", "epic"] = "feature",
            priority: Literal["low", "medium", "high", "critical"] = "medium"
        ) -> Dict[str, Any]:
            """Generate development-ready user stories from PRD epics."""
            tool_instance = CreateNextStoryTool(self.state_manager, self.crewai_config)
            current_progress_dict = current_progress.model_dump() if current_progress else {}
            return await tool_instance.execute({
                "prd_content": prd_content,
                "architecture_content": architecture_content,
                "current_progress": current_progress_dict,
                "story_type": story_type,
                "priority": priority
            })

        @self.mcp.tool()
        async def validate_story(
            story_content: str,
            checklist_types: Optional[List[Literal["story_draft_checklist", "story_dod_checklist", "story_review_checklist"]]] = None,
            validation_mode: Literal["strict", "standard", "lenient"] = "standard",
            story_phase: Literal["draft", "review", "ready", "in_progress", "done"] = "draft"
        ) -> Dict[str, Any]:
            """Validate user stories against Definition of Done checklists."""
            tool_instance = ValidateStoryTool(self.state_manager, self.crewai_config)
            return await tool_instance.execute({
                "story_content": story_content,
                "checklist_types": checklist_types or ["story_draft_checklist"], # Default if None
                "validation_mode": validation_mode,
                "story_phase": story_phase
            })

        # --- Validation Tools ---
        @self.mcp.tool()
        async def run_checklist(
            document_content: str,
            checklist_name: ChecklistType, # Enum
            validation_context: Optional[ValidationContext] = None, # Pydantic model
            validation_mode: Literal["strict", "standard", "lenient"] = "standard"
        ) -> Dict[str, Any]:
            """Execute BMAD quality checklists against documents."""
            tool_instance = RunChecklistTool(self.state_manager, self.crewai_config)
            validation_context_dict = validation_context.model_dump() if validation_context else {}
            return await tool_instance.execute({
                "document_content": document_content,
                "checklist_name": checklist_name.value, # Pass enum value
                "validation_context": validation_context_dict,
                "validation_mode": validation_mode
            })

        @self.mcp.tool()
        async def correct_course(
            current_situation: str,
            desired_outcome: str,
            change_context: ChangeContext, # Pydantic model
            existing_artifacts: Optional[List[str]] = None,
            constraints: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            """Handle change management scenarios and course corrections."""
            tool_instance = CorrectCourseTool(self.state_manager, self.crewai_config)
            return await tool_instance.execute({
                "current_situation": current_situation,
                "desired_outcome": desired_outcome,
                "change_context": change_context.model_dump(), # Pass as dict
                "existing_artifacts": existing_artifacts or [],
                "constraints": constraints or []
            })
        
        logger.info(f"Registered tools.")

    async def run_stdio(self) -> None:
        """Run the server in stdio mode."""
        logger.info("Starting BMAD MCP Server in stdio mode")
        
        try:
            # Use FastMCP's async stdio runner
            await self.mcp.run_stdio_async()
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error in stdio mode: {e}")
            raise
    
    async def run_sse(self, host: str = "localhost", port: int = 8000) -> None:
        """Run the server in Server-Sent Events mode."""
        logger.info(f"Starting BMAD MCP Server in SSE mode on {host}:{port}")
        
        try:
            # Use FastMCP's async HTTP runner
            await self.mcp.run_http_async(transport="streamable-http", host=host, port=port)
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error in SSE mode: {e}")
            raise

    
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
