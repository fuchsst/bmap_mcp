# bmad-mcp-server/src/bmad_mcp_server/tools/planning/generate_prd.py
"""
PRD generation tool using BMAD methodology.
"""

import json
from typing import Any, Dict
from crewai import Agent, Crew, Task, Process
from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel

from ...tools.base import BMadTool
from ...crewai_integration.agents import get_pm_agent
from ...templates.loader import load_template

class PRDGenerationState(BaseModel):
    """State for PRD generation flow."""
    project_brief: str = ""
    workflow_mode: str = "incremental"
    technical_depth: str = "standard"
    prd_content: str = ""
    epics_count: int = 0

class PRDGenerationFlow(Flow[PRDGenerationState]):
    """CrewAI Flow for PRD generation using BMAD methodology."""
    
    @start()
    def analyze_brief(self):
        """Analyze the project brief and set parameters."""
        # Extract key information from the brief
        brief_lines = self.state.project_brief.split('\n')
        
        # Simple analysis - in real implementation would be more sophisticated
        if len(brief_lines) > 50:
            self.state.technical_depth = "detailed"
        elif len(brief_lines) < 20:
            self.state.technical_depth = "basic"
        
        return "Brief analyzed"
    
    @listen(analyze_brief)
    def generate_prd_content(self, _):
        """Generate PRD using PM agent."""
        pm_agent = get_pm_agent()
        
        # Create PRD generation task
        prd_task = Task(
            description=f"""
            Create a comprehensive Product Requirements Document (PRD) based on this project brief:
            
            {self.state.project_brief}
            
            Workflow mode: {self.state.workflow_mode}
            Technical depth: {self.state.technical_depth}
            
            Follow the BMAD PRD template structure:
            1. Goal, Objective and Context
            2. Functional Requirements (MVP)
            3. Non Functional Requirements (MVP)
            4. User Interaction and Design Goals (if UI applicable)
            5. Technical Assumptions
            6. Epic Overview with detailed user stories
            7. Out of Scope Ideas Post MVP
            
            Ensure each epic has:
            - Clear goal statement
            - 3-5 well-defined user stories
            - Specific acceptance criteria for each story
            - Logical sequencing and dependencies
            
            Focus on creating actionable, development-ready requirements.
            """,
            expected_output="Complete PRD document in markdown format following BMAD template",
            agent=pm_agent
        )
        
        # Execute PRD generation
        crew = Crew(
            agents=[pm_agent],
            tasks=[prd_task],
            process=Process.sequential,
            verbose=False
        )
        
        result = crew.kickoff()
        self.state.prd_content = result.raw
        
        # Count epics
        self.state.epics_count = self.state.prd_content.count("Epic ")
        
        return "PRD generated"

class GeneratePRDTool(BMadTool):
    """
    Generate comprehensive PRD with epics and user stories using BMAD methodology.
    
    This tool transforms project briefs into detailed Product Requirements Documents
    with well-structured epics, user stories, and technical guidance.
    It returns the generated content for the assistant to handle.
    """
    
    def __init__(self, state_manager=None): # Added state_manager
        super().__init__(state_manager)    # Pass state_manager to base
        self.category = "planning"
        self.description = "Generates content for a comprehensive PRD with epics and user stories from project brief. Does not write files."
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for PRD generation."""
        return {
            "type": "object",
            "properties": {
                "project_brief": {
                    "type": "string",
                    "description": "Complete project brief content to base PRD on"
                },
                "workflow_mode": {
                    "type": "string",
                    "enum": ["incremental", "yolo"],
                    "description": "PRD generation approach - incremental for step-by-step, yolo for comprehensive",
                    "default": "incremental"
                },
                "technical_depth": {
                    "type": "string",
                    "enum": ["basic", "standard", "detailed"],
                    "description": "Level of technical detail to include",
                    "default": "standard"
                },
                "include_architecture_prompt": {
                    "type": "boolean",
                    "description": "Whether to include architect prompt in PRD",
                    "default": True
                }
            },
            "required": ["project_brief"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]: # Returns Dict
        """Execute PRD generation and return content and suggestions."""
        validated_args = self.validate_input(arguments)
        
        project_brief_content = validated_args["project_brief"]
        
        # Create and configure flow
        flow = PRDGenerationFlow()
        flow.state.project_brief = project_brief_content
        flow.state.workflow_mode = validated_args.get("workflow_mode", "incremental")
        flow.state.technical_depth = validated_args.get("technical_depth", "standard")
        
        # Execute the flow
        flow.kickoff() # kickoff is synchronous in the example, result is in flow.state
        
        prd_content = flow.state.prd_content
        
        # Optionally add architect prompt if requested
        if validated_args.get("include_architecture_prompt", True):
            arch_prompt = """
