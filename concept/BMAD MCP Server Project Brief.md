# Project Brief: BMAD MCP Server

## Introduction / Problem Statement

Current AI development workflows lack standardized access to proven methodologies like BMAD (Breakthrough Method of Agile AI-driven Development). While the BMAD method provides powerful agent-based workflows for project planning, architecture, and development, these capabilities are currently siloed and require manual orchestration. There's a need for a standardized way to expose BMAD methodology as reusable tools that any MCP-compatible AI system can leverage.

## Vision & Goals

- **Vision:** Create a bridge between the BMAD methodology and the broader AI ecosystem through MCP (Model Context Protocol), enabling any AI system to leverage BMAD's structured approach to project development.

- **Primary Goals:**
  - Goal 1: Develop an MCP Server that exposes core BMAD agent capabilities as standardized tools
  - Goal 2: Enable seamless integration of BMAD workflows into any MCP-compatible AI environment
  - Goal 3: Provide structured, validated outputs that follow BMAD templates and checklists
  - Goal 4: Demonstrate "eating our own dog food" by using BMAD methodology to build the BMAD MCP Server

- **Success Metrics:**
  - MCP Server successfully exposes 8-10 core BMAD tools
  - Tools can be called from external AI systems (Claude, Cursor, etc.)
  - Generated outputs follow BMAD templates and quality standards
  - Server handles concurrent requests and maintains state appropriately

## Target Audience / Users

**Primary Users:**
- AI developers and engineers wanting to integrate BMAD methodology into their workflows
- Organizations seeking standardized project planning and development approaches
- MCP-compatible AI systems (Claude, Cursor, etc.) that need structured project development capabilities

**Secondary Users:**
- Product managers and architects wanting AI-assisted planning tools
- Development teams adopting AI-driven development practices

## Key Features / Scope (High-Level Ideas for MVP)

### Core BMAD Tool Categories:

1. **Project Planning Tools**
   - `create_project_brief` - Generate structured project briefs
   - `generate_prd` - Create Product Requirements Documents with epics/stories
   - `validate_requirements` - Run PM checklists on requirements

2. **Architecture Tools**
   - `create_architecture` - Generate technical architecture documents
   - `validate_architecture` - Run architect checklists
   - `create_frontend_architecture` - Design frontend-specific architecture

3. **Design Tools**
   - `create_uxui_spec` - Generate UI/UX specifications
   - `create_ai_frontend_prompt` - Generate prompts for AI UI tools

4. **Story Management Tools**
   - `create_next_story` - Generate development-ready user stories
   - `validate_story` - Check stories against DoD checklists

5. **Validation Tools**
   - `run_checklist` - Execute any BMAD checklist against documents
   - `correct_course` - Handle change management scenarios

## Post MVP Features / Scope and Ideas

- **Advanced Integration Tools**
  - Git repository integration for document management
  - Automated story progression and status tracking
  - Integration with project management tools (Jira, Linear, etc.)

- **Enhanced AI Capabilities**
  - Multi-model support for different tool types
  - Adaptive prompting based on project context
  - Learning from project outcomes

- **Collaboration Features**
  - Multi-user project state management
  - Real-time collaboration on documents
  - Role-based access to different tool sets

## Known Technical Constraints or Preferences

- **Constraints:**
  - Must implement MCP protocol specifications correctly
  - Should handle concurrent requests efficiently
  - Must maintain backward compatibility with BMAD templates/checklists
  - Server should be stateless or use appropriate persistence mechanisms

- **Initial Architectural Preferences:**
  - Python-based implementation for CrewAI compatibility
  - Use FastAPI for HTTP transport and asyncio for SSE transport
  - Structured state management using Pydantic models
  - Modular design allowing individual tool development and testing

- **Risks:**
  - MCP protocol complexity and correct implementation
  - Managing state across tool calls for related documents
  - Performance with complex CrewAI workflows
  - Integration complexity with various MCP clients

- **User Preferences:**
  - Follow BMAD methodology strictly in implementation
  - Use CrewAI Flows for complex multi-step tools
  - Implement comprehensive error handling and validation
  - Provide clear tool descriptions and parameter schemas

## Relevant Research (Optional)

Based on the MCP documentation and CrewAI integration examples, the server should:
- Support both stdio and SSE transport mechanisms
- Provide clear tool schemas with proper parameter validation
- Handle async operations appropriately for long-running CrewAI tasks
- Follow security best practices for MCP servers

## PM Prompt

This Project Brief provides the full context for the BMAD MCP Server. Please start in 'PRD Generation Mode', review the brief thoroughly to work with the user to create the PRD section by section, asking for any necessary clarification or suggesting improvements as your mode programming allows. Focus on creating a comprehensive PRD that will enable the Architect to design a robust MCP Server implementation using CrewAI and following BMAD principles.