# BMAD MCP Server Tool Catalog

This document provides a comprehensive catalog of all available BMAD tools exposed by the MCP server.

## Tool Categories

All tools interact with a `StateManager` instance to persist and retrieve BMAD artifacts from the `.bmad` directory in the project root. They leverage `CrewAI` agents for complex generation tasks and follow defined BMAD templates and checklists.

### Project Planning Tools

Tools for establishing project foundations and requirements.

#### 1. `create_project_brief`
**Purpose**: Generate a structured project brief following BMAD methodology. Uses the BMAD Analyst agent for creation.
**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "topic": {
      "type": "string",
      "description": "The main topic or idea for the project"
    },
    "target_audience": {
      "type": "string",
      "description": "Target audience or users for the project",
      "default": "General users"
    },
    "constraints": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Known constraints, preferences, or requirements",
      "default": []
    },
    "scope_level": {
      "type": "string",
      "enum": ["minimal", "standard", "comprehensive"],
      "description": "Desired scope level for the brief",
      "default": "standard"
    }
  },
  "required": ["topic"]
}
```
**Output**: Structured project brief in markdown format, saved to `.bmad/ideation/project_brief_{topic}.md`.
**Example Usage**:
```json
{
  "name": "create_project_brief",
  "arguments": {
    "topic": "AI-powered code review tool",
    "target_audience": "software development teams",
    "scope_level": "standard"
  }
}
```

#### 2. `generate_prd`
**Purpose**: Create comprehensive Product Requirements Documents with epics and user stories using BMAD methodology and the PM agent.
**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "project_brief_content": {
      "type": "string",
      "description": "Complete project brief content to base PRD on"
    },
    "workflow_mode": {
      "type": "string",
      "enum": ["incremental", "yolo"],
      "description": "PRD generation approach",
      "default": "incremental"
    },
    "technical_depth": {
      "type": "string",
      "enum": ["basic", "standard", "detailed"],
      "description": "Level of technical detail",
      "default": "standard"
    },
    "include_architecture_prompt": {
      "type": "boolean",
      "description": "Whether to include architect prompt in PRD",
      "default": true
    }
  },
  "required": ["project_brief_content"]
}
```
**Output**: Complete PRD in markdown format, saved to `.bmad/prd/prd_{project_name}.md`.
**Execution Time**: 2-5 minutes.

#### 3. `validate_requirements`
**Purpose**: Validate PRD documents against PM quality checklists (e.g., `pm_checklist.md`).
**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "prd_content": {
      "type": "string",
      "description": "PRD content to validate"
    },
    "checklist_type": {
      "type": "string",
      "enum": ["pm_checklist", "standard", "comprehensive"],
      "description": "Type of checklist to use",
      "default": "pm_checklist"
    },
    "validation_mode": {
      "type": "string",
      "enum": ["strict", "standard", "lenient"],
      "description": "Validation strictness level",
      "default": "standard"
    },
    "include_recommendations": {
      "type": "boolean",
      "description": "Whether to include recommendations",
      "default": true
    }
  },
  "required": ["prd_content"]
}
```
**Output**: Validation report in markdown format, saved to `.bmad/checklists/requirements_validation_{checklist_type}.md`.

### Architecture Tools

Tools for technical design and system architecture.

#### 4. `create_architecture`
**Purpose**: Generate technical architecture from PRD requirements using the Architect agent.
**Input Schema**:
```json
{
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
      "default": true
    }
  },
  "required": ["prd_content"]
}
```
**Output**: Comprehensive architecture document in markdown, saved to `.bmad/architecture/architecture_main.md`.

#### 5. `create_frontend_architecture`
**Purpose**: Generate frontend-specific architecture specifications using the Architect agent.
**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "main_architecture": {
      "type": "string",
      "description": "Main architecture document content"
    },
    "ux_specification": {
      "type": "string",
      "description": "UI/UX requirements and specifications",
      "default": ""
    },
    "framework_preference": {
      "type": "string",
      "enum": ["React", "Vue", "Angular", "Svelte", "React Native", "Flutter", ""],
      "description": "Preferred frontend framework",
      "default": ""
    },
    "component_strategy": {
      "type": "string",
      "enum": ["atomic", "modular", "feature-based", "layered"],
      "description": "Component design strategy",
      "default": "atomic"
    },
    "state_management": {
      "type": "string",
      "enum": ["Redux", "Zustand", "Context API", "Vuex", "Pinia", "NgRx", ""],
      "description": "Preferred state management approach",
      "default": ""
    }
  },
  "required": ["main_architecture"]
}
```
**Output**: Frontend architecture document in markdown, saved to `.bmad/architecture/frontend_architecture_{framework}.md`.

### Story Management Tools

Tools for creating and managing development stories.

