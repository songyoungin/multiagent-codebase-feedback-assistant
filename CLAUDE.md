# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project is an AI-powered multi-agent system that analyzes Python codebases to identify code smells, architectural issues, unused dependencies, missing documentation, and more. It is implemented using the Model Context Protocol (MCP).

## Project Structure

```
multiagent-codebase-feedback-assistant/
├── agents/                          # Agent implementations
│   ├── helpers/                     # Shared utilities for agents
│   │   ├── create_a2a_server.py    # A2A server factory
│   │   └── test_agent.py           # Local agent testing utilities
│   ├── project_scanner/             # Project structure scanner
│   │   ├── project_scanner_agent.py # Agent definition
│   │   └── project_scanner_server.py # A2A server entry point
│   └── dependency_checker/          # Dependency checker
│       ├── dependency_checker_agent.py # Agent definition
│       └── dependency_checker_server.py # A2A server entry point
├── common/                          # Shared modules
│   ├── logger.py                   # Logging utilities
│   ├── prompts.py                  # Agent system prompts
│   ├── schemas.py                  # Data schemas
│   └── settings.py                 # Configuration management
├── tools/                           # Agent tools
│   ├── filesystem_tool.py          # Filesystem scanning tool
│   └── dependency_checker_tool.py  # Dependency analysis tool
├── typings/                         # Type stubs for third-party packages
│   └── google/adk/                 # google-adk type stubs
├── main.py                          # A2A client for testing agents
└── pyproject.toml                   # Project configuration
```

## Development Setup

### Package Management
This project uses `uv` as the package manager.

```bash
# Install dependencies
uv sync

# Activate development environment
source .venv/bin/activate

# Add a dependency
uv add <package-name>

# Add a development dependency
uv add --dev <package-name>
```

### Environment Configuration

Create a `.env` file in the project root with the following variables:

```bash
# OpenAI API configuration (required)
OPENAI_API_KEY=your_openai_api_key_here

# LLM model configuration
OPENAI_MODEL=openai/gpt-4o-mini

# Shared bind host for all agents
BIND_HOST=0.0.0.0

# Project Scanner Agent configuration
PROJECT_SCANNER_AGENT_URL=http://localhost:8301

# Dependency Checker Agent configuration
DEPENDENCY_CHECKER_AGENT_URL=http://localhost:8302

# Filesystem MCP configuration
FILESYSTEM_MCP_ENABLED=true
```

See [.env.example](.env.example) for reference.

### Running the Application

#### Starting an Agent Server

Each agent runs as a standalone A2A server:

```bash
# Start the Project Scanner Agent server
uv run python -m agents.project_scanner.project_scanner_server

# Start the Dependency Checker Agent server
uv run python -m agents.dependency_checker.dependency_checker_server
```

The servers will start on the ports specified in their respective URL settings:
- Project Scanner: default 8301
- Dependency Checker: default 8302

#### Using the A2A Client

Once an agent server is running, use the client to send requests:

```bash
# Send a command to the Project Scanner Agent
uv run python main.py \
  --agent-url http://localhost:8301 \
  --command "Scan the project at /path/to/your/project"
```

The client supports:
- `--agent-url`: Agent server URL (defaults to PROJECT_SCANNER_AGENT_URL from settings)
- `--command`: User request message to send to the agent

## Core Architecture

### Multi-Agent System
This project follows a collaborative multi-agent architecture for codebase analysis:
- Each agent is responsible for a specific analysis domain (code smells, architecture, dependencies, documentation)
- Agent coordination and communication is handled via MCP
- Agents communicate via the A2A (Agent-to-Agent) protocol over HTTP

### Implemented Agents

#### Project Scanner Agent
**Location**: `agents/project_scanner/`

Scans project directory structures and collects file/directory statistics.

**Capabilities**:
- Recursive directory scanning with configurable depth limits
- Pattern-based exclusion (e.g., `.git`, `__pycache__`, `node_modules`)
- File extension statistics
- Metadata collection (file size, modification time)

**Tools**:
- `scan_project`: Scans project structure and returns a `ProjectStructure` object

**Usage**:
```bash
# Start the server
uv run python -m agents.project_scanner.project_scanner_server

# Send a request
uv run python main.py \
  --agent-url http://localhost:8301 \
  --command "Scan the project at /path/to/project"
```

#### Dependency Checker Agent
**Location**: `agents/dependency_checker/`

Analyzes Python project dependencies to identify unused packages.

**Capabilities**:
- Parse declared dependencies from `pyproject.toml`
- Extract actually imported packages from Python source files using AST
- Identify unused dependencies (declared but never imported)
- Filter out standard library modules
- Pattern-based file exclusion

**Tools**:
- `check_unused_dependencies`: Analyzes project dependencies and returns a `DependencyCheckResult` object
  - Parses `[project.dependencies]` from pyproject.toml
  - Scans all Python files for import statements
  - Compares declared vs. used packages
  - Returns detailed results with actionable recommendations

**Usage**:
```bash
# Start the server
uv run python -m agents.dependency_checker.dependency_checker_server

# Send a request
uv run python main.py \
  --agent-url http://localhost:8302 \
  --command "Check unused dependencies in /path/to/project"
```

### Key Dependencies
- `google-adk[a2a]`: Google AI Development Kit with Agent-to-Agent capabilities
- `litellm`: Multi-provider LLM API wrapper (supports OpenAI, Anthropic, etc.)
- `pydantic`: Data validation and settings management
- `fastapi` + `uvicorn`: A2A server implementation
- Python 3.13 or higher is required

## Development Guidelines

### Code Quality
- Provide explicit type hints for all public interfaces
- Prioritize readability over performance
- Follow the Single Responsibility Principle

### Type Checking
This project uses strict type checking with mypy:

```bash
# Run type checking via pre-commit
uv run pre-commit run mypy --all-files

# Or run mypy directly
uv run mypy .
```

**Configuration** (`pyproject.toml`):
- Strict mode enabled (disallow untyped defs, incomplete defs)
- Custom type stubs in `typings/` directory for third-party packages
- Python 3.13 target

**Type Stubs**:
- `typings/google/adk/`: Type stubs for google-adk library
- These stubs provide type hints for untyped third-party packages

### Code Formatting & Linting

Pre-commit hooks are configured to run on every commit:

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run all checks manually
uv run pre-commit run --all-files
```

**Tools**:
- `ruff`: Fast Python linter and formatter (replaces Black, isort, flake8)
- `mypy`: Static type checker

### Testing
- Write tests as test methods, not test classes
- Use decorators for mocking instead of context managers
- Include docstrings and comments in test methods (specify mock conditions and validation checks)

### Documentation
- **All docstrings and inline comments must be written in English**
- Follow Google-style docstrings for all public classes and methods
- Keep docstrings concise and clear
- Avoid unnecessary line breaks in docstrings

### Virtual Environment
The virtual environment is located in the `.venv` directory at the project root. Include `.venv` activation when providing code execution commands.
