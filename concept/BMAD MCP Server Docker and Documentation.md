# bmad-mcp-server/Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user
RUN groupadd -r bmad && useradd -r -g bmad bmad

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Change ownership to non-root user
RUN chown -R bmad:bmad /app

# Switch to non-root user
USER bmad

# Expose port for SSE mode
EXPOSE 8000

# Default command (stdio mode)
CMD ["python", "-m", "bmad_mcp_server.main", "--mode", "stdio"]

---

# bmad-mcp-server/docker-compose.yml
version: '3.8'

services:
  bmad-mcp-server:
    build: .
    container_name: bmad-mcp-server
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - BMAD_LOG_LEVEL=${BMAD_LOG_LEVEL:-INFO}
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    command: ["python", "-m", "bmad_mcp_server.main", "--mode", "sse", "--host", "0.0.0.0"]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  bmad-mcp-stdio:
    build: .
    container_name: bmad-mcp-stdio
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - BMAD_LOG_LEVEL=${BMAD_LOG_LEVEL:-INFO}
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
    stdin_open: true
    tty: true
    command: ["python", "-m", "bmad_mcp_server.main", "--mode", "stdio"]
    restart: unless-stopped

---

# bmad-mcp-server/.env.example
# LLM Provider API Keys (at least one required)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Server Configuration
BMAD_LOG_LEVEL=INFO
BMAD_MAX_CONCURRENT_TOOLS=5
BMAD_TOOL_TIMEOUT_SECONDS=300

# SSE Mode Configuration
BMAD_SSE_HOST=localhost
BMAD_SSE_PORT=8000

# CrewAI Configuration
CREWAI_DEFAULT_LLM=openai/gpt-4o-mini
CREWAI_VERBOSE=false

---

# bmad-mcp-server/README.md
# BMAD MCP Server

A Model Context Protocol (MCP) Server that exposes the BMAD (Breakthrough Method of Agile AI-driven Development) methodology as standardized tools for AI systems.

## Overview

The BMAD MCP Server bridges the proven BMAD methodology with the broader AI ecosystem through the Model Context Protocol standard. It enables any MCP-compatible AI system to leverage structured project development workflows including:

- **Project Planning**: Generate project briefs and comprehensive PRDs
- **Architecture Design**: Create technical and frontend architectures
- **Story Management**: Generate and validate development-ready user stories
- **Quality Assurance**: Run BMAD checklists and validation tools

## Features

- 🔧 **8+ BMAD Tools** - Complete toolkit for AI-driven development
- 🚀 **CrewAI Integration** - Powered by collaborative AI agents
- 📡 **Dual Transport** - Supports both stdio and Server-Sent Events
- ✅ **Template Compliance** - All outputs follow BMAD methodology
- 🔍 **Built-in Validation** - Quality checks using BMAD checklists
- 🐳 **Docker Ready** - Easy deployment and scaling

## Quick Start

### Using Docker (Recommended)

1. Clone and configure:
```bash
git clone https://github.com/bmad-project/bmad-mcp-server
cd bmad-mcp-server
cp .env.example .env
# Edit .env with your API keys
```

2. Start in SSE mode:
```bash
docker-compose up bmad-mcp-server
```

3. Or start in stdio mode:
```bash
docker-compose up bmad-mcp-stdio
```

### Local Installation

1. Install Python dependencies:
```bash
pip install -e .
```

2. Set environment variables:
```bash
export OPENAI_API_KEY=your_key_here
```

3. Run the server:
```bash
# Stdio mode (for local MCP clients)
python -m bmad_mcp_server.main --mode stdio

# SSE mode (for web-based clients)
python -m bmad_mcp_server.main --mode sse --host localhost --port 8000
```

## Available Tools

### Project Planning Tools

- **`create_project_brief`** - Generate structured project briefs
- **`generate_prd`** - Create comprehensive PRDs with epics and stories
- **`validate_requirements`** - Check PRDs against PM quality standards

### Architecture Tools

