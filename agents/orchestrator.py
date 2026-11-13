"""
VerityOS - Orchestrator
Part of the Agent Runtime Layer (Member 1)

Responsibility:
    End-to-end pipeline coordinator.
    Chains Research Agent -> Data Agent -> Verification Agent -> Trust Engine.
    Enforces the Trust Gate to decide whether to APPROVE, QUARANTINE, or report
    INSUFFICIENT_DATA for a given task.
    Accepts any custom trust_engine_callable to seamlessly integrate Member 2's engine.
"""

import json
from typing import Any, Callable, Dict, Optional
import uuid

from .mocks import make_envelope, TEST_CASE_VALID, TEST_CASE_CONTRADICTORY, TEST_CASE_EMPTY
from .research_agent import run_research
from .data_agent import run_data_processing
from .verification_agent import run_verification
from .trust_engine_mock import evaluate_trust as default_mock_trust_engine


def synthesize_answer(
    query: str,
    decision: str,
    verifications: list,
    trust_score: float,
    trust_grade: str
) -> str:
    """
    Synthesizes the final user-facing answer based on verified claims and trust gate outcome.
    """
    if decision == "INSUFFICIENT_DATA":
        return f"No verifiable sources or evidence could be retrieved for the query: '{query}'."

    supported_statements = [
        v["statement"] for v in verifications if v.get("verdict") == "SUPPORTED"
    ]
    contradicted_statements = [
        v["statement"] for v in verifications if v.get("verdict") == "CONTRADICTED"
    ]

    if decision == "APPROVED":
        core = " ".join(supported_statements)
        return (
            f"[VERIFIED TRUST PASS - Score: {trust_score:.2f} | Grade: {trust_grade}]\n"
            f"Consensus Answer: {core}"
        )
    else:
        # QUARANTINED
        warning = (
            f"[TRUST ALERT - QUARANTINED - Score: {trust_score:.2f} | Grade: {trust_grade}]\n"
            f"The system detected low trust or contradictory information for the query: '{query}'.\n"
        )
        if supported_statements:
            warning += f"- Corroborated Evidence: {' '.join(supported_statements)}\n"
        if contradicted_statements:
            warning += f"- Flagged / Contradictory Claims: {' '.join(contradicted_statements)}\n"
        warning += "Action: Output quarantined. Downstream systems should not execute unverified claims."
        return warning


