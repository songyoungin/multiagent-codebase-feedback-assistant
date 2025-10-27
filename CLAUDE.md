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
│   ├── dependency_checker/          # Dependency checker
│   │   ├── dependency_checker_agent.py # Agent definition
│   │   └── dependency_checker_server.py # A2A server entry point
│   ├── documentation_generator/     # Documentation analyzer
│   │   ├── documentation_generator_agent.py # Agent definition
│   │   └── documentation_generator_server.py # A2A server entry point
│   └── srp_violation_detector/      # SRP violation detector
│       ├── srp_violation_detector_agent.py # Agent definition
│       └── srp_violation_detector_server.py # A2A server entry point
├── common/                          # Shared modules
│   ├── logger.py                   # Logging utilities
│   ├── prompts.py                  # Agent system prompts
│   ├── schemas.py                  # Data schemas
│   └── settings.py                 # Configuration management
├── tools/                           # Agent tools
│   ├── filesystem_tool.py          # Filesystem scanning tool
│   ├── dependency_checker_tool.py  # Dependency analysis tool
│   ├── documentation_analyzer_tool.py # Documentation coverage tool
│   └── srp_analyzer_tool.py        # SRP violation analysis tool
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

# Documentation Generator Agent configuration
DOCUMENTATION_GENERATOR_AGENT_URL=http://localhost:8303

# SRP Violation Detector Agent configuration
SRP_VIOLATION_DETECTOR_AGENT_URL=http://localhost:8304

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

# Start the Documentation Generator Agent server
uv run python -m agents.documentation_generator.documentation_generator_server

# Start the SRP Violation Detector Agent server
uv run python -m agents.srp_violation_detector.srp_violation_detector_server
```

The servers will start on the ports specified in their respective URL settings:
- Project Scanner: default 8301
- Dependency Checker: default 8302
- Documentation Generator: default 8303
- SRP Violation Detector: default 8304

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
- Each agent is responsible for a specific analysis domain (project structure, dependencies, documentation, code smells)
- Agent coordination and communication is handled via MCP
- Agents communicate via the A2A (Agent-to-Agent) protocol over HTTP
- Agents use semantic analysis (LLM understanding) rather than just static metrics

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

#### Documentation Generator Agent
**Location**: `agents/documentation_generator/`

Analyzes Python code documentation coverage and identifies missing docstrings.

**Capabilities**:
- Parse Python files using AST to find classes and functions
- Check for missing docstrings on public and private items
- Calculate documentation coverage percentage
- Extract function/class signatures with type hints
- Prioritize missing docstrings by importance (High/Medium/Low)

**Tools**:
- `analyze_documentation`: Analyzes docstring coverage and returns a `DocumentationAnalysisResult` object
  - Scans all Python files for class/function definitions
  - Checks docstring presence using `ast.get_docstring()`
  - Extracts complete signatures including parameters and return types
  - Optional: `include_private=true` to analyze private methods/functions

**Usage**:
```bash
# Start the server
uv run python -m agents.documentation_generator.documentation_generator_server

# Send a request (public items only)
uv run python main.py \
  --agent-url http://localhost:8303 \
  --command "Analyze documentation in /path/to/project"

# Include private methods
uv run python main.py \
  --agent-url http://localhost:8303 \
  --command "Analyze documentation including private methods in /path/to/project"
```

#### SRP Violation Detector Agent
**Location**: `agents/srp_violation_detector/`

Detects Single Responsibility Principle (SRP) violations in Python code through semantic analysis.

**Capabilities**:
- Extract functions and classes with full source code using AST
- Capture function calls, imports, parameters, and code length for context
- Use LLM to perform semantic analysis (not just metrics)
- Identify code with multiple responsibilities or reasons to change
- Categorize violations by severity (Critical/High/Medium/Low)
- Provide specific refactoring suggestions

**Tools**:
- `analyze_srp_violations`: Extracts code items with rich context and returns an `SRPAnalysisResult` object
  - Scans all Python files for function/class definitions
  - Extracts full source code, function calls, imports used
  - Captures signatures with type hints, parameter counts, code length
  - Optional: `max_items=N` to limit analysis (default: 20, manages LLM context)
  - Optional: `include_private=true` to analyze private methods

**What Makes This Different from Static Tools**:
Unlike ruff, pylint, or other static analyzers that check syntax and metrics, this agent:
- Understands semantic meaning and relationships in code
- Identifies responsibilities across different domains (e.g., validation + database + email)
- Considers "reasons to change" rather than just code length
- Analyzes function call patterns and import diversity for coupling detection
- Provides context-aware refactoring suggestions

**Usage**:
```bash
# Start the server
uv run python -m agents.srp_violation_detector.srp_violation_detector_server

# Send a request (analyze public items, max 20)
uv run python main.py \
  --agent-url http://localhost:8304 \
  --command "Analyze SRP violations in /path/to/project"

# Analyze more items
uv run python main.py \
  --agent-url http://localhost:8304 \
  --command "Analyze SRP violations in /path/to/project, check up to 50 items"

