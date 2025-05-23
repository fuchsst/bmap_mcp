"""
PRD generation tool using BMAD methodology.
"""

import json
from typing import Any, Dict, Optional
from crewai import Agent, Crew, Task, Process
from pydantic import BaseModel, Field
import logging

from ..base import BMadTool
from ...crewai_integration.agents import get_pm_agent
from ...templates.loader import load_template
from ...utils.state_manager import StateManager

logger = logging.getLogger(__name__)


class PRDGenerationRequest(BaseModel):
    """Request model for PRD generation."""
    project_brief_content: str = Field(..., description="Complete project brief content to base PRD on")
    workflow_mode: str = Field(
        default="incremental", 
        description="PRD generation approach - incremental for step-by-step, yolo for comprehensive"
    )
    technical_depth: str = Field(
        default="standard", 
        description="Level of technical detail to include"
    )
    include_architecture_prompt: bool = Field(
        default=True, 
        description="Whether to include architect prompt in PRD"
    )

    class Config:
        schema_extra = {
            "properties": {
                "workflow_mode": {
                    "enum": ["incremental", "yolo"]
                },
                "technical_depth": {
                    "enum": ["basic", "standard", "detailed"]
                }
            }
        }


class PRDGenerationResult(BaseModel):
    """Result model for PRD generation."""
    prd_content: str = Field(..., description="Generated PRD content")
    epics_count: int = Field(..., description="Number of epics identified")
    workflow_mode: str = Field(..., description="Workflow mode used")
    technical_depth: str = Field(..., description="Technical depth level used")
    artifact_path: str = Field(..., description="Path where PRD was saved")


class GeneratePRDTool(BMadTool):
    """
    Generate comprehensive PRD with epics and user stories using BMAD methodology.
    
    This tool transforms project briefs into detailed Product Requirements Documents
    with well-structured epics, user stories, and technical guidance.
    """
    
    def __init__(self, state_manager: StateManager):
        super().__init__(state_manager)
        self.category = "planning"
        self.description = "Generate comprehensive PRD with epics and user stories from project brief"
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for PRD generation using Pydantic model."""
        schema = PRDGenerationRequest.model_json_schema()
        # Add enum constraints that aren't automatically included
        schema["properties"]["workflow_mode"]["enum"] = ["incremental", "yolo"]
        schema["properties"]["technical_depth"]["enum"] = ["basic", "standard", "detailed"]
        return schema
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute PRD generation."""
        # Validate input using Pydantic
        request = PRDGenerationRequest(**arguments)
        
        logger.info("Starting PRD generation")
        
        # Analyze brief complexity to adjust technical depth
        brief_lines = len(request.project_brief_content.split('\n'))
        technical_depth = request.technical_depth
        if brief_lines > 50:
            technical_depth = "detailed"
        elif brief_lines < 20:
            technical_depth = "basic"
        
        # Create PM agent
        pm_agent = get_pm_agent()
        
        # Create PRD generation task
        prd_task = Task(
            description=f"""
            Create a comprehensive Product Requirements Document (PRD) based on this project brief:
            
            {request.project_brief_content}
            
            Workflow mode: {request.workflow_mode}
            Technical depth: {technical_depth}
            
            Follow the BMAD PRD template structure:
            1. Goal, Objective and Context
            2. Functional Requirements (MVP)
            3. Non Functional Requirements (MVP)
            4. User Interaction and Design Goals (if UI applicable)
            5. Technical Assumptions
            6. Epic Overview with detailed user stories
            7. Out of Scope Ideas Post MVP
            
            Ensure each epic has:
            - Clear goal statement
            - 3-5 well-defined user stories
            - Specific acceptance criteria for each story
            - Logical sequencing and dependencies
            
            Focus on creating actionable, development-ready requirements.
            """,
            expected_output="Complete PRD document in markdown format following BMAD template",
            agent=pm_agent
        )
        
        # Execute PRD generation
        crew = Crew(
            agents=[pm_agent],
            tasks=[prd_task],
            process=Process.sequential,
            verbose=False
        )
        
        result = crew.kickoff()
        prd_content = result.raw if hasattr(result, 'raw') else str(result)
        
        # Count epics
        epics_count = prd_content.count("Epic ")
        
        # Format the final PRD
        formatted_prd = self._format_prd(prd_content, request.include_architecture_prompt)
        
        # Save the artifact
        metadata = self.create_metadata(
            status="completed",
            workflow_mode=request.workflow_mode,
            technical_depth=technical_depth,
            epics_count=epics_count
        )
        
        # Generate filename based on project brief content
        # Sanitize the topic to create a valid filename
        brief_topic_sanitized = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in request.project_brief_content[:30])
        brief_topic_sanitized = brief_topic_sanitized.replace(' ', '_').lower()
        if not brief_topic_sanitized: # Handle empty or fully sanitized topic
            brief_topic_sanitized = "unnamed_project"
        
        file_name = f"prd_{brief_topic_sanitized}.md"
        artifact_path = f"prd/{file_name}"
        
        await self.state_manager.save_artifact(artifact_path, formatted_prd, metadata)
        await self.state_manager.update_project_phase("prd_completed")
        
        logger.info(f"PRD saved to: {artifact_path}")
        
        return formatted_prd
    
    def _format_prd(self, content: str, include_arch_prompt: bool) -> str:
        """Format PRD with proper structure and prompts."""
        formatted = content
        
        if include_arch_prompt:
            arch_prompt = """
---

## Initial Architect Prompt

Based on the requirements analysis above, please create a comprehensive technical architecture that:

1. **Supports all functional and non-functional requirements**
2. **Follows the technical assumptions and constraints outlined**
3. **Provides clear technology stack selections with justification**
4. **Includes detailed component design and data flow**
5. **Addresses security, scalability, and performance considerations**
6. **Optimizes for AI agent implementation and BMAD methodology**

Use the BMAD architecture template and ensure the design enables efficient development execution by AI agents following the defined epics and stories.
"""
            formatted += arch_prompt
        
        formatted += "\n\n---\n*Generated using BMAD MCP Server - PRD Generation Tool*"
        return formatted
