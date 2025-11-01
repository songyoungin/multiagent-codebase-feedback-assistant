"""Agent system prompt definition (loaded from Langfuse)."""

from common.prompt_manager import prompt_manager

# Load prompts from Langfuse (cached for performance)
PROJECT_SCANNER_PROMPT = prompt_manager.get_prompt("project_scanner")
DEPENDENCY_CHECKER_PROMPT = prompt_manager.get_prompt("dependency_checker")
DOCUMENTATION_GENERATOR_PROMPT = prompt_manager.get_prompt("documentation_generator")
SRP_VIOLATION_DETECTOR_PROMPT = prompt_manager.get_prompt("srp_violation_detector")
NAMING_QUALITY_ANALYZER_PROMPT = prompt_manager.get_prompt("naming_quality_analyzer")
ORCHESTRATOR_PROMPT = prompt_manager.get_prompt("orchestrator")
