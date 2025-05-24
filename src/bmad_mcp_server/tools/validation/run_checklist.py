"""
Checklist execution tool for BMAD quality validation.
Returns the validation report content to the assistant.
"""

from typing import Any, Dict, List, Literal as PyLiteral
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import logging

from ..base import BMadTool
from ...checklists.loader import load_checklist, execute_checklist, ChecklistExecutionResult
from ...utils.state_manager import StateManager
from ...crewai_integration.config import CrewAIConfig

logger = logging.getLogger(__name__)


class ChecklistType(str, Enum):
    """Available BMAD checklist types."""
    PM_CHECKLIST = "pm_checklist"
    ARCHITECT_CHECKLIST = "architect_checklist"
    FRONTEND_ARCHITECTURE_CHECKLIST = "frontend_architecture_checklist"
    STORY_DRAFT_CHECKLIST = "story_draft_checklist"
    STORY_DOD_CHECKLIST = "story_dod_checklist"
    STORY_REVIEW_CHECKLIST = "story_review_checklist"
    CHANGE_CHECKLIST = "change_checklist"


class ValidationContext(BaseModel):
    """Context for validation."""
    document_type: str = Field(default="", description="Type of document being validated")
    project_phase: str = Field(default="", description="Current project phase")
    specific_requirements: List[str] = Field(default_factory=list, description="Specific requirements to check")


class ChecklistRequest(BaseModel):
    """Request model for checklist execution."""
    document_content: str = Field(..., description="Document content to validate against checklist")
    checklist_name: ChecklistType = Field(..., description="BMAD checklist to execute")
    validation_context: ValidationContext = Field(
        default_factory=ValidationContext,
        description="Additional context for validation"
    )
    validation_mode: str = Field(
        default="standard",
        description="Validation strictness level"
    )
    # No Config.json_schema_extra needed if enums are handled by FastMCP or tool logic

