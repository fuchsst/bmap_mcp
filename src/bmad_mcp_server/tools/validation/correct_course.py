"""
Course correction tool for BMAD change management.
"""

from typing import Any, Dict, List, Optional
from crewai import Agent, Crew, Task, Process
from pydantic import BaseModel, Field
import logging

from ..base import BMadTool
from ...crewai_integration.agents import get_pm_agent, get_analyst_agent
from ...utils.state_manager import StateManager

logger = logging.getLogger(__name__)


class ChangeContext(BaseModel):
    """Model for change context information."""
    change_type: str = Field(..., description="Type of change being requested")
    change_reason: str = Field(..., description="Reason for the change")
    impact_areas: List[str] = Field(default_factory=list, description="Areas impacted by the change")
    urgency: str = Field(default="medium", description="Urgency level of the change")


class CorrectCourseRequest(BaseModel):
    """Request model for course correction."""
    current_situation: str = Field(..., description="Description of current project situation")
    desired_outcome: str = Field(..., description="Desired outcome or goal")
    change_context: ChangeContext = Field(..., description="Context about the change needed")
    existing_artifacts: List[str] = Field(
        default_factory=list,
        description="List of existing project artifacts to consider"
    )
    constraints: List[str] = Field(
        default_factory=list,
        description="Constraints that must be considered"
    )


