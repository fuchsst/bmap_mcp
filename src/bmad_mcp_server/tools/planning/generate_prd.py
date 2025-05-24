"""
PRD generation tool using BMAD methodology.
Returns generated content and suggestions to the assistant.
"""

import json
from typing import Any, Dict, Optional, Literal
from datetime import datetime
from crewai import Agent, Crew, Task, Process
from pydantic import BaseModel, Field
import logging

from ..base import BMadTool
from ...crewai_integration.agents import get_pm_agent
from ...crewai_integration.config import CrewAIConfig
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
        json_schema_extra = {
            "properties": {
                "workflow_mode": {
                    "enum": ["incremental", "yolo"]
                },
                "technical_depth": {
                    "enum": ["basic", "standard", "detailed"]
                }
            }
        }



class GeneratePRDTool(BMadTool):
    """
    Generates content for a comprehensive PRD with epics and user stories using BMAD methodology.
    This tool transforms project briefs into detailed Product Requirements Documents.
    """
    
    def __init__(self, state_manager: StateManager, crew_ai_config: CrewAIConfig):
        super().__init__(state_manager, crew_ai_config)
        self.category = "planning"
        self.description = "Generates content for a PRD from a project brief. Does not write files."
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for PRD generation using Pydantic model."""
        schema = PRDGenerationRequest.model_json_schema()
        # Ensure enum constraints are present if not automatically added by Pydantic/FastMCP
        if "enum" not in schema["properties"]["workflow_mode"]:
             schema["properties"]["workflow_mode"]["enum"] = ["incremental", "yolo"]
        if "enum" not in schema["properties"]["technical_depth"]:
            schema["properties"]["technical_depth"]["enum"] = ["basic", "standard", "detailed"]
        return schema
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute PRD generation and return content and suggestions."""
        try:
            args = PRDGenerationRequest(**arguments)
        except Exception as e:
            logger.error(f"Input validation failed for GeneratePRDTool: {e}", exc_info=True)
            raise ValueError(f"Invalid arguments for GeneratePRDTool: {e}")

        logger.info(f"Generating PRD content based on brief (first 100 chars): {args.project_brief_content[:100]}...")
        
        # Analyze brief complexity to adjust technical depth (can be part of agent's logic too)
        brief_lines = len(args.project_brief_content.split('\n'))
        effective_technical_depth = args.technical_depth
        if brief_lines > 50 and args.technical_depth == "standard":
            effective_technical_depth = "detailed"
        elif brief_lines < 20 and args.technical_depth == "standard":
            effective_technical_depth = "basic"
        
        # Create PM agent using the passed CrewAIConfig
        pm_agent = get_pm_agent(config=self.crew_ai_config)
        
        prd_task_description = f"""
        Create a comprehensive Product Requirements Document (PRD) based on this project brief:
        
        {args.project_brief_content}
        
        Workflow mode: {args.workflow_mode}
        Technical depth: {effective_technical_depth}
        
        Follow the BMAD PRD template structure:
        1. Goal, Objective and Context
        2. Functional Requirements (MVP)
        3. Non Functional Requirements (MVP)
        4. User Interaction and Design Goals (if UI applicable)
        5. Technical Assumptions
        6. Epic Overview with detailed user stories (Ensure each epic has a clear goal, 3-5 user stories with acceptance criteria, and logical sequencing)
        7. Out of Scope Ideas Post MVP
        
        Focus on creating actionable, development-ready requirements.
        The final output should be a complete PRD document in well-formatted markdown.
        """

        if args.include_architecture_prompt:
            prd_task_description += """

---

## Initial Architect Prompt (To be included at the end of the PRD)

Based on the requirements analysis above, please create a comprehensive technical architecture that:

1. **Supports all functional and non-functional requirements**
2. **Follows the technical assumptions and constraints outlined**
3. **Provides clear technology stack selections with justification**
4. **Includes detailed component design and data flow**
5. **Addresses security, scalability, and performance considerations**
6. **Optimizes for AI agent implementation and BMAD methodology**

Use the BMAD architecture template and ensure the design enables efficient development execution by AI agents following the defined epics and stories.
"""
        
        prd_task = Task(
            description=prd_task_description,
            expected_output="A complete PRD document in markdown format, adhering to the BMAD template structure. If requested, include the 'Initial Architect Prompt' section at the end.",
            agent=pm_agent
        )
        
        crew = Crew(
            agents=[pm_agent],
            tasks=[prd_task],
            process=Process.sequential,
            verbose=self.crew_ai_config.verbose_logging # Use config for verbosity
        )
        
        try:
            result = crew.kickoff()
            generated_prd_content = result.raw if hasattr(result, 'raw') else str(result)
        except Exception as e:
            logger.error(f"CrewAI kickoff failed for PRD generation: {e}", exc_info=True)
            # Re-raise to be caught by server's MCP handler, which will format an MCPError
            raise Exception(f"PRD generation by CrewAI failed: {e}") 
        
        epics_count = generated_prd_content.count("Epic ")
        
        # Determine a suggested path
        brief_topic_line = args.project_brief_content.split('\n', 1)[0]
        safe_topic = "".join(c if c.isalnum() else '_' for c in brief_topic_line[:50]).strip('_').lower()
        if not safe_topic: safe_topic = "prd"
        suggested_path = f"prd/prd_{safe_topic}.md"

        suggested_metadata = self.create_suggested_metadata(
            artifact_type="prd",
            status="draft",
            workflow_mode=args.workflow_mode,
            technical_depth=effective_technical_depth,
            epics_count=epics_count,
            include_architecture_prompt=args.include_architecture_prompt
        )
        
        logger.info(f"PRD content generated by tool. Epics found: {epics_count}.")
        
        return {
            "content": generated_prd_content,
            "suggested_path": suggested_path,
            "metadata": suggested_metadata,
            "message": "PRD content generated. Please review and save."
        }
    