# Include private methods
uv run python main.py \
  --agent-url http://localhost:8304 \
  --command "Analyze SRP violations including private methods in /path/to/project"
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

## Creating New Agents

### Agent Architecture Pattern

Each agent follows a consistent three-file structure:

```
agents/<agent_name>/
├── __init__.py                    # Empty module marker
├── <agent_name>_agent.py         # Agent definition
└── <agent_name>_server.py        # A2A server entry point
```

### Step-by-Step Agent Creation

1. **Create Tool** (in `tools/`)
   - Tools collect and process data
   - Return structured data (Pydantic models)
   - Should NOT make decisions or call LLM
   - Must use `Optional[type]` instead of `type | None` for optional parameters (google-adk function parsing limitation)

2. **Define Schema** (in `common/schemas.py`)
   - Create Pydantic models for tool outputs
   - Use clear, descriptive field names

3. **Write Agent Prompt** (in `common/prompts.py`)
   - **Critical**: Explicitly state "Call tool ONLY ONCE" to prevent multiple calls
   - Use step-by-step instructions (Step 1, Step 2, etc.)
   - Clearly define what data the tool provides
   - Specify analysis tasks for the agent (not the tool)

4. **Create Agent Definition** (`agents/<agent_name>/<agent_name>_agent.py`)
```python
from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.function_tool import FunctionTool

from common.prompts import YOUR_AGENT_PROMPT
from common.settings import settings
from tools.your_tool import your_function

YOUR_TOOL = FunctionTool(func=your_function)
YOUR_MODEL = LiteLlm(model=settings.openai_model, tool_choice="auto")

YOUR_AGENT = LlmAgent(
    name="your_agent_name",
    model=YOUR_MODEL,
    instruction=YOUR_AGENT_PROMPT,
    tools=[YOUR_TOOL],
)
```

5. **Create A2A Server** (`agents/<agent_name>/<agent_name>_server.py`)
   - Use `create_agent_a2a_server` helper
   - Define agent URL in `common/settings.py`
   - Add URL to `.env.example`

### Agent-Tool Separation of Concerns

**Tools** (in `tools/`):
- Collect data from filesystem, code, etc.
- Process and structure data
- Return Pydantic models
- No LLM calls, no decisions

**Agents** (in `agents/`):
- Receive structured data from tools
- Analyze and interpret data
- Make decisions using LLM knowledge
- Generate user-friendly reports

**Example**: Dependency Checker
- **Tool**: Scans pyproject.toml, extracts imports via AST, reads venv metadata
- **Agent**: Determines if packages are unused, considers transitive dependencies, generates recommendations

### Important: Preventing Multiple Tool Calls

With `tool_choice="auto"`, LLM may call tools multiple times if it thinks more information is needed. Prevent this in prompts:

```
CRITICAL: Call <tool_name> ONLY ONCE at the beginning. Do NOT call it again.

Step 1: Call the tool ONCE
- The tool provides complete information
- You do NOT need to call it multiple times

Step 2: Analyze the results (DO NOT call the tool again)
- The tool returns ALL necessary information: ...
```

## Dependency Checker Implementation

### Hybrid Analysis Approach

The Dependency Checker uses a two-stage approach:

**Stage 1: Venv Metadata Analysis (Tool)**
- Searches project's virtual environment (`.venv`, `venv`, etc.)
- Reads `.dist-info/top_level.txt` files
- Directly maps packages to import names (e.g., `google-adk` → `{google, a2a}`)
- Packages with metadata are definitively classified as used/unused

**Stage 2: Agent Analysis (LLM)**
- Analyzes packages WITHOUT metadata
- Uses LLM knowledge of package-import mappings (e.g., `scikit-learn` → `sklearn`)
- Considers transitive dependencies
- Generates final report

### Why This Approach?

- **Efficient**: Most packages have metadata → fast, free classification
- **Accurate**: Venv metadata is ground truth
- **Extensible**: LLM handles edge cases without hardcoded mappings
- **Scalable**: Works for any project without maintaining mapping tables

### Tool Output Schema

```python
DependencyCheckResult:
    declared_dependencies: list[str]        # From pyproject.toml
    used_dependencies: list[str]            # Import statements found
    unused_dependencies: list[str]          # Confirmed unused (via metadata)
    packages_without_metadata: list[str]    # Needs agent analysis
```

## Common Development Patterns

### Adding Settings

1. Add field to `AppSettings` class in `common/settings.py`
2. Add to `.env.example`
3. Document in CLAUDE.md environment configuration section

### Type Hints for Third-Party Packages

If mypy complains about missing type information:

1. Create stubs in `typings/<package_name>/`
2. Add stub files (e.g., `__init__.pyi`)
3. Configure `mypy_path = "typings"` in `pyproject.toml`

### Google-ADK Function Tool Constraints

When creating tools for google-adk agents:

```python
# ❌ This will fail to parse
def my_tool(param: str | None = None) -> dict:
    ...

# ✅ Use Optional instead
from typing import Optional

def my_tool(param: Optional[str] = None) -> dict:  # noqa: UP045
    ...
```

Add `# noqa: UP045` to suppress ruff's suggestion to use `| None` syntax.
