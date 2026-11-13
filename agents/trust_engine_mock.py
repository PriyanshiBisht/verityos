"""
=============================================================================
VerityOS - Trust Engine Mock Adapter
=============================================================================
NOTICE: THIS IS A MOCK IMPLEMENTATION DESIGNED FOR INDEPENDENT TESTING.
Member 2 will supply the real Trust Engine.

To replace this mock with Member 2's implementation:
    1. Import Member 2's Trust Engine module / class.
    2. Route `evaluate_trust(verification_packet)` to their engine's scoring function.
    3. Ensure the return structure adheres to the envelope format specified below.
=============================================================================
"""

import json
from typing import Any, Dict
from .mocks import make_envelope, get_mock_case_by_key_or_query


def evaluate_trust(verification_packet: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mock evaluation representing Member 2's Trust Engine.

    Input Envelope:
        verification_packet["data"]["verifications"]: List of claim verification dicts.

    Output Envelope:
        data:
            - is_mock: True (Explicit flag)
            - mock_engine_version: str
            - mock_notice: str
            - overall_trust_score: float (0.0 to 1.0)
            - trust_grade: "HIGH" | "MEDIUM" | "LOW" | "UNTRUSTED"
            - policy_decision: "PASS" | "REVIEW" | "REJECT"
            - claim_evaluations: Dict[claim_id, dict]
    """
    task_id = verification_packet.get("task_id", "unknown-task")
    status = verification_packet.get("status", "SUCCESS")

    # Handle empty or error states from upstream
    if status == "EMPTY":
        return make_envelope(
            task_id=task_id,
            status="EMPTY",
            agent="trust_engine",
            data={
                "is_mock": True,
                "mock_engine_version": "0.1.0-hackathon-mock",
                "mock_notice": "MOCK ACTIVE: Replace with Member 2 Trust Engine",
                "overall_trust_score": 0.0,
                "trust_grade": "UNTRUSTED",
                "policy_decision": "REJECT",
                "claim_evaluations": {}
            },
            error="No claims available to evaluate trust."
        )

    data_payload = verification_packet.get("data", {})
    verifications = data_payload.get("verifications", [])

    if not verifications:
        return make_envelope(
            task_id=task_id,
            status="EMPTY",
            agent="trust_engine",
            data={
                "is_mock": True,
                "mock_engine_version": "0.1.0-hackathon-mock",
                "mock_notice": "MOCK ACTIVE: Replace with Member 2 Trust Engine",
                "overall_trust_score": 0.0,
                "trust_grade": "UNTRUSTED",
                "policy_decision": "REJECT",
                "claim_evaluations": {}
            },
            error="Verifications list is empty."
        )

    # Compute mock trust scores
    claim_evaluations = {}
    total_score = 0.0
    has_contradiction = False

    for v in verifications:
        cid = v.get("claim_id", "unknown")
        verdict = v.get("verdict", "INSUFFICIENT_EVIDENCE")
        consistency = float(v.get("internal_consistency_score", 0.5))

        if verdict == "SUPPORTED":
            score = round(min(1.0, consistency * 1.05), 2)
            level = "HIGH" if score >= 0.75 else "MEDIUM"
        elif verdict == "CONTRADICTED":
            has_contradiction = True
            score = round(max(0.05, consistency * 0.8), 2)
            level = "LOW"
        else:
            score = 0.50
            level = "MEDIUM"

        claim_evaluations[cid] = {
            "score": score,
            "trust_level": level,
            "verdict": verdict
        }
        total_score += score

    # Calculate overall trust score
    avg_score = round(total_score / len(verifications), 2)

    # Penalize if direct contradictions exist
    if has_contradiction and avg_score > 0.40:
        overall_score = round(avg_score * 0.6, 2)
    else:
        overall_score = avg_score

    # Assign trust grade and policy decision
    if overall_score >= 0.75:
        trust_grade = "HIGH"
        policy_decision = "PASS"
    elif overall_score >= 0.50:
        trust_grade = "MEDIUM"
        policy_decision = "REVIEW"
    else:
        trust_grade = "LOW"
        policy_decision = "REJECT"

    output_data = {
        "is_mock": True,
        "mock_engine_version": "0.1.0-hackathon-mock",
        "mock_notice": "MOCK ACTIVE: Replace with Member 2 Trust Engine",
        "overall_trust_score": overall_score,
        "trust_grade": trust_grade,
        "policy_decision": policy_decision,
        "claim_evaluations": claim_evaluations
    }

    return make_envelope(
        task_id=task_id,
        status="SUCCESS",
        agent="trust_engine",
        data=output_data,
        error=None
    )


# ---------------------------------------------------------------------------
# Standalone Test Execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n--- Testing agents/trust_engine_mock.py independently ---")
    mock_input = make_envelope(
        task_id="standalone-test-te",
        status="SUCCESS",
        agent="verification_agent",
        data={
            "verifications": [
                {
                    "claim_id": "claim-101",
                    "statement": "Quantum computers lack qubits to factor RSA-2048.",
                    "verdict": "SUPPORTED",
                    "internal_consistency_score": 0.90
                },
                {
                    "claim_id": "claim-102",
                    "statement": "A private quantum processor factored RSA-2048.",
                    "verdict": "CONTRADICTED",
                    "internal_consistency_score": 0.20
                }
            ]
        }
    )

    result = evaluate_trust(mock_input)
    print("Trust Engine Mock Output Envelope:")
    print(json.dumps(result, indent=2))
