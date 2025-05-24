# Docker Deployment for BMAD MCP Server

Using Docker and Docker Compose is the recommended way to deploy and manage the BMAD MCP Server. This approach simplifies dependency management, ensures consistent environments, and makes it easy to run the server in different modes.

## Prerequisites

-   **Docker**: Install Docker Desktop (for Windows/Mac) or Docker Engine (for Linux).
-   **Docker Compose**: Usually included with Docker Desktop. For Linux, you might need to install it separately.
-   **Git**: For cloning the repository.

## Setup

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/bmad-project/bmad-mcp-server
    cd bmad-mcp-server
    ```

2.  **Configure Environment Variables**:
    The server relies on a `.env` file in the project root for API keys and other configurations.
    ```bash
    cp .env.example .env
    ```
    Open the `.env` file and add your LLM API keys (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`). Refer to the [Configuration](./configuration.md#environment-variables) guide for details on all available variables.

    **Example `.env` content:**
    ```env
    OPENAI_API_KEY=your_openai_api_key_here
    ANTHROPIC_API_KEY=your_anthropic_api_key_here
    BMAD_LOG_LEVEL=INFO
    ```

## Using Docker Compose

The `docker-compose.yml` file defines two services:

-   `bmad-mcp-server`: Runs the server in SSE (Server-Sent Events) mode, typically on `http://localhost:8000`. This is suitable for AI assistants that connect via HTTP.
-   `bmad-mcp-stdio`: Runs the server in stdio mode. This is for AI assistants that manage the server as a child process.

### Running in SSE Mode (Recommended for most clients)

This mode makes the server accessible over the network (by default, on your local machine at port 8000).

```bash
docker-compose up bmad-mcp-server
```

-   To run in the background (detached mode):
    ```bash
    docker-compose up -d bmad-mcp-server
    ```
-   The server's MCP endpoint will typically be `http://localhost:8000/mcp`.
-   Logs can be viewed with: `docker-compose logs -f bmad-mcp-server`

### Running in Stdio Mode

This mode is for clients that expect to communicate with the server via standard input/output.

```bash
docker-compose up bmad-mcp-stdio
```
-   This service will typically run, wait for input, process it, and then might exit or wait for more input, depending on the client's behavior.
-   Logs: `docker-compose logs -f bmad-mcp-stdio`

### Stopping the Server

-   If running in the foreground, press `Ctrl+C`.
-   If running in detached mode or to stop all services:
    ```bash
    docker-compose down
    ```

### Rebuilding the Image

If you make changes to the server's source code or `Dockerfile`, you'll need to rebuild the Docker image:

```bash
docker-compose build bmad-mcp-server
# or
docker-compose build bmad-mcp-stdio
# or to rebuild all services
docker-compose build
```
Then, restart the services using `docker-compose up ...`.

## Dockerfile Overview

The `Dockerfile` in the project root defines how the BMAD MCP Server image is built:

-   Uses a `python:3.11-slim` base image.
-   Sets up a non-root user (`bmad`) for better security.
-   Installs system dependencies (like `gcc` if needed for Python packages).
-   Copies `pyproject.toml` and installs Python dependencies using `pip install -e .` (editable mode, which is useful if you mount source code for development).
-   Copies the application source code (`src/` and `scripts/`).
-   Sets the working directory to `/app` and changes ownership to the `bmad` user.
-   Exposes port `8000` (for SSE mode).
-   The default command runs the server in stdio mode: `CMD ["python", "-m", "bmad_mcp_server.main", "--mode", "stdio", "--project-root", "/app"]`.
    -   Note: The `--project-root /app` assumes that if you mount your project into `/app/project_data` (see below), the server should manage artifacts there. The `docker-compose.yml` handles this by setting the command.

## Managing Project Artifacts (`.bmad` directory)

The BMAD MCP Server creates and manages artifacts in a `.bmad` directory. When running via Docker, you need to ensure this directory is persisted and accessible.

The provided `docker-compose.yml` includes volume mounts:

```yaml
services:
  bmad-mcp-server:
    # ...
    volumes:
      - ./config:/app/config:ro  # Mounts a local config directory (read-only)
      - ./logs:/app/logs          # Mounts a local logs directory
      - .:/app/project_data       # Mounts the current project directory
    command: ["python", "-m", "bmad_mcp_server.main", "--mode", "sse", "--host", "0.0.0.0", "--project-root", "/app/project_data"]
    # ...
  bmad-mcp-stdio:
    # ...
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
      - .:/app/project_data
    command: ["python", "-m", "bmad_mcp_server.main", "--mode", "stdio", "--project-root", "/app/project_data"]
    # ...
```

-   **`./config:/app/config:ro`**: Mounts a local `./config` directory into the container at `/app/config` (read-only). You can place your `server.json` here.
-   **`./logs:/app/logs`**: Mounts a local `./logs` directory into `/app/logs`. If the server is configured to log to a file in `/app/logs`, those logs will appear in your local `./logs` directory.
-   **`.:/app/project_data`**: This is crucial. It mounts your current host project directory (where `docker-compose.yml` is located) into `/app/project_data` inside the container.
-   **`--project-root /app/project_data`**: The `command` in `docker-compose.yml` overrides the Dockerfile's default CMD and tells the server to use `/app/project_data` (which is your mounted project directory) as the root for managing the `.bmad` folder.

This setup means:
-   The `.bmad` directory will be created and managed directly within your local project folder on your host machine.
-   Any artifacts generated by the server (e.g., PRDs, stories) will appear in `./.bmad/` on your host.
-   This allows you to easily access, review, and version-control these artifacts.

## Customization

-   **Ports**: If port `8000` is already in use on your host, you can change the host port mapping in `docker-compose.yml`:
    ```yaml
    ports:
      - "8001:8000" # Host port 8001 maps to container port 8000
    ```
-   **Configuration**: Modify the `.env` file for API keys and basic settings. For more advanced server settings, create/edit `config/server.json` locally, and it will be available to the container.
-   **Source Code Development**: If you are actively developing the BMAD MCP Server itself, the `docker-compose.yml` can be modified to mount your local `src` directory into the container to reflect code changes without rebuilding the image (though a server restart might be needed). However, the current `docker-compose.yml` copies the source code during the build, so image rebuilds are necessary for source code changes.

By using Docker, you get a portable, reproducible, and isolated environment for running the BMAD MCP Server, making it easier to integrate into various development setups.
