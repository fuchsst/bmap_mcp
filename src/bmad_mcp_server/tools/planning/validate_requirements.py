"""
Requirements validation tool using BMAD methodology.
"""

from typing import Any, Dict, List
from pydantic import BaseModel, Field
import logging

from ..base import BMadTool
from ...checklists.loader import load_checklist, execute_checklist, ChecklistExecutionResult
from ...utils.state_manager import StateManager

logger = logging.getLogger(__name__)


class RequirementsValidationRequest(BaseModel):
    """Request model for requirements validation."""
    prd_content: str = Field(..., description="PRD content to validate")
    checklist_type: str = Field(
        default="pm_checklist",
        description="Type of checklist to use for validation"
    )
    validation_mode: str = Field(
        default="standard",
        description="Validation strictness level"
    )
    include_recommendations: bool = Field(
        default=True,
        description="Whether to include improvement recommendations"
    )


class ValidateRequirementsTool(BMadTool):
    """
    Validate PRD documents against PM quality checklists using BMAD methodology.
    
    This tool runs quality validation on Product Requirements Documents to ensure
    they meet BMAD standards before proceeding to architecture phase.
    """
    
    def __init__(self, state_manager: StateManager):
        super().__init__(state_manager)
        self.category = "planning"
        self.description = "Validate PRD documents against PM quality checklists"
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for requirements validation using Pydantic model."""
        schema = RequirementsValidationRequest.model_json_schema()
        # Add enum constraints
        schema["properties"]["checklist_type"]["enum"] = ["pm_checklist", "standard", "comprehensive"]
        schema["properties"]["validation_mode"]["enum"] = ["strict", "standard", "lenient"]
        return schema
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute requirements validation."""
        # Validate input using Pydantic
        request = RequirementsValidationRequest(**arguments)
        
        logger.info(f"Validating requirements using {request.checklist_type}")
        
        try:
            # Load the appropriate checklist
            checklist_name = request.checklist_type
            if checklist_name in ["standard", "comprehensive"]:
                checklist_name = "pm_checklist"  # Map to actual file
            
            checklist = load_checklist(checklist_name)
            
            # Execute validation
            validation_result = execute_checklist(
                checklist=checklist,
                document_content=request.prd_content,
                context={"document_type": "prd", "validation_type": "requirements"},
                mode=request.validation_mode
            )
            
            # Format validation report
            report = self._format_validation_report(
                validation_result=validation_result,
                document_length=len(request.prd_content),
                include_recommendations=request.include_recommendations
            )
            
            # Save validation report
            metadata = self.create_metadata(
                status="completed",
                checklist_type=request.checklist_type,
                validation_mode=request.validation_mode,
                pass_rate=round((validation_result.passed_items / validation_result.total_items * 100), 1) if validation_result.total_items > 0 else 0
            )
            
            # Generate filename
            file_name = f"requirements_validation_{request.checklist_type}.md"
            artifact_path = f"checklists/{file_name}"
            
            await self.state_manager.save_artifact(artifact_path, report, metadata)
            
            logger.info(f"Requirements validation report saved to: {artifact_path}")
            
            return report
            
        except FileNotFoundError as e:
            error_msg = f"Checklist not found: {request.checklist_type}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Error validating requirements: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _format_validation_report(
        self, 
        validation_result: ChecklistExecutionResult, 
        document_length: int,
        include_recommendations: bool
    ) -> str:
        """Format requirements validation report."""
        
        total_items = validation_result.total_items
        passed_items = validation_result.passed_items
        failed_items = validation_result.failed_items
        na_items = validation_result.na_items
        
        pass_rate = (passed_items / total_items * 100) if total_items > 0 else 0
        
        report = f"""# BMAD Requirements Validation Report

## PRD Quality Assessment

### Validation Summary
- **Document Length:** {document_length:,} characters
- **Total Quality Items:** {total_items}
- **Passed Items:** {passed_items} ✅
- **Failed Items:** {failed_items} ❌
- **Not Applicable:** {na_items} ⚪
- **Quality Score:** {pass_rate:.1f}%

### Readiness Assessment
"""
        
        if pass_rate >= 90:
            report += "🟢 **READY FOR ARCHITECTURE** - PRD meets BMAD quality standards"
            readiness = "ready"
        elif pass_rate >= 80:
            report += "🟡 **MOSTLY READY** - Minor improvements recommended before architecture phase"
            readiness = "mostly_ready"
        elif pass_rate >= 70:
            report += "🟠 **NEEDS IMPROVEMENT** - Address key issues before proceeding"
            readiness = "needs_improvement"
        else:
            report += "🔴 **NOT READY** - Significant revision required"
            readiness = "not_ready"
        
        # Add section breakdown
        if validation_result.section_results:
            report += "\n\n### Section Quality Breakdown\n"
            for section in validation_result.section_results:
                section_pass_rate = (section.passed / section.total * 100) if section.total > 0 else 0
                status_icon = "✅" if section_pass_rate >= 80 else "⚠️" if section_pass_rate >= 60 else "❌"
                report += f"- **{section.title}:** {section.passed}/{section.total} ({section_pass_rate:.0f}%) {status_icon}\n"
        
        # Add critical issues
        if validation_result.failed_items_details and include_recommendations:
            report += "\n\n### Critical Issues to Address\n"
            for i, item in enumerate(validation_result.failed_items_details, 1):
                report += f"{i}. **{item['category']}:** {item['description']}\n"
                if item.get('recommendation'):
                    report += f"   *Action:* {item['recommendation']}\n"
        
        # Add specific recommendations
        if validation_result.recommendations and include_recommendations:
            report += "\n\n### Improvement Recommendations\n"
            for i, rec in enumerate(validation_result.recommendations, 1):
                report += f"{i}. {rec}\n"
        
        # Add next steps based on readiness
        report += f"\n\n### Next Steps\n"
        if readiness == "ready":
            report += "- ✅ PRD is ready for architecture phase\n"
            report += "- Proceed with technical architecture design\n"
            report += "- Consider addressing any remaining minor issues\n"
        elif readiness == "mostly_ready":
            report += "- 🔄 Address failed items for optimal quality\n"
            report += "- Re-validate after improvements (optional)\n"
            report += "- Can proceed to architecture with caution\n"
        else:
            report += "- ❌ Address all critical issues before proceeding\n"
            report += "- Re-run validation after improvements\n"
            report += "- Do not proceed to architecture phase yet\n"
        
        report += "\n---\n*Generated using BMAD MCP Server - Requirements Validation Tool*"
        return report
