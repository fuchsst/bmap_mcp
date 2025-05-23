"""
Story validation tool using BMAD methodology.
"""

from typing import Any, Dict, List
from pydantic import BaseModel, Field
import logging

from ..base import BMadTool
from ...checklists.loader import load_checklist, execute_checklist, ChecklistExecutionResult
from ...utils.state_manager import StateManager

logger = logging.getLogger(__name__)


class StoryValidationRequest(BaseModel):
    """Request model for story validation."""
    story_content: str = Field(..., description="Story content to validate")
    checklist_types: List[str] = Field(
        default=["story_draft_checklist"],
        description="List of checklists to run against the story"
    )
    validation_mode: str = Field(
        default="standard",
        description="Validation strictness level"
    )
    story_phase: str = Field(
        default="draft",
        description="Current phase of the story"
    )


class ValidateStoryTool(BMadTool):
    """
    Validate user stories against Definition of Done and quality checklists.
    
    This tool runs comprehensive validation on user stories to ensure they meet
    BMAD quality standards and are ready for development implementation.
    """
    
    def __init__(self, state_manager: StateManager):
        super().__init__(state_manager)
        self.category = "story"
        self.description = "Validate user stories against Definition of Done checklists"
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for story validation using Pydantic model."""
        schema = StoryValidationRequest.model_json_schema()
        # Add enum constraints
        schema["properties"]["validation_mode"]["enum"] = ["strict", "standard", "lenient"]
        schema["properties"]["story_phase"]["enum"] = ["draft", "review", "ready", "in_progress", "done"]
        schema["properties"]["checklist_types"]["items"]["enum"] = [
            "story_draft_checklist", 
            "story_dod_checklist", 
            "story_review_checklist"
        ]
        return schema
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute story validation."""
        # Validate input using Pydantic
        request = StoryValidationRequest(**arguments)
        
        logger.info(f"Validating story using {len(request.checklist_types)} checklists")
        
        validation_results = []
        overall_pass_rate = 0
        total_items = 0
        total_passed = 0
        
        # Run each checklist
        for checklist_type in request.checklist_types:
            try:
                # Load and execute checklist
                checklist = load_checklist(checklist_type)
                
                validation_result = execute_checklist(
                    checklist=checklist,
                    document_content=request.story_content,
                    context={
                        "document_type": "story",
                        "story_phase": request.story_phase,
                        "validation_type": "story_quality"
                    },
                    mode=request.validation_mode
                )
                
                validation_results.append({
                    "checklist_type": checklist_type,
                    "result": validation_result
                })
                
                total_items += validation_result.total_items
                total_passed += validation_result.passed_items
                
            except FileNotFoundError:
                logger.warning(f"Checklist not found: {checklist_type}, skipping")
                continue
            except Exception as e:
                logger.error(f"Error running checklist {checklist_type}: {e}")
                continue
        
        if not validation_results:
            return "No valid checklists could be executed. Please check checklist names."
        
        # Calculate overall pass rate
        overall_pass_rate = (total_passed / total_items * 100) if total_items > 0 else 0
        
        # Format comprehensive validation report
        report = self._format_story_validation_report(
            validation_results=validation_results,
            overall_pass_rate=overall_pass_rate,
            story_phase=request.story_phase,
            document_length=len(request.story_content)
        )
        
        # Save validation report
        metadata = self.create_metadata(
            status="completed",
            story_phase=request.story_phase,
            validation_mode=request.validation_mode,
            overall_pass_rate=round(overall_pass_rate, 1),
            checklists_run=len(validation_results)
        )
        
        # Generate filename
        story_title_sanitized = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in request.story_content[:30])
        story_title_sanitized = story_title_sanitized.replace(' ', '_').lower()
        if not story_title_sanitized: # Handle empty or fully sanitized title
            story_title_sanitized = "unnamed_story"
            
        file_name = f"story_validation_{request.story_phase}_{story_title_sanitized}.md"
        artifact_path = f"checklists/{file_name}"
        
        await self.state_manager.save_artifact(artifact_path, report, metadata)
        
        logger.info(f"Story validation report saved to: {artifact_path}")
        
        return report
    
    def _format_story_validation_report(
        self, 
        validation_results: List[Dict[str, Any]], 
        overall_pass_rate: float,
        story_phase: str,
        document_length: int
    ) -> str:
        """Format comprehensive story validation report."""
        
        report = f"""# BMAD Story Validation Report

## Story Quality Assessment

### Overall Validation Summary
- **Story Phase:** {story_phase.title()}
- **Document Length:** {document_length:,} characters
- **Checklists Executed:** {len(validation_results)}
- **Overall Quality Score:** {overall_pass_rate:.1f}%

### Story Readiness Status
"""
        
        # Determine readiness based on phase and pass rate
        if story_phase == "draft":
            if overall_pass_rate >= 80:
                report += "🟢 **READY FOR REVIEW** - Story meets draft quality standards"
                readiness = "ready_for_review"
            elif overall_pass_rate >= 60:
                report += "🟡 **NEEDS MINOR IMPROVEMENTS** - Address key issues before review"
                readiness = "needs_improvements"
            else:
                report += "🔴 **NOT READY** - Significant improvements needed"
                readiness = "not_ready"
        elif story_phase == "review":
            if overall_pass_rate >= 90:
                report += "🟢 **READY FOR DEVELOPMENT** - Story meets all quality standards"
                readiness = "ready_for_development"
            elif overall_pass_rate >= 75:
                report += "🟡 **MOSTLY READY** - Minor refinements recommended"
                readiness = "mostly_ready"
            else:
                report += "🔴 **NEEDS REVISION** - Return to draft for improvements"
                readiness = "needs_revision"
        else:
            if overall_pass_rate >= 85:
                report += "🟢 **QUALITY STANDARDS MET** - Story is well-defined"
                readiness = "quality_met"
            else:
                report += "🟡 **QUALITY CONCERNS** - Consider improvements"
                readiness = "quality_concerns"
        
        # Add detailed results for each checklist
        report += "\n\n### Checklist Results\n"
        
        for validation_data in validation_results:
            checklist_type = validation_data["checklist_type"]
            result = validation_data["result"]
            
            checklist_pass_rate = (result.passed_items / result.total_items * 100) if result.total_items > 0 else 0
            status_icon = "✅" if checklist_pass_rate >= 80 else "⚠️" if checklist_pass_rate >= 60 else "❌"
            
            report += f"\n#### {checklist_type.replace('_', ' ').title()} {status_icon}\n"
            report += f"- **Score:** {checklist_pass_rate:.1f}% ({result.passed_items}/{result.total_items})\n"
            report += f"- **Failed Items:** {result.failed_items}\n"
            report += f"- **Not Applicable:** {result.na_items}\n"
            
            # Add section breakdown
            if result.section_results:
                report += "- **Section Breakdown:**\n"
                for section in result.section_results:
                    section_rate = (section.passed / section.total * 100) if section.total > 0 else 0
                    section_icon = "✅" if section_rate >= 80 else "⚠️" if section_rate >= 60 else "❌"
                    report += f"  - {section.title}: {section.passed}/{section.total} ({section_rate:.0f}%) {section_icon}\n"
        
        # Add critical issues across all checklists
        all_failed_items = []
        for validation_data in validation_results:
            all_failed_items.extend(validation_data["result"].failed_items_details)
        
        if all_failed_items:
            report += "\n\n### Critical Issues to Address\n"
            for i, item in enumerate(all_failed_items, 1):
                report += f"{i}. **{item['category']}:** {item['description']}\n"
                if item.get('recommendation'):
                    report += f"   *Action:* {item['recommendation']}\n"
        
        # Add recommendations based on readiness
        report += f"\n\n### Next Steps\n"
        if readiness == "ready_for_development":
            report += "- ✅ Story is ready for development implementation\n"
            report += "- Assign to development team\n"
            report += "- Set up development environment and dependencies\n"
        elif readiness == "ready_for_review":
            report += "- 🔄 Move story to review phase\n"
            report += "- Schedule stakeholder review\n"
            report += "- Address any remaining minor issues\n"
        elif readiness in ["needs_improvements", "mostly_ready"]:
            report += "- 🔧 Address identified issues\n"
            report += "- Re-validate after improvements\n"
            report += "- Focus on failed checklist items\n"
        else:
            report += "- ❌ Significant revision required\n"
            report += "- Return to story creation/refinement\n"
            report += "- Address all critical quality issues\n"
        
        # Add story-specific guidance
        report += f"\n\n### Story Development Guidance\n"
        if "acceptance criteria" in " ".join([item['description'].lower() for item in all_failed_items]):
            report += "- **Focus:** Improve acceptance criteria clarity and testability\n"
        if "technical" in " ".join([item['description'].lower() for item in all_failed_items]):
            report += "- **Focus:** Add more detailed technical implementation guidance\n"
        if "dependency" in " ".join([item['description'].lower() for item in all_failed_items]):
            report += "- **Focus:** Clarify dependencies and prerequisites\n"
        
        report += "- **Remember:** Stories should be self-contained and implementable by AI agents\n"
        report += "- **Quality:** Ensure all acceptance criteria are specific and testable\n"
        
        report += "\n---\n*Generated using BMAD MCP Server - Story Validation Tool*"
        return report
