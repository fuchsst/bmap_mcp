# IDE Integration for BMAD MCP Server

This guide explains how to configure your AI Coding Assistant (Cline, Claude Code, GitHub Copilot) in your Integrated Development Environment (IDE) to connect to and use the BMAD MCP Server.

Ensure the BMAD MCP Server is running before attempting to configure your IDE. Refer to the [Getting Started](./getting-started.md) guide for server installation and startup instructions.

## General Concepts

Most AI assistants that support MCP require you to specify how to connect to an MCP server. This usually involves:

-   **Transport Mode**:
    -   **Stdio (Standard Input/Output)**: The AI assistant runs the MCP server as a child process and communicates with it via stdin/stdout. This is common for local servers.
    -   **SSE (Server-Sent Events)**: The AI assistant connects to an MCP server running as an HTTP service, typically on `localhost` or a remote URL.
-   **Server Command/URL**:
    -   For stdio: The command to execute the server (e.g., `python -m bmad_mcp_server.main --mode stdio --project-root .`).
    -   For SSE: The URL of the server's MCP endpoint (e.g., `http://localhost:8000/mcp` if the server is running locally on port 8000).
-   **Scope**: Configuration can often be project-specific (shared with a team via a config file in the repo) or user-specific (global to your IDE setup).

## Cline

Cline provides a user interface within your IDE (e.g., VS Code extension) for managing MCP servers.

### Configuring BMAD MCP Server in Cline:

1.  **Open Cline Extension**: In VS Code, open the Cline sidebar.
2.  **Access MCP Servers**: Click the "MCP Servers" icon/tab.
3.  **Add New Server**:
    *   You might find an option to "Add Server Manually" or "Configure MCP Servers".
    *   Cline stores its MCP server configurations in a `cline_mcp_settings.json` file. You can often edit this directly or through the UI.

#### Example Stdio Configuration for Cline:

If you are running the BMAD MCP Server locally via `python -m ...`:

