"""
VerityOS - Verification Agent
Part of the Agent Runtime Layer (Member 1)

Responsibility:
    Validates atomic claims against all gathered evidence.
    STRICT RULE: Never invents or introduces new claims. Operates strictly
    on the input claims provided by the Data Agent.
    Identifies supporting sources, detecting direct contradictions, and assessing
    internal consistency prior to submission to the Trust Engine.
"""

import json
from typing import Any, Dict, List
from .mocks import make_envelope


def evaluate_single_claim(claim: Dict[str, Any], evidence_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluates one specific claim against the full evidence body without altering the claim.
    """
    claim_id = claim.get("claim_id", "claim-unknown")
    statement = claim.get("statement", "")
    claim_src = claim.get("source_id", "")
    claim_rep = float(claim.get("source_reputation_hint", 0.50))

    supporting_sources = []
    contradicting_sources = []

    # Simple heuristic sentiment & negation cross-examination
    statement_lower = statement.lower()
    claim_has_negation = any(neg in statement_lower for neg in ["insufficient", "lack", "not", "cannot", "unable", "no "])

    for ev in evidence_list:
        src_id = ev.get("source_id", "")
        snippet_lower = ev.get("snippet", "").lower()

        # Check if the evidence discusses the same core subject
        overlap_keywords = [w for w in ["quantum", "rsa", "light", "vacuum", "speed", "metre", "encryption"] if w in statement_lower and w in snippet_lower]
        if not overlap_keywords:
            continue

        ev_has_negation = any(neg in snippet_lower for neg in ["insufficient", "lack", "not", "cannot", "unable", "no "])

        if claim_has_negation == ev_has_negation:
            supporting_sources.append(src_id)
        else:
            contradicting_sources.append(src_id)

    # Ensure source itself is credited as supporting
    if claim_src and claim_src not in supporting_sources and claim_src not in contradicting_sources:
        supporting_sources.append(claim_src)

    # Determine verdict and consistency score
    if contradicting_sources:
        verdict = "SUPPORTED" if claim_rep >= 0.70 and len(supporting_sources) >= len(contradicting_sources) else "CONTRADICTED"
        consistency_score = round(max(0.15, claim_rep - 0.50 * len(contradicting_sources)), 2)
    elif supporting_sources:
        verdict = "SUPPORTED"
        consistency_score = round(min(0.99, claim_rep + 0.05 * (len(supporting_sources) - 1)), 2)
    else:
        verdict = "INSUFFICIENT_EVIDENCE"
        consistency_score = 0.50

    return {
        "claim_id": claim_id,
        "statement": statement,
        "verdict": verdict,
        "supporting_sources": supporting_sources,
        "contradicting_sources": contradicting_sources,
        "internal_consistency_score": consistency_score
    }


def run_verification(input_packet: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for Verification Agent.

    Input Envelope:
        data:
            - claims: List[Dict] from Data Agent (Strictly evaluated, none invented)
            - evidence_list: List[Dict]

    Output Envelope:
        data:
            - verifications: List[Dict[claim_id, statement, verdict, supporting_sources,
                                       contradicting_sources, internal_consistency_score]]
    """
    task_id = input_packet.get("task_id")
    status = input_packet.get("status", "SUCCESS")
    data_in = input_packet.get("data", {})
    claims = data_in.get("claims", [])
    evidence_list = data_in.get("evidence_list", [])

    if status == "EMPTY" or not claims:
        return make_envelope(
            task_id=task_id,
            status="EMPTY",
            agent="verification_agent",
            data={"verifications": []},
            error=None
        )

    # Strictly evaluate only provided claims — no inventions
    verifications = []
    for claim in claims:
        evaluated = evaluate_single_claim(claim, evidence_list)
        verifications.append(evaluated)

    return make_envelope(
        task_id=task_id,
        status="SUCCESS",
        agent="verification_agent",
        data={
            "verifications": verifications
        },
        error=None
    )


# ---------------------------------------------------------------------------
# Standalone Test Execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n--- Testing agents/verification_agent.py independently ---")

    mock_input = make_envelope(
        task_id="test-verify-01",
        status="SUCCESS",
        agent="data_agent",
        data={
            "claims": [
                {
                    "claim_id": "claim-101",
                    "statement": "Current quantum systems have insufficient fault-tolerant qubits to factor RSA-2048 keys.",
                    "source_id": "src-1",
                    "source_reputation_hint": 0.95
                },
                {
                    "claim_id": "claim-102",
                    "statement": "A private quantum processor factored RSA-2048.",
                    "source_id": "src-2",
                    "source_reputation_hint": 0.20
                }
            ],
            "evidence_list": [
                {
                    "source_id": "src-1",
                    "snippet": "Current quantum systems have insufficient fault-tolerant qubits to factor RSA-2048 keys."
                },
                {
                    "source_id": "src-2",
                    "snippet": "Anonymous researchers claim a private quantum processor factored RSA-2048 yesterday."
                }
            ]
        }
    )

    result = run_verification(mock_input)
    print("Verification Agent Output Envelope:")
    print(json.dumps(result, indent=2))
