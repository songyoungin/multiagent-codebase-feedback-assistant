"""Main CLI entry point for codebase analyzer."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import click

from cli.api_client import AgentClient
from cli.docker_manager import DockerManager
from cli.formatters import print_error, print_response, print_status_table, print_success
from common.settings import settings


@click.group()
@click.version_option(version="0.1.0")
@click.option(
    "--volume-mount",
    default=None,
    help=f"Host path to mount in Docker containers (default: {settings.volume_mount})",
)
@click.pass_context
def cli(ctx: click.Context, volume_mount: str | None) -> None:
    """Codebase Analyzer - AI-powered code analysis using multi-agent system."""
    ctx.ensure_object(dict)
    ctx.obj["volume_mount"] = volume_mount or settings.volume_mount


@cli.group()
@click.pass_context
def server(ctx: click.Context) -> None:
    """Manage analysis server lifecycle."""
    pass


@server.command()
@click.pass_context
def start(ctx: click.Context) -> None:
    """Start all analysis servers."""
    try:
        manager = DockerManager()
        volume_mount = ctx.obj["volume_mount"]
        manager.start_containers(volume_mount=volume_mount)
    except Exception as e:
        print_error(f"Failed to start servers: {e}")
        raise click.Abort() from e


@server.command()
def stop() -> None:
    """Stop all analysis servers."""
    try:
        manager = DockerManager()
        manager.stop_containers()
    except Exception as e:
        print_error(f"Failed to stop servers: {e}")
        raise click.Abort() from e


@server.command()
@click.pass_context
def restart(ctx: click.Context) -> None:
    """Restart all analysis servers."""
    try:
        manager = DockerManager()
        volume_mount = ctx.obj["volume_mount"]
        manager.restart_containers(volume_mount=volume_mount)
    except Exception as e:
        print_error(f"Failed to restart servers: {e}")
        raise click.Abort() from e


@server.command()
def status() -> None:
    """Show status of all analysis servers."""
    try:
        manager = DockerManager()
        container_status = manager.get_container_status()
        print_status_table(container_status)
    except Exception as e:
        print_error(f"Failed to get server status: {e}")
        raise click.Abort() from e


@cli.command()
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--oneshot", is_flag=True, help="Start servers, analyze, then stop servers")
@click.pass_context
def scan(ctx: click.Context, project_path: str, oneshot: bool) -> None:
    """Scan project structure and collect statistics."""
    manager = DockerManager()
    client = AgentClient()
    volume_mount = ctx.obj["volume_mount"]

    try:
        # Ensure servers are running
        if oneshot or not manager.are_containers_running():
            manager.start_containers(volume_mount=volume_mount)

        # Call agent
        result = client.scan_project(str(Path(project_path).absolute()))
        print_response(result)
        print_success("Project scan completed")

    except Exception as e:
        print_error(f"Scan failed: {e}")
        raise click.Abort() from e
    finally:
        if oneshot:
            manager.stop_containers()


@cli.command()
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--oneshot", is_flag=True, help="Start servers, analyze, then stop servers")
@click.pass_context
def check_deps(ctx: click.Context, project_path: str, oneshot: bool) -> None:
    """Check for unused dependencies."""
    manager = DockerManager()
    client = AgentClient()
    volume_mount = ctx.obj["volume_mount"]

    try:
        # Ensure servers are running
        if oneshot or not manager.are_containers_running():
            manager.start_containers(volume_mount=volume_mount)

        # Call agent
        result = client.check_dependencies(str(Path(project_path).absolute()))
        print_response(result)
        print_success("Dependency check completed")

    except Exception as e:
        print_error(f"Dependency check failed: {e}")
        raise click.Abort() from e
    finally:
        if oneshot:
            manager.stop_containers()


@cli.command()
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--include-private", is_flag=True, help="Include private methods/functions")
@click.option("--oneshot", is_flag=True, help="Start servers, analyze, then stop servers")
@click.pass_context
def check_docs(ctx: click.Context, project_path: str, include_private: bool, oneshot: bool) -> None:
    """Analyze documentation coverage."""
    manager = DockerManager()
    client = AgentClient()
    volume_mount = ctx.obj["volume_mount"]

    try:
        # Ensure servers are running
        if oneshot or not manager.are_containers_running():
            manager.start_containers(volume_mount=volume_mount)

        # Call agent
        result = client.analyze_documentation(str(Path(project_path).absolute()), include_private=include_private)
        print_response(result)
        print_success("Documentation analysis completed")

    except Exception as e:
        print_error(f"Documentation analysis failed: {e}")
        raise click.Abort() from e
    finally:
        if oneshot:
            manager.stop_containers()


@cli.command()
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--max-items", default=20, help="Maximum number of items to analyze")
@click.option("--include-private", is_flag=True, help="Include private methods/functions")
@click.option("--oneshot", is_flag=True, help="Start servers, analyze, then stop servers")
@click.pass_context
def check_srp(ctx: click.Context, project_path: str, max_items: int, include_private: bool, oneshot: bool) -> None:
    """Check for Single Responsibility Principle violations."""
    manager = DockerManager()
    client = AgentClient()
    volume_mount = ctx.obj["volume_mount"]

    try:
        # Ensure servers are running
        if oneshot or not manager.are_containers_running():
            manager.start_containers(volume_mount=volume_mount)

        # Call agent
        result = client.check_srp_violations(
            str(Path(project_path).absolute()), max_items=max_items, include_private=include_private
        )
        print_response(result)
        print_success("SRP analysis completed")

    except Exception as e:
        print_error(f"SRP analysis failed: {e}")
        raise click.Abort() from e
    finally:
        if oneshot:
            manager.stop_containers()


@cli.command()
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--max-items", default=30, help="Maximum number of items to analyze")
@click.option("--include-private", is_flag=True, help="Include private methods/functions")
@click.option("--oneshot", is_flag=True, help="Start servers, analyze, then stop servers")
@click.pass_context
def check_naming(ctx: click.Context, project_path: str, max_items: int, include_private: bool, oneshot: bool) -> None:
    """Analyze naming quality."""
    manager = DockerManager()
    client = AgentClient()
    volume_mount = ctx.obj["volume_mount"]

    try:
        # Ensure servers are running
        if oneshot or not manager.are_containers_running():
            manager.start_containers(volume_mount=volume_mount)

        # Call agent
        result = client.analyze_naming_quality(
            str(Path(project_path).absolute()), max_items=max_items, include_private=include_private
        )
        print_response(result)
        print_success("Naming quality analysis completed")

    except Exception as e:
        print_error(f"Naming quality analysis failed: {e}")
        raise click.Abort() from e
    finally:
        if oneshot:
            manager.stop_containers()


@cli.command()
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--oneshot", is_flag=True, help="Start servers, analyze, then stop servers")
@click.pass_context
def analyze_all(ctx: click.Context, project_path: str, oneshot: bool) -> None:
    """Run all available analyses on the project."""
    manager = DockerManager()
    client = AgentClient()
    volume_mount = ctx.obj["volume_mount"]

    analyses: list[tuple[str, Callable[[], dict[str, Any]]]] = [
        ("Project Structure", lambda: client.scan_project(project_path)),
        ("Dependencies", lambda: client.check_dependencies(project_path)),
        ("Documentation", lambda: client.analyze_documentation(project_path)),
        ("SRP Violations", lambda: client.check_srp_violations(project_path)),
        ("Naming Quality", lambda: client.analyze_naming_quality(project_path)),
    ]

    try:
        # Ensure servers are running
        if oneshot or not manager.are_containers_running():
            manager.start_containers(volume_mount=volume_mount)

        # Run all analyses
        for name, analysis_func in analyses:
            click.echo(f"\n{'=' * 60}")
            click.echo(f"Running {name} analysis...")
            click.echo("=" * 60)

            try:
                result = analysis_func()
                print_response(result)
            except Exception as e:
                print_error(f"{name} analysis failed: {e}")
                continue

        print_success("All analyses completed")

    except Exception as e:
        print_error(f"Analysis failed: {e}")
        raise click.Abort() from e
    finally:
        if oneshot:
            manager.stop_containers()


@cli.command()
@click.argument("query")
@click.option("--oneshot", is_flag=True, help="Start servers, analyze, then stop servers")
@click.pass_context
def ask(ctx: click.Context, query: str, oneshot: bool) -> None:
    """Ask orchestrator in natural language.

    The orchestrator will analyze your query and coordinate the appropriate
    agents to provide a comprehensive response.

    Examples:
        codebase-analyzer ask "Analyze the entire project at /path/to/project"
        codebase-analyzer ask "Check for code quality issues in /path/to/project"
        codebase-analyzer ask "What improvements can be made to /path/to/project?"
    """
    manager = DockerManager()
    client = AgentClient()
    volume_mount = ctx.obj["volume_mount"]

    try:
        # Ensure servers are running
        if oneshot or not manager.are_containers_running():
            manager.start_containers(volume_mount=volume_mount)

        # Call orchestrator
        result = client.query_orchestrator(query)
        print_response(result)
        print_success("Orchestrator query completed")

    except Exception as e:
        print_error(f"Orchestrator query failed: {e}")
        raise click.Abort() from e
    finally:
        if oneshot:
            manager.stop_containers()


def main() -> None:
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