- **`create_architecture`** - Generate technical architecture documents
- **`create_frontend_architecture`** - Design frontend-specific architectures
- **`validate_architecture`** - Check architectures against quality standards

### Story Management Tools

- **`create_next_story`** - Generate development-ready user stories
- **`validate_story`** - Check stories against Definition of Done

### Quality Tools

- **`run_checklist`** - Execute any BMAD checklist against documents
- **`correct_course`** - Handle change management scenarios

## Usage Examples

### With CrewAI Tools

```python
from crewai_tools import MCPServerAdapter

# Connect to BMAD MCP Server
with MCPServerAdapter({"url": "http://localhost:8000/mcp"}) as tools:
    # Create an agent with BMAD tools
    agent = Agent(
        role="Project Manager",
        goal="Create comprehensive project documentation",
        tools=tools
    )
    
    # Use BMAD methodology in your workflows
    result = agent.execute_task(
        "Create a project brief for an AI-powered task management app"
    )
```

### With MCP Clients

The server works with any MCP-compatible client:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call_tool",
  "params": {
    "name": "create_project_brief",
    "arguments": {
      "topic": "AI-powered task management app",
      "target_audience": "busy professionals",
      "scope_level": "standard"
    }
  }
}
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY` - OpenAI API key (required if using OpenAI models)
- `ANTHROPIC_API_KEY` - Anthropic API key (required if using Claude models)
- `GOOGLE_API_KEY` - Google API key (required if using Gemini models)
- `BMAD_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `BMAD_MAX_CONCURRENT_TOOLS` - Maximum concurrent tool executions
- `BMAD_TOOL_TIMEOUT_SECONDS` - Tool execution timeout

### Server Configuration

Create a `config/server.json` file:

```json
{
  "log_level": "INFO",
  "max_concurrent_tools": 5,
  "tool_timeout_seconds": 300,
  "enable_stdio": true,
  "enable_sse": true,
  "sse_host": "localhost",
  "sse_port": 8000
}
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Run linting
flake8 src/ tests/
mypy src/
```

### Building Documentation

```bash
mkdocs serve
```

## Architecture

The BMAD MCP Server follows a modular architecture:

