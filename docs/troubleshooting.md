# Troubleshooting BMAD MCP Server

This guide provides solutions to common issues you might encounter when setting up or using the BMAD MCP Server.

## Server Startup Issues

### Issue: `Address already in use` or `Port already in use` (SSE Mode)

-   **Cause**: Another application is already using the port the BMAD MCP Server is trying to bind to (default: `8000` for SSE).
-   **Solution**:
    1.  Identify and stop the other application using the port.
    2.  Or, configure the BMAD MCP Server to use a different port:
        -   **Local Python Run**:
            ```bash
            python -m bmad_mcp_server.main --mode sse --port 8001
            ```
        -   **Docker Compose**: Modify `docker-compose.yml`:
            ```yaml
            services:
              bmad-mcp-server:
                ports:
                  - "8001:8000" # Host port 8001 maps to container port 8000
            ```
            Then run `docker-compose up -d bmad-mcp-server`. Your server will be accessible on `http://localhost:8001`.
        -   **`config/server.json`**: You can also set `sse_port` in `config/server.json`.

### Issue: Server fails to start with "Already running asyncio in this thread"

-   **Cause**: This typically indicates an issue with how asyncio event loops are being managed, often if `asyncio.run()` is called from within an already running asyncio context. This was an issue in older versions of the server startup logic.
-   **Solution**: Ensure you are using the latest version of the BMAD MCP Server code, as this has been addressed by using FastMCP's asynchronous runner methods. If you encounter this with custom modifications, ensure you are not nesting `asyncio.run()` calls.

### Issue: Missing API Keys for LLMs

-   **Symptom**: Server starts, but tools that use CrewAI agents fail with errors related to missing API keys (e.g., `openai.AuthenticationError`, `anthropic.AuthenticationError`).
-   **Cause**: The necessary API keys for the LLM providers (OpenAI, Anthropic, Google Gemini, AWS Bedrock) used by CrewAI agents are not correctly set in the environment.
-   **Solution**:
    1.  Ensure your `.env` file (in the project root) is correctly populated with your API keys. Example:
        ```env
        OPENAI_API_KEY=your_sk_...
        ANTHROPIC_API_KEY=your_sk_ant_...
        ```
    2.  If running locally without Docker, ensure these environment variables are exported in your current shell session or set system-wide.
    3.  If using Docker Compose, the `.env` file is automatically used. Verify its contents.
    4.  Check `config/server.json` or `src/bmad_mcp_server/crewai_integration/config.py` if you have custom LLM configurations there that might be missing credentials.

### Issue: `ModuleNotFoundError` or `ImportError`

-   **Cause**: Python dependencies are not installed correctly, or your Python environment is not set up properly.
-   **Solution**:
    1.  **Local Python Run**:
        -   Ensure your virtual environment is activated: `source .venv/bin/activate` (or `.venv\Scripts\activate` on Windows).
        -   Reinstall dependencies: `pip install -e .`
    2.  **Docker**:
        -   Rebuild the Docker image: `docker-compose build`
        -   Ensure the `Dockerfile` correctly copies `pyproject.toml` and runs `pip install`.

## AI Assistant Connection Issues

### Issue: AI Assistant cannot find/connect to the BMAD MCP Server

-   **Cause (Stdio Mode)**:
    -   Incorrect command or path specified in the AI assistant's MCP configuration.
    -   The server script is not executable or Python environment is not found by the assistant.
    -   `--project-root` path is incorrect, and the server cannot find/create the `.bmad` directory.
-   **Solution (Stdio Mode)**:
    -   Verify the `command` and `args` in your assistant's MCP settings (e.g., `cline_mcp_settings.json`, `.vscode/mcp.json`, or `claude mcp add` command).
    -   Use absolute paths for the Python interpreter and the `--project-root` argument if relative paths are causing issues.
    -   Ensure the server script has execute permissions if run directly (less common with `python -m ...`).
    -   Check the AI assistant's logs for more specific error messages.

-   **Cause (SSE Mode)**:
    -   Server is not running or not accessible on the configured URL/port.
    -   Firewall is blocking the connection.
    -   Incorrect URL specified in the AI assistant's MCP configuration (e.g., missing `/mcp` path for FastMCP).
