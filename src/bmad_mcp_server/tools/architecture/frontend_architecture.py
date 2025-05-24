"""
Frontend architecture creation tool using BMAD methodology.
Returns generated content and suggestions to the assistant.
"""

from typing import Any, Dict, Optional, Literal
from datetime import datetime
from crewai import Agent, Crew, Task, Process
from pydantic import BaseModel, Field
import logging

from ..base import BMadTool
from ...crewai_integration.agents import get_architect_agent
from ...crewai_integration.config import CrewAIConfig
from ...utils.state_manager import StateManager

logger = logging.getLogger(__name__)


class FrontendArchitectureRequest(BaseModel):
    """Request model for frontend architecture creation."""
    main_architecture_content: str = Field(..., alias="main_architecture", description="Main architecture document content") # Alias for server.py
    ux_specification_content: str = Field(
        default="",
        alias="ux_specification",
        description="UI/UX requirements and specifications"
    )
    framework_preference: str = Field(
        default="",
        description="Preferred frontend framework"
    )
    component_strategy: str = Field(
        default="atomic",
        description="Component design strategy"
    )
    state_management: str = Field(
        default="",
        description="Preferred state management approach"
    )


class CreateFrontendArchitectureTool(BMadTool):
    """
    Generates content for frontend-specific architecture specifications using BMAD methodology.
    This tool creates detailed frontend architecture documents that complement
    the main technical architecture with frontend-specific concerns and patterns.
    """
    
    def __init__(self, state_manager: StateManager, crew_ai_config: CrewAIConfig):
        super().__init__(state_manager, crew_ai_config)
        self.category = "architecture"
        self.description = "Generates content for frontend-specific architecture. Does not write files."
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for frontend architecture creation using Pydantic model."""
        schema = FrontendArchitectureRequest.model_json_schema()
        # Add enum constraints to match server.py registration if they are Literals there
        schema["properties"]["component_strategy"]["enum"] = ["atomic", "modular", "feature-based", "layered"]
        # Ensure framework_preference and state_management allow empty string if that's the intent for "any"
        # Or define specific enums if choices are limited.
        # For server.py, framework_preference is Optional[Literal["React", ..., ""]]
        # Pydantic schema should reflect this if strict validation is desired.
        # For now, keeping as string, server-side Literal will handle validation.
        return schema
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute frontend architecture generation and return content and suggestions."""
        try:
            # Map server.py argument names to Pydantic model field names if different
            # 'main_architecture' from server.py maps to 'main_architecture_content' here if we used alias
            # For now, assuming direct mapping or that server.py uses the model's field names
            args = FrontendArchitectureRequest(**arguments)
        except Exception as e:
            logger.error(f"Input validation failed for CreateFrontendArchitectureTool: {e}", exc_info=True)
            raise ValueError(f"Invalid arguments for CreateFrontendArchitectureTool: {e}")

        logger.info(f"Generating frontend architecture content, preferred framework: {args.framework_preference or 'None'}")

        frontend_complexity = self._analyze_frontend_complexity(args.main_architecture_content)
        
        # Create architect agent using the passed CrewAIConfig
        architect_agent = get_architect_agent(config=self.crew_ai_config)
        
        ux_spec_info = f"UX Specification Content:\n{args.ux_specification_content}\n" if args.ux_specification_content else "No UX specification content provided. Infer frontend requirements from the main architecture and general best practices."

        task_description = f"""
        Based on the main technical architecture document provided below, and the UX specifications (if any), 
        create a comprehensive frontend architecture.

        Main Architecture Content:
        {args.main_architecture_content}

        {ux_spec_info}

        Frontend Architecture Parameters:
        - Preferred Framework: {args.framework_preference or 'Not specified, choose a suitable modern framework.'}
        - Component Strategy: {args.component_strategy}
        - Preferred State Management: {args.state_management or 'Not specified, recommend based on framework and complexity.'}
        - Frontend Complexity Score: {frontend_complexity}/10
            
        Follow the BMAD frontend architecture template structure:
        1. Frontend Technical Summary & Goals
        2. Alignment with Main Architecture (Key integration points, API consumption)
        3. Chosen Frontend Stack (Framework, UI libraries, State Management, Build tools - with versions)
        4. Directory Structure for Frontend Code (as a code block)
        5. Component Design Strategy (e.g., {args.component_strategy}, examples of component hierarchy)
        6. State Management Approach (Detailed strategy, choice justification)
        7. Routing Strategy
        8. API Integration Strategy (How frontend interacts with backend APIs)
        9. Build, Bundling, and Deployment Process
        10. Frontend Testing Strategy (Unit, Integration, E2E)
        11. Performance Considerations & Optimizations
        12. Accessibility (A11Y) Guidelines
        13. Security Considerations for Frontend
        14. Coding Standards & Conventions for Frontend (e.g., naming, formatting)

        Ensure the frontend architecture:
        - Is consistent with the main technical architecture.
        - Is optimized for AI agent implementation if applicable to UI generation or component creation.
        - Follows modern frontend best practices.
        - Provides clear guidance for frontend development.
        The final output should be a complete frontend architecture document in well-formatted markdown.
        """
        
        frontend_arch_task = Task(
            description=task_description,
            expected_output="Complete frontend architecture document in markdown format, adhering to the BMAD frontend template.",
            agent=architect_agent
        )
        
        crew = Crew(
            agents=[architect_agent],
            tasks=[frontend_arch_task],
            process=Process.sequential,
            verbose=self.crew_ai_config.verbose_logging
        )
        
        try:
            result = crew.kickoff()
            generated_frontend_arch_content = result.raw if hasattr(result, 'raw') else str(result)
        except Exception as e:
            logger.error(f"CrewAI kickoff failed for frontend architecture generation: {e}", exc_info=True)
            raise Exception(f"Frontend architecture generation by CrewAI failed: {e}")
        
        # Determine a suggested path
        framework_suffix = args.framework_preference.lower().replace(' ', '_').replace('.', '') if args.framework_preference else "generic"
        suggested_path = f"architecture/frontend_architecture_{framework_suffix}.md"

        suggested_metadata = self.create_suggested_metadata(
            artifact_type="frontend_architecture_document",
            status="draft",
            framework_preference=args.framework_preference,
            component_strategy=args.component_strategy,
            state_management=args.state_management,
            complexity_score=frontend_complexity
        )
        
        logger.info(f"Frontend architecture content generated for framework: {args.framework_preference or 'generic'}")
        
        return {
            "content": generated_frontend_arch_content,
            "suggested_path": suggested_path,
            "metadata": suggested_metadata,
            "message": "Frontend architecture content generated. Please review and save."
        }
    
    def _analyze_frontend_complexity(self, main_architecture_content: str) -> int:
        """Analyze frontend complexity based on main architecture."""
        arch_lower = main_architecture_content.lower()
        
        ui_complexity = 0
        if "dashboard" in arch_lower or "admin" in arch_lower:
            ui_complexity += 2
        if "real-time" in arch_lower or "websocket" in arch_lower:
            ui_complexity += 2
        if "mobile" in arch_lower or "responsive" in arch_lower:
            ui_complexity += 1
        if "authentication" in arch_lower or "auth" in arch_lower:
            ui_complexity += 1
        if "api" in arch_lower: # This is very generic, might need refinement
            ui_complexity += 1
        if "microservice" in arch_lower: # Main arch type, might imply complex FE if many services
            ui_complexity += 1 
        if "spa" in arch_lower or "single page application" in arch_lower:
            ui_complexity += 1
        
        return min(ui_complexity, 10)
