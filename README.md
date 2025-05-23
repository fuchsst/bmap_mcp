# BMAD MCP Server

A Model Context Protocol ([MCP](https://modelcontextprotocol.io/)) Server that exposes the [BMAD](https://github.com/bmadcode/BMAD-METHOD) (Breakthrough Method of Agile AI-driven Development) methodology as standardized tools for AI systems.

## Overview

The BMAD MCP Server bridges the proven BMAD methodology with the broader AI ecosystem through the Model Context Protocol standard. It enables any MCP-compatible AI system to leverage structured project development workflows including:

- **Project Planning**: Generate project briefs and comprehensive PRDs
- **Architecture Design**: Create technical and frontend architectures
- **Story Management**: Generate and validate development-ready user stories
- **Quality Assurance**: Run BMAD checklists and validation tools

## Features

- 🔧 **9 BMAD Tools** - Complete toolkit for AI-driven development
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
Depending on the used model provider:
```bash
export OPENAI_API_KEY=<your_openai_key_here>
export GEMINI_API_KEY=<your_google_gemini_key_here>
export ANTHROPIC_API_KEY=<your_anthropic_claude_key_here>
export AWS_ACCESS_KEY_ID=<aws-key>
export AWS_SECRET_ACCESS_KEY=<aws-secret>
export AWS_DEFAULT_REGION=eu-central-1
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
- **`validate_architecture`** - Check architectures against quality standards (Note: This tool is conceptual, `run_checklist` with `architect_checklist.md` serves this purpose)

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
