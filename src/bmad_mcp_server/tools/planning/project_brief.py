"""
Project Brief creation tool using BMAD methodology.
Returns generated content and suggestions to the assistant.
"""

import logging
from typing import Any, Dict
from datetime import datetime

from bmad_mcp_server.utils.state_manager import StateManager
from bmad_mcp_server.crewai_integration.config import CrewAIConfig
from crewai import Agent, Task, Crew, Process

from ..base import BMadTool
from ...crewai_integration.agents import get_analyst_agent

logger = logging.getLogger(__name__)


class CreateProjectBriefTool(BMadTool):
    """
    Generates content for a structured project brief following BMAD methodology.
    This tool uses the BMAD Analyst agent.
    """
    
    def __init__(self, state_manager: StateManager, crew_ai_config: CrewAIConfig):
        super().__init__(state_manager, crew_ai_config)
        self.category = "planning"
        self.description = "Generates content for a project brief. Does not write files."
    
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
        """Execute project brief creation and return content and suggestions."""
        validated_args = self.validate_input(arguments)
        
        topic = validated_args["topic"]
        target_audience = validated_args.get("target_audience", "General users")
        constraints = validated_args.get("constraints", [])
        scope_level = validated_args.get("scope_level", "standard")
        
        logger.info(f"Generating project brief content for: {topic}")

        # Get project name from state_manager for context, if available
        project_meta = self.state_manager.get_project_meta()
        project_name = project_meta.get("project_name", "the current project")
        
        # Create analyst agent using the passed CrewAIConfig
        analyst = get_analyst_agent(config=self.crew_ai_config)
        
        # Define the CrewAI task
        # Template content can be loaded here or be part of the agent's default knowledge/prompting
        # For simplicity, embedding structure in prompt.
        # template_content = load_template("project_brief_tmpl.md") # If using external template
        task_description = f"""
        Create a comprehensive project brief for the topic: '{topic}' for project '{project_name}'.
        Target audience: {target_audience}
        Known constraints: {', '.join(constraints) if constraints else 'None specified'}
        Scope level: {scope_level}
        
        Follow a standard BMAD project brief template structure, including sections for:
        1. Introduction / Problem Statement
        2. Vision & Goals (with specific, measurable goals)
        3. Target Audience / Users
        4. Key Features / Scope (High-Level Ideas for MVP)
        5. Post MVP Features / Scope and Ideas
        6. Known Technical Constraints or Preferences
        
        Ensure the brief is detailed enough to guide PRD creation and provides
        clear direction for the project scope and objectives. The output should be clean Markdown.
        """
        brief_task = Task(
            description=task_description,
            expected_output="A complete project brief in markdown format.",
            agent=analyst
        )
        
        crew = Crew(
            agents=[analyst],
            tasks=[brief_task],
            process=Process.sequential,
            verbose=self.crew_ai_config.verbose_logging
        )
        
        result = crew.kickoff()
        generated_content = result.raw if hasattr(result, 'raw') else str(result)
        
        # Prepare the structured response for the assistant
        file_name_safe_topic = topic.lower().replace(' ', '_').replace('.', '').replace('/', '_').replace('\\', '_')
        suggested_path = f"ideation/project_brief_{file_name_safe_topic}.md"

        suggested_metadata = self.create_suggested_metadata(
            artifact_type="project_brief",
            status="draft", 
            topic=topic, 
            target_audience=target_audience,
            scope_level=scope_level
        )
        
        logger.info(f"Project brief content for '{topic}' generated by tool.")
        
        return {
            "content": generated_content,
            "suggested_path": suggested_path,
            "metadata": suggested_metadata,
            "message": f"Project brief content for '{topic}' generated. Please review and save to the suggested path or your preferred location within the .bmad directory."
        }

    # _format_project_brief method is removed as the server no longer adds footers.
    # Formatting should be part of the agent's task or handled by the assistant.
