"""
VerityOS - Data Agent
Part of the Agent Runtime Layer (Member 1)

Responsibility:
    Ingests raw evidence snippets from Research Agent.
    Sanitizes content, atomizes sentences into verifiable claim statements,
    and maintains strict source provenance anchors (source_id).
    Forwards both claims and evidence to downstream consumers.
"""

import json
from typing import Any, Dict, List
from .mocks import make_envelope, get_mock_case_by_key_or_query


def extract_atomic_claims(evidence_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extracts atomic claims from evidence snippets, anchoring each claim to its exact source_id.
    """
    claims = []
    claim_counter = 100

    for item in evidence_list:
        src_id = item.get("source_id", "src-unknown")
        rep_hint = item.get("source_reputation_hint", 0.50)
        snippet = item.get("snippet", "").strip()

        if not snippet:
            continue

        # Split snippet into sentences if composite, or take as an atomic statement
        sentences = [s.strip() for s in snippet.split(".") if len(s.strip()) > 10]
        if not sentences:
            sentences = [snippet]

        for sentence in sentences:
            claim_counter += 1
            claims.append({
                "claim_id": f"claim-{claim_counter}",
                "statement": sentence if sentence.endswith(".") else f"{sentence}.",
                "source_id": src_id,
                "source_reputation_hint": rep_hint
            })

    return claims


def run_data_processing(input_packet: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for Data Agent.

    Input Envelope:
        data:
            - evidence_list: List[Dict] from Research Agent

    Output Envelope:
        data:
            - claims: List[Dict[claim_id, statement, source_id, source_reputation_hint]]
            - evidence_list: Forwarded evidence list for downstream context
    """
    task_id = input_packet.get("task_id")
    status = input_packet.get("status", "SUCCESS")
    data_in = input_packet.get("data", {})
    evidence_list = data_in.get("evidence_list", [])

    if status == "EMPTY" or not evidence_list:
        return make_envelope(
            task_id=task_id,
            status="EMPTY",
            agent="data_agent",
            data={
                "claims": [],
                "evidence_list": []
            },
            error=None
        )

    claims = extract_atomic_claims(evidence_list)

    if not claims:
        return make_envelope(
            task_id=task_id,
            status="EMPTY",
            agent="data_agent",
            data={
                "claims": [],
                "evidence_list": evidence_list
            },
            error="No verifiable claims could be extracted from evidence."
        )

    return make_envelope(
        task_id=task_id,
        status="SUCCESS",
        agent="data_agent",
        data={
            "claims": claims,
            "evidence_list": evidence_list
        },
        error=None
    )


# ---------------------------------------------------------------------------
# Standalone Test Execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n--- Testing agents/data_agent.py independently ---")
    
    mock_input = make_envelope(
        task_id="test-data-01",
        status="SUCCESS",
        agent="research_agent",
        data={
            "evidence_list": [
                {
                    "source_id": "src-1",
                    "title": "NIST Report",
                    "snippet": "Current quantum systems have insufficient qubits to factor RSA-2048 keys.",
                    "source_reputation_hint": 0.95
                },
                {
                    "source_id": "src-2",
                    "title": "Rumor Forum",
                    "snippet": "Anonymous researchers claim a private quantum processor factored RSA-2048 yesterday.",
                    "source_reputation_hint": 0.20
                }
            ]
        }
    )

    result = run_data_processing(mock_input)
    print("Data Agent Output Envelope:")
    print(json.dumps(result, indent=2))
