# Multiagent Codebase Feedback Assistant

AI-powered multi-agent system that scans your Python projects to identify code smells, architectural issues, unused dependencies, and documentation gaps using MCP.

## Features

- **Project Structure Analysis**: Scan directory structures and collect statistics
- **Dependency Checker**: Identify unused dependencies in Python projects
- **Documentation Coverage**: Find missing docstrings and documentation gaps
- **SRP Violation Detection**: Detect Single Responsibility Principle violations
- **Naming Quality Analysis**: Analyze code naming quality and conventions
- **Orchestrator**: Natural language queries to coordinate multiple analyses

## Prerequisites

Before installing, make sure you have:

- **Docker Desktop**: Installed and running
- **API Key**: OpenAI API key or Google Gemini API key
- **Python**: Python 3.13+ installed
- **Package Manager**: `uv` package manager installed

## Installation

Install directly from GitHub:

```bash
# Install with pip
pip install git+https://github.com/songyoungin/multiagent-codebase-feedback-assistant.git

# Or install with uv
uv pip install git+https://github.com/songyoungin/multiagent-codebase-feedback-assistant.git
```

## Setup

1. Set up environment variables:

```bash
# Create .env file and add your API key
OPENAI_API_KEY=your_key_here
# or
GEMINI_API_KEY=your_key_here
```

2. Start the agent servers:

```bash
codebase-analyzer server start
```

## Usage

Use natural language queries to analyze your codebase:

```bash
codebase-analyzer ask "Analyze the entire project at /path/to/your/project"
```
