Okay, I can outline the project structure and key Python code for a BMAD MCP server based on the provided implementation guide.

The BMAD MCP Server is designed to expose the BMAD methodology as a set of standardized tools, allowing AI systems to interact with structured project development workflows. It utilizes Python, CrewAI for agent orchestration, and FastMCP for handling the Model Context Protocol. Artifacts and project state are managed within a `.bmad` directory in the project root, primarily using Markdown and JSON files.

---
## Project Structure 🏗️

Here's the anticipated directory layout for the `bmad-mcp-server`:

```
bmad-mcp-server/
├── pyproject.toml                # Project metadata, dependencies, and build configuration
├── README.md                     # Project overview and setup instructions
├── config.json                   # Optional server configuration file (e.g., log level, LLM keys)
├── instruction.md                # Example project-specific instructions for the AI assistant
├── .bmad/                        # Directory for BMAD artifacts, managed by StateManager
│   ├── project_meta.json         # Metadata about the project (phase, name, etc.)
│   ├── prd/                      # Product Requirement Documents
│   ├── stories/                  # User stories
│   ├── architecture/             # Architecture documents
│   ├── decisions/                # Technical decision logs
│   ├── ideation/                 # Ideation notes and project briefs
│   └── checklists/               # BMAD checklists
├── src/
│   └── bmad_mcp_server/
│       ├── __init__.py           # Makes the directory a Python package
│       ├── server.py             # Core BMadMCPServer class implementation
│       ├── main.py               # Main entry point for running the server (CLI)
│       ├── utils/                # Utility modules
│       │   ├── __init__.py
│       │   ├── logging.py        # Logging setup (inferred, used in server.py)
│       │   └── state_manager.py  # Manages BMAD project state and artifacts
│       ├── tools/                # BMAD tools exposed via MCP
│       │   ├── __init__.py
│       │   ├── base.py           # Abstract base class for BMAD tools
│       │   ├── registry.py       # Tool registry (inferred, used in server.py)
│       │   ├── planning/         # Planning-phase tools
│       │   │   ├── __init__.py
│       │   │   ├── project_brief.py
│       │   │   ├── generate_prd.py
│       │   │   └── validate_requirements.py
│       │   ├── architecture/     # Architecture-phase tools
│       │   │   ├── __init__.py
│       │   │   ├── create_architecture.py
│       │   │   └── frontend_architecture.py
│       │   ├── story/            # Story-related tools
│       │   │   ├── __init__.py
│       │   │   ├── create_story.py
│       │   │   └── validate_story.py
│       │   └── validation/       # Validation tools
│       │       ├── __init__.py
│       │       ├── run_checklist.py
│       │       └── correct_course.py
│       ├── crewai_integration/   # CrewAI specific integrations
│       │   ├── __init__.py
│       │   ├── agents.py         # Definitions of CrewAI agents (Analyst, PM, etc.)
│       │   └── config.py         # Configuration for CrewAI (e.g., LLM settings)
│       └── templates/            # Templates for generating artifacts
│           ├── __init__.py
│           ├── loader.py         # Logic to load templates
│           ├── project-brief-tmpl.md # Template for project briefs
│           └── prd-tmpl.md       # Template for PRDs
└── venv/                         # Python virtual environment (recommended)
```

---
## Key Code Components 🐍

### 1. `pyproject.toml`
This file defines project dependencies like `fastmcp`, `crewai`, `pydantic`, `fastapi`, `uvicorn`, `pyyaml`, and LLM SDKs (`openai`, `anthropic`). It also specifies project metadata and scripts, such as the entry point for the server.

```toml
# bmad-mcp-server/pyproject.toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "bmad-mcp-server"
version = "1.0.0"
# ... other metadata ...
dependencies = [
    "fastmcp>=0.1.0",
    "crewai>=0.1.0",
    "pydantic>=2.0.0",
    # ... other dependencies from the implementation guide ...
]

[project.scripts]
bmad-mcp-server = "bmad_mcp_server.main:main"
```
*(Code based on)*

### 2. `src/bmad_mcp_server/server.py`
The `BMadMCPServer` class initializes FastMCP, loads configurations, registers BMAD tools, and handles the server runtime (stdio or SSE).

