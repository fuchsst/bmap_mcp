# BMAD MCP Server

A Model Context Protocol ([MCP](https://modelcontextprotocol.io/)) Server that exposes the [BMAD](https://github.com/bmadcode/BMAD-METHOD) (Breakthrough Method of Agile AI-driven Development) methodology as standardized tools for AI systems.

## Overview

The BMAD MCP Server bridges the proven BMAD methodology with the broader AI ecosystem through the Model Context Protocol standard. It enables any MCP-compatible AI system to leverage structured project development workflows including:

- **Project Planning**: Generate project briefs and comprehensive PRDs.
- **Architecture Design**: Create technical and frontend architectures.
- **Story Management**: Generate and validate development-ready user stories.
- **Quality Assurance**: Run BMAD checklists and validation tools.

## Features

- 🔧 **9 BMAD Tools**: A comprehensive toolkit for AI-driven development.
- 🚀 **CrewAI Integration**: Powered by collaborative AI agents for complex reasoning.
- 📡 **Dual Transport**: Supports both stdio (for local clients) and Server-Sent Events (SSE for web-based clients).
- ✅ **Template Compliance**: All generated artifacts adhere to BMAD methodology templates.
- 🔍 **Built-in Validation**: Quality checks using BMAD checklists ensure high-quality outputs.
- 🐳 **Docker Ready**: Easy deployment and scaling with Docker and Docker Compose.

## Documentation

For detailed setup, configuration, usage examples, and development workflow, please refer to our full [**Documentation**](./docs/index.md).

## Quick Start (Docker Recommended)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/bmad-project/bmad-mcp-server
    cd bmad-mcp-server
    ```
2.  **Configure environment variables:**
    Copy the example environment file and edit it with your API keys:
    ```bash
    cp .env.example .env
    # Open .env and add your LLM API keys (OpenAI, Anthropic, Google Gemini, AWS Bedrock)
    ```
3.  **Run with Docker Compose:**
    *   For SSE mode (recommended for most clients):
        ```bash
        docker-compose up bmad-mcp-server
        ```
        The server will be available at `http://localhost:8000`.
    *   For stdio mode:
        ```bash
        docker-compose up bmad-mcp-stdio
        ```

For local installation without Docker, see the [Getting Started](./docs/getting-started.md) guide in our documentation.

## Available Tools (Summary)

### Project Planning Tools

- **`create_project_brief`** - Generate structured project briefs
- **`generate_prd`** - Create comprehensive PRDs with epics and stories
- **`validate_requirements`** - Check PRDs against PM quality standards

### Architecture Tools

- **`create_architecture`** - Generate technical architecture documents
- **`create_frontend_architecture`** - Design frontend-specific architectures
- **`validate_architecture`** - Check architectures against quality standards (Note: This tool is conceptual, `run_checklist` with `architect_checklist.md` or `frontend_architecture_checklist.md` serves this purpose)

### Story Management Tools

- **`create_next_story`** - Generate development-ready user stories
- **`validate_story`** - Check stories against Definition of Done

### Quality Tools

- **`run_checklist`** - Execute any BMAD checklist against documents
- **`correct_course`** - Handle change management scenarios

## Documentation

For detailed usage examples with various AI assistants (Cline, Claude Code, GitHub Copilot) and direct MCP client interactions, please see our [Development Workflow](./docs/development-workflow.md) and [IDE Integration](./docs/ide-integration.md) documentation.

Detailed configuration options for environment variables and server settings are available in the [Configuration](./docs/configuration.md) documentation.


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
