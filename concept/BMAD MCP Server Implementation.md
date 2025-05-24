# bmad-mcp-server/src/bmad_mcp_server/server.py
"""
BMAD MCP Server - Core server implementation that exposes BMAD methodology as MCP tools.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from pydantic import BaseModel, Field

# MCP Protocol imports (would be from actual MCP library)
from .protocol.schemas import (
    MCPRequest, MCPResponse, MCPError, 
    ToolDefinition, ToolRequest, ToolResponse
)
from .protocol.handlers import MCPProtocolHandler
from .tools.registry import ToolRegistry
from .crewai_integration.config import CrewAIConfig
from .utils.logging import setup_logging

logger = logging.getLogger(__name__)

class BMadMCPServer:
    """
    Core BMAD MCP Server that orchestrates tool execution and protocol handling.
    
    This server exposes BMAD methodology as standardized MCP tools, enabling
    any MCP-compatible AI system to leverage structured project development workflows.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the BMAD MCP Server."""
        self.config = self._load_config(config_path)
        self.tool_registry = ToolRegistry()
        self.protocol_handler = MCPProtocolHandler(self)
        self.crewai_config = CrewAIConfig()
        
        # Setup logging
        setup_logging(self.config.log_level)
        
        # Register all BMAD tools
        self._register_tools()
        
        logger.info("BMAD MCP Server initialized successfully")
    
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
            with open(config_path, 'r') as f:
                user_config = json.load(f)
            default_config.update(user_config)
        
        return default_config
    
    def _register_tools(self) -> None:
        """Register all BMAD tools with the tool registry."""
        from .tools.planning.project_brief import CreateProjectBriefTool
        from .tools.planning.generate_prd import GeneratePRDTool
        from .tools.planning.validate_requirements import ValidateRequirementsTool
        from .tools.architecture.create_architecture import CreateArchitectureTool
        from .tools.architecture.frontend_architecture import CreateFrontendArchitectureTool
        from .tools.story.create_story import CreateNextStoryTool
        from .tools.validation.run_checklist import RunChecklistTool
        
        # Register planning tools
        self.tool_registry.register(CreateProjectBriefTool())
        self.tool_registry.register(GeneratePRDTool())
        self.tool_registry.register(ValidateRequirementsTool())
        
        # Register architecture tools
        self.tool_registry.register(CreateArchitectureTool())
        self.tool_registry.register(CreateFrontendArchitectureTool())
        
        # Register story tools
        self.tool_registry.register(CreateNextStoryTool())
        
        # Register validation tools
        self.tool_registry.register(RunChecklistTool())
        
        logger.info(f"Registered {len(self.tool_registry.tools)} BMAD tools")
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle incoming MCP requests."""
        try:
            method = request.method
            
            if method == "list_tools":
                return await self._handle_list_tools(request)
            elif method == "call_tool":
                return await self._handle_call_tool(request)
            else:
                raise MCPError(f"Unknown method: {method}", code=-32601)
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return MCPResponse(
                id=request.id,
                error=MCPError(str(e), code=-32603)
            )
    
    async def _handle_list_tools(self, request: MCPRequest) -> MCPResponse:
        """Handle tool listing requests."""
        tools = []
        for tool in self.tool_registry.tools.values():
            tools.append(ToolDefinition(
                name=tool.name,
                description=tool.description,
                inputSchema=tool.get_input_schema()
            ))
        
        return MCPResponse(
            id=request.id,
            result={"tools": [tool.dict() for tool in tools]}
        )
    
    async def _handle_call_tool(self, request: MCPRequest) -> MCPResponse:
        """Handle tool execution requests."""
        tool_request = ToolRequest(**request.params)
        
        tool = self.tool_registry.get_tool(tool_request.name)
        if not tool:
            logger.error(f"Tool not found: {tool_request.name}")
            return MCPResponse(
                id=request.id,
                error=MCPError(f"Tool not found: {tool_request.name}", code=-32602)
            )
        
        try:
            # Tools now return a dictionary with content, suggested_path, metadata, etc.
            tool_output_dict = await tool.execute(tool_request.arguments)
            
            # The MCP response should ideally structure this dictionary in a way
            # that the assistant can easily parse and present to the user.
            # For example, the main content could be primary, and other details in a structured way.
            # FastMCP might have specific ways to format complex results.
            # For now, we'll pass the dictionary as the main result.
            # The assistant will then need to know how to handle this structure.
            
            # Example: Wrap the dict in a 'structured_artifact' content block type
            # This is a hypothetical MCP content block type.
            # The actual format will depend on what the AI assistant expects
            # or what FastMCP supports for complex return types.
            
            # A simple approach is to return the whole dictionary.
            # The AI assistant would then be responsible for presenting this to the user.
            return MCPResponse(
                id=request.id,
                result=tool_output_dict # The entire dictionary is the result
            )

        except Exception as e:
            logger.error(f"Tool execution failed for {tool_request.name}: {e}", exc_info=True)
            return MCPResponse(
                id=request.id,
                error=MCPError(f"Tool execution failed: {str(e)}", code=-32603)
            )
    
    async def start_stdio(self) -> None:
        """Start the server in stdio mode."""
        logger.info("Starting BMAD MCP Server in stdio mode")
        
        async for line in sys.stdin:
            try:
                request_data = json.loads(line.strip())
                request = MCPRequest(**request_data)
                
                response = await self.handle_request(request)
                
                print(json.dumps(response.dict()))
                sys.stdout.flush()
                
            except Exception as e:
                logger.error(f"Error processing stdio request: {e}")
                error_response = MCPResponse(
                    id=None,
                    error=MCPError(str(e), code=-32700)
                )
                print(json.dumps(error_response.dict()))
                sys.stdout.flush()
    
    async def start_sse(self, host: str = "localhost", port: int = 8000) -> None:
        """Start the server in Server-Sent Events mode."""
        from fastapi import FastAPI, Request
        from fastapi.responses import StreamingResponse
        import uvicorn
        
        app = FastAPI(title="BMAD MCP Server", version="1.0.0")
        
        @app.post("/mcp")
        async def handle_mcp_request(request: Request):
            """Handle MCP requests via HTTP."""
            request_data = await request.json()
            mcp_request = MCPRequest(**request_data)
            
            response = await self.handle_request(mcp_request)
            return response.dict()
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "tools": len(self.tool_registry.tools)}
        
        logger.info(f"Starting BMAD MCP Server in SSE mode on {host}:{port}")
        await uvicorn.run(app, host=host, port=port)