class RunChecklistTool(BMadTool):
    """
    Execute BMAD checklists against documents for quality validation.
    
    This tool runs any BMAD checklist against provided documents and generates
    detailed validation reports with specific recommendations for improvement.
    It returns the report content.
    """
    
    def __init__(self, state_manager: StateManager, crew_ai_config: CrewAIConfig):
        super().__init__(state_manager, crew_ai_config)
        self.category = "validation"
        self.description = "Execute BMAD quality checklists against documents. Does not write files." # Updated
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for checklist execution using Pydantic model."""
        schema = ChecklistRequest.model_json_schema()
        # Pydantic/FastMCP should handle enum for checklist_name from ChecklistType Enum
        # Explicitly define enums for clarity if not automatically picked up
        if "enum" not in schema["properties"]["validation_mode"]:
            schema["properties"]["validation_mode"]["enum"] = ["strict", "standard", "lenient"]
        # checklist_name enum is derived from ChecklistType by Pydantic
        return schema
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute checklist validation and return report content and suggestions."""
        try:
            # Pydantic will convert string to Enum for checklist_name if it's a valid member
            args = ChecklistRequest(**arguments)
        except Exception as e:
            logger.error(f"Input validation failed for RunChecklistTool: {e}", exc_info=True)
            # Provide available checklist names in error if it's a checklist_name issue
            if "checklist_name" in str(e).lower():
                 available_checklists = ", ".join([member.value for member in ChecklistType])
                 raise ValueError(f"Invalid checklist_name. Available: {available_checklists}. Original error: {e}")
            raise ValueError(f"Invalid arguments for RunChecklistTool: {e}")

        logger.info(f"Running checklist: {args.checklist_name.value} in mode: {args.validation_mode}")
        
        checklist_name_str = args.checklist_name.value # Use the string value of the enum

        try:
            checklist_data = load_checklist(checklist_name_str)
            
            validation_result_data = execute_checklist(
                checklist=checklist_data,
                document_content=args.document_content,
                context=args.validation_context.model_dump(exclude_none=True),
                mode=args.validation_mode
            )
        except FileNotFoundError:
            error_msg = f"Checklist '{checklist_name_str}' not found."
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Error executing checklist '{checklist_name_str}': {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)

        report_content = self._format_validation_report(
            checklist_name=checklist_name_str, # Pass string value
            validation_result=validation_result_data,
            document_length=len(args.document_content)
        )
        
        # Determine a suggested path
        doc_type_suffix = args.validation_context.document_type.replace(" ", "_").lower() if args.validation_context.document_type else "document"
        report_filename = f"checklist_report_{checklist_name_str}_{doc_type_suffix}.md"
        suggested_path = f"checklists/reports/{report_filename}" # Standardized subfolder

        suggested_metadata = self.create_suggested_metadata(
            artifact_type="checklist_validation_report",
            status="completed",
            checklist_used=checklist_name_str,
            validation_mode=args.validation_mode,
            pass_rate=round((validation_result_data.passed_items / validation_result_data.total_items * 100), 1) if validation_result_data.total_items > 0 else 0,
            document_type_validated=args.validation_context.document_type
        )
        
        logger.info(f"Checklist report content generated for: {checklist_name_str}")
        
        return {
            "content": report_content,
            "suggested_path": suggested_path,
            "metadata": suggested_metadata,
            "message": f"Checklist report for '{checklist_name_str}' generated. Please review and save."
        }
    
    def _format_validation_report(
        self, 
        checklist_name: str, # Expect string here
        validation_result: ChecklistExecutionResult, 
        document_length: int
    ) -> str:
        """Format checklist validation report. Footer removed."""
        
        total_items = validation_result.total_items
        passed_items = validation_result.passed_items
        failed_items = validation_result.failed_items
        na_items = validation_result.na_items
        
        pass_rate = (passed_items / total_items * 100) if total_items > 0 else 0
        
        report = f"# BMAD Checklist Validation Report\n\n"
        report += f"## Checklist: {checklist_name.replace('_', ' ').title()}\n\n" # checklist_name is already a string
        report += f"### Validation Summary\n"
        report += f"- **Document Length:** {document_length:,} characters\n"
        report += f"- **Total Checklist Items:** {total_items}\n"
        report += f"- **Passed Items:** {passed_items} ✅\n"
        report += f"- **Failed Items:** {failed_items} ❌\n"
        report += f"- **Not Applicable:** {na_items} ⚪\n"
        report += f"- **Pass Rate:** {pass_rate:.1f}%\n\n"
        
        report += "### Overall Status\n"
        if pass_rate >= 90:
            report += "🟢 **EXCELLENT** - Document meets BMAD quality standards for this checklist.\n"
        elif pass_rate >= 80:
            report += "🟡 **GOOD** - Document meets most requirements with minor improvements needed.\n"
        elif pass_rate >= 70:
            report += "🟠 **NEEDS IMPROVEMENT** - Several areas require attention.\n"
        else:
            report += "🔴 **REQUIRES REVISION** - Significant improvements needed before proceeding.\n"
        
        if validation_result.section_results: # Added check from other tool
            report += "\n\n### Section Results\n"
            for section in validation_result.section_results:
                section_pass_rate = (section.passed / section.total * 100) if section.total > 0 else 0
                status_icon = "✅" if section_pass_rate >= 80 else "⚠️" if section_pass_rate >= 60 else "❌"
                report += f"- **{section.title}:** {section.passed}/{section.total} ({section_pass_rate:.0f}%) {status_icon}\n"

        if validation_result.failed_items_details:
            report += "\n### Failed Items Requiring Attention\n"
            for i, item in enumerate(validation_result.failed_items_details, 1):
                report += f"{i}. **{item['category']}:** {item['description']}\n"
                if item.get("recommendation"):
                    report += f"   *Recommendation:* {item['recommendation']}\n"
        
        if validation_result.recommendations:
            report += "\n### Specific Overall Recommendations\n"
            for i, rec in enumerate(validation_result.recommendations, 1):
                report += f"{i}. {rec}\n"
        
        report += f"\n### Next Steps Suggested\n"
        if pass_rate >= 80:
            report += "- Document is likely ready for the next phase concerning this checklist's scope.\n"
            report += "- Address any minor failed items for optimal quality.\n"
        else:
            report += "- Address all failed items before proceeding with activities related to this checklist.\n"
            report += "- Re-run validation after improvements.\n"
        
        # Footer removed
        return report.strip()