```python
# bmad-mcp-server/src/bmad_mcp_server/server.py
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from fastmcp import FastMCP
# from .tools.registry import ToolRegistry # Assumed or part of tool registration logic
from .crewai_integration.config import CrewAIConfig
from .utils.logging import setup_logging # Assumed based on usage
from .utils.state_manager import StateManager

logger = logging.getLogger(__name__)

class BMadMCPServer:
    def __init__(self, config_path: Optional[Path] = None):
        self.config = self._load_config(config_path)
        self.mcp = FastMCP("BMAD-Server", version="1.0.0")
        # self.tool_registry = ToolRegistry() # From implementation guide
        self.crewai_config = CrewAIConfig() # From implementation guide
        self.state_manager = StateManager(project_root=Path(self.config.get("project_root", Path.cwd()))) # Adjusted based on guide
        
        setup_logging(self.config.get("log_level", "INFO"))
        self._register_tools()
        logger.info("BMAD MCP Server initialized successfully")

    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        # ... loads server configuration from JSON file or defaults ...
        # Example default config items: log_level, project_root, bmad_dir, crewai_config
        default_config = { # Simplified from guide
            "log_level": "INFO",
            "project_root": str(Path.cwd()), # Ensure string for JSON serializability if saved
            "bmad_dir": ".bmad",
            "crewai_config": {"default_llm": "gpt-4"}
        }
        # ... logic to load from config_path and update defaults ...
        return default_config # Placeholder

    def _register_tools(self) -> None:
        from .tools.planning.project_brief import CreateProjectBriefTool
        from .tools.planning.generate_prd import GeneratePRDTool
        # ... import other tools mentioned in the guide ...

        tools_to_register = [
            CreateProjectBriefTool(self.state_manager),
            GeneratePRDTool(self.state_manager),
            # ... instantiate other tools ...
        ]

        for tool_instance in tools_to_register:
            # self.tool_registry.register(tool_instance) # If using a separate registry
            self._register_mcp_tool(tool_instance)
        logger.info(f"Registered {len(tools_to_register)} BMAD tools")

    def _register_mcp_tool(self, tool_instance):
        @self.mcp.tool(
            name=tool_instance.name,
            description=tool_instance.description,
            schema=tool_instance.get_input_schema()
        )
        async def mcp_tool_wrapper(**kwargs):
            try:
                # Assuming tool.execute is an async method as per FastMCP examples
                result = await tool_instance.execute(kwargs)
                return result
            except Exception as e:
                logger.error(f"Tool {tool_instance.name} execution failed: {e}")
                # FastMCP might handle re-raising or formatting errors
                raise
        # Store a reference to the wrapper if necessary, e.g., setattr(self, f"_tool_wrapper_{tool_instance.name}", mcp_tool_wrapper)


    def run(self, mode: str = "stdio", host: str = "localhost", port: int = 8000):
        if mode == "stdio":
            logger.info("Starting BMAD MCP Server in stdio mode")
            self.mcp.run_stdio()
        elif mode == "sse":
            logger.info(f"Starting BMAD MCP Server in SSE mode on {host}:{port}")
            # self.mcp.run_sse(host=host, port=port) # Assuming FastMCP has run_sse
            # The guide uses run_http_sse for FastMCP, so aligning with that.
            # However, the provided server.py uses self.mcp.run_sse()
            # For consistency with the provided code:
            self.mcp.run_sse(host=host, port=port)


```
*(Code adapted from)*

### 3. `src/bmad_mcp_server/main.py`
This script handles command-line arguments for running the server (e.g., mode, host, port, config path) and starts the `BMadMCPServer`.

```python
# bmad-mcp-server/src/bmad_mcp_server/main.py
import argparse
from pathlib import Path
from .server import BMadMCPServer

def main():
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
    
    server = BMadMCPServer(config_path=args.config)
    server.run(mode=args.mode, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
```
*(Code based on)*

### 4. `src/bmad_mcp_server/utils/state_manager.py`
The `StateManager` class is responsible for all file system interactions within the `.bmad` directory. This includes creating the directory structure, saving and loading artifacts (Markdown with YAML frontmatter, JSON), and managing project metadata like the current BMAD phase.