- **Protocol Layer** - MCP compliance for stdio and SSE transports
- **Tool Registry** - Dynamic tool discovery and execution
- **BMAD Engine** - Core methodology implementation
- **CrewAI Integration** - Agent-based workflow orchestration
- **Template System** - BMAD template and checklist management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the coding standards
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- [BMAD Methodology](https://github.com/bmad-project/bmad-method) - Core BMAD framework
- [CrewAI](https://github.com/crewAIInc/crewAI) - Multi-agent AI framework
- [Model Context Protocol](https://modelcontextprotocol.io/) - Standard for AI tool integration

---

# bmad-mcp-server/scripts/start_stdio.py
#!/usr/bin/env python3
"""
Startup script for BMAD MCP Server in stdio mode.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bmad_mcp_server.main import main

if __name__ == "__main__":
    # Force stdio mode
    sys.argv = [sys.argv[0], "--mode", "stdio"]
    asyncio.run(main())

---

# bmad-mcp-server/scripts/start_sse.py
#!/usr/bin/env python3
"""
Startup script for BMAD MCP Server in SSE mode.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bmad_mcp_server.main import main

if __name__ == "__main__":
    # Force SSE mode with default settings
    sys.argv = [sys.argv[0], "--mode", "sse", "--host", "0.0.0.0", "--port", "8000"]
    asyncio.run(main())

---

# bmad-mcp-server/docs/tool_catalog.md
# BMAD MCP Server Tool Catalog

This document provides a comprehensive catalog of all available BMAD tools exposed by the MCP server.

## Tool Categories

### Project Planning Tools

Tools for establishing project foundations and requirements.

#### create_project_brief

**Purpose**: Generate structured project briefs following BMAD methodology

**Input Schema**:
```json
{
  "topic": "string (required) - Main project topic",
  "target_audience": "string (optional) - Target users",
  "constraints": "array (optional) - Known constraints",
  "scope_level": "enum (optional) - minimal|standard|comprehensive"
}
```

**Output**: Structured project brief in markdown format

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

#### generate_prd

**Purpose**: Create comprehensive Product Requirements Documents with epics and stories

**Input Schema**:
```json
{
  "project_brief": "string (required) - Input project brief",
  "workflow_mode": "enum (optional) - incremental|yolo",
  "technical_depth": "enum (optional) - basic|standard|detailed"
}
```

**Output**: Complete PRD with epics, stories, and technical guidance

**Execution Time**: 2-5 minutes

#### validate_requirements

**Purpose**: Validate PRD documents against PM quality checklists

**Input Schema**:
```json
{
  "prd_content": "string (required) - PRD to validate",
  "checklist_type": "enum (optional) - standard|comprehensive"
}
```

**Output**: Validation report with specific recommendations

### Architecture Tools

Tools for technical design and system architecture.

#### create_architecture

**Purpose**: Generate technical architecture from requirements

**Input Schema**:
```json
{
  "prd_content": "string (required) - PRD with requirements",
  "tech_preferences": "object (optional) - Technology constraints",
  "architecture_type": "enum (optional) - monolith|microservices|serverless"
}
```

**Output**: Comprehensive architecture document

#### create_frontend_architecture

**Purpose**: Generate frontend-specific architecture specifications

**Input Schema**:
```json
{
  "main_architecture": "string (required) - Main architecture doc",
  "ux_specification": "string (optional) - UI/UX requirements",
  "framework_preference": "string (optional) - Frontend framework"
}
```

**Output**: Frontend architecture with component strategy

### Story Management Tools

Tools for creating and managing development stories.

#### create_next_story

**Purpose**: Generate development-ready user stories

**Input Schema**:
```json
{
  "prd_content": "string (required) - PRD with epics",
  "architecture_content": "string (required) - Architecture context",
  "current_progress": "object (optional) - Story completion status"
}
```

**Output**: Comprehensive story with technical guidance

#### validate_story

**Purpose**: Validate stories against Definition of Done

**Input Schema**:
```json
{
  "story_content": "string (required) - Story to validate",
  "checklist_types": "array (optional) - Checklists to run"
}
```

**Output**: Validation report with improvements

### Quality Tools

Tools for validation and quality assurance.

#### run_checklist

**Purpose**: Execute BMAD checklists against documents

**Input Schema**:
```json
{
  "document_content": "string (required) - Document to validate",
  "checklist_name": "string (required) - Checklist identifier",
  "validation_context": "object (optional) - Additional context"
}
```

**Output**: Detailed checklist execution report

**Available Checklists**:
- `pm_checklist` - Product Manager quality checks
- `architect_checklist` - Architecture validation
- `story_draft_checklist` - Story readiness validation
- `story_dod_checklist` - Definition of Done checks

## Usage Patterns

### Sequential Workflow

1. **Start with Planning**: Use `create_project_brief` to establish foundations
2. **Define Requirements**: Use `generate_prd` to create comprehensive requirements
3. **Design Architecture**: Use `create_architecture` and `create_frontend_architecture`
4. **Create Stories**: Use `create_next_story` iteratively for development
5. **Validate Quality**: Use validation tools throughout the process

### Validation-First Approach

- Run `validate_requirements` after PRD creation
- Use `validate_story` before story implementation
- Execute `run_checklist` for quality assurance at any stage

### Error Handling

All tools provide structured error responses:
- Parameter validation errors
- Execution timeout errors
- CrewAI workflow failures
- Resource availability issues

## Integration Examples

### With CrewAI

```python
from crewai_tools import MCPServerAdapter

with MCPServerAdapter({"url": "http://localhost:8000/mcp"}) as bmad_tools:
    planning_agent = Agent(
        role="Project Planner",
        tools=bmad_tools
    )
```

### Direct MCP Usage

```json
{
  "jsonrpc": "2.0",
  "method": "call_tool", 
  "params": {
    "name": "create_project_brief",
    "arguments": {"topic": "Mobile app for fitness tracking"}
  }
}
```