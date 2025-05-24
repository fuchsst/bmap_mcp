# Configuring the BMAD MCP Server

This document provides detailed information on configuring the BMAD MCP Server, including environment variables, server configuration files, and transport modes.

## Environment Variables

The BMAD MCP Server uses environment variables for sensitive information like API keys and for some operational settings. These can be set directly in your shell, in a `.env` file at the project root, or via Docker Compose environment settings.

A `.env.example` file is provided as a template:
```env
# LLM Provider API Keys (at least one required for CrewAI agents)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
# GEMINI_API_KEY=your_google_gemini_key_here # If using Google Gemini via CrewAI
# AWS_ACCESS_KEY_ID=your_aws_access_key
# AWS_SECRET_ACCESS_KEY=your_aws_secret_key
# AWS_DEFAULT_REGION=your_aws_region # e.g., us-east-1

# Server Configuration
BMAD_LOG_LEVEL=INFO
# BMAD_MAX_CONCURRENT_TOOLS=5 # Currently not implemented, managed by FastMCP/Asyncio
# BMAD_TOOL_TIMEOUT_SECONDS=300 # Currently not implemented

# SSE Mode Configuration (primarily for local non-Docker runs)
BMAD_SSE_HOST=localhost # Default host for SSE mode if run directly
BMAD_SSE_PORT=8000      # Default port for SSE mode if run directly

# CrewAI Configuration
# CREWAI_DEFAULT_LLM=openai/gpt-4o-mini # Example, depends on your CrewAI setup
# CREWAI_VERBOSE=false # Controls verbosity of CrewAI agents
```

**Key Environment Variables:**

-   **LLM API Keys**:
    -   `OPENAI_API_KEY`: Your API key for OpenAI models (e.g., GPT-4).
    -   `ANTHROPIC_API_KEY`: Your API key for Anthropic Claude models.
    -   `GEMINI_API_KEY`: Your API key for Google Gemini models.
    -   `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`: Credentials for using AWS Bedrock models.
    *At least one set of LLM API keys is required for the CrewAI agents to function.*

-   **`BMAD_LOG_LEVEL`**:
    -   Sets the logging verbosity for the server.
    -   Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
    -   Default: `INFO`.

-   **`BMAD_PROJECT_ROOT`**:
    -   If running the server executable directly, this can specify the root directory for the `.bmad` artifacts.
    -   When using `python -m bmad_mcp_server.main`, the `--project-root` CLI argument is preferred.

-   **`BMAD_SSE_HOST` / `BMAD_SSE_PORT`**:
    -   Defines the host and port for the SSE server when run directly (not via Docker Compose, which has its own port mapping).
    -   Defaults: `localhost` and `8000`.

-   **CrewAI Variables**:
    -   `CREWAI_DEFAULT_LLM`: Can specify a default LLM for CrewAI if not configured elsewhere (e.g., `openai/gpt-4o-mini`). The actual LLM used depends on the `CrewAIConfig` and agent definitions.
    -   `CREWAI_VERBOSE`: Set to `true` or `false` to control the verbosity of CrewAI's internal logging.

**Loading `.env` files**:
If you place a `.env` file in the root of the `bmad-mcp-server` project directory, Python's `python-dotenv` library (a dependency) will automatically load these variables when the server starts locally. Docker Compose also uses the `.env` file by default.

## Server Configuration File (`config/server.json`)

You can optionally create a `config/server.json` file in the project root to provide more detailed server configurations. This file is automatically created by Docker Compose if you mount a local `./config` directory.

**Example `config/server.json`:**
```json
{
  "log_level": "DEBUG",
  "log_file": "logs/bmad_server.log", // Path relative to project root, or absolute
  "project_root": ".", // Specifies where the .bmad folder is managed relative to server CWD
  "crewai_config": {
    "default_llm": "openai/gpt-4o", // Overrides CREWAI_DEFAULT_LLM
    "verbose_logging": true // Overrides CREWAI_VERBOSE
    // You can add other CrewAI specific configurations here
  }
  // "max_concurrent_tools": 5, // Future use
  // "tool_timeout_seconds": 300, // Future use
  // "enable_stdio": true, // Future use for fine-grained control
  // "enable_sse": true, // Future use
  // "sse_host": "0.0.0.0", // Overrides BMAD_SSE_HOST
  // "sse_port": 8001 // Overrides BMAD_SSE_PORT
}
```