#### 6. `create_next_story`
**Purpose**: Generate development-ready user stories from PRD epics and architecture context using the PM agent.
**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "prd_content": {
      "type": "string",
      "description": "PRD content with epics and requirements"
    },
    "architecture_content": {
      "type": "string",
      "description": "Architecture context for technical guidance"
    },
    "current_progress": {
      "type": "object",
      "properties": {
        "completed_stories": {
          "type": "array",
          "items": {"type": "string"},
          "default": [],
          "description": "List of completed story IDs"
        },
        "current_epic": {
          "type": "integer",
          "default": 1,
          "description": "Current epic number"
        },
        "epic_progress": {
          "type": "object",
          "default": {},
          "description": "Progress within current epic"
        }
      },
      "default": {"completed_stories": [], "current_epic": 1, "epic_progress": {}}
    },
    "story_type": {
      "type": "string",
      "enum": ["feature", "bug", "technical", "research", "epic"],
      "default": "feature"
    },
    "priority": {
      "type": "string",
      "enum": ["low", "medium", "high", "critical"],
      "default": "medium"
    }
  },
  "required": ["prd_content", "architecture_content"]
}
```
**Output**: User story document in markdown, saved to `.bmad/stories/story_{epic}_{number}.md`.

#### 7. `validate_story`
**Purpose**: Validate user stories against Definition of Done and quality checklists (e.g., `story_draft_checklist.md`, `story_dod_checklist.md`).
**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "story_content": {
      "type": "string",
      "description": "Story content to validate"
    },
    "checklist_types": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["story_draft_checklist", "story_dod_checklist", "story_review_checklist"]
      },
      "description": "List of checklists to run",
      "default": ["story_draft_checklist"]
    },
    "validation_mode": {
      "type": "string",
      "enum": ["strict", "standard", "lenient"],
      "default": "standard"
    },
    "story_phase": {
      "type": "string",
      "enum": ["draft", "review", "ready", "in_progress", "done"],
      "default": "draft"
    }
  },
  "required": ["story_content"]
}
```
**Output**: Validation report in markdown, saved to `.bmad/checklists/story_validation_{phase}.md`.

### Quality Tools

Tools for validation and quality assurance.

#### 8. `run_checklist`
**Purpose**: Execute any BMAD checklist against provided documents.
**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "document_content": {
      "type": "string",
      "description": "Document content to validate"
    },
    "checklist_name": {
      "type": "string",
      "enum": ["pm_checklist", "architect_checklist", "frontend_architecture_checklist", "story_draft_checklist", "story_dod_checklist", "story_review_checklist", "change_checklist"],
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
```
**Output**: Detailed checklist execution report in markdown, saved to `.bmad/checklists/validation_report_{checklist_name}.md`.
**Available Checklists**:
- `pm_checklist`
- `architect_checklist`
- `frontend_architecture_checklist`
- `story_draft_checklist`
- `story_dod_checklist`
- `story_review_checklist`
- `change_checklist`

#### 9. `correct_course`
**Purpose**: Handle change management scenarios and course corrections using Analyst or PM agent.
**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "current_situation": {
      "type": "string",
      "description": "Description of current project situation"
    },
    "desired_outcome": {
      "type": "string",
      "description": "Desired outcome or goal"
    },
    "change_context": {
      "type": "object",
      "properties": {
        "change_type": {
          "type": "string",
          "enum": ["scope_change", "requirement_change", "technical_pivot", "timeline_adjustment", "resource_change", "priority_shift", "architecture_change", "feature_addition", "feature_removal", "quality_improvement"],
          "description": "Type of change requested"
        },
        "change_reason": {
          "type": "string",
          "description": "Reason for the change"
        },
        "impact_areas": {
          "type": "array",
          "items": {"type": "string"},
          "default": [],
          "description": "Areas impacted"
        },
        "urgency": {
          "type": "string",
          "enum": ["low", "medium", "high", "critical"],
          "default": "medium"
        }
      },
      "required": ["change_type", "change_reason"]
    },
    "existing_artifacts": {
      "type": "array",
      "items": {"type": "string"},
      "default": [],
      "description": "List of existing project artifacts"
    },
    "constraints": {
      "type": "array",
      "items": {"type": "string"},
      "default": [],
      "description": "Constraints to consider"
    }
  },
  "required": ["current_situation", "desired_outcome", "change_context"]
}
```
**Output**: Course correction plan in markdown, saved to `.bmad/decisions/course_correction_{change_type}.md`.

## Usage Patterns

### Sequential Workflow Example
1. **Start with Planning**: Use `create_project_brief` to establish foundations.
2. **Define Requirements**: Use `generate_prd` to create comprehensive requirements.
3. **Validate PRD**: Use `validate_requirements` with `pm_checklist`.
4. **Design Architecture**: Use `create_architecture` and `create_frontend_architecture`.
5. **Validate Architecture**: Use `run_checklist` with `architect_checklist` and `frontend_architecture_checklist`.
6. **Create Stories**: Use `create_next_story` iteratively for development.
7. **Validate Stories**: Use `validate_story` with `story_draft_checklist` and `story_review_checklist`.
8. **Implement Story & Validate DoD**: After implementation, use `validate_story` with `story_dod_checklist`.
9. **Handle Changes**: Use `correct_course` and `run_checklist` with `change_checklist` as needed.

### Error Handling
All tools provide structured error responses if execution fails, typically returning the error message as a string. Detailed logs are available in the server console and configured log files.
