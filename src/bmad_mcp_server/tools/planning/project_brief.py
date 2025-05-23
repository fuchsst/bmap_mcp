"""
Project Brief creation tool using BMAD methodology.
"""

import logging
from typing import Any, Dict

from bmad_mcp_server.utils.state_manager import StateManager
from crewai import Agent, Task, Crew, Process

from ..base import BMadTool
from ...crewai_integration.agents import get_analyst_agent

logger = logging.getLogger(__name__)


class CreateProjectBriefTool(BMadTool):
    """
    Generate a structured project brief following BMAD methodology.
    
    This tool uses the BMAD Analyst agent to create comprehensive project briefs
    that serve as the foundation for subsequent PRD and architecture work.
    """
    
    def __init__(self, state_manager: StateManager):
        super().__init__(state_manager)
        self.category = "planning"
    
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
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute project brief creation."""
        # Validate inputs
        validated_args = self.validate_input(arguments)
        
        topic = validated_args["topic"]
        target_audience = validated_args.get("target_audience", "General users")
        constraints = validated_args.get("constraints", [])
        scope_level = validated_args.get("scope_level", "standard")
        
        logger.info(f"Creating project brief for: {topic}")
        
        # Create analyst agent
        analyst = get_analyst_agent()
        
        # Create project brief task
        brief_task = Task(
            description=f"""
            Create a comprehensive project brief for: {topic}
            
            Target audience: {target_audience}
            Known constraints: {', '.join(constraints) if constraints else 'None specified'}
            Scope level: {scope_level}
            
            Follow the BMAD project brief template structure:
            1. Introduction / Problem Statement
            2. Vision & Goals (with specific, measurable goals)
            3. Target Audience / Users
            4. Key Features / Scope (High-Level Ideas for MVP)
            5. Post MVP Features / Scope and Ideas
            6. Known Technical Constraints or Preferences
            
            Ensure the brief is detailed enough to guide PRD creation and provides
            clear direction for the project scope and objectives.
            """,
            expected_output="Complete project brief in markdown format following BMAD template",
            agent=analyst
        )
        
        # Create and execute crew
        crew = Crew(
            agents=[analyst],
            tasks=[brief_task],
            process=Process.sequential,
            verbose=False
        )
        
        # Execute the crew
        result = crew.kickoff()
        
        # Get the generated content
        generated_brief = result.raw if hasattr(result, 'raw') else str(result)
        
        # Format the result
        formatted_brief = self._format_project_brief(generated_brief, topic)
        
        # Save the artifact using StateManager
        metadata = self.create_metadata(
            status="completed", 
            topic=topic, 
            target_audience=target_audience,
            scope_level=scope_level
        )
        
        # Define a standardized path within .bmad
        file_name = f"project_brief_{topic.lower().replace(' ', '_').replace('.', '')}.md"
        artifact_path_in_bmad = f"ideation/{file_name}"
        
        await self.state_manager.save_artifact(artifact_path_in_bmad, formatted_brief, metadata)
        await self.state_manager.update_project_phase("project_brief_completed")
        
        logger.info(f"Project brief saved to: {artifact_path_in_bmad}")
        
        return formatted_brief
    
    def _format_project_brief(self, content: str, topic: str) -> str:
        """Format the project brief with proper structure."""
        if not content.startswith("#"):
            content = f"# Project Brief: {topic}\n\n{content}"
        
        # Add metadata footer
        formatted = f"""{content}

---
*Generated using BMAD MCP Server - Project Brief Tool*
*Template: project_brief_tmpl.md*
"""
        return formatted
