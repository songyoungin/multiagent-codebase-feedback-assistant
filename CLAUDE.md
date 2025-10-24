# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

이 프로젝트는 Python 코드베이스를 분석하여 코드 스멜, 아키텍처 이슈, 미사용 의존성, 문서 누락 등을 식별하는 AI 기반 멀티에이전트 시스템입니다. MCP(Model Context Protocol)를 활용하여 구현됩니다.

## Development Setup

### Package Management
이 프로젝트는 `uv`를 패키지 관리자로 사용합니다.

```bash
# 의존성 설치
uv sync

# 개발 환경 활성화
source .venv/bin/activate

# 의존성 추가
uv add <package-name>

# 개발 의존성 추가
uv add --dev <package-name>
```

### Running the Application

```bash
# 메인 애플리케이션 실행
uv run python main.py
```

## Core Architecture

### Multi-Agent System
이 프로젝트는 여러 에이전트가 협력하여 코드베이스를 분석하는 구조를 가집니다:
- 각 에이전트는 특정 분석 영역(코드 스멜, 아키텍처, 의존성, 문서)을 담당
- MCP를 통해 에이전트 간 통신 및 조율이 이루어짐

### Key Dependencies
- `google-adk[a2a]`: Google AI Development Kit with Agent-to-Agent 기능 사용
- Python 3.13 이상 필수

## Development Guidelines

### Code Quality
- 모든 공개 인터페이스에 타입 힌트를 명시적으로 작성
- 가독성을 성능보다 우선시
- 단일 책임 원칙(Single Responsibility Principle) 준수

### Testing
- 테스트는 테스트 클래스가 아닌 테스트 메소드 형식으로 작성
- 모킹은 context manager 대신 decorator 사용
- 테스트 메소드에는 docstring과 주석 포함 (모킹 조건 및 검증 내용 명시)

### Virtual Environment
가상 환경은 프로젝트 루트의 `.venv` 디렉토리에 위치합니다. 코드 실행 명령 제공 시 `.venv` 활성화를 포함하세요.
