"""
Story creation tool using BMAD methodology.
"""

from typing import Any, Dict, List, Optional
from crewai import Agent, Crew, Task, Process
from pydantic import BaseModel, Field
import logging

from ..base import BMadTool
from ...crewai_integration.agents import get_pm_agent
from ...utils.state_manager import StateManager

logger = logging.getLogger(__name__)


class CurrentProgress(BaseModel):
    """Model for tracking current project progress."""
    completed_stories: List[str] = Field(default_factory=list, description="List of completed story IDs")
    current_epic: int = Field(default=1, description="Current epic number being worked on")
    epic_progress: Dict[str, Any] = Field(default_factory=dict, description="Progress within current epic")


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
    Generate development-ready user stories using BMAD methodology.
    
    This tool creates detailed user stories with technical guidance, acceptance criteria,
    and implementation notes based on PRD epics and architecture context.
    """
    
    def __init__(self, state_manager: StateManager):
        super().__init__(state_manager)
        self.category = "story"
        self.description = "Generate development-ready user stories from PRD epics"
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for story creation using Pydantic model."""
        schema = CreateStoryRequest.model_json_schema()
        # Add enum constraints
        schema["properties"]["story_type"]["enum"] = ["feature", "bug", "technical", "research", "epic"]
        schema["properties"]["priority"]["enum"] = ["low", "medium", "high", "critical"]
        return schema
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute story creation."""
        # Validate input using Pydantic
        request = CreateStoryRequest(**arguments)
        
        logger.info(f"Creating next story for epic {request.current_progress.current_epic}")
        
        # Analyze PRD to identify next story
        next_story_context = self._analyze_next_story_context(
            request.prd_content,
            request.current_progress
        )
        
        if not next_story_context:
            return "No more stories to create. All epics appear to be complete."
        
        # Create PM agent for story generation
        pm_agent = get_pm_agent()
        
        # Create story generation task
        story_task = Task(
            description=f"""
            Create a comprehensive, development-ready user story based on this context:
            
            PRD Content:
            {request.prd_content}
            
            Architecture Context:
            {request.architecture_content}
            
            Next Story Context:
            {next_story_context}
            
            Current Progress:
            - Current Epic: {request.current_progress.current_epic}
            - Completed Stories: {len(request.current_progress.completed_stories)}
            - Story Type: {request.story_type}
            - Priority: {request.priority}
            
            Create a story following the BMAD story template:
            1. Story Header (ID, Title, Epic Reference)
            2. User Story Statement (As a... I want... So that...)
            3. Story Context and Background
            4. Detailed Acceptance Criteria
            5. Technical Implementation Notes
            6. Dependencies and Prerequisites
            7. Definition of Done Checklist
            8. Estimated Effort and Complexity
            9. Testing Requirements
            10. Risk Assessment and Mitigation
            
            Ensure the story:
            - Is self-contained and implementable
            - Includes specific technical guidance from architecture
            - Has clear, testable acceptance criteria
            - Follows BMAD story quality standards
            - Is properly sized for development (not too large/small)
            - Includes all necessary context for AI agent implementation
            """,
            expected_output="Complete user story document in markdown format following BMAD template",
            agent=pm_agent
        )
        
        # Execute story generation
        crew = Crew(
            agents=[pm_agent],
            tasks=[story_task],
            process=Process.sequential,
            verbose=False
        )
        
        result = crew.kickoff()
        story_content = result.raw if hasattr(result, 'raw') else str(result)
        
        # Format the final story
        formatted_story = self._format_story(
            story_content,
            next_story_context,
            request.current_progress.current_epic
        )
        
        # Generate story ID
        story_id = f"STORY-{request.current_progress.current_epic:02d}-{len(request.current_progress.completed_stories) + 1:02d}"
        
        # Save the artifact
        metadata = self.create_metadata(
            status="draft",
            story_id=story_id,
            epic_number=request.current_progress.current_epic,
            story_type=request.story_type,
            priority=request.priority,
            estimated_effort=next_story_context.get("estimated_effort", "medium")
        )
        
        # Generate filename
        file_name = f"{story_id.lower().replace('-', '_')}.md"
        artifact_path = f"stories/{file_name}"
        
        await self.state_manager.save_artifact(artifact_path, formatted_story, metadata)
        
        logger.info(f"Story saved to: {artifact_path}")
        
        return formatted_story
    
    def _analyze_next_story_context(self, prd_content: str, progress: CurrentProgress) -> Optional[Dict[str, Any]]:
        """Analyze PRD to determine the next story to create."""
        
        # Simple analysis - in a real implementation this would be more sophisticated
        prd_lines = prd_content.split('\n')
        
        # Find epic sections
        epic_sections = []
        current_epic = None
        current_stories = []
        
        for line in prd_lines:
            line = line.strip()
            if line.startswith("### Epic") or line.startswith("## Epic"):
                if current_epic:
                    epic_sections.append({
                        "epic": current_epic,
                        "stories": current_stories
                    })
                current_epic = line
                current_stories = []
            elif line.startswith("- Story") or line.startswith("* Story"):
                current_stories.append(line)
        
        # Add final epic
        if current_epic:
            epic_sections.append({
                "epic": current_epic,
                "stories": current_stories
            })
        
        # Find next story to implement
        if progress.current_epic <= len(epic_sections):
            current_epic_data = epic_sections[progress.current_epic - 1]
            completed_count = len(progress.completed_stories)
            
            if completed_count < len(current_epic_data["stories"]):
                # Next story in current epic
                next_story = current_epic_data["stories"][completed_count]
                return {
                    "epic_title": current_epic_data["epic"],
                    "story_description": next_story,
                    "epic_number": progress.current_epic,
                    "story_number": completed_count + 1,
                    "estimated_effort": "medium",
                    "context": f"Story {completed_count + 1} of {len(current_epic_data['stories'])} in epic {progress.current_epic}"
                }
        
        return None
    
    def _format_story(self, content: str, story_context: Dict[str, Any], epic_number: int) -> str:
        """Format story with proper structure and metadata."""
        
        story_id = f"STORY-{epic_number:02d}-{story_context.get('story_number', 1):02d}"
        
        formatted = f"""# {story_id}: {story_context.get('story_description', 'User Story')}

## Status: Draft

## Epic Reference
- **Epic:** {story_context.get('epic_title', f'Epic {epic_number}')}
- **Story Position:** {story_context.get('context', 'Story in epic')}

{content}

## Implementation Notes for AI Agents

### Development Approach
- Follow the technical architecture guidelines
- Implement with proper error handling and logging
- Include comprehensive unit tests
- Document any architectural decisions

### Quality Gates
- [ ] Code review completed
- [ ] Unit tests passing (>90% coverage)
- [ ] Integration tests passing
- [ ] Acceptance criteria validated
- [ ] Documentation updated

---
*Generated using BMAD MCP Server - Story Creation Tool*
"""
        
        return formatted