# bmad-mcp-server/src/bmad_mcp_server/tools/base.py
"""
Base classes and interfaces for BMAD MCP tools.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class BMadTool(ABC):
    """Base class for all BMAD MCP tools."""
    
    def __init__(self, state_manager=None): # Accept StateManager if needed for reading context
        self.name = self.__class__.__name__.lower().replace('tool', '')
        self.description = self.__doc__ or "BMAD tool"
        self.category = "general"
        self.state_manager = state_manager # Store if provided, for reading context

    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]: # Return type is now Dict
        """
        Execute the tool with given arguments.
        Should return a dictionary containing:
        - 'content': The generated artifact content (e.g., Markdown string).
        - 'suggested_path': A string suggesting where the artifact might be saved (relative to .bmad).
        - 'metadata': A dictionary of metadata for the artifact (e.g., type, status).
        - 'message': (Optional) A message for the user/assistant.
        """
        pass
    
    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for tool input validation."""
        pass
    
    def validate_input(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize input arguments."""
        # Base validation logic here
        return arguments


# bmad-mcp-server/src/bmad_mcp_server/tools/registry.py
"""
Tool registry for managing BMAD MCP tools.
"""

from typing import Dict, Optional
from .base import BMadTool

class ToolRegistry:
    """Registry for managing BMAD tools."""
    
    def __init__(self):
        self.tools: Dict[str, BMadTool] = {}
    
    def register(self, tool: BMadTool) -> None:
        """Register a tool."""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[BMadTool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def list_tools(self) -> Dict[str, BMadTool]:
        """List all registered tools."""
        return self.tools.copy()


# bmad-mcp-server/src/bmad_mcp_server/tools/planning/project_brief.py
"""
Project Brief creation tool using BMAD methodology.
"""

import json
from typing import Any, Dict
from crewai import Agent, Crew, Task, Process
from ...tools.base import BMadTool
from ...crewai_integration.agents import get_analyst_agent
from ...templates.loader import load_template

class CreateProjectBriefTool(BMadTool):
    """
    Generate a structured project brief following BMAD methodology.
    
    This tool uses the BMAD Analyst agent to create comprehensive project briefs
    that serve as the foundation for subsequent PRD and architecture work.
    """
    
    def __init__(self, state_manager=None):
        super().__init__(state_manager) # Pass state_manager to base
        self.category = "planning"
        self.description = "Generates content for a structured project brief using BMAD methodology. Does not write files."
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for project brief creation."""
        return {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The main topic or idea for the project"
                },
                "target_audience": {
                    "type": "string",
                    "description": "Target audience or users for the project",
                    "default": "General users"
                },
                "constraints": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Known constraints, preferences, or requirements",
                    "default": []
                },
                "scope_level": {
                    "type": "string",
                    "enum": ["minimal", "standard", "comprehensive"],
                    "description": "Desired scope level for the brief",
                    "default": "standard"
                }
            },
            "required": ["topic"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project brief creation, returning content and suggestions."""
        validated_args = self.validate_input(arguments)
        
        topic = validated_args["topic"]
        target_audience = validated_args.get("target_audience", "General users")
        constraints = validated_args.get("constraints", [])
        scope_level = validated_args.get("scope_level", "standard")

        project_name = "UnknownProject"
        if self.state_manager:
            project_meta = self.state_manager.get_project_meta()
            project_name = project_meta.get("project_name", project_name)
        
        template_name = "project_brief_tmpl.md"
        try:
            template_content = load_template(template_name)
        except FileNotFoundError:
            logger.warning(f"Template {template_name} not found. Using default prompt structure.")
            template_content = "Default template: Introduction, Vision, Goals, Audience, Features, Constraints."

        analyst = get_analyst_agent()
        
        brief_task = Task(
            description=f"""
            Create a comprehensive project brief for the topic: '{topic}' for project '{project_name}'.
            Target audience: {target_audience}
            Known constraints: {', '.join(constraints) if constraints else 'None specified'}
            Scope level: {scope_level}
            
            Follow this template structure:
            {template_content}
            
            Ensure the brief is detailed enough to guide PRD creation and provides
            clear direction for the project scope and objectives.
            """,
            expected_output="Complete project brief in markdown format.",
            agent=analyst
        )
        
        crew = Crew(agents=[analyst], tasks=[brief_task], process=Process.sequential, verbose=False)
        result_content = crew.kickoff() # Assuming result is the raw string content
        
        # Prepare the structured response
        file_name_safe_topic = topic.lower().replace(' ', '_').replace('.', '').replace('/', '_')
        suggested_path = f"ideation/project_brief_{file_name_safe_topic}.md"

        suggested_metadata = {
            "artifact_type": "project_brief",
            "status": "draft",
            "topic": topic,
            "target_audience": target_audience,
            "scope_level": scope_level,
            "source_template": template_name,
            "generated_by_tool": self.name,
            "timestamp": datetime.now().isoformat()
        }
        
        # No direct file writing by the tool
        # formatted_brief = self._format_project_brief(result_content, topic) # Formatting can be part of the agent's task or assistant's responsibility

        return {
            "content": result_content, # Raw content from CrewAI
            "suggested_path": suggested_path,
            "metadata": suggested_metadata,
            "message": f"Project brief content for '{topic}' generated. Please review and save to the suggested path or your preferred location within the .bmad directory."
        }
    
    # _format_project_brief method might be removed or adapted if formatting is handled by CrewAI or client-side.
    # For now, the raw content from CrewAI is returned.

# bmad-mcp-server/src/bmad_mcp_server/crewai_integration/agents.py
"""
BMAD agent definitions for CrewAI integration.
"""

from crewai import Agent
from typing import Optional

def get_analyst_agent(llm_model: Optional[str] = None) -> Agent:
    """Get configured BMAD Analyst agent."""
    return Agent(
        role="Senior Research Specialist and Business Analyst",
        goal="Conduct thorough analysis and create comprehensive project documentation that establishes clear foundations for development",
        backstory="""You are an experienced analyst with a talent for understanding complex business requirements
        and translating them into clear, actionable project documentation. You excel at asking the right questions,
        identifying key constraints and opportunities, and structuring information in a way that guides successful
        project execution. You follow the BMAD methodology strictly and ensure all outputs meet quality standards.""",
        verbose=True,
        llm=llm_model
    )

def get_pm_agent(llm_model: Optional[str] = None) -> Agent:
    """Get configured BMAD Product Manager agent."""
    return Agent(
        role="Senior Product Manager and Requirements Specialist",
        goal="Transform project briefs into comprehensive PRDs with well-structured epics and user stories",
        backstory="""You are a seasoned product manager with deep expertise in requirement gathering and
        product definition. You excel at breaking down complex projects into manageable epics and stories,
        ensuring clear acceptance criteria, and maintaining focus on MVP goals. You follow BMAD methodology
        principles and create PRDs that serve as solid foundations for architecture and development work.""",
        verbose=True,
        llm=llm_model
    )

def get_architect_agent(llm_model: Optional[str] = None) -> Agent:
    """Get configured BMAD Architect agent."""
    return Agent(
        role="Senior Software Architect and Technical Leader",
        goal="Design robust, scalable technical architectures that meet all requirements and follow best practices",
        backstory="""You are an experienced software architect with expertise in designing systems that are
        maintainable, scalable, and aligned with business requirements. You excel at making clear technical
        decisions, documenting architectural patterns, and ensuring designs are optimized for AI-agent
        implementation. You follow BMAD architecture principles and create documentation that enables
        successful development execution.""",
        verbose=True,
        llm=llm_model
    )


# bmad-mcp-server/src/bmad_mcp_server/templates/loader.py
"""
Template loading and management for BMAD documents.
"""

from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent

# Template cache
_template_cache: Dict[str, str] = {}

def load_template(template_name: str) -> str:
    """Load a BMAD template by name."""
    if template_name in _template_cache:
        return _template_cache[template_name]
    
    template_path = TEMPLATE_DIR / template_name
    
    if not template_path.exists():
        logger.error(f"Template not found: {template_name}")
        raise FileNotFoundError(f"Template not found: {template_name}")
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        _template_cache[template_name] = content
        logger.debug(f"Loaded template: {template_name}")
        return content
        
    except Exception as e:
        logger.error(f"Error loading template {template_name}: {e}")
        raise

def list_templates() -> list[str]:
    """List available templates."""
    return [f.name for f in TEMPLATE_DIR.glob("*.md")]


# bmad-mcp-server/src/bmad_mcp_server/protocol/schemas.py
"""
MCP protocol schemas and data models.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class MCPRequest(BaseModel):
    """MCP request message."""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: str
    params: Optional[Dict[str, Any]] = None

class MCPError(BaseModel):
    """MCP error response."""
    code: int
    message: str
    data: Optional[Any] = None

class MCPResponse(BaseModel):
    """MCP response message."""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Any] = None
    error: Optional[MCPError] = None