```python
# bmad-mcp-server/src/bmad_mcp_server/utils/state_manager.py
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List
from datetime import datetime
import yaml

logger = logging.getLogger(__name__)

class StateManager:
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.bmad_dir_name = ".bmad" # As per BMAD-MCP-Concept.md
        self.bmad_dir = self.project_root / self.bmad_dir_name
        self._ensure_structure()

    def _ensure_structure(self):
        # Ensures directories like .bmad/prd, .bmad/stories exist
        directories = [
            self.bmad_dir,
            self.bmad_dir / "prd",
            self.bmad_dir / "stories",
            self.bmad_dir / "architecture",
            self.bmad_dir / "decisions",
            self.bmad_dir / "ideation",
            self.bmad_dir / "checklists", # From implementation guide
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        meta_path = self.bmad_dir / "project_meta.json"
        if not meta_path.exists():
            self._init_project_meta()

    def _init_project_meta(self):
        # Initializes .bmad/project_meta.json
        meta = {
            "project_name": self.project_root.name,
            "bmad_version": "1.0", # From implementation guide
            "created_at": datetime.now().isoformat(), # From implementation guide
            "current_phase": "initialization", # From implementation guide
            "artifact_paths": { # From implementation guide
                "prd": "prd/",
                "stories": "stories/",
                "architecture": "architecture/",
                "decisions": "decisions/",
                "ideation": "ideation/"
            }
        }
        self.save_json("project_meta.json", meta) # Uses relative path to bmad_dir

    def save_artifact(self, path_in_bmad: str, content: str, metadata: Optional[Dict] = None) -> str:
        # Saves artifact, adds YAML frontmatter if .md and metadata provided
        full_path = self.bmad_dir / path_in_bmad
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        if metadata and path_in_bmad.endswith('.md'):
            frontmatter_str = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
            file_content = f"---\n{frontmatter_str}---\n\n{content}"
        else:
            file_content = content
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        logger.info(f"Saved artifact: {path_in_bmad}")
        return str(full_path) # Returns absolute path

    def load_artifact(self, path_in_bmad: str) -> Dict[str, Any]:
        # Loads artifact, parses YAML frontmatter if .md
        full_path = self.bmad_dir / path_in_bmad
        if not full_path.exists():
            raise FileNotFoundError(f"Artifact not found: {path_in_bmad}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        
        parsed_metadata = {}
        main_content = raw_content
        if path_in_bmad.endswith('.md'):
            if raw_content.startswith('---'):
                parts = raw_content.split('---', 2)
                if len(parts) >= 3:
                    parsed_metadata = yaml.safe_load(parts[1])
                    main_content = parts[2].strip()
        
        return {"content": main_content, "metadata": parsed_metadata, "path": str(full_path)}

    def save_json(self, path_in_bmad: str, data: Dict[str, Any]) -> str:
        # Saves JSON data to a file within .bmad directory
        full_path = self.bmad_dir / path_in_bmad
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return str(full_path)

    def load_json(self, path_in_bmad: str) -> Dict[str, Any]:
        # Loads JSON data from a file within .bmad directory
        full_path = self.bmad_dir / path_in_bmad
        if not full_path.exists():
            raise FileNotFoundError(f"JSON file not found: {path_in_bmad}")
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def update_project_phase(self, phase: str) -> None: #
        meta = self.load_json("project_meta.json")
        meta["current_phase"] = phase
        meta["phase_updated_at"] = datetime.now().isoformat()
        self.save_json("project_meta.json", meta)

    def get_project_meta(self) -> Dict[str, Any]: #
        return self.load_json("project_meta.json")

```
*(Code adapted from)*

### 5. `src/bmad_mcp_server/tools/base.py`
The `BMadTool` abstract base class defines the interface for all BMAD tools, including `name`, `description`, an `execute` method, and `get_input_schema` for MCP compatibility. It also includes helper methods like `create_metadata`.

```python
# bmad-mcp-server/src/bmad_mcp_server/tools/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime
from ..utils.state_manager import StateManager # Relative import

class BMadTool(ABC):
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        # Tool name derived from class name, e.g., CreateProjectBriefTool -> createprojectbrief
        self.name = self.__class__.__name__.lower().replace('tool', '')
        self.description = self.__doc__ or f"BMAD {self.name} tool" # Default description
        self.category = "general" # Default category, can be overridden by subclasses

    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> Any: # Return type can be more specific
        pass

    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        # Returns JSON schema for tool's input parameters
        pass
    
    def create_metadata(self, status: str = "draft", **kwargs) -> Dict[str, Any]: #
        """Create standard metadata for artifacts."""
        metadata = {
            "status": status,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "created_by": "BMAD-MCP-Server", # From implementation guide
            "bmad_version": "1.0" # From implementation guide
        }
        metadata.update(kwargs)
        return metadata

```
*(Code adapted from)*

### 6. Example Tool: `src/bmad_mcp_server/tools/planning/project_brief.py`
Each tool (e.g., `CreateProjectBriefTool`, `GeneratePRDTool`) inherits from `BMadTool`. It defines its specific input schema and implements the `execute` method, often leveraging CrewAI agents and tasks to perform its function and then using the `StateManager` to save the resulting artifact.