---

## Initial Architect Prompt

Based on the requirements analysis above, please create a comprehensive technical architecture that:

1. **Supports all functional and non-functional requirements**
2. **Follows the technical assumptions and constraints outlined**
3. **Provides clear technology stack selections with justification**
4. **Includes detailed component design and data flow**
5. **Addresses security, scalability, and performance considerations**
6. **Optimizes for AI agent implementation and BMAD methodology**

Use the BMAD architecture template and ensure the design enables efficient development execution by AI agents following the defined epics and stories.
"""
            prd_content += arch_prompt

        # Determine a suggested path (example, can be more sophisticated)
        # Extracting a title or topic from the brief for the filename
        brief_title_line = project_brief_content.split('\n', 1)[0]
        safe_title = brief_title_line.replace("#", "").strip().lower().replace(' ', '_').replace(':', '').replace('/', '_')
        if not safe_title or len(safe_title) > 50: # Fallback for very long or empty titles
            safe_title = "prd_document"
        
        suggested_path = f"prd/{safe_title}.md"

        suggested_metadata = {
            "artifact_type": "prd",
            "status": "draft",
            "workflow_mode": flow.state.workflow_mode,
            "technical_depth": flow.state.technical_depth,
            "epics_count": flow.state.epics_count,
            "generated_by_tool": self.name,
            "timestamp": datetime.now().isoformat() # Added import for datetime
        }
        
        return {
            "content": prd_content,
            "suggested_path": suggested_path,
            "metadata": suggested_metadata,
            "message": "PRD content generated. Please review and save."
        }

    # _format_prd method is integrated into execute or handled by CrewAI agent's expected output.
    # The footer "*Generated using BMAD MCP Server...*" should be omitted as the server isn't writing the file.

# bmad-mcp-server/src/bmad_mcp_server/tools/validation/run_checklist.py
"""
Checklist execution tool for BMAD quality validation.
"""

import json
from typing import Any, Dict, List
from enum import Enum

from ...tools.base import BMadTool
from ...checklists.loader import load_checklist, execute_checklist

class ChecklistType(str, Enum):
    """Available BMAD checklist types."""
    PM_CHECKLIST = "pm_checklist"
    ARCHITECT_CHECKLIST = "architect_checklist" 
    FRONTEND_ARCHITECTURE_CHECKLIST = "frontend_architecture_checklist"
    STORY_DRAFT_CHECKLIST = "story_draft_checklist"
    STORY_DOD_CHECKLIST = "story_dod_checklist"
    CHANGE_CHECKLIST = "change_checklist"

class RunChecklistTool(BMadTool):
    """
    Execute BMAD checklists against documents for quality validation.
    
    This tool runs any BMAD checklist against provided documents and generates
    detailed validation reports with specific recommendations for improvement.
    The report content is returned to the assistant.
    """
    
    def __init__(self, state_manager=None): # Added state_manager
        super().__init__(state_manager)    # Pass state_manager to base
        self.category = "validation"
        self.description = "Executes BMAD quality checklists against documents and returns the validation report. Does not write files."
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for checklist execution."""
        return {
            "type": "object",
            "properties": {
                "document_content": {
                    "type": "string",
                    "description": "Document content to validate against checklist"
                },
                "checklist_name": {
                    "type": "string",
                    "enum": [e.value for e in ChecklistType],
                    "description": "BMAD checklist to execute"
                },
                "validation_context": {
                    "type": "object",
                    "description": "Additional context for validation",
                    "properties": {
                        "document_type": {"type": "string"},
                        "project_phase": {"type": "string"},
                        "specific_requirements": {"type": "array", "items": {"type": "string"}}
                    },
                    "default": {}
                },
                "validation_mode": {
                    "type": "string",
                    "enum": ["strict", "standard", "lenient"],
                    "description": "Validation strictness level",
                    "default": "standard"
                }
            },
            "required": ["document_content", "checklist_name"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]: # Returns Dict
        """Execute checklist validation and return report content."""
        validated_args = self.validate_input(arguments)
        
        document_content = validated_args["document_content"]
        checklist_name_str = validated_args["checklist_name"]
        # Ensure checklist_name is a string, as ChecklistType enum might be passed if schema is not strictly enforced by client
        checklist_name = checklist_name_str if isinstance(checklist_name_str, str) else checklist_name_str.value

        validation_context = validated_args.get("validation_context", {})
        validation_mode = validated_args.get("validation_mode", "standard")
        
        # Load the checklist
        checklist_data = load_checklist(checklist_name) # load_checklist is from ...checklists.loader
        
        # Execute checklist against document
        validation_result_data = execute_checklist( # execute_checklist is from ...checklists.loader
            checklist=checklist_data,
            document_content=document_content,
            context=validation_context,
            mode=validation_mode
        )
        
        # Format the validation report (this internal formatting is fine)
        report_content = self._format_validation_report(
            checklist_name=checklist_name,
            validation_result=validation_result_data,
            document_length=len(document_content)
        )
        
        # Determine a suggested path
        # Example: validation_report_pm_checklist_on_mydoc.md
        # This requires knowing the original document's name, which is not in args.
        # So, a generic name or one based on checklist.
        safe_checklist_name = checklist_name.lower().replace(' ', '_')
        suggested_path = f"checklists/validation_report_{safe_checklist_name}.md"

        suggested_metadata = {
            "artifact_type": "validation_report",
            "status": "completed", # Reports are typically complete once generated
            "checklist_used": checklist_name,
            "validation_mode": validation_mode,
            "pass_rate": (validation_result_data.get("passed_items", 0) / validation_result_data.get("total_items", 1) * 100),
            "generated_by_tool": self.name,
            "timestamp": datetime.now().isoformat() # Added import for datetime
        }

        return {
            "content": report_content,
            "suggested_path": suggested_path,
            "metadata": suggested_metadata,
            "message": f"Validation report for checklist '{checklist_name}' generated. Please review and save."
        }
    
    def _format_validation_report(self, checklist_name: str, validation_result: Dict, document_length: int) -> str:
        """Format checklist validation report. (Internal helper, footer will be removed)"""
        
        total_items = validation_result.get("total_items", 0)
        passed_items = validation_result.get("passed_items", 0)
        failed_items = validation_result.get("failed_items", 0)
        na_items = validation_result.get("na_items", 0)
        
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
        
        if validation_result.get("failed_items_details"):
            report += "\n\n### Failed Items Requiring Attention\n"
            for i, item in enumerate(validation_result["failed_items_details"], 1):
                report += f"{i}. **{item['category']}:** {item['description']}\n"
                if item.get("recommendation"):
                    report += f"   *Recommendation:* {item['recommendation']}\n"
        
        if validation_result.get("recommendations"):
            report += "\n\n### Specific Recommendations\n"
            for i, rec in enumerate(validation_result["recommendations"], 1):
                report += f"{i}. {rec}\n"
        
        report += f"\n\n### Next Steps\n"
        if pass_rate >= 80:
            report += "- Document is ready for next phase\n"
            report += "- Address any failed items for optimal quality\n"
        else:
            report += "- Address all failed items before proceeding\n"
            report += "- Re-run validation after improvements\n"
            report += "- Consider consulting BMAD methodology documentation\n"
        
        # Removed the footer: "*Generated using BMAD MCP Server - Checklist Validation Tool*"
        return report.strip()


# bmad-mcp-server/src/bmad_mcp_server/tools/architecture/create_architecture.py
"""
Architecture creation tool using BMAD methodology.
"""

from typing import Any, Dict
from crewai import Agent, Crew, Task, Process
from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel

from ...tools.base import BMadTool
from ...crewai_integration.agents import get_architect_agent
from ...templates.loader import load_template

class ArchitectureGenerationState(BaseModel):
    """State for architecture generation flow."""
    prd_content: str = ""
    tech_preferences: Dict[str, Any] = {}
    architecture_type: str = "monolith"
    architecture_content: str = ""
    complexity_score: int = 5

class ArchitectureGenerationFlow(Flow[ArchitectureGenerationState]):
    """CrewAI Flow for architecture generation using BMAD methodology."""
    
    @start()
    def analyze_requirements(self):
        """Analyze PRD requirements and determine architecture complexity."""
        
        # Analyze PRD complexity
        prd_lines = len(self.state.prd_content.split('\n'))
        epic_count = self.state.prd_content.count("Epic ")
        integration_count = self.state.prd_content.lower().count("integration")
        api_count = self.state.prd_content.lower().count("api")
        
        # Calculate complexity score (1-10)
        complexity_factors = [
            min(prd_lines // 50, 3),  # Document size
            min(epic_count, 3),       # Number of epics
            min(integration_count, 2), # Integration complexity
            min(api_count, 2)         # API complexity
        ]
        
        self.state.complexity_score = min(sum(complexity_factors), 10)
        
        # Suggest architecture type based on complexity
        if self.state.complexity_score >= 8:
            self.state.architecture_type = "microservices"
        elif self.state.complexity_score >= 6:
            self.state.architecture_type = "modular_monolith"
        
        return "Requirements analyzed"
    
    @listen(analyze_requirements)
    def generate_architecture(self, _):
        """Generate architecture document using Architect agent."""
        
        architect_agent = get_architect_agent()
        
        # Prepare technology preferences
        tech_prefs_text = ""
        if self.state.tech_preferences:
            tech_prefs_text = f"Technology Preferences: {json.dumps(self.state.tech_preferences, indent=2)}"
        
        architecture_task = Task(
            description=f"""
            Create a comprehensive technical architecture document based on these requirements:
            
            {self.state.prd_content}
            
            Architecture Parameters:
            - Recommended Architecture Type: {self.state.architecture_type}
            - Complexity Score: {self.state.complexity_score}/10
            {tech_prefs_text}
            
            Follow the BMAD architecture template structure:
            1. Technical Summary
            2. High-Level Overview with architecture diagrams (Mermaid)
            3. Architectural/Design Patterns Adopted
            4. Component View with detailed descriptions
            5. Project Structure with complete directory layout
            6. API Reference for external and internal APIs
            7. Data Models with complete schemas
            8. Definitive Tech Stack Selections (specific versions)
            9. Infrastructure and Deployment Overview
            10. Error Handling Strategy
            11. Coding Standards (focused on AI agent implementation)
            12. Overall Testing Strategy
            13. Security Best Practices
            
            Ensure the architecture:
            - Supports all functional and non-functional requirements
            - Is optimized for AI agent implementation
            - Follows BMAD best practices
            - Includes specific technology versions and justifications
            - Provides clear implementation guidance
            """,
            expected_output="Complete architecture document in markdown format following BMAD template",
            agent=architect_agent
        )
        
        # Execute architecture generation
        crew = Crew(
            agents=[architect_agent],
            tasks=[architecture_task],
            process=Process.sequential,
            verbose=False
        )
        
        result = crew.kickoff()
        self.state.architecture_content = result.raw
        
        return "Architecture generated"

class CreateArchitectureTool(BMadTool):
    """
    Generate technical architecture from PRD requirements using BMAD methodology.
    
    This tool creates comprehensive architecture documents with technology selections,
    component designs, and implementation guidance optimized for AI agent development.
    It returns the generated content for the assistant to handle.
    """
    
    def __init__(self, state_manager=None): # Added state_manager
        super().__init__(state_manager)    # Pass state_manager to base
        self.category = "architecture"
        self.description = "Generates content for a comprehensive technical architecture from PRD requirements. Does not write files."
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for architecture creation."""
        return {
            "type": "object",
            "properties": {
                "prd_content": {
                    "type": "string",
                    "description": "Complete PRD content with requirements and epics"
                },
                "tech_preferences": {
                    "type": "object",
                    "description": "Technology preferences and constraints",
                    "properties": {
                        "backend_framework": {"type": "string"},
                        "frontend_framework": {"type": "string"},
                        "database": {"type": "string"},
                        "cloud_provider": {"type": "string"},
                        "programming_language": {"type": "string"},
                        "api_style": {"type": "string", "enum": ["REST", "GraphQL", "gRPC"]},
                        "deployment_style": {"type": "string", "enum": ["containers", "serverless", "traditional"]}
                    },
                    "default": {}
                },
                "architecture_type": {
                    "type": "string",
                    "enum": ["monolith", "modular_monolith", "microservices", "serverless"],
                    "description": "Preferred architecture pattern",
                    "default": "monolith"
                },
                "include_frontend_prompt": {
                    "type": "boolean",
                    "description": "Whether to include frontend architect prompt",
                    "default": True
                }
            },
            "required": ["prd_content"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]: # Returns Dict
        """Execute architecture generation and return content and suggestions."""
        validated_args = self.validate_input(arguments)
        
        prd_content_input = validated_args["prd_content"]

        # Create and configure flow
        flow = ArchitectureGenerationFlow()
        flow.state.prd_content = prd_content_input
        flow.state.tech_preferences = validated_args.get("tech_preferences", {})
        flow.state.architecture_type = validated_args.get("architecture_type", "monolith")
        
        # Execute the flow
        flow.kickoff() # kickoff is synchronous, result in flow.state
        
        architecture_content = flow.state.architecture_content
        
        # Optionally add frontend prompt if requested
        if validated_args.get("include_frontend_prompt", True) and "frontend" in architecture_content.lower():
            frontend_prompt = """
---

## Prompt for Design Architect (Frontend Architecture Mode)

Based on the main architecture document above, please create a comprehensive frontend architecture that:

1. **Aligns with the main technical architecture and technology selections**
2. **Follows the BMAD frontend architecture template**
3. **Defines component strategy, state management, and routing approaches**
4. **Includes build, bundling, and deployment specifications**
5. **Addresses performance, accessibility, and testing requirements**
6. **Optimizes for AI agent implementation with clear patterns and conventions**

Use the main architecture's technology stack as the foundation and elaborate on frontend-specific concerns while maintaining consistency with the overall system design.
"""
            architecture_content += frontend_prompt
        
        # Determine a suggested path
        # Example: architecture_document_monolith.md
        arch_type_suffix = flow.state.architecture_type.lower().replace(' ', '_')
        suggested_path = f"architecture/architecture_document_{arch_type_suffix}.md"

        suggested_metadata = {
            "artifact_type": "architecture_document",
            "status": "draft",
            "architecture_type": flow.state.architecture_type,
            "complexity_score": flow.state.complexity_score,
            "tech_preferences_used": flow.state.tech_preferences,
            "generated_by_tool": self.name,
            "timestamp": datetime.now().isoformat() # Added import for datetime
        }

        return {
            "content": architecture_content,
            "suggested_path": suggested_path,
            "metadata": suggested_metadata,
            "message": "Architecture document content generated. Please review and save."
        }

    # _format_architecture method is integrated into execute or handled by CrewAI agent.
    # The footer "*Generated using BMAD MCP Server...*" should be omitted.

# bmad-mcp-server/src/bmad_mcp_server/checklists/loader.py
"""
BMAD checklist loading and execution system.
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from enum import Enum

# Checklist directory
CHECKLIST_DIR = Path(__file__).parent

# Checklist cache
_checklist_cache: Dict[str, Dict] = {}

class ValidationMode(str, Enum):
    """Validation strictness modes."""
    STRICT = "strict"
    STANDARD = "standard"
    LENIENT = "lenient"

def load_checklist(checklist_name: str) -> Dict[str, Any]:
    """Load and parse a BMAD checklist."""
    if checklist_name in _checklist_cache:
        return _checklist_cache[checklist_name]
    
    checklist_path = CHECKLIST_DIR / f"{checklist_name}.md"
    
    if not checklist_path.exists():
        raise FileNotFoundError(f"Checklist not found: {checklist_name}")
    
    try:
        with open(checklist_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        parsed_checklist = _parse_checklist_content(content, checklist_name)
        _checklist_cache[checklist_name] = parsed_checklist
        
        return parsed_checklist
        
    except Exception as e:
        raise Exception(f"Error loading checklist {checklist_name}: {e}")

def _parse_checklist_content(content: str, checklist_name: str) -> Dict[str, Any]:
    """Parse checklist markdown content into structured format."""
    
    checklist = {
        "name": checklist_name,
        "sections": [],
        "total_items": 0
    }
    
    current_section = None
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Section headers (## or ###)
        if line.startswith('##') and not line.startswith('###'):
            if current_section:
                checklist["sections"].append(current_section)
            
            section_title = line.replace('#', '').strip()
            current_section = {
                "title": section_title,
                "items": [],
                "description": ""
            }
        
        # Checklist items (- [ ])
        elif line.startswith('- [ ]'):
            if current_section:
                item_text = line.replace('- [ ]', '').strip()
                current_section["items"].append({
                    "text": item_text,
                    "required": True,
                    "category": current_section["title"]
                })
                checklist["total_items"] += 1
        
        # Section descriptions
        elif current_section and line and not line.startswith('#') and not line.startswith('-'):
            if current_section["description"]:
                current_section["description"] += " " + line
            else:
                current_section["description"] = line
    
    # Add final section
    if current_section:
        checklist["sections"].append(current_section)
    
    return checklist

def execute_checklist(checklist: Dict[str, Any], document_content: str, 
                     context: Dict[str, Any] = None, mode: str = "standard") -> Dict[str, Any]:
    """Execute checklist against document content."""
    
    context = context or {}
    validation_mode = ValidationMode(mode)
    
    results = {
        "checklist_name": checklist["name"],
        "total_items": checklist["total_items"],
        "passed_items": 0,
        "failed_items": 0,
        "na_items": 0,
        "section_results": [],
        "failed_items_details": [],
        "recommendations": []
    }
    
    for section in checklist["sections"]:
        section_result = {
            "title": section["title"],
            "total": len(section["items"]),
            "passed": 0,
            "failed": 0,
            "na": 0,
            "items": []
        }
        
        for item in section["items"]:
            item_result = _evaluate_checklist_item(
                item, document_content, context, validation_mode
            )
            
            section_result["items"].append(item_result)
            
            if item_result["status"] == "pass":
                section_result["passed"] += 1
                results["passed_items"] += 1
            elif item_result["status"] == "fail":
                section_result["failed"] += 1
                results["failed_items"] += 1
                results["failed_items_details"].append({
                    "category": section["title"],
                    "description": item["text"],
                    "recommendation": item_result.get("recommendation", "")
                })
            else:  # N/A
                section_result["na"] += 1
                results["na_items"] += 1
        
        results["section_results"].append(section_result)
    
    # Generate overall recommendations
    results["recommendations"] = _generate_recommendations(results, validation_mode)
    
    return results

def _evaluate_checklist_item(item: Dict, document_content: str, 
                           context: Dict, mode: ValidationMode) -> Dict[str, Any]:
    """Evaluate a single checklist item against document content."""
    
    item_text = item["text"].lower()
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
    
    return {
        "text": item["text"],
        "status": status,
        "recommendation": recommendation
    }

def _generate_recommendations(results: Dict, mode: ValidationMode) -> List[str]:
    """Generate overall recommendations based on validation results."""
    
    recommendations = []
    
    pass_rate = (results["passed_items"] / results["total_items"] * 100) if results["total_items"] > 0 else 0
    
    if pass_rate < 70:
        recommendations.append("Document requires significant improvement before proceeding to next phase")
        recommendations.append("Focus on addressing failed items systematically")
    elif pass_rate < 85:
        recommendations.append("Document is good but could benefit from addressing remaining failed items")
    
    # Analyze failed items by category
    failed_categories = {}
    for item in results["failed_items_details"]:
        category = item["category"]
        failed_categories[category] = failed_categories.get(category, 0) + 1
    
    if failed_categories:
        worst_category = max(failed_categories.items(), key=lambda x: x[1])
        recommendations.append(f"Pay special attention to '{worst_category[0]}' section - {worst_category[1]} items need improvement")
    
    return recommendations

def list_checklists() -> List[str]:
    """List available BMAD checklists."""
    return [f.stem for f in CHECKLIST_DIR.glob("*.md")]
