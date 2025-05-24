"""
Story creation tool using BMAD methodology.
Returns generated content and suggestions to the assistant.
"""

import json
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime
from crewai import Agent, Crew, Task, Process
from pydantic import BaseModel, Field
import logging

from ..base import BMadTool
from ...crewai_integration.agents import get_pm_agent # Or get_developer_agent
from ...crewai_integration.config import CrewAIConfig
from ...utils.state_manager import StateManager

logger = logging.getLogger(__name__)


class CurrentProgress(BaseModel):
    """Model for tracking current project progress."""
    completed_stories: List[str] = Field(default_factory=list, description="List of completed story IDs or titles")
    current_epic: int = Field(default=1, description="Current epic number being worked on (1-indexed)")


class CreateStoryRequest(BaseModel):
    """Request model for story creation."""
    prd_content: str = Field(..., description="PRD content with epics and requirements")
    architecture_content: str = Field(..., description="Architecture context for technical guidance")
    current_progress: CurrentProgress = Field(
        default_factory=CurrentProgress,
        description="Current project progress and story completion status"
    )
    story_type: str = Field(
        default="feature",
        description="Type of story to create"
    )
    priority: str = Field(
        default="medium",
        description="Story priority level"
    )


class CreateNextStoryTool(BMadTool):
    """
    Generates content for the next development-ready user story based on PRD and architecture.
    This tool uses AI to analyze the PRD, architecture, and current progress
    to generate a well-defined user story with acceptance criteria and technical notes.
    """
    
    def __init__(self, state_manager: StateManager, crew_ai_config: CrewAIConfig):
        super().__init__(state_manager, crew_ai_config)
        self.category = "story"
        self.description = "Generates content for a user story. Does not write files."
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for story creation using Pydantic model."""
        schema = CreateStoryRequest.model_json_schema()
        # Ensure enums are correctly represented
        schema["properties"]["story_type"]["enum"] = ["feature", "bug", "technical", "research", "epic"]
        schema["properties"]["priority"]["enum"] = ["low", "medium", "high", "critical"]
        return schema
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute story generation and return content and suggestions."""
        try:
            args = CreateStoryRequest(**arguments)
        except Exception as e:
            logger.error(f"Input validation failed for CreateNextStoryTool: {e}", exc_info=True)
            raise ValueError(f"Invalid arguments for CreateNextStoryTool: {e}")

        logger.info(f"Generating next story content for epic {args.current_progress.current_epic}, type '{args.story_type}', priority '{args.priority}'")
        
        next_story_context_data = self._analyze_next_story_context(
            args.prd_content,
            args.current_progress
        )
        
        if not next_story_context_data:
            return {
                "content": "No more stories to create based on the provided PRD and progress. All epics appear to be complete or no further stories were identified.",
                "suggested_path": None, # No file to suggest
                "metadata": self.create_suggested_metadata(artifact_type="story_generation_status", status="completed_no_story"),
                "message": "Story generation complete: No further stories identified."
            }
        
        # Using PM agent for story writing, could also be a Developer agent
        story_writer_agent = get_pm_agent(config=self.crew_ai_config) 
        
        progress_info_str = (
            f"Current Progress:\n"
            f"- Current Epic Number: {args.current_progress.current_epic}\n"
            f"- Completed Stories in this Epic (titles/IDs): {', '.join(args.current_progress.completed_stories) if args.current_progress.completed_stories else 'None yet'}\n"
        )

        task_description = f"""
        Based on the provided Product Requirements Document (PRD) and Technical Architecture, generate the next logical user story.
        The context for the next story to be generated is: {json.dumps(next_story_context_data, indent=2)}
        Consider the overall progress: {progress_info_str}

        PRD Content (excerpt relevant to current epic might be better if PRD is very large):
        {args.prd_content}

        Architecture Content (relevant parts):
        {args.architecture_content}
        
        Story Parameters for the new story:
        - Story Type: {args.story_type}
        - Priority: {args.priority}

        Follow the BMAD user story template:
        1. Story Header (ID: [e.g., EPIC{next_story_context_data.get('epic_number', 'X')}-STORY{next_story_context_data.get('story_sequence_in_epic', 'Y')}], Title: [Clear, concise title based on story_description], Epic: [{next_story_context_data.get('epic_title', 'N/A')}])
        2. User Story Statement ("As a [type of user], I want [an action] so that [a benefit/value]" - based on story_description)
        3. Story Context and Background (Briefly elaborate on the story_description)
        4. Detailed Acceptance Criteria (3-7 specific, measurable, testable criteria)
        5. Technical Implementation Notes (Key technical considerations, API endpoints, components to modify/create, libraries to use. Be specific. Refer to Architecture Content.)
        6. Dependencies and Prerequisites (Other stories or tasks this depends on, or that depend on this)
        7. Out of Scope (Clearly define what is NOT part of this story)
        8. Estimated Effort (Optional, e.g., S, M, L or story points if a system is defined - use '{next_story_context_data.get('estimated_effort', 'Medium')}' as a hint)
        9. Testing Requirements (Key areas to test)
        10. Risk Assessment and Mitigation (Optional, brief)

        Ensure the story is development-ready, actionable, and aligns with the overall project goals.
        The story should be self-contained enough for a developer to implement.
        The final output should be a complete user story in well-formatted markdown.
        """
        
        story_task = Task(
            description=task_description,
            expected_output="A complete, development-ready user story in markdown format, following the BMAD template.",
            agent=story_writer_agent
        )
        
        crew = Crew(
            agents=[story_writer_agent],
            tasks=[story_task],
            process=Process.sequential,
            verbose=self.crew_ai_config.verbose_logging
        )
        
        try:
            result = crew.kickoff()
            generated_story_content = result.raw if hasattr(result, 'raw') else str(result)
        except Exception as e:
            logger.error(f"CrewAI kickoff failed for story generation: {e}", exc_info=True)
            raise Exception(f"Story generation by CrewAI failed: {e}")
        
        # Suggest a filename
        story_id_placeholder = f"EPIC{next_story_context_data.get('epic_number', 'X')}_STORY{next_story_context_data.get('story_sequence_in_epic', 'Y')}"
        # Try to extract a title from the generated content for a more descriptive filename
        title_line = generated_story_content.split('\n', 2)[0] # First line
        safe_title_suffix = "".join(c if c.isalnum() else '_' for c in title_line.replace("#", "").strip()[:30]).strip('_').lower()
        if not safe_title_suffix: safe_title_suffix = "next_story"
        
        suggested_path = f"stories/{story_id_placeholder}_{safe_title_suffix}.md"

        suggested_metadata = self.create_suggested_metadata(
            artifact_type="user_story",
            status="draft", 
            story_type=args.story_type,
            priority=args.priority,
            epic_reference=next_story_context_data.get('epic_title'),
            story_id_suggestion=story_id_placeholder # The actual ID might be embedded by the agent
        )
        
        logger.info(f"User story content generated by tool: {story_id_placeholder}")
        
        return {
            "content": generated_story_content,
            "suggested_path": suggested_path,
            "metadata": suggested_metadata,
            "message": f"User story content for '{story_id_placeholder}' generated. Please review and save."
        }
    
    def _analyze_next_story_context(self, prd_content: str, progress: CurrentProgress) -> Optional[Dict[str, Any]]:
        """
        Analyze PRD to determine the context for the next story to create.
        This is a simplified placeholder. A real implementation would involve more sophisticated PRD parsing
        and understanding of dependencies and story flow.
        """
        logger.debug(f"Analyzing PRD for next story. Current epic: {progress.current_epic}, completed stories in epic: {len(progress.completed_stories)}")
        
        # Placeholder logic: Assumes PRD epics are clearly marked and stories listed under them.
        # This would ideally parse the PRD to find the current epic and the next uncompleted story.
        # For now, it just provides a generic context based on the epic number.
        
        # This is a very naive way to find an epic title.
        epic_title_search = f"Epic {progress.current_epic}"
        epic_title_found = "Unknown Epic"
        for line in prd_content.split('\n'):
            if epic_title_search in line and ("###" in line or "##" in line):
                epic_title_found = line.replace("###","").replace("##","").replace(epic_title_search, "").strip().split(':',1)[0].strip()
                break
        
        # This is just a placeholder to simulate finding the "next" story.
        # A real implementation would need to parse the PRD for actual story titles/descriptions.
        story_sequence_in_epic = len(progress.completed_stories) + 1
        
        return {
            "epic_title": epic_title_found if epic_title_found != "Unknown Epic" else f"Epic {progress.current_epic}",
            "story_description_prompt": f"Generate the content for story number {story_sequence_in_epic} of {epic_title_found if epic_title_found != 'Unknown Epic' else f'Epic {progress.current_epic}'}. "
                                        f"Consider it's a new feature unless specified otherwise by story_type argument. "
                                        f"Ensure it logically follows previously completed stories (if any) for this epic: {', '.join(progress.completed_stories)}.",
            "epic_number": progress.current_epic,
            "story_sequence_in_epic": story_sequence_in_epic,
            "estimated_effort": "Medium", # Default placeholder
        }
