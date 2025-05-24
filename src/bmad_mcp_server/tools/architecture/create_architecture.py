"""
Architecture creation tool using BMAD methodology.
Returns generated content and suggestions to the assistant.
"""

from typing import Any, Dict, Optional, Literal # Added Literal
from datetime import datetime # Added import
from crewai import Agent, Crew, Task, Process
from pydantic import BaseModel, Field
import json
import logging

from ..base import BMadTool
from ...crewai_integration.agents import get_architect_agent
from ...crewai_integration.config import CrewAIConfig
from ...utils.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechPreferences(BaseModel):
    """Technology preferences model."""
    backend_framework: Optional[str] = Field(None, description="Preferred backend framework")
    frontend_framework: Optional[str] = Field(None, description="Preferred frontend framework")
    database: Optional[str] = Field(None, description="Preferred database")
    cloud_provider: Optional[str] = Field(None, description="Preferred cloud provider")
    programming_language: Optional[str] = Field(None, description="Preferred programming language")
    api_style: Optional[str] = Field(None, description="API style preference")
    deployment_style: Optional[str] = Field(None, description="Deployment style preference")


class ArchitectureRequest(BaseModel):
    """Request model for architecture creation."""
    prd_content: str = Field(..., description="Complete PRD content with requirements and epics")
    tech_preferences: TechPreferences = Field(
        default_factory=TechPreferences,
        description="Technology preferences and constraints"
    )
    architecture_type: str = Field(
        default="monolith",
        description="Preferred architecture pattern"
    )
    include_frontend_prompt: bool = Field(
        default=True,
        description="Whether to include frontend architect prompt"
    )