```python
# bmad-mcp-server/src/bmad_mcp_server/tools/planning/project_brief.py
from typing import Any, Dict
from crewai import Agent, Task, Crew, Process # Assuming these are the core CrewAI components needed

from ..base import BMadTool
from ...crewai_integration.agents import get_analyst_agent # Assumes this function exists
from ...templates.loader import load_template # Assumes this function exists
from ...utils.state_manager import StateManager


class CreateProjectBriefTool(BMadTool):
    """
    Generate a structured project brief following BMAD methodology.
    Uses the BMAD Analyst agent for creation.
    """
    
    def __init__(self, state_manager: StateManager): # StateManager passed from server
        super().__init__(state_manager)
        self.category = "planning"
        # self.description is inherited from docstring if not set explicitly

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Main topic for the project"},
                "target_audience": {"type": "string", "description": "Target audience"},
                "constraints": {"type": "array", "items": {"type": "string"}, "description": "Known constraints"},
                "scope_level": {
                    "type": "string", 
                    "enum": ["minimal", "standard", "comprehensive"], 
                    "default": "standard",
                    "description": "Desired scope level"
                }
            },
            "required": ["topic"]
        }

    async def execute(self, arguments: Dict[str, Any]) -> str: # Returns the generated brief content
        topic = arguments["topic"]
        target_audience = arguments.get("target_audience", "General users")
        constraints = arguments.get("constraints", [])
        scope_level = arguments.get("scope_level", "standard")

        analyst_agent = get_analyst_agent() # Get pre-configured CrewAI agent
        
        # Load a template for the brief, e.g., from .templates/project-brief-tmpl.md
        brief_template = load_template("project-brief-tmpl.md")

        # Define the CrewAI task
        task_description = f"""
        Create a comprehensive project brief for the topic: '{topic}'.
        Target Audience: {target_audience}
        Constraints: {', '.join(constraints) if constraints else 'None'}
        Scope Level: {scope_level}
        Use the following template structure:
        {brief_template}
        Fill all sections thoughtfully to guide PRD creation.
        """
        brief_task = Task(
            description=task_description,
            expected_output="A complete project brief in Markdown format.",
            agent=analyst_agent
        )

        # Create and run the Crew
        project_crew = Crew(
            agents=[analyst_agent],
            tasks=[brief_task],
            process=Process.sequential,
            verbose=False # Or configure via server config
        )
        
        # The kickoff method in CrewAI might be synchronous or need await depending on version/setup.
        # Assuming kickoff is synchronous and result.raw contains the string output as per the guide
        crew_result = project_crew.kickoff() 
        generated_brief_content = crew_result # Or crew_result.raw if it's an object

        # Save the artifact using StateManager
        metadata = self.create_metadata(
            status="completed", 
            topic=topic, 
            target_audience=target_audience,
            scope_level=scope_level
        )
        # Define a standardized path within .bmad, e.g., ideation/project_brief_TOPIC.md
        file_name = f"project_brief_{topic.lower().replace(' ', '_').replace('.', '')}.md"
        artifact_path_in_bmad = f"ideation/{file_name}"
        
        self.state_manager.save_artifact(artifact_path_in_bmad, generated_brief_content, metadata)
        self.state_manager.update_project_phase("project_brief_completed") #

        return generated_brief_content # Return the content for the MCP response
```
*(Code adapted from)*

### 7. `src/bmad_mcp_server/crewai_integration/agents.py`
This file would define functions to instantiate and configure various CrewAI agents (e.g., `get_analyst_agent`, `get_pm_agent`) with their specific roles, goals, backstories, and tools (which might include other BMAD MCP tools or general-purpose Python functions).

```python
# bmad-mcp-server/src/bmad_mcp_server/crewai_integration/agents.py
from crewai import Agent
# from crewai_tools import SerperDevTool, WebsiteSearchTool # Example tools an agent might have

# Global LLM configuration (can be loaded from CrewAIConfig or server config)
# For example: llm = ChatOpenAI(model_name="gpt-4", temperature=0.7)

def get_analyst_agent(llm=None): # llm can be passed for flexibility
    return Agent(
        role="BMAD Business Analyst",
        goal="Analyze project requirements and generate comprehensive project briefs and initial documentation.",
        backstory=(
            "You are an expert Business Analyst specialized in the BMAD methodology. "
            "Your primary function is to elicit and document project needs clearly, "
            "ensuring a solid foundation for development."
        ),
        # tools=[SerperDevTool(), WebsiteSearchTool()], # Example tools
        llm=llm, # Pass the configured LLM
        allow_delegation=False,
        verbose=True
    )

def get_pm_agent(llm=None):
    return Agent(
        role="BMAD Product Manager",
        goal="Translate project briefs and requirements into actionable Product Requirement Documents (PRDs), epics, and user stories.",
        backstory=(
            "As a Product Manager adhering to BMAD principles, you excel at defining product vision, "
            "breaking down complex problems into manageable development items, and ensuring alignment "
            "between business goals and technical execution."
        ),
        llm=llm,
        allow_delegation=True, # PM might delegate specific analysis to Analyst
        verbose=True
    )

# ... other agent definitions (Developer, Architect, etc.)
```