**Key `config/server.json` Settings:**

-   `log_level`: Overrides `BMAD_LOG_LEVEL`.
-   `log_file`: Specifies a file path to write logs to. If not provided, logs go to stdout/stderr. The `logs/` directory will be created if it doesn't exist.
-   `project_root`: Defines the root directory for the project whose `.bmad` artifacts the server will manage. Defaults to the current working directory of the server if not set by CLI or this config.
-   `crewai_config`: A nested object for CrewAI-specific settings.
    -   `default_llm`: Sets the default LLM for CrewAI agents.
    -   `verbose_logging`: Controls CrewAI's verbosity.

*Note: Settings from `config/server.json` generally take precedence over environment variables if both are set for the same option.*

## Transport Modes

The BMAD MCP Server supports two primary transport modes for communication with AI assistants:

### 1. Stdio (Standard Input/Output)

-   **How it works**: The AI assistant launches the BMAD MCP Server as a child process. Communication happens via the server's standard input (stdin) and standard output (stdout) streams using JSON-RPC messages.
-   **Pros**:
    -   Lower latency as there's no network overhead.
    -   Generally more secure as it doesn't expose network ports.
    -   Simpler setup for purely local development if the assistant manages the server lifecycle.
-   **Cons**:
    -   Typically limited to one client (the parent AI assistant).
    -   The server runs only when the assistant needs it (can be a pro or con).
-   **Activation**:
    -   Local: `python -m bmad_mcp_server.main --mode stdio --project-root /path/to/your/project`
    -   Docker: `docker-compose up bmad-mcp-stdio`

### 2. SSE (Server-Sent Events)

-   **How it works**: The BMAD MCP Server runs as an HTTP server. The AI assistant connects to it as an HTTP client, and communication (tool calls, results) happens over an HTTP connection, often using Server-Sent Events for streaming results. FastMCP uses a streamable HTTP transport.
-   **Pros**:
    -   Can be accessed by multiple clients over the network (e.g., different IDEs, web UIs).
    -   Can be hosted on a separate machine or centrally.
    -   Persistent server process, always ready to accept connections.
-   **Cons**:
    -   Slightly higher latency due to network communication.
    -   Requires network port exposure, which might have security implications if not managed properly.
-   **Activation**:
    -   Local: `python -m bmad_mcp_server.main --mode sse --host 0.0.0.0 --port 8000 --project-root /path/to/your/project`
        -   `--host 0.0.0.0` makes it accessible from other machines on your network. Use `localhost` for local access only.
    -   Docker: `docker-compose up bmad-mcp-server` (typically exposes port 8000).

Your AI assistant's MCP client configuration will determine which mode it expects. Refer to the [IDE Integration](./ide-integration.md) guide for specifics.

## Security Considerations

-   **API Keys**: Never commit API keys directly into your repository. Use `.env` files (added to `.gitignore`) or secure environment variable management provided by your OS or deployment platform.
-   **Network Exposure (SSE Mode)**: If running in SSE mode and exposing the server to a broader network (e.g., using `0.0.0.0` as host), ensure your firewall rules are appropriately configured to restrict access to trusted clients only. For production, consider placing the server behind a reverse proxy with SSL/TLS encryption and authentication.
-   **Tool Permissions**: AI assistants often have mechanisms to request user approval before executing tools from an MCP server, especially for the first time or for project-specific servers. Always review what tools an MCP server exposes and what actions they can perform. The BMAD MCP Server tools are designed to operate within the specified `--project-root` and its `.bmad` subdirectory.
-   **Input Validation**: The server uses Pydantic for input validation for each tool, which helps prevent malformed requests.

By understanding these configuration options, you can tailor the BMAD MCP Server to your specific development environment and security requirements.
