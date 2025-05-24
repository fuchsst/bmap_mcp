"""
Course correction tool for BMAD change management.
Returns a suggested course correction plan to the assistant.
"""

from typing import Any, Dict, List, Optional, Literal as PyLiteral
from datetime import datetime
from crewai import Agent, Crew, Task, Process
from pydantic import BaseModel, Field
import logging

from ..base import BMadTool
from ...crewai_integration.agents import get_pm_agent, get_analyst_agent
from ...crewai_integration.config import CrewAIConfig
from ...utils.state_manager import StateManager

logger = logging.getLogger(__name__)


class ChangeContext(BaseModel):
    """Model for change context information."""
    change_type: str = Field(..., description="Type of change being requested")
    change_reason: str = Field(..., description="Reason for the change")
    impact_areas: List[str] = Field(default_factory=list, description="Areas impacted by the change")
    urgency: str = Field(default="medium", description="Urgency level of the change")
    # No Config.json_schema_extra needed if enums are handled by FastMCP or tool logic

class CorrectCourseRequest(BaseModel):
    """Request model for course correction."""
    current_situation: str = Field(..., description="Description of current project situation")
    desired_outcome: str = Field(..., description="Desired outcome or goal")
    change_context: ChangeContext = Field(..., description="Context about the change needed")
    existing_artifacts_paths: Optional[List[str]] = Field( # Made Optional for flexibility
        default_factory=list,
        description="Paths to relevant existing artifacts (e.g., PRD, architecture doc, specific story files)"
    )
    constraints: Optional[List[str]] = Field(
        default_factory=list,
        description="Any constraints for the solution (e.g., time, budget, tech stack)"
    )