-   **Solution (SSE Mode)**:
    -   Ensure the server (local or Docker) is running and logs indicate it's listening on the expected host/port (e.g., `http://localhost:8000`).
    -   Try accessing the server's health check endpoint (if available, e.g., `http://localhost:8000/health`) or the MCP endpoint (`http://localhost:8000/mcp`) from your browser or `curl`.
    -   Check firewall settings on your machine and network.
    -   Verify the URL in your assistant's MCP configuration (e.g., `http://localhost:8000/mcp`).

### Issue: AI Assistant reports "Tool Not Found"

-   **Cause**:
    -   The tool name used by the assistant doesn't match the name registered by the server. Tool names are case-sensitive and typically snake_case (e.g., `create_project_brief`).
    -   The server failed to register the tool during startup (check server logs).
-   **Solution**:
    -   Verify the tool names in the server's `_register_native_tools` method in `src/bmad_mcp_server/server.py`.
    -   Check your AI assistant's documentation for how it discovers/lists available tools from an MCP server. Some assistants allow you to inspect available tools.
    -   Ensure there were no errors during server startup related to tool registration.

## Tool Execution Issues

### Issue: Tool execution fails or returns unexpected results

-   **Cause**:
    -   Incorrect arguments passed to the tool.
    -   Bugs in the tool's implementation logic (Python code within the tool class).
    -   Errors from CrewAI agents (e.g., LLM API errors, prompt issues).
    -   Problems with `StateManager` (e.g., cannot read/write artifacts in `.bmad` directory due to permissions).
    -   Missing templates or checklists.
-   **Solution**:
    1.  **Check Server Logs**: The BMAD MCP Server logs (console or file specified in `config/server.json`) are your primary source for diagnosing tool execution errors. Look for tracebacks or error messages.
    2.  **Input Validation**: Tools use Pydantic for input validation. If arguments are incorrect, the server should ideally return a validation error to the assistant.
    3.  **CrewAI Verbosity**: If a tool uses CrewAI, you can try increasing CrewAI's verbosity. Set `CREWAI_VERBOSE=true` in your `.env` file or `"verbose_logging": true` in `config/server.json` under `crewai_config`. This will provide more detailed logs from the agents and tasks.
    4.  **Permissions**: Ensure the server process (local user or Docker user) has read/write permissions for the project directory and its `.bmad` subdirectory.
    5.  **Templates/Checklists**: Verify that required template files (in `src/bmad_mcp_server/templates/`) and checklist files (in `src/bmad_mcp_server/checklists/`) exist and are correctly named.
    6.  **Isolate the Tool**: If possible, try to test the tool's logic directly by writing a small Python script that instantiates the tool class and calls its `execute` method with sample arguments.

### Issue: Artifacts not saved or saved in the wrong location

-   **Cause**:
    -   Incorrect `--project-root` specified when starting the server.
    -   Permissions issues preventing file writes.
    -   Logic error in the tool's `execute` method regarding how it uses `StateManager.save_artifact()`.
-   **Solution**:
    -   Verify the `--project-root` argument. The `.bmad` directory will be created relative to this root.
    -   Check file system permissions for the project root directory.
    -   Review the `save_artifact` calls within the specific tool's code.

## General Debugging Tips

-   **Increase Log Level**: Set `BMAD_LOG_LEVEL=DEBUG` in your `.env` file or `"log_level": "DEBUG"` in `config/server.json` for more detailed server output.
-   **Inspect `.bmad` Directory**: Regularly check the contents of the `.bmad` directory to see what artifacts are being created and their content.
-   **Simplify Prompts**: When testing, start with simple prompts to your AI assistant to isolate whether the issue is with the prompt, the assistant's interpretation, or the server/tool itself.
-   **Check AI Assistant Logs**: Your AI coding assistant might also have its own logs or debug console that can provide clues about MCP communication issues.
-   **Restart Everything**: Sometimes, restarting the BMAD MCP Server, your AI assistant, and/or your IDE can resolve transient issues.

If you encounter an issue not covered here, consider opening an issue on the project's GitHub repository with detailed steps to reproduce the problem and relevant log excerpts.
