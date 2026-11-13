"""
VerityOS - Agents & Orchestration Module
Member 1: AI Agents and Orchestration Layer

Exposes the core functions and fixtures of the VerityOS agent layer.
Supports clean lazy exports to avoid runpy RuntimeWarnings when submodules
are executed directly via `python -m agents.<module>`.
"""

from typing import Any

__all__ = [
    "make_envelope",
    "MOCK_TEST_CASES",
    "TEST_CASE_VALID",
    "TEST_CASE_CONTRADICTORY",
    "TEST_CASE_EMPTY",
    "get_mock_case_by_key_or_query",
    "run_research",
    "fetch_sources",
    "run_data_processing",
    "extract_atomic_claims",
    "run_verification",
    "evaluate_single_claim",
    "evaluate_trust",
    "execute_pipeline",
    "synthesize_answer",
]


def __getattr__(name: str) -> Any:
    if name in (
        "make_envelope",
        "MOCK_TEST_CASES",
        "TEST_CASE_VALID",
        "TEST_CASE_CONTRADICTORY",
        "TEST_CASE_EMPTY",
        "get_mock_case_by_key_or_query",
    ):
        from . import mocks
        return getattr(mocks, name)
    elif name in ("run_research", "fetch_sources"):
        from . import research_agent
        return getattr(research_agent, name)
    elif name in ("run_data_processing", "extract_atomic_claims"):
        from . import data_agent
        return getattr(data_agent, name)
    elif name in ("run_verification", "evaluate_single_claim"):
        from . import verification_agent
        return getattr(verification_agent, name)
    elif name == "evaluate_trust":
        from . import trust_engine_mock
        return getattr(trust_engine_mock, name)
    elif name in ("execute_pipeline", "synthesize_answer"):
        from . import orchestrator
        return getattr(orchestrator, name)
    raise AttributeError(f"module 'agents' has no attribute '{name}'")
