"""
Architecture creation tool using BMAD methodology.
"""

from typing import Any, Dict, Optional
from crewai import Agent, Crew, Task, Process
from pydantic import BaseModel, Field
import json
import logging

from ..base import BMadTool
from ...crewai_integration.agents import get_architect_agent
from ...templates.loader import load_template
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


class ArchitectureResult(BaseModel):
    """Result model for architecture creation."""
    architecture_content: str = Field(..., description="Generated architecture content")
    complexity_score: int = Field(..., description="Calculated complexity score")
    architecture_type: str = Field(..., description="Architecture type used")
    artifact_path: str = Field(..., description="Path where architecture was saved")


class CreateArchitectureTool(BMadTool):
    """
    Generate technical architecture from PRD requirements using BMAD methodology.
    
    This tool creates comprehensive architecture documents with technology selections,
    component designs, and implementation guidance optimized for AI agent development.
    """
    
    def __init__(self, state_manager: StateManager):
        super().__init__(state_manager)
        self.category = "architecture"
        self.description = "Generate comprehensive technical architecture from PRD requirements"
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for architecture creation using Pydantic model."""
        schema = ArchitectureRequest.model_json_schema()
        # Add enum constraints
        schema["properties"]["architecture_type"]["enum"] = ["monolith", "modular_monolith", "microservices", "serverless"]
        schema["properties"]["tech_preferences"]["properties"]["api_style"]["enum"] = ["REST", "GraphQL", "gRPC"]
        schema["properties"]["tech_preferences"]["properties"]["deployment_style"]["enum"] = ["containers", "serverless", "traditional"]
        return schema
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute architecture generation."""
        # Validate input using Pydantic
        request = ArchitectureRequest(**arguments)
        
        logger.info("Starting architecture generation")
        
        # Analyze PRD complexity
        complexity_score = self._calculate_complexity_score(request.prd_content)
        
        # Suggest architecture type based on complexity if not specified
        architecture_type = request.architecture_type
        if complexity_score >= 8:
            architecture_type = "microservices"
        elif complexity_score >= 6:
            architecture_type = "modular_monolith"
        
        # Create architect agent
        architect_agent = get_architect_agent()
        
        # Prepare technology preferences text
        tech_prefs_text = ""
        if request.tech_preferences:
            tech_dict = request.tech_preferences.model_dump(exclude_none=True)
            if tech_dict:
                tech_prefs_text = f"Technology Preferences: {json.dumps(tech_dict, indent=2)}"
        
        # Create architecture generation task
        architecture_task = Task(
            description=f"""
            Create a comprehensive technical architecture document based on these requirements:
            
            {request.prd_content}
            
            Architecture Parameters:
            - Recommended Architecture Type: {architecture_type}
            - Complexity Score: {complexity_score}/10
            {tech_prefs_text}
            
            Follow the BMAD architecture template structure:
            1. Technical Summary
            2. High-Level Overview with architecture diagrams (Mermaid)
            3. Architectural/Design Patterns Adopted
            4. Component View with detailed descriptions
            5. Project Structure with complete directory layout
            6. API Reference for external and internal APIs
            7. Data Models with complete schemas
            8. Definitive Tech Stack Selections (specific versions)
            9. Infrastructure and Deployment Overview
            10. Error Handling Strategy
            11. Coding Standards (focused on AI agent implementation)
            12. Overall Testing Strategy
            13. Security Best Practices
            
            Ensure the architecture:
            - Supports all functional and non-functional requirements
            - Is optimized for AI agent implementation
            - Follows BMAD best practices
            - Includes specific technology versions and justifications
            - Provides clear implementation guidance
            """,
            expected_output="Complete architecture document in markdown format following BMAD template",
            agent=architect_agent
        )
        
        # Execute architecture generation
        crew = Crew(
            agents=[architect_agent],
            tasks=[architecture_task],
            process=Process.sequential,
            verbose=False
        )
        
        result = crew.kickoff()
        architecture_content = result.raw if hasattr(result, 'raw') else str(result)
        
        # Format the final architecture
        formatted_arch = self._format_architecture(
            architecture_content,
            request.include_frontend_prompt
        )
        
        # Save the artifact
        metadata = self.create_metadata(
            status="completed",
            architecture_type=architecture_type,
            complexity_score=complexity_score,
            tech_preferences=request.tech_preferences.model_dump(exclude_none=True)
        )
        
        # Generate filename
        prd_topic_sanitized = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in request.prd_content[:30])
        prd_topic_sanitized = prd_topic_sanitized.replace(' ', '_').lower()
        if not prd_topic_sanitized: # Handle empty or fully sanitized topic
            prd_topic_sanitized = "unnamed_project"
            
        file_name = f"architecture_{architecture_type}_{prd_topic_sanitized}.md"
        artifact_path = f"architecture/{file_name}"
        
        await self.state_manager.save_artifact(artifact_path, formatted_arch, metadata)
        await self.state_manager.update_project_phase("architecture_completed")
        
        logger.info(f"Architecture saved to: {artifact_path}")
        
        return formatted_arch
    
    def _calculate_complexity_score(self, prd_content: str) -> int:
        """Calculate architecture complexity score based on PRD content."""
        prd_lines = len(prd_content.split('\n'))
        epic_count = prd_content.count("Epic ")
        integration_count = prd_content.lower().count("integration")
        api_count = prd_content.lower().count("api")
        
        # Calculate complexity score (1-10)
        complexity_factors = [
            min(prd_lines // 50, 3),  # Document size
            min(epic_count, 3),       # Number of epics
            min(integration_count, 2), # Integration complexity
            min(api_count, 2)         # API complexity
        ]
        
        return min(sum(complexity_factors), 10)
    
    def _format_architecture(self, content: str, include_frontend_prompt: bool) -> str:
        """Format architecture document with proper structure."""
        formatted = content
        
        if include_frontend_prompt and "frontend" in content.lower():
            frontend_prompt = """
---

## Prompt for Design Architect (Frontend Architecture Mode)

Based on the main architecture document above, please create a comprehensive frontend architecture that:

1. **Aligns with the main technical architecture and technology selections**
2. **Follows the BMAD frontend architecture template**
3. **Defines component strategy, state management, and routing approaches**
4. **Includes build, bundling, and deployment specifications**
5. **Addresses performance, accessibility, and testing requirements**
6. **Optimizes for AI agent implementation with clear patterns and conventions**

Use the main architecture's technology stack as the foundation and elaborate on frontend-specific concerns while maintaining consistency with the overall system design.
"""
            formatted += frontend_prompt
        
        formatted += "\n\n---\n*Generated using BMAD MCP Server - Architecture Creation Tool*"
        return formatted