class CreateArchitectureTool(BMadTool):
    """
    Generates content for a technical architecture from PRD requirements using BMAD methodology.
    This tool creates comprehensive architecture documents with technology selections,
    component designs, and implementation guidance optimized for AI agent development.
    """
    
    def __init__(self, state_manager: StateManager, crew_ai_config: CrewAIConfig):
        super().__init__(state_manager, crew_ai_config)
        self.category = "architecture"
        self.description = "Generates content for a technical architecture from PRD. Does not write files."
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for architecture creation using Pydantic model."""
        schema = ArchitectureRequest.model_json_schema()
        # Ensure enums are correctly represented
        schema["properties"]["architecture_type"]["enum"] = ["monolith", "modular_monolith", "microservices", "serverless"]
        # Enums for TechPreferences are often handled by Pydantic's schema generation if Literal is used,
        # but can be explicitly set if needed, e.g., for older Pydantic or specific FastMCP behavior.
        # For nested models, FastMCP might require explicit full schema definition if it doesn't auto-resolve.
        # For now, assuming Pydantic schema for TechPreferences is sufficient.
        return schema
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute architecture generation and return content and suggestions."""
        try:
            args = ArchitectureRequest(**arguments)
        except Exception as e:
            logger.error(f"Input validation failed for CreateArchitectureTool: {e}", exc_info=True)
            raise ValueError(f"Invalid arguments for CreateArchitectureTool: {e}")

        logger.info(f"Generating architecture content of type: {args.architecture_type}")

        # Analyze PRD complexity
        complexity_score = self._calculate_complexity_score(args.prd_content)
        
        effective_architecture_type = args.architecture_type
        if complexity_score >= 8 and args.architecture_type not in ["microservices", "serverless"]:
            effective_architecture_type = "microservices"
        elif complexity_score >= 6 and args.architecture_type == "monolith":
            effective_architecture_type = "modular_monolith"
        
        # Create architect agent using the passed CrewAIConfig
        architect_agent = get_architect_agent(config=self.crew_ai_config)
        
        tech_prefs_text = ""
        if args.tech_preferences:
            tech_dict = args.tech_preferences.model_dump(exclude_none=True)
            if tech_dict:
                tech_prefs_text = f"Technology Preferences: {json.dumps(tech_dict, indent=2)}"
        
        architecture_task_description = f"""
        Create a comprehensive technical architecture document based on these requirements:
        
        {args.prd_content}
        
        Architecture Parameters:
        - Architecture Type: {effective_architecture_type}
        - Complexity Score (1-10): {complexity_score}/10
        {tech_prefs_text}
        
        Follow the BMAD architecture template structure:
        1. Technical Summary
        2. High-Level Overview with architecture diagrams (Mermaid format for diagrams)
        3. Architectural/Design Patterns Adopted
        4. Component View with detailed descriptions
        5. Project Structure with complete directory layout (as a code block)
        6. API Reference for external and internal APIs (if any)
        7. Data Models with complete schemas (e.g., Pydantic models or SQL DDL)
        8. Definitive Tech Stack Selections (including specific versions where appropriate)
        9. Infrastructure and Deployment Overview
        10. Error Handling Strategy
        11. Coding Standards (focused on AI agent implementation)
        12. Overall Testing Strategy
        13. Security Best Practices
        
        Ensure the architecture:
        - Supports all functional and non-functional requirements from the PRD.
        - Is optimized for AI agent implementation.
        - Follows BMAD best practices.
        - Includes specific technology versions and justifications where critical.
        - Provides clear implementation guidance.
        The final output should be a complete architecture document in well-formatted markdown.
        """

        if args.include_frontend_prompt and "frontend" in args.prd_content.lower():
            architecture_task_description += """

---

## Prompt for Design Architect (Frontend Architecture Mode) (To be included at the end)

Based on the main architecture document above, please create a comprehensive frontend architecture that:

1. **Aligns with the main technical architecture and technology selections**
2. **Follows the BMAD frontend architecture template**
3. **Defines component strategy, state management, and routing approaches**
4. **Includes build, bundling, and deployment specifications**
5. **Addresses performance, accessibility, and testing requirements**
6. **Optimizes for AI agent implementation with clear patterns and conventions**

Use the main architecture's technology stack as the foundation and elaborate on frontend-specific concerns while maintaining consistency with the overall system design.
"""

        architecture_task = Task(
            description=architecture_task_description,
            expected_output="Complete architecture document in markdown format, adhering to the BMAD template. Include Mermaid diagrams for overviews and component interactions where appropriate. If requested, include the 'Prompt for Design Architect' section at the end.",
            agent=architect_agent
        )
        
        crew = Crew(
            agents=[architect_agent],
            tasks=[architecture_task],
            process=Process.sequential,
            verbose=self.crew_ai_config.verbose_logging
        )
        
        try:
            result = crew.kickoff()
            generated_arch_content = result.raw if hasattr(result, 'raw') else str(result)
        except Exception as e:
            logger.error(f"CrewAI kickoff failed for architecture generation: {e}", exc_info=True)
            raise Exception(f"Architecture generation by CrewAI failed: {e}")
        
        # Determine a suggested path
        prd_topic_line = args.prd_content.split('\n', 1)[0] # Get first line for a hint
        safe_topic = "".join(c if c.isalnum() else '_' for c in prd_topic_line[:30]).strip('_').lower()
        if not safe_topic: safe_topic = "architecture"
        suggested_path = f"architecture/arch_{effective_architecture_type}_{safe_topic}.md"

        suggested_metadata = self.create_suggested_metadata(
            artifact_type="architecture_document",
            status="draft",
            architecture_type=effective_architecture_type,
            complexity_score=complexity_score,
            tech_preferences_used=args.tech_preferences.model_dump(exclude_none=True) if args.tech_preferences else {}
        )
        
        logger.info(f"Architecture document content generated for type: {effective_architecture_type}")
        
        return {
            "content": generated_arch_content,
            "suggested_path": suggested_path,
            "metadata": suggested_metadata,
            "message": "Architecture document content generated. Please review and save."
        }
    
    def _calculate_complexity_score(self, prd_content: str) -> int:
        """Calculate architecture complexity score based on PRD content."""
        prd_lines = len(prd_content.split('\n'))
        epic_count = prd_content.count("Epic ") # Case-sensitive count
        integration_count = prd_content.lower().count("integration")
        api_count = prd_content.lower().count("api")
        
        complexity_factors = [
            min(prd_lines // 100, 3),  # Adjusted divisor for lines
            min(epic_count // 2, 3),   # Adjusted for epic count
            min(integration_count // 2, 2),
            min(api_count // 2, 2)
        ]
        return max(1, min(sum(complexity_factors), 10)) # Ensure score is at least 1
