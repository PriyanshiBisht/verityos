"""
VerityOS - Research Agent
Part of the Agent Runtime Layer (Member 1)

Responsibility:
    Retrieves source documents and evidence snippets matching the user query.
    Supports mock fixture execution (for offline testing) and extensible API hooks.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Enable both direct execution (`python agents/research_agent.py`) and module execution (`python -m agents.research_agent`)
if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from agents.mocks import make_envelope, get_mock_case_by_key_or_query
else:
    from .mocks import make_envelope, get_mock_case_by_key_or_query


def fetch_sources(
    query: str,
    use_mock: bool = True,
    test_case_key: str = None
) -> List[Dict[str, Any]]:
    """
    Retrieves evidence sources.
    In MVP mode (use_mock=True), sources are fetched deterministically from test fixtures.
    """
    if use_mock:
        case = get_mock_case_by_key_or_query(key=test_case_key, query=query)
        # Deep copy evidence list to prevent accidental state mutation
        return [dict(item) for item in case.get("evidence_list", [])]

    # Placeholder for live web/API retrieval if expanded during hackathon
    return []


def run_research(input_packet: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for Research Agent.

    Input Envelope:
        data:
            - query: str (Required)
            - use_mock: bool (Default True)
            - test_case_key: str (Optional)

    Output Envelope:
        data:
            - query: str
            - evidence_list: List[Dict[source_id, title, url, snippet, source_reputation_hint]]
    """
    task_id = input_packet.get("task_id")
    data_in = input_packet.get("data", {})
    query = data_in.get("query", "").strip()
    use_mock = data_in.get("use_mock", True)
    test_case_key = data_in.get("test_case_key")

    if not query:
        return make_envelope(
            task_id=task_id,
            status="EMPTY",
            agent="research_agent",
            data={"query": "", "evidence_list": []},
            error="Query string is empty or missing."
        )

    evidence_list = fetch_sources(query=query, use_mock=use_mock, test_case_key=test_case_key)

    if not evidence_list:
        return make_envelope(
            task_id=task_id,
            status="EMPTY",
            agent="research_agent",
            data={"query": query, "evidence_list": []},
            error=None
        )

    return make_envelope(
        task_id=task_id,
        status="SUCCESS",
        agent="research_agent",
        data={
            "query": query,
            "evidence_list": evidence_list
        },
        error=None
    )


# ---------------------------------------------------------------------------
# Standalone Test Execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n--- Testing agents/research_agent.py independently ---")
    
    # Test valid query
    req = make_envelope(
        task_id="test-research-01",
        agent="test_runner",
        data={"query": "Is quantum computing breaking RSA-2048 encryption today?", "use_mock": True}
    )
    res = run_research(req)
    print("Research Agent Output Envelope:")
    print(json.dumps(res, indent=2))
