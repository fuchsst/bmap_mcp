# Getting Started with BMAD MCP Server

This guide will walk you through the process of installing and setting up the BMAD MCP Server.

## Prerequisites

Before you begin, ensure you have the following installed:

-   **Python**: Version 3.11 or higher.
-   **Pip**: Python package installer.
-   **Git**: For cloning the repository.
-   **Docker and Docker Compose**: (Recommended) For the easiest setup and deployment.
-   **An AI Coding Assistant**: Such as [Cline](https://cline.com/), [Claude Code](https://www.anthropic.com/claude#claude-code), or [GitHub Copilot](https://github.com/features/copilot) with MCP support in your IDE (e.g., VS Code).

## Installation

You can install the BMAD MCP Server using Docker (recommended) or by setting up a local Python environment.

### Option 1: Using Docker (Recommended)

This is the simplest way to get the server running.

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/bmad-project/bmad-mcp-server
    cd bmad-mcp-server
    ```

2.  **Configure Environment Variables**:
    The server requires API keys for the LLM providers you intend to use with CrewAI (e.g., OpenAI, Anthropic, Google Gemini, AWS Bedrock).
    ```bash
    cp .env.example .env
    ```
    Now, open the `.env` file in a text editor and add your API keys:
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
    # BMAD_MAX_CONCURRENT_TOOLS=5
    # BMAD_TOOL_TIMEOUT_SECONDS=300

    # SSE Mode Configuration (if not using Docker defaults)
    # BMAD_SSE_HOST=0.0.0.0
    # BMAD_SSE_PORT=8000

    # CrewAI Configuration
    # CREWAI_DEFAULT_LLM=openai/gpt-4o-mini # Example, depends on your CrewAI setup
    # CREWAI_VERBOSE=false
    ```
    Ensure you provide at least one LLM API key that your CrewAI agents are configured to use.

    **Configuring LLMs for CrewAI Agents:**

    The BMAD MCP Server uses CrewAI, which in turn can leverage various Large Language Models (LLMs) for its agents. You can configure a default LLM and agent-specific LLMs via environment variables. These variables expect string identifiers that CrewAI can resolve (e.g., "openai/gpt-4o-mini", "anthropic/claude-3-opus-20240229", "ollama/mistral").

    -   `BMAD_DEFAULT_LLM`: Sets the default LLM for all agents if no specific LLM is defined for an agent.
        Example: `BMAD_DEFAULT_LLM=anthropic/claude-3-5-haiku-20241022`
    -   `BMAD_ANALYST_AGENT_LLM`: Specific LLM for the Analyst agent.
        Example: `BMAD_ANALYST_AGENT_LLM=gemini/gemini-2-5-flash-preview-05-20`
    -   `BMAD_PM_AGENT_LLM`: Specific LLM for the Product Manager agent.
        Example: `BMAD_PM_AGENT_LLM=anthropic/claude-3-7-sonnet-20250219`
    -   `BMAD_ARCHITECT_AGENT_LLM`: Specific LLM for the Architect agent.
        Example: `BMAD_ARCHITECT_AGENT_LLM=google/gemini-2.5-pro-preview-05-06`
    -   *(Add similar variables for other agents like `BMAD_DEVELOPER_AGENT_LLM`, `BMAD_QA_AGENT_LLM` as they are defined in `src/bmad_mcp_server/crewai_integration/config.py`)*

    If an agent-specific LLM variable is not set, the agent will use the `BMAD_DEFAULT_LLM`. If `BMAD_DEFAULT_LLM` is also not set, it will fall back to the default specified in `config.py` (currently "openai/gpt-4o-mini").

    Add these to your `.env` file as needed:
    ```env
    # ... (other API keys) ...

    # CrewAI LLM Configuration Examples
    BMAD_DEFAULT_LLM=openai/gpt-4o-mini
    BMAD_PM_AGENT_LLM=anthropic/claude-3-sonnet-20240229
    # BMAD_ARCHITECT_AGENT_LLM=ollama/llama3 # If you have Ollama running with llama3
    ```

3.  **Run with Docker Compose**:
    Docker Compose will build the image and run the server.
    *   **For SSE Mode** (Server-Sent Events - recommended for most AI assistants that connect via HTTP):
        ```bash
        docker-compose up bmad-mcp-server
        ```
        The server will start, and you should see logs indicating it's running, typically on `http://localhost:8000`.
    *   **For Stdio Mode** (Standard Input/Output - for AI assistants that run the server as a child process):
        ```bash
        docker-compose up bmad-mcp-stdio
        ```
        This will start the server in stdio mode, ready for an MCP client to connect.

### Option 2: Local Python Environment Setup

If you prefer not to use Docker, you can set up a local Python environment.

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/bmad-project/bmad-mcp-server
    cd bmad-mcp-server
    ```

2.  **Create a Virtual Environment** (Recommended):
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -e .
    ```
    This command installs the server and all its dependencies listed in `pyproject.toml`.

4.  **Set Environment Variables**:
    Similar to the Docker setup, you need to provide API keys for your LLM providers. Set these in your shell environment:
    ```bash
    export OPENAI_API_KEY="your_openai_api_key_here"
    export ANTHROPIC_API_KEY="your_anthropic_api_key_here"
    # Add other keys (GEMINI_API_KEY, AWS keys) as needed
    export BMAD_LOG_LEVEL="INFO"
    
    # Optionally, configure CrewAI LLMs (see .env examples above for format)
    # export BMAD_DEFAULT_LLM="openai/gpt-4o-mini"
    # export BMAD_PM_AGENT_LLM="anthropic/claude-3-sonnet-20240229"
    ```
    On Windows, use `set OPENAI_API_KEY=your_openai_api_key_here` or manage them through system environment variable settings.

5.  **Run the Server**:
    *   **For Stdio Mode**:
        ```bash
        python -m bmad_mcp_server.main --mode stdio --project-root .
        ```
    *   **For SSE Mode**:
        ```bash
        python -m bmad_mcp_server.main --mode sse --host localhost --port 8000 --project-root .
        ```
    The `--project-root .` argument tells the server to use the current directory for managing its `.bmad` artifacts. You can specify a different project directory if needed.

## First-Time Configuration in Your IDE

Once the BMAD MCP Server is running (either via Docker or locally), you need to configure your AI Coding Assistant to connect to it.

Please refer to the **[IDE Integration](./ide-integration.md)** guide for detailed, step-by-step instructions specific to:
-   Cline
-   Claude Code
-   GitHub Copilot

This typically involves telling your assistant how to find and communicate with the BMAD MCP Server (e.g., by specifying the command for stdio mode or the URL for SSE mode).

## Verification

After installation and IDE configuration:

1.  **Check Server Logs**: Ensure the server started without errors. You should see log messages indicating initialization and tool registration.
2.  **Test with AI Assistant**:
    *   Open your IDE and activate your AI assistant.
    *   Try a simple prompt that should invoke a BMAD tool, for example:
        `"Create a project brief for a 'Personal Task Manager' app."`
    *   Your AI assistant should detect the BMAD MCP Server and its tools. It might ask for permission to use the `create_project_brief` tool.
    *   If successful, the server will execute the tool (you'll see activity in its logs), and the AI assistant should present the generated project brief.
    *   Check your project directory for a `.bmad/ideation/project_brief_personal_task_manager.md` file.

If you encounter issues, consult the **[Troubleshooting](./troubleshooting.md)** guide.

You are now ready to use the BMAD MCP Server to streamline your development workflow!
