"""
VerityOS - Mock Fixtures and Shared Test Cases
Part of the Agent Runtime Layer (Member 1)

This module defines standard envelope helpers and 3 deterministic test cases:
1. TEST_CASE_VALID: Clear factual consensus; expected to pass the trust gate.
2. TEST_CASE_CONTRADICTORY: Conflicting evidence; expected to be quarantined.
3. TEST_CASE_EMPTY: Zero retrieved evidence; handled gracefully without crashing.
"""

from typing import Any, Dict, Optional
import uuid


def make_envelope(
    task_id: Optional[str] = None,
    status: str = "SUCCESS",
    agent: str = "system",
    data: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> Dict[str, Any]:
    """
    Constructs a standardized JSON-compatible envelope for inter-agent messaging.
    """
    return {
        "task_id": task_id or f"task-{uuid.uuid4().hex[:8]}",
        "status": status,
        "agent": agent,
        "data": data if data is not None else {},
        "error": error
    }


# ---------------------------------------------------------------------------
# Test Case 1: Valid Consensus (High Trust -> APPROVED)
# ---------------------------------------------------------------------------
TEST_CASE_VALID = {
    "key": "TEST_CASE_VALID",
    "query": "What is the speed of light in a vacuum?",
    "description": "Factual query with agreement across high-credibility scientific bodies.",
    "evidence_list": [
        {
            "source_id": "src-1",
            "title": "NIST Reference on Physical Constants",
            "url": "https://physics.nist.gov/constants/c",
            "snippet": "The speed of light in vacuum, c, is defined as exactly 299,792,458 meters per second.",
            "source_reputation_hint": 0.99
        },
        {
            "source_id": "src-2",
            "title": "BIPM SI Units Brochure",
            "url": "https://www.bipm.org/en/measurement-units",
            "snippet": "In the International System of Units, the metre is defined by taking the fixed numerical value of the speed of light in vacuum c to be 299,792,458.",
            "source_reputation_hint": 0.98
        }
    ],
    "claims": [
        {
            "claim_id": "claim-001",
            "statement": "The speed of light in vacuum is defined as exactly 299,792,458 meters per second.",
            "source_id": "src-1",
            "source_reputation_hint": 0.99
        },
        {
            "claim_id": "claim-002",
            "statement": "The SI metre is standardized using the fixed speed of light value 299,792,458 m/s.",
            "source_id": "src-2",
            "source_reputation_hint": 0.98
        }
    ],
    "mock_trust_evaluation": {
        "overall_trust_score": 0.98,
        "trust_grade": "HIGH",
        "policy_decision": "PASS",
        "claim_scores": {
            "claim-001": 0.99,
            "claim-002": 0.97
        }
    }
}


# ---------------------------------------------------------------------------
# Test Case 2: Contradictory Rumor (Low Trust -> QUARANTINED)
# ---------------------------------------------------------------------------
TEST_CASE_CONTRADICTORY = {
    "key": "TEST_CASE_CONTRADICTORY",
    "query": "Is quantum computing breaking RSA-2048 encryption today?",
    "description": "Conflicting claims between official cryptographic bodies and anonymous forums.",
    "evidence_list": [
        {
            "source_id": "src-1",
            "title": "NIST Post-Quantum Cryptography Status",
            "url": "https://csrc.nist.gov/publications/pqc-status",
            "snippet": "Current quantum systems have insufficient fault-tolerant physical and logical qubits to factor RSA-2048 keys.",
            "source_reputation_hint": 0.95
        },
        {
            "source_id": "src-2",
            "title": "Tech Rumor Forum",
            "url": "https://unverified-blog.io/rsa-broken-yesterday",
            "snippet": "Anonymous researchers claim a private quantum processor factored RSA-2048 yesterday.",
            "source_reputation_hint": 0.20
        }
    ],
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
    "mock_trust_evaluation": {
        "overall_trust_score": 0.35,
        "trust_grade": "LOW",
        "policy_decision": "REJECT",
        "claim_scores": {
            "claim-101": 0.92,
            "claim-102": 0.18
        }
    }
}


# ---------------------------------------------------------------------------
# Test Case 3: Empty / No Evidence (Zero Evidence -> INSUFFICIENT_DATA)
# ---------------------------------------------------------------------------
TEST_CASE_EMPTY = {
    "key": "TEST_CASE_EMPTY",
    "query": "query_with_zero_results_12345",
    "description": "Query returns no matching sources; verifies safe empty-state handling.",
    "evidence_list": [],
    "claims": [],
    "mock_trust_evaluation": {
        "overall_trust_score": 0.0,
        "trust_grade": "UNTRUSTED",
        "policy_decision": "REJECT",
        "claim_scores": {}
    }
}


# Lookup map
MOCK_TEST_CASES = {
    "TEST_CASE_VALID": TEST_CASE_VALID,
    "TEST_CASE_CONTRADICTORY": TEST_CASE_CONTRADICTORY,
    "TEST_CASE_EMPTY": TEST_CASE_EMPTY,
}


def get_mock_case_by_key_or_query(key: Optional[str] = None, query: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieves a mock test case either by exact case key or by query keyword matching.
    Defaults to TEST_CASE_CONTRADICTORY if nothing matches.
    """
    if key and key in MOCK_TEST_CASES:
        return MOCK_TEST_CASES[key]

    if query:
        q_lower = query.lower()
        if "speed of light" in q_lower or "299" in q_lower or "physics" in q_lower:
            return TEST_CASE_VALID
        if "empty" in q_lower or "zero" in q_lower or "12345" in q_lower:
            return TEST_CASE_EMPTY
        if "quantum" in q_lower or "rsa" in q_lower:
            return TEST_CASE_CONTRADICTORY

    return TEST_CASE_CONTRADICTORY