class CorrectCourseTool(BMadTool):
    """
    Handle change management scenarios using BMAD methodology.
    
    This tool provides guidance for course corrections, scope changes, and
    project pivots while maintaining BMAD quality standards and methodology.
    """
    
    def __init__(self, state_manager: StateManager):
        super().__init__(state_manager)
        self.category = "validation"
        self.description = "Handle change management scenarios and course corrections"
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for course correction using Pydantic model."""
        schema = CorrectCourseRequest.model_json_schema()
        # Add enum constraints
        schema["properties"]["change_context"]["properties"]["change_type"]["enum"] = [
            "scope_change", "requirement_change", "technical_pivot", "timeline_adjustment",
            "resource_change", "priority_shift", "architecture_change", "feature_addition",
            "feature_removal", "quality_improvement"
        ]
        schema["properties"]["change_context"]["properties"]["urgency"]["enum"] = [
            "low", "medium", "high", "critical"
        ]
        return schema
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute course correction analysis and recommendations."""
        # Validate input using Pydantic
        request = CorrectCourseRequest(**arguments)
        
        logger.info(f"Analyzing course correction for {request.change_context.change_type}")
        
        # Analyze the change impact
        impact_analysis = self._analyze_change_impact(request)
        
        # Create appropriate agent based on change type
        if request.change_context.change_type in ["scope_change", "requirement_change", "priority_shift"]:
            agent = get_pm_agent()
            agent_role = "Product Manager"
        else:
            agent = get_analyst_agent()
            agent_role = "Business Analyst"
        
        # Create course correction task
        correction_task = Task(
            description=f"""
            Analyze the following change management scenario and provide comprehensive guidance:
            
            Current Situation:
            {request.current_situation}
            
            Desired Outcome:
            {request.desired_outcome}
            
            Change Context:
            - Type: {request.change_context.change_type}
            - Reason: {request.change_context.change_reason}
            - Impact Areas: {', '.join(request.change_context.impact_areas)}
            - Urgency: {request.change_context.urgency}
            
            Existing Artifacts:
            {chr(10).join(f"- {artifact}" for artifact in request.existing_artifacts)}
            
            Constraints:
            {chr(10).join(f"- {constraint}" for constraint in request.constraints)}
            
            Impact Analysis:
            {impact_analysis}
            
            Provide a comprehensive course correction plan following BMAD methodology:
            1. Change Impact Assessment
            2. Risk Analysis and Mitigation
            3. Artifact Update Requirements
            4. Implementation Strategy
            5. Timeline and Resource Implications
            6. Quality Assurance Considerations
            7. Stakeholder Communication Plan
            8. Success Criteria and Validation
            9. Rollback Plan (if applicable)
            10. Next Steps and Action Items
            
            Ensure the plan:
            - Maintains BMAD methodology compliance
            - Addresses all identified risks and constraints
            - Provides clear, actionable guidance
            - Considers impact on existing work
            - Includes validation and quality checks
            """,
            expected_output="Comprehensive course correction plan in markdown format",
            agent=agent
        )
        
        # Execute course correction analysis
        crew = Crew(
            agents=[agent],
            tasks=[correction_task],
            process=Process.sequential,
            verbose=False
        )
        
        result = crew.kickoff()
        correction_content = result.raw if hasattr(result, 'raw') else str(result)
        
        # Format the final course correction plan
        formatted_plan = self._format_course_correction_plan(
            correction_content,
            request.change_context,
            impact_analysis
        )
        
        # Save the artifact
        metadata = self.create_metadata(
            status="completed",
            change_type=request.change_context.change_type,
            urgency=request.change_context.urgency,
            impact_areas=request.change_context.impact_areas,
            agent_role=agent_role
        )
        
        # Generate filename
        change_type_clean = request.change_context.change_type.replace("_", "-")
        situation_summary_sanitized = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in request.current_situation[:30])
        situation_summary_sanitized = situation_summary_sanitized.replace(' ', '_').lower()
        if not situation_summary_sanitized:
            situation_summary_sanitized = "unspecified_situation"
            
        file_name = f"course_correction_{change_type_clean}_{situation_summary_sanitized}.md"
        artifact_path = f"decisions/{file_name}"
        
        await self.state_manager.save_artifact(artifact_path, formatted_plan, metadata)
        
        logger.info(f"Course correction plan saved to: {artifact_path}")
        
        return formatted_plan
    
    def _analyze_change_impact(self, request: CorrectCourseRequest) -> str:
        """Analyze the potential impact of the requested change."""
        
        change_type = request.change_context.change_type
        impact_areas = request.change_context.impact_areas
        urgency = request.change_context.urgency
        
        impact_analysis = f"## Change Impact Analysis\n\n"
        
        # Analyze by change type
        if change_type == "scope_change":
            impact_analysis += "**Scope Change Impact:**\n"
            impact_analysis += "- PRD updates required\n"
            impact_analysis += "- Epic and story reassessment needed\n"
            impact_analysis += "- Timeline and resource reallocation\n"
            impact_analysis += "- Stakeholder expectation management\n"
        
        elif change_type == "requirement_change":
            impact_analysis += "**Requirement Change Impact:**\n"
            impact_analysis += "- Requirements documentation updates\n"
            impact_analysis += "- Acceptance criteria modifications\n"
            impact_analysis += "- Testing strategy adjustments\n"
            impact_analysis += "- Potential architecture implications\n"
        
        elif change_type == "technical_pivot":
            impact_analysis += "**Technical Pivot Impact:**\n"
            impact_analysis += "- Architecture document revision\n"
            impact_analysis += "- Technology stack reassessment\n"
            impact_analysis += "- Development approach changes\n"
            impact_analysis += "- Team skill requirements\n"
        
        elif change_type == "timeline_adjustment":
            impact_analysis += "**Timeline Adjustment Impact:**\n"
            impact_analysis += "- Sprint planning modifications\n"
            impact_analysis += "- Resource allocation changes\n"
            impact_analysis += "- Milestone date adjustments\n"
            impact_analysis += "- Dependency management\n"
        
        else:
            impact_analysis += f"**{change_type.replace('_', ' ').title()} Impact:**\n"
            impact_analysis += "- Project artifact updates required\n"
            impact_analysis += "- Process and workflow adjustments\n"
            impact_analysis += "- Team coordination needs\n"
            impact_analysis += "- Quality assurance considerations\n"
        
        # Add urgency considerations
        impact_analysis += f"\n**Urgency Considerations ({urgency}):**\n"
        if urgency == "critical":
            impact_analysis += "- Immediate action required\n"
            impact_analysis += "- May require emergency procedures\n"
            impact_analysis += "- High risk of project disruption\n"
        elif urgency == "high":
            impact_analysis += "- Prompt action needed\n"
            impact_analysis += "- Significant impact on timeline\n"
            impact_analysis += "- Requires priority attention\n"
        elif urgency == "medium":
            impact_analysis += "- Planned implementation recommended\n"
            impact_analysis += "- Moderate impact on project flow\n"
            impact_analysis += "- Can be integrated into normal workflow\n"
        else:  # low
            impact_analysis += "- Can be scheduled for future implementation\n"
            impact_analysis += "- Minimal immediate impact\n"
            impact_analysis += "- Consider for next planning cycle\n"
        
        # Add impact area analysis
        if impact_areas:
            impact_analysis += f"\n**Affected Areas:**\n"
            for area in impact_areas:
                impact_analysis += f"- {area}: Requires assessment and potential updates\n"
        
        return impact_analysis
    
    def _format_course_correction_plan(
        self, 
        content: str, 
        change_context: ChangeContext, 
        impact_analysis: str
    ) -> str:
        """Format course correction plan with proper structure."""
        
        formatted = f"""# BMAD Course Correction Plan

## Change Summary
- **Change Type:** {change_context.change_type.replace('_', ' ').title()}
- **Urgency Level:** {change_context.urgency.title()}
- **Impact Areas:** {', '.join(change_context.impact_areas) if change_context.impact_areas else 'To be determined'}

## Change Justification
{change_context.change_reason}

{impact_analysis}

{content}

## BMAD Methodology Compliance

### Quality Assurance
- [ ] All affected artifacts identified and updated
- [ ] Change impact fully assessed and documented
- [ ] Stakeholder approval obtained for significant changes
- [ ] Risk mitigation strategies defined
- [ ] Success criteria established

### Process Adherence
- [ ] BMAD templates used for updated artifacts
- [ ] Quality checklists run on modified documents
- [ ] Proper version control and change tracking
- [ ] Team communication completed
- [ ] Documentation updated

## Change Tracking
- **Change ID:** CC-{change_context.change_type.upper()}-{change_context.urgency.upper()}
- **Requested Date:** {self.create_metadata()['created_at']}
- **Status:** Planned
- **Approval Required:** {'Yes' if change_context.urgency in ['high', 'critical'] else 'No'}

---
*Generated using BMAD MCP Server - Course Correction Tool*
"""
        
        return formatted