In your `cline_mcp_settings.json` (accessible via Cline's "Configure MCP Servers" button):

```json
{
  "mcpServers": {
    "bmad-mcp-server-stdio": {
      "command": "python", // Or the full path to your virtualenv python
      "args": [
        "-m",
        "bmad_mcp_server.main",
        "--mode",
        "stdio",
        "--project-root",
        "." // Or the absolute path to your project if Cline runs from a different CWD
      ],
      "env": {
        // Ensure API keys are set if not globally available
        // "OPENAI_API_KEY": "your_key",
        // "ANTHROPIC_API_KEY": "your_key"
      },
      "disabled": false
    }
  }
}
```
-   **`command`**: The executable (e.g., `python` or `docker-compose`).
-   **`args`**: Arguments to pass to the command.
-   **`env`**: Environment variables for the server process.
-   **`project-root .`**: This assumes Cline will execute the command from your project's root directory. If not, provide an absolute path.

#### Example SSE Configuration for Cline:

If the BMAD MCP Server is running via Docker Compose (`docker-compose up bmad-mcp-server`) or locally in SSE mode (`python -m bmad_mcp_server.main --mode sse ...`), it's typically available at `http://localhost:8000`.

In your `cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "bmad-mcp-server-sse": {
      "url": "http://localhost:8000/mcp", // Default MCP path for FastMCP SSE
      "headers": {
        // "Authorization": "Bearer your-token" // If your server requires auth
      },
      "disabled": false
    }
  }
}
```

### Using BMAD Tools with Cline:

-   Once configured and enabled, Cline will automatically detect the BMAD MCP Server's tools.
-   When you chat with Cline, if a task can be aided by a BMAD tool, Cline will suggest its use or use it automatically (depending on your approval settings).
-   Example prompt: `"Draft a PRD for a new feature: user profile customization."` Cline might then use the `generate_prd` tool.

Refer to the [Cline MCP Documentation](https://github.com/cline/cline/blob/main/docs/mcp/configuring-mcp-servers.mdx) for more details.

## Claude Code

Claude Code (Anthropic's coding assistant) also supports MCP for extending its capabilities.

### Configuring BMAD MCP Server in Claude Code:

Claude Code uses a CLI command `claude mcp add` to configure servers.

1.  **Open your terminal.**
2.  **Add the BMAD MCP Server**:

    #### Stdio Mode:
    If you're running the server locally via `python -m ...`:
    ```bash
    claude mcp add bmad-server -- /path/to/your/project/.venv/bin/python -m bmad_mcp_server.main --mode stdio --project-root /path/to/your/project
    ```
    -   Replace `/path/to/your/project/.venv/bin/python` with the actual path to the Python interpreter in your project's virtual environment (if you use one).
    -   Replace `/path/to/your/project` with the absolute path to your project.
    -   You can set environment variables using `-e API_KEY=value`.
    -   Use `-s project` to save this configuration to a `.mcp.json` file in your project root (sharable with your team) or `-s user` for a global user-level configuration. Default is `local` (project-specific, not shared).

    Example for a project-scoped stdio server (creates/updates `.mcp.json`):
    ```bash
    # Assuming you are in your project root
    claude mcp add bmad-server -s project -- venv/bin/python -m bmad_mcp_server.main --mode stdio --project-root .
    ```

    #### SSE Mode:
    If the server is running via Docker or locally in SSE mode (e.g., on `http://localhost:8000`):
    ```bash
    claude mcp add --transport sse bmad-server-sse http://localhost:8000/mcp
    ```
    -   Use `-s project` or `-s user` as needed.

3.  **Manage Servers**:
    -   List servers: `claude mcp list`
    -   Get server details: `claude mcp get bmad-server`
    -   Remove a server: `claude mcp remove bmad-server`

### Using BMAD Tools with Claude Code:

-   Start a Claude Code session (`claude` in your terminal).
-   Claude Code will automatically discover and make available the tools from your configured and enabled MCP servers.
-   When you interact with Claude, it will use these tools as needed. For example, asking it to `"Generate a project brief for an e-commerce platform"` might trigger the `create_project_brief` tool.
-   You might be prompted for approval before a tool is executed, depending on the tool's nature and your settings.

Refer to the [Claude Code MCP Documentation](https://docs.anthropic.com/en/docs/claude-code/tutorials#set-up-model-context-protocol-mcp) for more details.

## GitHub Copilot

GitHub Copilot in VS Code can be extended with MCP servers, particularly when using its "Agent" mode.

### Configuring BMAD MCP Server for GitHub Copilot:

GitHub Copilot looks for MCP server configurations in a `.vscode/mcp.json` file in your repository root or in your user `settings.json`.

1.  **Create/Open Configuration File**:
    -   For a project-specific setup (recommended for team sharing), create or open `.vscode/mcp.json` in your project's root directory.
    -   For a user-specific setup, open your VS Code `settings.json` file (Ctrl+Shift+P or Cmd+Shift+P, then "Preferences: Open User Settings (JSON)").

2.  **Add Server Configuration**:

    #### Stdio Mode Example for `.vscode/mcp.json`:
    ```json
    {
      "servers": {
        "bmad-mcp-server": {
          "command": "python", // Or full path to python in your .venv
          "args": [
            "-m",
            "bmad_mcp_server.main",
            "--mode",
            "stdio",
            "--project-root",
            "${workspaceFolder}" // VS Code variable for current project root
          ],
          "env": {
            // "OPENAI_API_KEY": "your_key" // If needed
          }
        }
      }
    }
    ```
    -   `${workspaceFolder}` is a VS Code predefined variable that resolves to the path of the current workspace folder.

    #### SSE Mode Example for `.vscode/mcp.json`:
    If the server is running via Docker or locally in SSE mode (e.g., on `http://localhost:8000`):
    ```json
    {
      "servers": {
        "bmad-mcp-server-sse": {
          "url": "http://localhost:8000/mcp", // Default MCP path for FastMCP SSE
          "transport": "sse" // Explicitly state transport for URL-based servers
          // "headers": { "Authorization": "Bearer your_token" } // If auth is needed
        }
      }
    }
    ```
    *Note: The GitHub Copilot documentation structure for `mcp.json` might differ slightly (e.g., using an `inputs` array). Always refer to the latest official GitHub Copilot MCP documentation.*

3.  **Start/Enable Servers in VS Code**:
    -   VS Code might show a "Start" button in the `mcp.json` file or require a command/UI action to enable discovered MCP servers.
    -   You may need to grant permissions for Copilot to use tools from the server.

### Using BMAD Tools with GitHub Copilot:

1.  **Open Copilot Chat**: Click the Copilot icon in VS Code.
2.  **Select Agent Mode**: Ensure Copilot Chat is in "Agent" mode (often a selection in the chat input area).
3.  **Interact**: Prompt Copilot. For example: `"@bmad-mcp-server create a project brief for a new mobile game."`
    -   You might need to explicitly mention the server or tool if Copilot doesn't pick it up automatically.
    -   Copilot will likely ask for confirmation before executing tools.

Refer to the [GitHub Copilot MCP Documentation](https://docs.github.com/copilot/customizing-copilot/extending-copilot-chat-with-mcp) for the most up-to-date instructions.

## General Tips for IDE Integration

-   **Absolute Paths**: When configuring stdio servers, using absolute paths for the `command` (e.g., Python interpreter in a virtual environment) and `--project-root` can prevent issues related to the working directory from which the AI assistant spawns the server.
-   **Environment Variables**: Ensure that any necessary environment variables (like API keys for LLMs) are available to the MCP server process. This can be done by setting them in the `env` block of the MCP configuration, in your shell profile, or in the `.env` file if your server/assistant loads it.
-   **Permissions**: Be mindful of security. Your AI assistant will likely ask for permission before executing tools from a newly configured server, especially for project-specific configurations.
-   **Server Logs**: Keep an eye on the BMAD MCP Server's console output (or log file if configured) for troubleshooting. It will show incoming requests, tool executions, and any errors.
-   **Restart Assistant/IDE**: After adding or changing MCP server configurations, you might need to restart your AI assistant or even the entire IDE for the changes to take effect.
