# Multiagent Codebase Feedback Assistant

AI-powered multi-agent system that scans your Python projects to identify code smells, architectural issues, unused dependencies, and documentation gaps using MCP.

## Features

- **Project Structure Analysis**: Scan directory structures and collect statistics
- **Dependency Checker**: Identify unused dependencies in Python projects
- **Documentation Coverage**: Find missing docstrings and documentation gaps
- **SRP Violation Detection**: Detect Single Responsibility Principle violations
- **Naming Quality Analysis**: Analyze code naming quality and conventions
- **Orchestrator**: Natural language queries to coordinate multiple analyses

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/multiagent-codebase-feedback-assistant.git
cd multiagent-codebase-feedback-assistant
```

2. Install dependencies using `uv`:
```bash
uv sync
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys (OpenAI or Gemini)
```

4. Start the analysis servers:
```bash
uv run codebase-analyzer server start
```

## Usage

### Analyzing Projects from Within This Repository

When you're inside the `multiagent-codebase-feedback-assistant` directory:

```bash
# Scan any project by providing its absolute path
uv run codebase-analyzer scan /path/to/your/project

# Check dependencies
uv run codebase-analyzer check-deps /path/to/your/project

# Analyze documentation
uv run codebase-analyzer check-docs /path/to/your/project

# Check for SRP violations
uv run codebase-analyzer check-srp /path/to/your/project

# Analyze naming quality
uv run codebase-analyzer check-naming /path/to/your/project

# Run all analyses
uv run codebase-analyzer analyze-all /path/to/your/project

# Natural language query
uv run codebase-analyzer ask "Analyze the entire project at /path/to/your/project"
```

### Analyzing Projects from Any Directory

To use the CLI from any directory without navigating to this repository:

#### Option 1: Install from GitHub (Easiest)

Install directly from the GitHub repository:

```bash
# Install with pip
pip install git+https://github.com/yourusername/multiagent-codebase-feedback-assistant.git

# Or install with uv
uv pip install git+https://github.com/yourusername/multiagent-codebase-feedback-assistant.git

# Install specific branch
pip install git+https://github.com/yourusername/multiagent-codebase-feedback-assistant.git@branch-name

# Install specific commit
pip install git+https://github.com/yourusername/multiagent-codebase-feedback-assistant.git@commit-hash

# Now you can use it from anywhere
cd ~/my-python-project
codebase-analyzer scan $(pwd)
```

#### Option 2: Install from Local Directory

Install the package to make the CLI available system-wide:

```bash
# Install with uv (recommended)
cd /path/to/multiagent-codebase-feedback-assistant
uv pip install .

# Or install with pip
pip install .

# Install in editable mode (for development)
uv pip install -e .
pip install -e .

# Now you can use it from anywhere
cd ~/my-python-project
codebase-analyzer scan $(pwd)
```

**Note**: After installation, the `codebase-analyzer` command will be available in your Python environment. Make sure Docker is running before using the CLI, as it needs to start the agent containers.

#### Option 3: Using Full Path (Without Installation)

```bash
# From anywhere on your system
/path/to/multiagent-codebase-feedback-assistant/.venv/bin/codebase-analyzer scan $(pwd)

# Example: Analyze current directory
cd ~/my-python-project
/path/to/multiagent-codebase-feedback-assistant/.venv/bin/codebase-analyzer scan $(pwd)
```

#### Option 4: Add to PATH

Add the CLI to your PATH for easier access:

```bash
# Add to ~/.bashrc, ~/.zshrc, or equivalent
export PATH="/path/to/multiagent-codebase-feedback-assistant/.venv/bin:$PATH"

# Reload shell configuration
source ~/.bashrc  # or source ~/.zshrc

# Now you can use it from anywhere
cd ~/my-python-project
codebase-analyzer scan $(pwd)
```

#### Option 5: Create an Alias

```bash
# Add to ~/.bashrc, ~/.zshrc, or equivalent
alias codebase-analyzer="/path/to/multiagent-codebase-feedback-assistant/.venv/bin/codebase-analyzer"

# Reload shell configuration
source ~/.bashrc  # or source ~/.zshrc

# Use from anywhere
cd ~/my-python-project
codebase-analyzer scan $(pwd)
```

### Custom Volume Mount for Docker

By default, the Docker containers mount `/Users` (macOS) to access your project files. For other operating systems:

```bash
# Windows
codebase-analyzer --volume-mount "C:/Users" scan "C:/Users/yourname/project"

# Linux (mount /home)
codebase-analyzer --volume-mount "/home" scan /home/yourname/project

# Linux (mount entire filesystem)
codebase-analyzer --volume-mount "/" scan /any/path/to/project
```

You can also set the default volume mount in `.env`:

```bash
# For Windows
VOLUME_MOUNT=C:/Users

# For Linux
VOLUME_MOUNT=/home
```

### One-Shot Mode

Start servers, run analysis, and stop servers in one command:

```bash
codebase-analyzer scan /path/to/project --oneshot
```

### Server Management

```bash
# Start all servers
codebase-analyzer server start

# Check server status
codebase-analyzer server status

# Stop servers
codebase-analyzer server stop

# Restart servers
codebase-analyzer server restart
```

## Requirements

- Python 3.13+
- Docker and Docker Compose
- OpenAI API key or Google Gemini API key
- `uv` package manager

## Documentation

For detailed documentation, see [CLAUDE.md](CLAUDE.md).

## Architecture

This project uses a multi-agent architecture where each agent specializes in a specific analysis domain:
- **Project Scanner**: Directory structure analysis
- **Dependency Checker**: Unused dependency detection
- **Documentation Generator**: Docstring coverage analysis
- **SRP Violation Detector**: Single Responsibility Principle analysis
- **Naming Quality Analyzer**: Code naming quality assessment
- **Orchestrator**: Coordinates multiple agents for comprehensive analysis

All agents communicate via the A2A (Agent-to-Agent) protocol over HTTP.