class CorrectCourseTool(BMadTool):
    """
    Handles change management scenarios using BMAD methodology.
    
    This tool provides guidance for course corrections, scope changes, and
    project pivots while maintaining BMAD quality standards and methodology.
    It returns a suggested plan.
    """
    
    def __init__(self, state_manager: StateManager, crew_ai_config: CrewAIConfig):
        super().__init__(state_manager, crew_ai_config)
        self.category = "validation" # Or "management"
        self.description = "Generates a course correction plan for change management. Does not write files."
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for course correction using Pydantic model."""
        schema = CorrectCourseRequest.model_json_schema()
        # Explicitly define enums for clarity
        # Assuming change_context is a nested schema, Pydantic should handle its enums.
        # If not, they might need to be added here.
        # Example for top-level if needed:
        # schema["properties"]["some_top_level_enum_field"]["enum"] = ["value1", "value2"]
        # For nested, Pydantic usually handles this if ChangeContext defines enums.
        # For ChangeContext.severity:
        if "properties" in schema["properties"]["change_context"] and \
           "severity" in schema["properties"]["change_context"]["properties"] and \
           "enum" not in schema["properties"]["change_context"]["properties"]["severity"]:
            schema["properties"]["change_context"]["properties"]["severity"]["enum"] = ["low", "medium", "high", "critical"]
        # For ChangeContext.change_type:
        if "properties" in schema["properties"]["change_context"] and \
           "change_type" in schema["properties"]["change_context"]["properties"] and \
           "enum" not in schema["properties"]["change_context"]["properties"]["change_type"]:
            schema["properties"]["change_context"]["properties"]["change_type"]["enum"] = [
                "scope_change", "requirement_change", "technical_pivot", "timeline_adjustment",
                "resource_change", "priority_shift", "architecture_change", "feature_addition",
                "feature_removal", "quality_improvement"
            ]
        return schema

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute course correction analysis and return plan content and suggestions."""
        try:
            args = CorrectCourseRequest(**arguments)
        except Exception as e:
            logger.error(f"Input validation failed for CorrectCourseTool: {e}", exc_info=True)
            raise ValueError(f"Invalid arguments for CorrectCourseTool: {e}")

        logger.info(f"Initiating course correction analysis for: {args.change_context.change_reason} (Severity: {args.change_context.urgency})")

        # Simplified artifact loading for prompt context - actual loading logic might be more complex
        # and might not be needed if the agent is expected to request artifacts separately.
        # For now, we'll just pass paths/identifiers to the agent.
        artifacts_summary = "Provided artifact paths/identifiers:\n" + "\n".join(
            f"- {path_str}" for path_str in args.existing_artifacts_paths
        ) if args.existing_artifacts_paths else "No specific existing artifacts paths provided for direct loading by this tool."
        
        # Create appropriate agent based on change type
        # Using PM agent as a generalist for planning/correction
        agent_to_use = get_pm_agent(config=self.crew_ai_config)
        agent_role_for_metadata = "Product Manager" # Default
        if args.change_context.change_type in ["technical_pivot", "architecture_change"]:
            # Potentially use architect agent or a specialized change analyst
            # For simplicity, PM agent handles this with context.
            pass 
        
        impact_analysis_prompt_section = self._generate_impact_analysis_prompt(args)

        task_description = f"""
        Analyze the current project situation and propose a course correction plan.

        Current Situation:
        {args.current_situation}

        Desired Outcome:
        {args.desired_outcome}

        Change Context:
        - Reason for Change: {args.change_context.change_reason}
        - Type of Change: {args.change_context.change_type}
        - Impacted Area(s): {', '.join(args.change_context.impact_areas) if args.change_context.impact_areas else 'Not specified'}
        - Severity/Urgency: {args.change_context.urgency}

        Relevant Existing Artifacts (Paths/Identifiers for your reference, content not pre-loaded by this tool):
        {artifacts_summary}

        Constraints for Solution:
        {', '.join(args.constraints) if args.constraints else 'None specified'}

        Initial Impact Analysis (consider this as a starting point):
        {impact_analysis_prompt_section}

        Your task is to generate a comprehensive course correction plan. The plan should include:
        1. Detailed Impact Assessment: Elaborate on the impact on scope, timeline, resources, quality, and existing artifacts.
        2. Proposed Solution / Action Plan: Specific, actionable steps to address the situation and achieve the desired outcome.
        3. Artifact Update Requirements: List all artifacts that need creation or modification. For modifications, specify sections and the nature of changes.
        4. Risk Analysis: Identify potential risks with the proposed plan and suggest mitigation strategies.
        5. Resource & Timeline Implications: Estimate any changes to resources or timelines.
        6. Recommended Next Steps: What should be done immediately after this plan is reviewed? Suggest relevant BMAD tools for these steps if applicable (e.g., 'generate_prd', 'create_next_story', 'run_checklist').

        Format the output as a well-structured markdown document.
        The plan must be practical, align with BMAD principles, and provide clear guidance.
        """
        
        correction_task = Task(
            description=task_description,
            expected_output="A comprehensive course correction plan in markdown format.",
            agent=agent_to_use
        )
        
        crew = Crew(
            agents=[agent_to_use],
            tasks=[correction_task],
            process=Process.sequential,
            verbose=self.crew_ai_config.verbose_logging
        )
        
        try:
            result = crew.kickoff()
            correction_plan_content = result.raw if hasattr(result, 'raw') else str(result)
        except Exception as e:
            logger.error(f"CrewAI kickoff failed for course correction: {e}", exc_info=True)
            raise Exception(f"Course correction plan generation by CrewAI failed: {e}")
        
        # Determine a suggested path
        reason_safe = args.change_context.change_reason.lower().replace(' ', '_')[:30].replace('.', '').replace('/','_').replace('\\','_')
        if not reason_safe: reason_safe = "correction"
        suggested_path = f"decisions/course_correction_plan_{reason_safe}.md" # decisions or changes folder

        suggested_metadata = self.create_suggested_metadata(
            artifact_type="course_correction_plan",
            status="plan_generated", 
            reason_for_change=args.change_context.change_reason,
            change_type=args.change_context.change_type,
            impact_area=args.change_context.impact_areas,
            severity=args.change_context.urgency
        )
        
        logger.info(f"Course correction plan content generated for: {args.change_context.change_reason}")
        
        return {
            "content": correction_plan_content,
            "suggested_path": suggested_path,
            "metadata": suggested_metadata,
            "message": "Course correction plan generated. Please review and save."
        }
    
    def _generate_impact_analysis_prompt(self, request: CorrectCourseRequest) -> str:
        """Generates a text section for the agent's prompt regarding initial impact thoughts."""
        # This method now generates a string to be included in the agent's prompt,
        # rather than performing the analysis itself directly.
        # The agent will perform the actual detailed impact analysis.
        
        change_type = request.change_context.change_type
        impact_areas = request.change_context.impact_areas
        urgency = request.change_context.urgency
        
        prompt_section = f"Initial thoughts on impact for a '{change_type}' change affecting '{', '.join(impact_areas) if impact_areas else 'unspecified areas'}' with '{urgency}' urgency:\n"
        
        if change_type == "scope_change":
            prompt_section += "- Likely requires PRD updates, re-evaluation of epics/stories, and timeline adjustments.\n"
        elif change_type == "requirement_change":
            prompt_section += "- Expect updates to requirements docs, acceptance criteria, and possibly testing plans.\n"
        elif change_type == "technical_pivot":
            prompt_section += "- Architecture docs will need revision. Tech stack and development approach may change.\n"
        # Add more specific hints for other change types if desired.
        else:
            prompt_section += "- General project artifacts may need updates. Assess impact on workflow and team coordination.\n"
        
        prompt_section += "Consider these points when formulating the detailed impact assessment."
        return prompt_section