class ToolDefinition(BaseModel):
    """Tool definition for MCP."""
    name: str
    description: str
    inputSchema: Dict[str, Any]

class ToolRequest(BaseModel):
    """Tool execution request."""
    name: str
    arguments: Dict[str, Any]

class ToolResponse(BaseModel):
    """Tool execution response."""
    content: List[Dict[str, Any]]
    isError: bool = False


# bmad-mcp-server/src/bmad_mcp_server/protocol/handlers.py
"""
MCP protocol handlers for different transport mechanisms.
"""

import logging
from typing import Any
from .schemas import MCPRequest, MCPResponse

logger = logging.getLogger(__name__)

class MCPProtocolHandler:
    """Handles MCP protocol message processing."""
    
    def __init__(self, server):
        self.server = server
    
    async def handle_message(self, message: dict) -> dict:
        """Handle incoming MCP message."""
        try:
            request = MCPRequest(**message)
            response = await self.server.handle_request(request)
            return response.dict()
        except Exception as e:
            logger.error(f"Protocol handler error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }


# bmad-mcp-server/src/bmad_mcp_server/main.py
"""
Main entry point for BMAD MCP Server.
"""

import asyncio
import sys
import argparse
from pathlib import Path
from .server import BMadMCPServer

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="BMAD MCP Server")
    parser.add_argument("--mode", choices=["stdio", "sse"], default="stdio",
                       help="Transport mode")
    parser.add_argument("--host", default="localhost",
                       help="Host for SSE mode")
    parser.add_argument("--port", type=int, default=8000,
                       help="Port for SSE mode")
    parser.add_argument("--config", type=Path,
                       help="Configuration file path")
    
    args = parser.parse_args()
    
    # Create server
    server = BMadMCPServer(config_path=args.config)
    
    # Start server in requested mode
    if args.mode == "stdio":
        await server.start_stdio()
    elif args.mode == "sse":
        await server.start_sse(host=args.host, port=args.port)

if __name__ == "__main__":
    asyncio.run(main())