def execute_pipeline(
    query: str,
    test_case_key: Optional[str] = None,
    use_mock: bool = True,
    trust_engine_callable: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    trust_threshold: float = 0.70
) -> Dict[str, Any]:
    """
    Executes the complete VerityOS agent orchestration pipeline.

    Parameters:
        query: User or system task prompt.
        test_case_key: Optional key to pick a deterministic mock fixture ('TEST_CASE_VALID', etc.).
        use_mock: Whether to use mock fixtures for external data and fallback.
        trust_engine_callable: Callable for Member 2's Trust Engine. Defaults to evaluate_trust.
        trust_threshold: Minimum overall score (0.0 - 1.0) required to pass the Trust Gate.

    Returns:
        Standard envelope with final decision, trust score, and synthesized answer.
    """
    task_id = f"task-{uuid.uuid4().hex[:8]}"
    trust_evaluator = trust_engine_callable or default_mock_trust_engine

    # Step 1: Research Agent
    research_req = make_envelope(
        task_id=task_id,
        agent="orchestrator",
        data={
            "query": query,
            "test_case_key": test_case_key,
            "use_mock": use_mock
        }
    )
    research_res = run_research(research_req)

    if research_res.get("status") == "EMPTY" or not research_res.get("data", {}).get("evidence_list"):
        final_answer = synthesize_answer(query, "INSUFFICIENT_DATA", [], 0.0, "UNTRUSTED")
        return make_envelope(
            task_id=task_id,
            status="SUCCESS",
            agent="orchestrator",
            data={
                "query": query,
                "decision": "INSUFFICIENT_DATA",
                "final_trust_score": 0.0,
                "is_trust_score_mock": True,
                "synthesized_answer": final_answer,
                "audit_trail": {
                    "sources_found": 0,
                    "claims_extracted": 0,
                    "supported_claims": 0,
                    "contradicted_claims": 0
                }
            }
        )

    evidence_list = research_res["data"]["evidence_list"]

    # Step 2: Data Agent
    data_res = run_data_processing(research_res)
    claims = data_res.get("data", {}).get("claims", [])

    if not claims:
        final_answer = synthesize_answer(query, "INSUFFICIENT_DATA", [], 0.0, "UNTRUSTED")
        return make_envelope(
            task_id=task_id,
            status="SUCCESS",
            agent="orchestrator",
            data={
                "query": query,
                "decision": "INSUFFICIENT_DATA",
                "final_trust_score": 0.0,
                "is_trust_score_mock": True,
                "synthesized_answer": final_answer,
                "audit_trail": {
                    "sources_found": len(evidence_list),
                    "claims_extracted": 0,
                    "supported_claims": 0,
                    "contradicted_claims": 0
                }
            }
        )

    # Step 3: Verification Agent (Strict zero-invention evaluation)
    verify_res = run_verification(data_res)
    verifications = verify_res.get("data", {}).get("verifications", [])

    # Step 4: Trust Engine (External or Mock)
    trust_res = trust_evaluator(verify_res)
    trust_data = trust_res.get("data", {})
    overall_trust_score = float(trust_data.get("overall_trust_score", 0.0))
    trust_grade = trust_data.get("trust_grade", "LOW")
    policy_decision = trust_data.get("policy_decision", "REJECT")
    is_mock = bool(trust_data.get("is_mock", True))

    # Step 5: Trust Gate Evaluation
    if overall_trust_score >= trust_threshold and policy_decision == "PASS":
        decision = "APPROVED"
    else:
        decision = "QUARANTINED"

    synthesized = synthesize_answer(
        query=query,
        decision=decision,
        verifications=verifications,
        trust_score=overall_trust_score,
        trust_grade=trust_grade
    )

    supported_count = sum(1 for v in verifications if v.get("verdict") == "SUPPORTED")
    contradicted_count = sum(1 for v in verifications if v.get("verdict") == "CONTRADICTED")

    return make_envelope(
        task_id=task_id,
        status="SUCCESS",
        agent="orchestrator",
        data={
            "query": query,
            "decision": decision,
            "final_trust_score": overall_trust_score,
            "trust_grade": trust_grade,
            "policy_decision": policy_decision,
            "is_trust_score_mock": is_mock,
            "synthesized_answer": synthesized,
            "audit_trail": {
                "sources_found": len(evidence_list),
                "claims_extracted": len(claims),
                "claims_verified": len(verifications),
                "supported_claims": supported_count,
                "contradicted_claims": contradicted_count
            }
        },
        error=None
    )


# ---------------------------------------------------------------------------
# Standalone Test Execution Covering All 3 Test Cases
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" VERITYOS ORCHESTRATOR - 3 TEST CASE DEMO")
    print("=" * 70)

    test_scenarios = [
        ("CASE 1: VALID CONSENSUS", "TEST_CASE_VALID", "What is the speed of light in a vacuum?"),
        ("CASE 2: CONTRADICTORY RUMOR", "TEST_CASE_CONTRADICTORY", "Is quantum computing breaking RSA-2048 encryption today?"),
        ("CASE 3: EMPTY EVIDENCE", "TEST_CASE_EMPTY", "query_with_zero_results_12345"),
    ]

    for label, case_key, query_text in test_scenarios:
        print(f"\n>>> Running {label} ...")
        res = execute_pipeline(query=query_text, test_case_key=case_key, use_mock=True)
        data = res["data"]
        print(f"Decision:         {data['decision']}")
        print(f"Trust Score:      {data['final_trust_score']} (Mock: {data['is_trust_score_mock']})")
        print(f"Audit Trail:      {data['audit_trail']}")
        print(f"Answer:\n{data['synthesized_answer']}")
        print("-" * 70)
