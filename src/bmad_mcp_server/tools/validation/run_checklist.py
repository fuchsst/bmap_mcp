"""
Checklist execution tool for BMAD quality validation.
"""

from typing import Any, Dict, List
from enum import Enum
from pydantic import BaseModel, Field
import logging

from ..base import BMadTool
from ...checklists.loader import load_checklist, execute_checklist, ChecklistExecutionResult
from ...utils.state_manager import StateManager

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
    checklist_name: str = Field(..., description="BMAD checklist to execute")
    validation_context: ValidationContext = Field(
        default_factory=ValidationContext,
        description="Additional context for validation"
    )
    validation_mode: str = Field(
        default="standard",
        description="Validation strictness level"
    )


class RunChecklistTool(BMadTool):
    """
    Execute BMAD checklists against documents for quality validation.
    
    This tool runs any BMAD checklist against provided documents and generates
    detailed validation reports with specific recommendations for improvement.
    """
    
    def __init__(self, state_manager: StateManager):
        super().__init__(state_manager)
        self.category = "validation"
        self.description = "Execute BMAD quality checklists against documents"
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for checklist execution using Pydantic model."""
        schema = ChecklistRequest.model_json_schema()
        # Add enum constraints
        schema["properties"]["checklist_name"]["enum"] = [e.value for e in ChecklistType]
        schema["properties"]["validation_mode"]["enum"] = ["strict", "standard", "lenient"]
        return schema
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute checklist validation."""
        # Validate input using Pydantic
        request = ChecklistRequest(**arguments)
        
        logger.info(f"Running checklist: {request.checklist_name}")
        
        try:
            # Load the checklist
            checklist = load_checklist(request.checklist_name)
            
            # Execute checklist against document
            validation_result = execute_checklist(
                checklist=checklist,
                document_content=request.document_content,
                context=request.validation_context.model_dump(),
                mode=request.validation_mode
            )
            
            # Format the validation report
            report = self._format_validation_report(
                checklist_name=request.checklist_name,
                validation_result=validation_result,
                document_length=len(request.document_content)
            )
            
            # Save validation report
            metadata = self.create_metadata(
                status="completed",
                checklist_name=request.checklist_name,
                validation_mode=request.validation_mode,
                pass_rate=round((validation_result.passed_items / validation_result.total_items * 100), 1) if validation_result.total_items > 0 else 0
            )
            
            # Generate filename
            file_name = f"validation_{request.checklist_name}_{request.validation_context.document_type or 'document'}.md"
            artifact_path = f"checklists/{file_name}"
            
            await self.state_manager.save_artifact(artifact_path, report, metadata)
            
            logger.info(f"Validation report saved to: {artifact_path}")
            
            return report
            
        except FileNotFoundError as e:
            error_msg = f"Checklist not found: {request.checklist_name}. Available checklists: {', '.join([e.value for e in ChecklistType])}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Error executing checklist: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _format_validation_report(
        self, 
        checklist_name: str, 
        validation_result: ChecklistExecutionResult, 
        document_length: int
    ) -> str:
        """Format checklist validation report."""
        
        total_items = validation_result.total_items
        passed_items = validation_result.passed_items
        failed_items = validation_result.failed_items
        na_items = validation_result.na_items
        
        pass_rate = (passed_items / total_items * 100) if total_items > 0 else 0
        
        report = f"""# BMAD Checklist Validation Report

## Checklist: {checklist_name.replace('_', ' ').title()}

### Validation Summary
- **Document Length:** {document_length:,} characters
- **Total Checklist Items:** {total_items}
- **Passed Items:** {passed_items} ✅
- **Failed Items:** {failed_items} ❌
- **Not Applicable:** {na_items} ⚪
- **Pass Rate:** {pass_rate:.1f}%

### Overall Status
"""
        
        if pass_rate >= 90:
            report += "🟢 **EXCELLENT** - Document meets BMAD quality standards"
        elif pass_rate >= 80:
            report += "🟡 **GOOD** - Document meets most requirements with minor improvements needed"
        elif pass_rate >= 70:
            report += "🟠 **NEEDS IMPROVEMENT** - Several areas require attention"
        else:
            report += "🔴 **REQUIRES REVISION** - Significant improvements needed before proceeding"
        
        # Add section results
        if validation_result.section_results:
            report += "\n\n### Section Results\n"
            for section in validation_result.section_results:
                section_pass_rate = (section.passed / section.total * 100) if section.total > 0 else 0
                status_icon = "✅" if section_pass_rate >= 80 else "⚠️" if section_pass_rate >= 60 else "❌"
                report += f"- **{section.title}:** {section.passed}/{section.total} ({section_pass_rate:.0f}%) {status_icon}\n"
        
        # Add detailed findings
        if validation_result.failed_items_details:
            report += "\n\n### Failed Items Requiring Attention\n"
            for i, item in enumerate(validation_result.failed_items_details, 1):
                report += f"{i}. **{item['category']}:** {item['description']}\n"
                if item.get('recommendation'):
                    report += f"   *Recommendation:* {item['recommendation']}\n"
        
        # Add recommendations
        if validation_result.recommendations:
            report += "\n\n### Specific Recommendations\n"
            for i, rec in enumerate(validation_result.recommendations, 1):
                report += f"{i}. {rec}\n"
        
        # Add next steps
        report += f"\n\n### Next Steps\n"
        if pass_rate >= 80:
            report += "- Document is ready for next phase\n"
            report += "- Address any failed items for optimal quality\n"
        else:
            report += "- Address all failed items before proceeding\n"
            report += "- Re-run validation after improvements\n"
            report += "- Consider consulting BMAD methodology documentation\n"
        
        report += "\n---\n*Generated using BMAD MCP Server - Checklist Validation Tool*"
        return report
