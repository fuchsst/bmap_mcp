"""
BMAD checklist loading and execution system.
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

# Checklist directory
CHECKLIST_DIR = Path(__file__).parent

# Checklist cache
_checklist_cache: Dict[str, Dict] = {}


class ValidationMode(str, Enum):
    """Validation strictness modes."""
    STRICT = "strict"
    STANDARD = "standard"
    LENIENT = "lenient"


class ChecklistItem(BaseModel):
    """Model for a checklist item."""
    text: str = Field(..., description="Checklist item text")
    required: bool = Field(default=True, description="Whether this item is required")
    category: str = Field(..., description="Category/section this item belongs to")


class ChecklistSection(BaseModel):
    """Model for a checklist section."""
    title: str = Field(..., description="Section title")
    description: str = Field(default="", description="Section description")
    items: List[ChecklistItem] = Field(default_factory=list, description="Items in this section")


class Checklist(BaseModel):
    """Model for a complete checklist."""
    name: str = Field(..., description="Checklist name")
    sections: List[ChecklistSection] = Field(default_factory=list, description="Checklist sections")
    total_items: int = Field(default=0, description="Total number of items")


class ChecklistItemResult(BaseModel):
    """Result of evaluating a checklist item."""
    text: str = Field(..., description="Item text")
    status: str = Field(..., description="Evaluation status: pass, fail, or na")
    recommendation: str = Field(default="", description="Recommendation for improvement")


class ChecklistSectionResult(BaseModel):
    """Result of evaluating a checklist section."""
    title: str = Field(..., description="Section title")
    total: int = Field(..., description="Total items in section")
    passed: int = Field(default=0, description="Number of passed items")
    failed: int = Field(default=0, description="Number of failed items")
    na: int = Field(default=0, description="Number of N/A items")
    items: List[ChecklistItemResult] = Field(default_factory=list, description="Item results")


class ChecklistExecutionResult(BaseModel):
    """Complete result of checklist execution."""
    checklist_name: str = Field(..., description="Name of executed checklist")
    total_items: int = Field(..., description="Total items evaluated")
    passed_items: int = Field(default=0, description="Number of passed items")
    failed_items: int = Field(default=0, description="Number of failed items")
    na_items: int = Field(default=0, description="Number of N/A items")
    section_results: List[ChecklistSectionResult] = Field(default_factory=list, description="Section results")
    failed_items_details: List[Dict[str, str]] = Field(default_factory=list, description="Details of failed items")
    recommendations: List[str] = Field(default_factory=list, description="Overall recommendations")


def load_checklist(checklist_name: str) -> Checklist:
    """Load and parse a BMAD checklist."""
    if checklist_name in _checklist_cache:
        return Checklist(**_checklist_cache[checklist_name])
    
    checklist_path = CHECKLIST_DIR / f"{checklist_name}.md"
    
    if not checklist_path.exists():
        raise FileNotFoundError(f"Checklist not found: {checklist_name}")
    
    try:
        with open(checklist_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        parsed_checklist = _parse_checklist_content(content, checklist_name)
        _checklist_cache[checklist_name] = parsed_checklist.model_dump()
        
        return parsed_checklist
        
    except Exception as e:
        raise Exception(f"Error loading checklist {checklist_name}: {e}")


def _parse_checklist_content(content: str, checklist_name: str) -> Checklist:
    """Parse checklist markdown content into structured format."""
    
    checklist = Checklist(name=checklist_name)
    current_section = None
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Section headers (## or ###)
        if line.startswith('##') and not line.startswith('###'):
            if current_section:
                checklist.sections.append(current_section)
            
            section_title = line.replace('#', '').strip()
            current_section = ChecklistSection(title=section_title)
        
        # Checklist items (- [ ])
        elif line.startswith('- [ ]'):
            if current_section:
                item_text = line.replace('- [ ]', '').strip()
                item = ChecklistItem(
                    text=item_text,
                    required=True,
                    category=current_section.title
                )
                current_section.items.append(item)
                checklist.total_items += 1
        
        # Section descriptions
        elif current_section and line and not line.startswith('#') and not line.startswith('-'):
            if current_section.description:
                current_section.description += " " + line
            else:
                current_section.description = line
    
    # Add final section
    if current_section:
        checklist.sections.append(current_section)
    
    return checklist


def execute_checklist(
    checklist: Checklist, 
    document_content: str, 
    context: Optional[Dict[str, Any]] = None, 
    mode: str = "standard"
) -> ChecklistExecutionResult:
    """Execute checklist against document content."""
    
    context = context or {}
    validation_mode = ValidationMode(mode)
    
    result = ChecklistExecutionResult(
        checklist_name=checklist.name,
        total_items=checklist.total_items
    )
    
    for section in checklist.sections:
        section_result = ChecklistSectionResult(
            title=section.title,
            total=len(section.items)
        )
        
        for item in section.items:
            item_result = _evaluate_checklist_item(
                item, document_content, context, validation_mode
            )
            
            section_result.items.append(item_result)
            
            if item_result.status == "pass":
                section_result.passed += 1
                result.passed_items += 1
            elif item_result.status == "fail":
                section_result.failed += 1
                result.failed_items += 1
                result.failed_items_details.append({
                    "category": section.title,
                    "description": item.text,
                    "recommendation": item_result.recommendation
                })
            else:  # N/A
                section_result.na += 1
                result.na_items += 1
        
        result.section_results.append(section_result)
    
    # Generate overall recommendations
    result.recommendations = _generate_recommendations(result, validation_mode)
    
    return result


def _evaluate_checklist_item(
    item: ChecklistItem, 
    document_content: str, 
    context: Dict[str, Any], 
    mode: ValidationMode
) -> ChecklistItemResult:
    """Evaluate a single checklist item against document content."""
    
    item_text = item.text.lower()
    doc_lower = document_content.lower()
    
    # Simple keyword-based evaluation (in real implementation would be more sophisticated)
    evaluation_rules = {
        # Content presence rules
        "clear": lambda: any(word in doc_lower for word in ["clear", "clearly", "specific", "detailed"]),
        "goal": lambda: "goal" in doc_lower,
        "requirement": lambda: any(word in doc_lower for word in ["requirement", "must", "should", "shall"]),
        "user": lambda: "user" in doc_lower,
        "story": lambda: "story" in doc_lower,
        "acceptance": lambda: "acceptance" in doc_lower or "criteria" in doc_lower,
        "epic": lambda: "epic" in doc_lower,
        "architecture": lambda: "architecture" in doc_lower,
        "technical": lambda: any(word in doc_lower for word in ["technical", "technology", "tech"]),
        "testing": lambda: any(word in doc_lower for word in ["test", "testing", "quality"]),
        "security": lambda: "security" in doc_lower,
        
        # Structure rules
        "section": lambda: doc_lower.count("#") >= 3,  # Has multiple sections
        "list": lambda: doc_lower.count("-") >= 3,     # Has lists
        "table": lambda: "|" in doc_lower,             # Has tables
        
        # Length rules
        "comprehensive": lambda: len(document_content) > 2000,
        "detailed": lambda: len(document_content) > 1000,
        "brief": lambda: len(document_content) < 1000,
    }
    
    # Determine item status based on keywords and rules
    status = "fail"  # Default to fail
    recommendation = ""
    
    # Check if item is applicable
    if any(na_keyword in item_text for na_keyword in ["if applicable", "if needed", "optional"]):
        # Check if the optional item applies to this document
        if not any(keyword in doc_lower for keyword in ["ui", "frontend", "api", "database"]):
            status = "na"
    
    if status != "na":
        # Apply evaluation rules
        relevant_rules = []
        for keyword, rule_func in evaluation_rules.items():
            if keyword in item_text:
                relevant_rules.append(rule_func)
        
        if relevant_rules:
            # All relevant rules must pass in strict mode, most in standard, some in lenient
            rule_results = [rule() for rule in relevant_rules]
            pass_count = sum(rule_results)
            total_rules = len(rule_results)
            
            if mode == ValidationMode.STRICT:
                status = "pass" if pass_count == total_rules else "fail"
            elif mode == ValidationMode.STANDARD:
                status = "pass" if pass_count >= (total_rules * 0.7) else "fail"
            else:  # LENIENT
                status = "pass" if pass_count >= (total_rules * 0.5) else "fail"
        else:
            # No specific rules, do general content check
            if len(document_content) > 100:  # Has substantial content
                status = "pass"
    
    # Generate recommendation for failed items
    if status == "fail":
        if "clear" in item_text:
            recommendation = "Add more specific and detailed explanations"
        elif "goal" in item_text:
            recommendation = "Define clear, measurable goals"
        elif "requirement" in item_text:
            recommendation = "Add explicit requirements with clear language"
        elif "testing" in item_text:
            recommendation = "Include testing strategy and requirements"
        else:
            recommendation = "Review and enhance this aspect of the document"
    
    return ChecklistItemResult(
        text=item.text,
        status=status,
        recommendation=recommendation
    )


def _generate_recommendations(result: ChecklistExecutionResult, mode: ValidationMode) -> List[str]:
    """Generate overall recommendations based on validation results."""
    
    recommendations = []
    
    pass_rate = (result.passed_items / result.total_items * 100) if result.total_items > 0 else 0
    
    if pass_rate < 70:
        recommendations.append("Document requires significant improvement before proceeding to next phase")
        recommendations.append("Focus on addressing failed items systematically")
    elif pass_rate < 85:
        recommendations.append("Document is good but could benefit from addressing remaining failed items")
    
    # Analyze failed items by category
    failed_categories = {}
    for item in result.failed_items_details:
        category = item["category"]
        failed_categories[category] = failed_categories.get(category, 0) + 1
    
    if failed_categories:
        worst_category = max(failed_categories.items(), key=lambda x: x[1])
        recommendations.append(f"Pay special attention to '{worst_category[0]}' section - {worst_category[1]} items need improvement")
    
    return recommendations


def list_checklists() -> List[str]:
    """List available BMAD checklists."""
    return [f.stem for f in CHECKLIST_DIR.glob("*.md")]
