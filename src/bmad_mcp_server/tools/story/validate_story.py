"""
Story validation tool using BMAD methodology.
Returns the validation report content to the assistant.
"""

import json
from typing import Any, Dict, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field
import logging

from ..base import BMadTool
from ...checklists.loader import load_checklist, execute_checklist, ChecklistExecutionResult
from ...utils.state_manager import StateManager
from ...crewai_integration.config import CrewAIConfig

logger = logging.getLogger(__name__)


class StoryValidationRequest(BaseModel):
    """Request model for story validation."""
    story_content: str = Field(..., description="Story content to validate")
    checklist_types: List[str] = Field(
        default_factory=lambda: ["story_draft_checklist"], # Default to draft checklist
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
    # No Config.json_schema_extra needed if enums are handled by FastMCP or tool logic

class ValidateStoryTool(BMadTool):
    """
    Validate user stories against Definition of Done and quality checklists.
    
    This tool runs comprehensive validation on user stories to ensure they meet
    BMAD quality standards and are ready for development implementation.
    It returns the report content.
    """
    
    def __init__(self, state_manager: StateManager, crew_ai_config: CrewAIConfig):
        super().__init__(state_manager, crew_ai_config)
        self.category = "story"
        self.description = "Validate user stories against BMAD checklists. Does not write files."
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for story validation using Pydantic model."""
        schema = StoryValidationRequest.model_json_schema()
        # Explicitly define enums for clarity
        schema["properties"]["validation_mode"]["enum"] = ["strict", "standard", "lenient"]
        schema["properties"]["story_phase"]["enum"] = ["draft", "review", "ready", "in_progress", "done"]
        # Ensure items for checklist_types also has enum if it's a list of literals server-side
        if "items" not in schema["properties"]["checklist_types"]: # Should be there from Pydantic List[str]
             schema["properties"]["checklist_types"]["items"] = {} # Add if missing, though unlikely
        schema["properties"]["checklist_types"]["items"]["enum"] = [
            "story_draft_checklist", 
            "story_dod_checklist", 
            "story_review_checklist"
        ]
        return schema
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute story validation and return report content and suggestions."""
        try:
            args = StoryValidationRequest(**arguments)
        except Exception as e:
            logger.error(f"Input validation failed for ValidateStoryTool: {e}", exc_info=True)
            raise ValueError(f"Invalid arguments for ValidateStoryTool: {e}")

        logger.info(f"Validating story content using checklists: {', '.join(args.checklist_types)}")
        
        validation_reports_content = []
        all_results_summary = [] # To store ChecklistExecutionResult objects or key stats
        
        for checklist_name_input in args.checklist_types:
            try:
                checklist_data = load_checklist(checklist_name_input)
                
                validation_result_data = execute_checklist(
                    checklist=checklist_data,
                    document_content=args.story_content,
                    context={"document_type": "story", "story_phase": args.story_phase},
                    mode=args.validation_mode
                )
                all_results_summary.append(validation_result_data) # Store full result object
                
                # Format individual checklist report section
                report_section = self._format_individual_checklist_report(
                    checklist_name=checklist_name_input,
                    validation_result=validation_result_data
                )
                validation_reports_content.append(report_section)
                    
            except FileNotFoundError:
                error_msg = f"Checklist '{checklist_name_input}' not found."
                logger.warning(error_msg)
                validation_reports_content.append(f"## Checklist: {checklist_name_input}\nError: {error_msg}\n")
            except Exception as e:
                error_msg = f"Error validating story with {checklist_name_input}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                validation_reports_content.append(f"## Checklist: {checklist_name_input}\nError: {error_msg}\n")

        if not all_results_summary: # If no checklists were run successfully
            return {
                "content": "No valid checklists could be executed. Please check checklist names.",
                "suggested_path": None,
                "metadata": self.create_suggested_metadata(artifact_type="story_validation_report", status="error_no_checklists"),
                "message": "Story validation failed: No checklists could be run."
            }

        # Create a consolidated report
        full_report_content = self._create_consolidated_report(
            args=args,
            all_results_summary=all_results_summary,
            individual_reports_content="\n\n---\n\n".join(validation_reports_content)
        )
        
        # Determine a suggested path
        story_title_line = args.story_content.split('\n', 1)[0] # Get first line for a hint
        safe_title = "".join(c if c.isalnum() else '_' for c in story_title_line[:30]).strip('_').lower()
        if not safe_title: safe_title = "story"
        
        suggested_path = f"checklists/stories/validation_{safe_title}_{args.story_phase}.md"

        # Calculate overall pass rate for metadata
        total_items_overall = sum(res.total_items for res in all_results_summary)
        total_passed_overall = sum(res.passed_items for res in all_results_summary)
        overall_pass_rate_value = (total_passed_overall / total_items_overall * 100) if total_items_overall > 0 else 0

        suggested_metadata = self.create_suggested_metadata(
            artifact_type="story_validation_report",
            status="completed",
            checklists_used=args.checklist_types,
            validation_mode=args.validation_mode,
            story_phase=args.story_phase,
            overall_pass_rate=round(overall_pass_rate_value, 1)
        )
        
        logger.info(f"Story validation report content generated for checklists: {', '.join(args.checklist_types)}")
        
        return {
            "content": full_report_content,
            "suggested_path": suggested_path,
            "metadata": suggested_metadata,
            "message": f"Story validation report generated using {len(args.checklist_types)} checklist(s). Please review and save."
        }

    def _format_individual_checklist_report(
        self, 
        checklist_name: str, 
        validation_result: ChecklistExecutionResult
    ) -> str:
        """Formats a report section for a single checklist execution."""
        total_items = validation_result.total_items
        passed_items = validation_result.passed_items
        failed_items = validation_result.failed_items
        na_items = validation_result.na_items
        pass_rate = (passed_items / total_items * 100) if total_items > 0 else 0
        
        status_emoji = "🟢" if pass_rate >= 85 else "🟡" if pass_rate >= 70 else "🔴"

        report_section = f"## Checklist: {checklist_name.replace('_', ' ').title()} {status_emoji}\n"
        report_section += f"- **Pass Rate:** {pass_rate:.1f}% ({passed_items}/{total_items})\n"
        report_section += f"- Items Passed: {passed_items}, Failed: {failed_items}, N/A: {na_items}\n"

        if validation_result.failed_items_details:
            report_section += "\n**Failed Items:**\n"
            for item in validation_result.failed_items_details:
                report_section += f"  - **{item['category']}:** {item['description']}"
                if item.get('recommendation'):
                    report_section += f" (Recommendation: {item['recommendation']})\n"
                else:
                    report_section += "\n"
        
        if validation_result.recommendations:
            report_section += "\n**Overall Recommendations for this Checklist:**\n"
            for rec in validation_result.recommendations:
                report_section += f"- {rec}\n"
        return report_section.strip()

    def _create_consolidated_report(
        self,
        args: StoryValidationRequest,
        all_results_summary: List[ChecklistExecutionResult],
        individual_reports_content: str
    ) -> str:
        """Creates the final consolidated report string."""
        total_items_overall = sum(res.total_items for res in all_results_summary)
        total_passed_overall = sum(res.passed_items for res in all_results_summary)
        overall_pass_rate = (total_passed_overall / total_items_overall * 100) if total_items_overall > 0 else 0

        report = f"# BMAD Story Validation Report\n\n"
        report += f"## Overall Summary\n"
        report += f"- **Story Phase:** {args.story_phase.title()}\n"
        report += f"- **Document Length:** {len(args.story_content):,} characters\n"
        report += f"- **Checklists Executed:** {len(args.checklist_types)}\n"
        report += f"- **Overall Quality Score:** {overall_pass_rate:.1f}%\n"

        report += "\n### Story Readiness Status\n"
        readiness_message = "Status Undetermined"
        if args.story_phase == "draft":
            if overall_pass_rate >= 80: readiness_message = "🟢 READY FOR REVIEW - Story meets draft quality standards."
            elif overall_pass_rate >= 60: readiness_message = "🟡 NEEDS MINOR IMPROVEMENTS - Address key issues before review."
            else: readiness_message = "🔴 NOT READY - Significant improvements needed."
        elif args.story_phase == "review":
            if overall_pass_rate >= 90: readiness_message = "🟢 READY FOR DEVELOPMENT - Story meets all quality standards."
            elif overall_pass_rate >= 75: readiness_message = "🟡 MOSTLY READY - Minor refinements recommended."
            else: readiness_message = "🔴 NEEDS REVISION - Return to draft for improvements."
        else: # e.g. "ready", "in_progress", "done"
            if overall_pass_rate >= 85: readiness_message = "🟢 QUALITY STANDARDS MET - Story is well-defined for its phase."
            else: readiness_message = "🟡 QUALITY CONCERNS - Consider improvements based on phase."
        report += f"{readiness_message}\n"
        
        report += "\n---\n"
        report += individual_reports_content
        
        # Add combined critical issues if any
        all_failed_items_details_combined = []
        for res_summary in all_results_summary:
            all_failed_items_details_combined.extend(res_summary.failed_items_details)
        
        if all_failed_items_details_combined:
            report += "\n\n---\n## Combined Critical Issues to Address (All Checklists)\n"
            unique_failed_items = {json.dumps(item, sort_keys=True): item for item in all_failed_items_details_combined}.values() # Crude deduplication
            for i, item_dict in enumerate(unique_failed_items, 1):
                report += f"{i}. **{item_dict.get('category', 'N/A')}:** {item_dict.get('description', 'N/A')}\n"
                if item_dict.get('recommendation'):
                    report += f"   *Action:* {item_dict.get('recommendation')}\n"

        report += "\n\n---\n" # Footer for the whole report
        report += "End of BMAD Story Validation Report."
        return report.strip()
