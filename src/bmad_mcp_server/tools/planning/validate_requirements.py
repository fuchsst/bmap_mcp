"""
Requirements validation tool using BMAD methodology.
Returns the validation report content to the assistant.
"""

from typing import Any, Dict, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field
import logging

from ..base import BMadTool
from ...checklists.loader import load_checklist, execute_checklist, ChecklistExecutionResult
from ...utils.state_manager import StateManager
from ...crewai_integration.config import CrewAIConfig

logger = logging.getLogger(__name__)


class RequirementsValidationRequest(BaseModel):
    """Request model for requirements validation."""
    prd_content: str = Field(..., description="PRD content to validate")
    checklist_type: str = Field(
        default="pm_checklist",
        description="Type of checklist to use for validation (e.g., pm_checklist)"
    )
    validation_mode: str = Field(
        default="standard",
        description="Validation strictness level"
    )
    include_recommendations: bool = Field(
        default=True,
        description="Whether to include improvement recommendations"
    )
    # No Config.json_schema_extra needed if enums are handled by FastMCP or tool logic

class ValidateRequirementsTool(BMadTool):
    """
    Validate PRD documents against PM quality checklists using BMAD methodology.
    
    This tool runs quality validation on Product Requirements Documents to ensure
    they meet BMAD standards before proceeding to architecture phase.
    It returns the report content.
    """
    
    def __init__(self, state_manager: StateManager, crew_ai_config: CrewAIConfig):
        super().__init__(state_manager, crew_ai_config)
        self.category = "planning"
        self.description = "Validate PRD documents against PM quality checklists. Does not write files." # Updated
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for requirements validation using Pydantic model."""
        schema = RequirementsValidationRequest.model_json_schema()
        # Explicitly define enums for clarity if not automatically picked up by FastMCP from Literal in server
        schema["properties"]["checklist_type"]["enum"] = ["pm_checklist", "standard", "comprehensive"]
        schema["properties"]["validation_mode"]["enum"] = ["strict", "standard", "lenient"]
        return schema
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute requirements validation and return report content and suggestions."""
        try:
            args = RequirementsValidationRequest(**arguments)
        except Exception as e:
            logger.error(f"Input validation failed for ValidateRequirementsTool: {e}", exc_info=True)
            raise ValueError(f"Invalid arguments for ValidateRequirementsTool: {e}")

        logger.info(f"Validating PRD content against checklist: {args.checklist_type}")
        
        checklist_name = args.checklist_type
        try:
            # Map conceptual checklist types to actual filenames if necessary
            if checklist_name in ["standard", "comprehensive"]: # Example mapping
                checklist_name = "pm_checklist" 
            
            checklist_data = load_checklist(checklist_name)
            
            validation_result_data = execute_checklist(
                checklist=checklist_data,
                document_content=args.prd_content,
                context={"document_type": "PRD", "validation_type": "requirements"}, # Example context
                mode=args.validation_mode
            )
        except FileNotFoundError:
            error_msg = f"Checklist '{args.checklist_type}' (resolved to '{checklist_name}') not found."
            logger.error(error_msg, exc_info=True)
            # Re-raise to be caught by server's MCP handler
            raise ValueError(error_msg) 
        except Exception as e:
            error_msg = f"Error validating requirements: {str(e)}"
            logger.error(error_msg, exc_info=True)
            # Re-raise to be caught by server's MCP handler
            raise Exception(error_msg)

        report_content = self._format_validation_report(
            validation_result=validation_result_data, # Pass the ChecklistExecutionResult object
            document_length=len(args.prd_content),
            include_recommendations=args.include_recommendations,
            checklist_name_display=args.checklist_type # Use original for display
        )
        
        # Determine a suggested path
        report_filename = f"requirements_validation_{args.checklist_type.replace(' ', '_').lower()}.md"
        suggested_path = f"checklists/{report_filename}"

        suggested_metadata = self.create_suggested_metadata(
            artifact_type="validation_report",
            status="completed",
            checklist_used=args.checklist_type,
            validation_mode=args.validation_mode,
            pass_rate=round((validation_result_data.passed_items / validation_result_data.total_items * 100), 1) if validation_result_data.total_items > 0 else 0
        )
        
        logger.info(f"Requirements validation report content generated for checklist: {args.checklist_type}")
        
        return {
            "content": report_content,
            "suggested_path": suggested_path,
            "metadata": suggested_metadata,
            "message": f"Requirements validation report for checklist '{args.checklist_type}' generated. Please review and save."
        }

    def _format_validation_report(
        self, 
        validation_result: ChecklistExecutionResult, 
        document_length: int,
        include_recommendations: bool,
        checklist_name_display: str # Added for accurate report titling
    ) -> str:
        """Format requirements validation report."""
        
        total_items = validation_result.total_items
        passed_items = validation_result.passed_items
        failed_items = validation_result.failed_items
        na_items = validation_result.na_items
        
        pass_rate = (passed_items / total_items * 100) if total_items > 0 else 0
        
        report = f"# BMAD Requirements Validation Report\n\n"
        report += f"## Checklist: {checklist_name_display.replace('_', ' ').title()}\n\n" # Use display name
        report += f"### Validation Summary\n"
        report += f"- **Document Length:** {document_length:,} characters\n"
        report += f"- **Total Quality Items:** {total_items}\n"
        report += f"- **Passed Items:** {passed_items} ✅\n"
        report += f"- **Failed Items:** {failed_items} ❌\n"
        report += f"- **Not Applicable:** {na_items} ⚪\n"
        report += f"- **Quality Score:** {pass_rate:.1f}%\n\n"
        
        report += "### Readiness Assessment\n"
        readiness = "not_ready" # Default
        if pass_rate >= 90:
            report += "🟢 **READY FOR ARCHITECTURE** - PRD meets BMAD quality standards\n"
            readiness = "ready"
        elif pass_rate >= 80:
            report += "🟡 **MOSTLY READY** - Minor improvements recommended before architecture phase\n"
            readiness = "mostly_ready"
        elif pass_rate >= 70:
            report += "🟠 **NEEDS IMPROVEMENT** - Address key issues before proceeding\n"
            readiness = "needs_improvement"
        else:
            report += "🔴 **NOT READY** - Significant revision required\n"
            # readiness remains "not_ready"
        
        if validation_result.section_results:
            report += "\n\n### Section Quality Breakdown\n"
            for section in validation_result.section_results:
                section_pass_rate = (section.passed / section.total * 100) if section.total > 0 else 0
                status_icon = "✅" if section_pass_rate >= 80 else "⚠️" if section_pass_rate >= 60 else "❌"
                report += f"- **{section.title}:** {section.passed}/{section.total} ({section_pass_rate:.0f}%) {status_icon}\n"
        
        if validation_result.failed_items_details and include_recommendations:
            report += "\n\n### Critical Issues to Address\n"
            for i, item in enumerate(validation_result.failed_items_details, 1):
                report += f"{i}. **{item['category']}:** {item['description']}\n"
                if item.get('recommendation'):
                    report += f"   *Action:* {item['recommendation']}\n"
        
        if validation_result.recommendations and include_recommendations:
            report += "\n\n### Improvement Recommendations\n"
            for i, rec in enumerate(validation_result.recommendations, 1):
                report += f"{i}. {rec}\n"
        
        report += f"\n\n### Next Steps Suggested\n"
        if readiness == "ready":
            report += "- ✅ PRD is ready for architecture phase.\n"
            report += "- Proceed with technical architecture design.\n"
            report += "- Consider addressing any remaining minor issues for optimal quality.\n"
        elif readiness == "mostly_ready":
            report += "- 🔄 Address failed items for optimal quality.\n"
            report += "- Re-validate after improvements (optional).\n"
            report += "- Can proceed to architecture with caution, ensuring identified gaps are covered.\n"
        else:
            report += "- ❌ Address all critical issues before proceeding.\n"
            report += "- Re-run validation after improvements.\n"
            report += "- Do not proceed to architecture phase until quality standards are met.\n"
        
        # Removed the footer: "*Generated using BMAD MCP Server...*"
        return report.strip()
