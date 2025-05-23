"""
Main entry point for BMAD MCP Server.
"""

import asyncio
import sys
from pathlib import Path
import logging

import click
from rich.console import Console

from .server import BMadMCPServer
from .utils.logging import setup_logging

console = Console()
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--mode",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport mode (default: stdio)"
)
@click.option(
    "--host",
    default="localhost",
    help="Host for SSE mode (default: localhost)"
)
@click.option(
    "--port",
    type=int,
    default=8000,
    help="Port for SSE mode (default: 8000)"
)
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Configuration file path"
)
@click.option(
    "--project-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Project root directory (default: current directory)"
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
    help="Logging level (default: INFO)"
)
@click.version_option(version="1.0.0", prog_name="BMAD MCP Server")
def main(mode, host, port, config, project_root, log_level):
    """
    BMAD MCP Server - Expose BMAD methodology as standardized tools for AI systems.
    
    This server provides Model Context Protocol (MCP) tools that implement the
    BMAD (Breakthrough Method of Agile AI-driven Development) methodology.
    """
    # Setup basic logging first
    setup_logging(level=log_level)
    
    try:
        # Create and run server
        asyncio.run(_run_server(mode, host, port, config, project_root))
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Server failed to start: {e}[/red]")
        sys.exit(1)


async def _run_server(mode, host, port, config, project_root):
    """Run the server with given configuration."""
    try:
        # Create server
        server = BMadMCPServer(
            config_path=config,
            project_root=project_root
        )
        
        console.print(f"[green]Starting BMAD MCP Server in {mode} mode[/green]")
        
        if project_root:
            console.print(f"[blue]Project root: {project_root}[/blue]")
        
        # Start server in requested mode
        if mode == "stdio":
            await server.run_stdio()
        elif mode == "sse":
            console.print(f"[blue]Server URL: http://{host}:{port}[/blue]")
            await server.run_sse(host=host, port=port)
            
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
